import asyncio
from game_engine import GameEngine, create_players, initial_deal, dealer_turn, payout_winner, reset_for_new_round
from network import AsyncServer, AsyncClient
import json
from blackjack_rules import is_bust
import functools

async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def networked_bet_input(server, player_name):
    """Send a bet request to the client and wait for response."""
    writer = None
    for w, n in server.clients.items():
        if n == player_name:
            writer = w
            break
    if writer is None:
        raise RuntimeError(f"No connection for player {player_name}")
    await server.send_msg(writer, {"type": "bet_request"})
    while True:
        msg = await server.recv_msg(writer._transport._protocol._stream_reader)
        if msg and msg.get("type") == "bet_response":
            return msg.get("amount")

async def networked_action_input(server, player_name, prompt):
    """Send an action request to the client and wait for response."""
    writer = None
    for w, n in server.clients.items():
        if n == player_name:
            writer = w
            break
    if writer is None:
        raise RuntimeError(f"No connection for player {player_name}")
    await server.send_msg(writer, {"type": "action_request", "prompt": prompt})
    while True:
        msg = await server.recv_msg(writer._transport._protocol._stream_reader)
        if msg and msg.get("type") == "action_response":
            return msg.get("action")

def serialize_game_state(engine, phase, current_player=None):
    """Serialize the game state for broadcasting to clients."""
    # Determine if dealer cards should be hidden (only in certain phases)
    hide_dealer_cards = phase in ['betting', 'player_action']
    
    # Special handling for dealing phase - show at least one card
    dealer_hand = ""
    if phase == 'dealing' and len(engine.dealer.hand) >= 1:
        dealer_hand = f"{engine.dealer.hand[0]} | [Hidden]" if len(engine.dealer.hand) > 1 else str(engine.dealer.hand[0])
    else:
        dealer_hand = engine.dealer.show_hand(hide_first=hide_dealer_cards)
        
    return {
        'type': 'state',
        'phase': phase,
        'players': [
            {
                'name': p.name,
                'chips': p.chips,
                'hand': p.show_hand(),
                'current_bet': p.current_bet
            } for p in engine.players
        ],
        'dealer': {
            'hand': dealer_hand
        },
        'current_player': current_player,
        'round': engine.current_round
    }

async def broadcast_state(server, engine, phase, current_player=None):
    state = serialize_game_state(engine, phase, current_player)
    for w in list(server.clients.keys()):
        try:
            await server.send_msg(w, state)
        except Exception as e:
            print(f"[Server] Failed to send state: {e}")

async def start_multiplayer_game(host_name, server):
    player_names = [host_name] + list(server.clients.values())
    print(f"[Host] Starting multiplayer game with players: {player_names}")
    engine = GameEngine()
    # Input strategies
    async def host_bet_input(prompt):
        return await async_input(prompt)
    async def host_action_input(prompt):
        return await async_input(prompt)
    async def remote_bet_input(player_name):
        writer = next(w for w, n in server.clients.items() if n == player_name)
        await server.send_msg(writer, {"type": "bet_request"})
        queue = server.get_response_queue(player_name)
        while True:
            msg = await queue.get()
            if msg and msg.get("type") == "bet_response":
                return msg.get("amount")
    async def remote_action_input(player_name, prompt):
        writer = next(w for w, n in server.clients.items() if n == player_name)
        await server.send_msg(writer, {"type": "action_request", "prompt": prompt})
        queue = server.get_response_queue(player_name)
        while True:
            msg = await queue.get()
            if msg and msg.get("type") == "action_response":
                return msg.get("action")
    # Helper to bind player name
    def make_remote_bet_input(n):
        return lambda prompt: remote_bet_input(n)
    def make_remote_action_input(n):
        return lambda prompt: remote_action_input(n, prompt)
    # Build input strategy dicts
    bet_input_strategy = {}
    action_input_strategy = {}
    for name in player_names:
        if name == host_name:
            bet_input_strategy[name] = host_bet_input
            action_input_strategy[name] = host_action_input
        else:
            bet_input_strategy[name] = make_remote_bet_input(name)
            action_input_strategy[name] = make_remote_action_input(name)
    # Start game loop
    engine.deck.shuffle()
    engine.current_round = 0  # Initialize round counter
    engine.players = create_players(player_names)
    while True:
        # Increment round number at the start of each round
        engine.current_round += 1
        print(f"\nStarting round {engine.current_round}")
        
        # Betting phase
        await broadcast_state(server, engine, 'betting')
        for player in engine.players:
            # Check if player is out of chips and give them some
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
            
            await broadcast_state(server, engine, 'betting', current_player=player.name)
        # Dealing phase
        engine.deck.shuffle()
        await initial_deal(engine.deck, engine.players, engine.dealer)
        await broadcast_state(server, engine, 'dealing')
        # Player actions
        for player in engine.players:
            while not player.mustStand:
                await broadcast_state(server, engine, 'player_action', current_player=player.name)
                valid_actions = ['hit', 'stand']  # Simplified for now
                prompt = f"{player.name}, choose your action ({', '.join(valid_actions)}): "
                action = await action_input_strategy[player.name](prompt)
                if action == 'hit':
                    await player.handle_hit(engine.deck)
                    if is_bust(player.hand):
                        player.mustStand = True
                elif action == 'stand':
                    player.handle_stand()
                    break
        # Dealer turn
        await dealer_turn(engine.dealer, engine.deck)
        await broadcast_state(server, engine, 'dealer')
        # Payout/results
        payout_winner(engine.players, engine.dealer)
        
        # Handle zero chips
        for player in engine.players:
            if player.chips == 0:
                player.chips += 100
                print(f"{player.name} is out of chips! Adding 100 chips to keep playing.")
                
        await broadcast_state(server, engine, 'results')
        
        # Ask to continue
        continue_game = await async_input("Do you want to play another round? (yes/no): ")
        if continue_game.strip().lower() != 'yes':
            break
            
        # Reset for new round - moved here to ensure it happens at the right time
        engine.dealer.reset_hand()
        for p in engine.players:
            p.reset_hand()
    print("[Host] Multiplayer game finished.")

async def host_game():
    """
    Host game logic: prompt for name, start server, accept clients, collect names, allow host to type 'start' to begin.
    """
    host_name = await async_input("Enter your name (host): ")
    server = AsyncServer()
    player_names = [host_name.strip()]  # Host is always first
    print("[Host] Starting server... Waiting for players to join.")

    # Start server in background
    server_task = asyncio.create_task(server.start())

    # Simple lobby loop: print connected players, allow 'start' to begin
    try:
        while True:
            print(f"\nCurrent players: {player_names + list(server.clients.values())}")
            cmd = await async_input("Type 'start' to begin or press Enter to refresh: ")
            if cmd.strip().lower() == 'start':
                print("[Host] Starting game...")
                await start_multiplayer_game(host_name, server)
                break
    finally:
        if server.server is not None:
            server.server.close()
            await server.server.wait_closed()
        server_task.cancel()

async def join_game():
    """
    Client flow: prompt for IP/port and name, connect to server, send name, handle lobby and game state updates.
    """
    name = await async_input("Enter your name: ")
    host = await async_input("Enter server IP (default 127.0.0.1): ") or "127.0.0.1"
    port_str = await async_input("Enter server port (default 8765): ") or "8765"
    try:
        port = int(port_str)
    except ValueError:
        print("Invalid port. Exiting.")
        return
    client = AsyncClient(host, port)
    try:
        await client.connect()
        await client.send_msg({"type": "join", "name": name.strip()})
        print("[Client] Waiting for host to start the game...")
        while True:
            msg = await client.recv_msg()
            if msg is None:
                print("[Client] Disconnected from server.")
                break
            msg_type = msg.get("type")
            if msg_type == "join_ack":
                players = msg.get("players", [])
                print(f"[Lobby] Current players: {players}")
            elif msg_type == "start":
                print("[Client] Game is starting!")
            elif msg_type == "state":
                phase = msg.get('phase')
                round_num = msg.get('round')
                print(f"\n[Game State] Phase: {phase} | Round: {round_num}")
                
                # Display players' information
                for p in msg.get('players', []):
                    player_name = p['name']
                    chips = p['chips']
                    hand = p['hand']
                    bet = p['current_bet']
                    
                    # Format for better readability
                    if player_name == name:
                        print(f"YOU ({player_name}) - Chips: {chips} | Hand: {hand} | Bet: {bet}")
                    else:
                        print(f"{player_name} - Chips: {chips} | Hand: {hand} | Bet: {bet}")
                
                # Display dealer's hand
                dealer = msg.get('dealer', {})
                dealer_hand = dealer.get('hand', '')
                print(f"Dealer's hand: {dealer_hand}")
                
                # Highlight when it's the player's turn
                if msg.get('current_player') == name:
                    print("\n*** IT'S YOUR TURN! ***")
            elif msg_type == "bet_request":
                while True:
                    try:
                        bet = int(await async_input("Place your bet: "))
                        break
                    except ValueError:
                        print("Please enter a valid number.")
                await client.send_msg({"type": "bet_response", "amount": bet})
            elif msg_type == "action_request":
                prompt = msg.get("prompt", "Choose your action: ")
                action = await async_input(prompt)
                await client.send_msg({"type": "action_response", "action": action})
            elif msg_type == "error":
                print(f"[Error] {msg.get('message')}")
            else:
                print(f"[Client] Received: {msg}")
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