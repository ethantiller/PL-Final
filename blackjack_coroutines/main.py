import asyncio
import sys
import os
from game_engine import GameEngine, TerminalGameIO

async def async_input(prompt: str) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt)

async def start_game():
    """
    Start the blackjack game.
    - Initializes the game engine.
    - Creates players and collects bets.
    - Deals initial cards to players and dealer.
    """
    game_io = TerminalGameIO()
    engine = GameEngine(game_io=game_io)
    player_names = (await game_io.input("Enter player names (comma separated): ")).split(',')
    player_names = [name.strip() for name in player_names if name.strip()]
    await engine.start_game(player_names)

if __name__ == "__main__":
    async def startup_prompt():
        print("Select mode:")
        print("1. Single-terminal (local)")
        print("2. Host a game (server)")
        print("3. Join a game (client, not implemented)")
        mode = await async_input("Enter 1, 2, or 3: ")
        mode = mode.strip()
        if mode == '1':
            await start_game()
        elif mode == '2':
            # Run the server
            server_path = os.path.join(os.path.dirname(__file__), 'server', 'server.py')
            print("Starting server...")
            os.system(f'{sys.executable} "{server_path}"')
        elif mode == '3':
            # Run the client
            client_path = os.path.join(os.path.dirname(__file__), 'server', 'client.py')
            print("Starting client...")
            os.system(f'{sys.executable} "{client_path}"')
        else:
            print("Invalid selection. Exiting.")
    asyncio.run(startup_prompt())
    
# Dealer needs to not have his cards shown in the deal cards functions
# When it is dealers turn, it should show the hidden card first