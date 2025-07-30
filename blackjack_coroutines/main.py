import asyncio
from game_engine import GameEngine, create_players, initial_deal, dealer_turn, payout_winner, reset_for_new_round


async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

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
            
async def get_host_bet_input(prompt):
    """Get bet input from the host."""
    return await async_input(prompt)

async def get_host_action_input(prompt):
    """Get action input from the host."""
    return await async_input(prompt)

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

def display_game_state(game_state, player_name):
    """Display the current game state to the player."""
    phase = game_state.get('phase')
    round_number = game_state.get('round')
    print(f"\n[Game State] Phase: {phase} | Round: {round_number}")

    #Display players' information
    for player in game_state.get('players', []):
        name = player['name']
        chips = player['chips']
        hand = player['hand']
        current_bet = player['current_bet']
        if name == player_name:
            print(f"YOU ({name}) - Chips: {chips} | Hand: {hand} | Bet: {current_bet}")
        else:
            print(f"{name} - Chips: {chips} | Hand: {hand} | Bet: {current_bet}")

    #Display dealer's hand
    dealer_hand = game_state.get('dealer', {}).get('hand', '')
    print(f"Dealer's hand: {dealer_hand}")

    #Highlight when it's the player's turn
    if game_state.get('current_player') == player_name:
        print("\n*** IT'S YOUR TURN! ***")

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
    # elif mode == '2':
    #      await host_game()
    # elif mode == '3':
    #      await join_game()
    else:
        print("Invalid selection. Exiting.")

if __name__ == "__main__":
    asyncio.run(main())
    
#Dealer needs to not have his cards shown in the deal cards functions
#When it is dealers turn, it should show the hidden card first