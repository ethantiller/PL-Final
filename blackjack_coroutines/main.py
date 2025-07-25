import asyncio
from game_engine import GameEngine, create_players, initial_deal, dealer_turn, payout_winner, reset_for_new_round
from network import AsyncServer, AsyncClient
from blackjack_rules import is_bust

async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def networked_bet_input(server, player_name):
    """Send a bet request to the client and wait for response."""
    client_writer = None
    for writer, connected_player_name in server.clients.items():
        if connected_player_name == player_name:
            client_writer = writer
            break
    if client_writer is None:
        raise RuntimeError(f"No connection for player {player_name}")
    await server.send_message(client_writer, {"type": "bet_request"})
    while True:
        message = await server.recv_message(client_writer._transport._protocol._stream_reader)
        if message and message.get("type") == "bet_response":
            return message.get("amount")

async def networked_action_input(server, player_name, prompt):
    """Send an action request to the client and wait for response."""
    client_writer = None
    for writer, connected_player_name in server.clients.items():
        if connected_player_name == player_name:
            client_writer = writer
            break
    if client_writer is None:
        raise RuntimeError(f"No connection for player {player_name}")
    await server.send_message(client_writer, {"type": "action_request", "prompt": prompt})
    while True:
        message = await server.recv_message(client_writer._transport._protocol._stream_reader)
        if message and message.get("type") == "action_response":
            return message.get("action")

def serialize_game_state(game_engine, game_phase, current_player=None):
    """Serialize the game state for broadcasting to clients."""
    # Determine if dealer cards should be hidden (only in certain phases)
    hide_dealer_cards = game_phase in ['betting', 'player_action']
    
    # Special handling for dealing phase - show at least one card
    dealer_hand_representation = ""
    if game_phase == 'dealing' and len(game_engine.dealer.hand) >= 1:
        dealer_hand_representation = f"{game_engine.dealer.hand[0]} | [Hidden]" if len(game_engine.dealer.hand) > 1 else str(game_engine.dealer.hand[0])
    else:
        dealer_hand_representation = game_engine.dealer.show_hand(hide_first=hide_dealer_cards)
        
    return {
        'type': 'state',
        'phase': game_phase,
        'players': [
            {
                'name': player.name,
                'chips': player.chips,
                'hand': player.show_hand(),
                'current_bet': player.current_bet
            } for player in game_engine.players
        ],
        'dealer': {
            'hand': dealer_hand_representation
        },
        'current_player': current_player,
        'round': game_engine.current_round
    }

async def broadcast_state(server, game_engine, game_phase, current_player=None):
    serialized_state = serialize_game_state(game_engine, game_phase, current_player)
    for client_writer in list(server.clients.keys()):
        try:
            await server.send_message(client_writer, serialized_state)
        except Exception as error:
            print(f"[Server] Failed to send state: {error}")

async def get_remote_bet_input(server, player_name):
    """Get bet input from a remote player."""
    client_writer = next(writer for writer, connected_player_name in server.clients.items() if connected_player_name == player_name)
    await server.send_message(client_writer, {"type": "bet_request"})
    response_queue = server.get_response_queue(player_name)
    while True:
        message = await response_queue.get()
        if message and message.get("type") == "bet_response":
            return message.get("amount")

async def get_remote_action_input(server, player_name, action_prompt):
    """Get action input from a remote player."""
    client_writer = next(writer for writer, connected_player_name in server.clients.items() if connected_player_name == player_name)
    await server.send_message(client_writer, {"type": "action_request", "prompt": action_prompt})
    response_queue = server.get_response_queue(player_name)
    while True:
        message = await response_queue.get()
        if message and message.get("type") == "action_response":
            return message.get("action")

async def get_host_bet_input(prompt):
    """Get bet input from the host."""
    return await async_input(prompt)

async def get_host_action_input(prompt):
    """Get action input from the host."""
    return await async_input(prompt)

def create_remote_bet_input_function(server, player_name):
    """Create a function to get bet input for a specific remote player."""
    return lambda prompt: get_remote_bet_input(server, player_name)

def create_remote_action_input_function(server, player_name):
    """Create a function to get action input for a specific remote player."""
    return lambda prompt: get_remote_action_input(server, player_name, prompt)

def setup_input_strategies(host_name, server, player_names):
    """Set up input strategies for bets and actions."""
    bet_input_strategy = {}
    action_input_strategy = {}

    for player_name in player_names:
        if player_name == host_name:
            bet_input_strategy[player_name] = get_host_bet_input
            action_input_strategy[player_name] = get_host_action_input
        else:
            bet_input_strategy[player_name] = create_remote_bet_input_function(server, player_name)
            action_input_strategy[player_name] = create_remote_action_input_function(server, player_name)

    return bet_input_strategy, action_input_strategy

async def play_game_round(game_engine, server, bet_input_strategy, action_input_strategy):
    """Play a single round of the game."""
    game_engine.current_round += 1
    print(f"\nStarting round {game_engine.current_round}")

    # Betting phase
    await broadcast_state(server, game_engine, 'betting')
    for player in game_engine.players:
        if player.chips == 0:
            player.chips += 100
            print(f"{player.name} is out of chips! Adding 100 chips to keep playing.")

        while True:
            bet = await bet_input_strategy[player.name](f"{player.name}, place your bet (1-{player.chips}): ")
            try:
                bet_amount = int(bet)
                if bet_amount <= 0:
                    print(f"{player.name} cannot bet {bet_amount}. Bet must be positive.")
                    continue
                if bet_amount > player.chips:
                    print(f"{player.name} does not have enough chips to bet {bet_amount}.")
                    continue
                player.chips -= bet_amount
                player.current_bet = bet_amount
                print(f"{player.name} bets {bet_amount}. Remaining chips: {player.chips}")
                break
            except ValueError:
                print(f"Invalid bet from {player.name}. Please enter a number.")

        await broadcast_state(server, game_engine, 'betting', current_player=player.name)

    # Dealing phase
    game_engine.deck.shuffle()
    await initial_deal(game_engine.deck, game_engine.players, game_engine.dealer)
    await broadcast_state(server, game_engine, 'dealing')

    # Player actions
    for player in game_engine.players:
        while not player.mustStand:
            await broadcast_state(server, game_engine, 'player_action', current_player=player.name)
            valid_actions = ['hit', 'stand']
            action_prompt = f"{player.name}, choose your action ({', '.join(valid_actions)}): "
            action = await action_input_strategy[player.name](action_prompt)
            if action == 'hit':
                await player.handle_hit(game_engine.deck)
                if is_bust(player.hand):
                    player.mustStand = True
            elif action == 'stand':
                player.handle_stand()
                break

    # Dealer turn
    await dealer_turn(game_engine.dealer, game_engine.deck)
    await broadcast_state(server, game_engine, 'dealer')

    # Payout/results
    payout_winner(game_engine.players, game_engine.dealer)

    # Handle zero chips
    for player in game_engine.players:
        if player.chips == 0:
            player.chips += 100
            print(f"{player.name} is out of chips! Adding 100 chips to keep playing.")

    await broadcast_state(server, game_engine, 'results')

async def start_multiplayer_game(host_name, server):
    """Start the multiplayer game with the given host and server."""
    player_names = [host_name] + list(server.clients.values())
    print(f"[Host] Starting multiplayer game with players: {player_names}")
    
    # Send start message to all clients to transition them from lobby to game
    for client_writer in list(server.clients.keys()):
        try:
            await server.send_message(client_writer, {"type": "start"})
        except Exception as error:
            print(f"[Server] Failed to send start message: {error}")
            
    game_engine = GameEngine()

    # Set up input strategies
    bet_input_strategy, action_input_strategy = setup_input_strategies(host_name, server, player_names)

    # Initialize game engines
    game_engine.deck.shuffle()
    game_engine.current_round = 0
    game_engine.players = create_players(player_names)

    # Game loop
    while True:
        await play_game_round(game_engine, server, bet_input_strategy, action_input_strategy)

        # Ask to continue
        continue_game = await async_input("Do you want to play another round? (yes/no): ")
        if continue_game.strip().lower() != 'yes':
            break

        # Reset for new round
        game_engine.dealer.reset_hand()
        for player in game_engine.players:
            player.reset_hand()

    print("[Host] Multiplayer game finished.")

async def initialize_host_game():
    """
    This function initializes the host game function by receiving the host's name and starting the server.
    """
    host_name = await async_input("Enter your name (host): ")
    server = AsyncServer()
    player_names = [host_name.strip()] 
    print("[Host] Starting server... Waiting for players to join.")

    # Start server in background
    server_task = asyncio.create_task(server.start())

    return host_name, server, player_names, server_task

async def host_game():
    """
    Host game logic: prompt for name, start server, accept clients, collect names, allow host to type 'start' to begin.
    """
    host_name, server, player_names, server_task = await initialize_host_game()

    # Simple lobby loop: print connected players, allow 'start' to begin
    try:
        while True:
            print(f"\nCurrent players: {player_names + list(server.clients.values())}")
            command = await async_input("Type 'start' to begin or press Enter to refresh: ")
            if command.strip().lower() == 'start':
                print("[Host] Starting game...")
                await start_multiplayer_game(host_name, server)
                break
    finally:
        # If the server exists, close it
        if server.server is not None:
            server.server.close()
            await server.server.wait_closed()
        
        # If the server task is running, cancel it
        server_task.cancel()
async def handle_lobby_messages(client, player_name):
    """Handle lobby messages from the server."""
    while True:
        message = await client.recv_message()
        if message is None:
            print("[Client] Disconnected from server.")
            break
        
        message_type = message.get("type")
        if message_type == "join_ack":
            players_in_lobby = message.get("players", [])
            print(f"[Lobby] Current players: {players_in_lobby}")
        elif message_type == "start":
            print("[Client] Game is starting!")
            return  # Exit lobby phase and transition to game phase
        elif message_type == "state":
            # If we receive state messages in the lobby, the server might have skipped sending 'start'
            # Let's consider this as an implicit game start
            print("[Client] Game is starting! (Implicitly detected from state message)")
            return
        else:
            print(f"[Client] Unexpected message in lobby: {message}")

async def handle_game_state_updates(client, player_name):
    """Handle game state updates and player interactions."""
    while True:
        message = await client.recv_message()
        if message is None:
            print("[Client] Disconnected from server.")
            break
        message_type = message.get("type")
        if message_type == "state":
            display_game_state(message, player_name)
        elif message_type == "bet_request":
            await handle_bet_request(client)
        elif message_type == "action_request":
            await handle_action_request(client, message)
        elif message_type == "error":
            print(f"[Error] {message.get('message')}")
        else:
            print(f"[Client] Received unexpected message: {message}")

def display_game_state(game_state, player_name):
    """Display the current game state to the player."""
    phase = game_state.get('phase')
    round_number = game_state.get('round')
    print(f"\n[Game State] Phase: {phase} | Round: {round_number}")

    # Display players' information
    for player in game_state.get('players', []):
        name = player['name']
        chips = player['chips']
        hand = player['hand']
        current_bet = player['current_bet']
        if name == player_name:
            print(f"YOU ({name}) - Chips: {chips} | Hand: {hand} | Bet: {current_bet}")
        else:
            print(f"{name} - Chips: {chips} | Hand: {hand} | Bet: {current_bet}")

    # Display dealer's hand
    dealer_hand = game_state.get('dealer', {}).get('hand', '')
    print(f"Dealer's hand: {dealer_hand}")

    # Highlight when it's the player's turn
    if game_state.get('current_player') == player_name:
        print("\n*** IT'S YOUR TURN! ***")

async def handle_bet_request(client):
    """Handle a bet request from the server."""
    while True:
        try:
            bet_amount = int(await async_input("Place your bet: "))
            break
        except ValueError:
            print("Please enter a valid number.")
    await client.send_message({"type": "bet_response", "amount": bet_amount})

async def handle_action_request(client, action_message):
    """Handle an action request from the server."""
    action_prompt = action_message.get("prompt", "Choose your action: ")
    action = await async_input(action_prompt)
    await client.send_message({"type": "action_response", "action": action})

async def join_game():
    """
    Client flow: prompt for IP/port and name, connect to server, send name, handle lobby and game state updates.
    """
    player_name = await async_input("Enter your name: ")
    server_ip = await async_input("Enter server IP (default 127.0.0.1): ") or "127.0.0.1"
    port_input = await async_input("Enter server port (default 8765): ") or "8765"
    try:
        server_port = int(port_input)
    except ValueError:
        print("Invalid port. Exiting.")
        return

    client = AsyncClient(server_ip, server_port)
    try:
        await client.connect()
        await client.send_message({"type": "join", "name": player_name.strip()})
        print("[Client] Waiting for host to start the game...")
        await handle_lobby_messages(client, player_name)
        await handle_game_state_updates(client, player_name)
    except Exception as error:
        print(f"[Client] Error: {error}")

async def start_local_game():
    """
    Start the blackjack game in local (terminal) mode.
    """
    engine = GameEngine()
    player_names = (await async_input("Enter player names (comma separated): ")).split(',')
    player_names = [name.strip() for name in player_names if name.strip()]
    await engine.start_game(player_names)

async def main():
    print("Welcome to Blackjack!")
    print("Select mode:")
    print("1. Play locally in terminal")
    print("2. Host a game on local network")
    print("3. Join a game on local network")
    mode = await async_input("Enter 1, 2, or 3: ")
    if mode == '1':
        await start_local_game()
    elif mode == '2':
        await host_game()
    elif mode == '3':
        await join_game()
    else:
        print("Invalid selection. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())