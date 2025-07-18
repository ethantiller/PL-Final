import asyncio
from game_engine import GameEngine

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
    engine = GameEngine()
    player_names = (await async_input("Enter player names (comma separated): ")).split(',')
    player_names = [name.strip() for name in player_names if name.strip()]
    await engine.start_game(player_names)

if __name__ == "__main__":
    asyncio.run(start_game())
    
# Dealer needs to not have his cards shown in the deal cards functions
# When it is dealers turn, it should show the hidden card first