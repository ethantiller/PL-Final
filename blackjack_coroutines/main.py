from game_engine import GameEngine

def start_game():
    """
    Start the blackjack game.
    - Initializes the game engine.
    - Creates players and collects bets.
    - Deals initial cards to players and dealer.
    """
    engine = GameEngine()
    
    player_names = input("Enter player names (comma separated): ").split(',')
    player_names = [name.strip() for name in player_names if name.strip()]
    
    engine.start_game(player_names)
    

if __name__ == "__main__":
    start_game()
    
# Dealer needs to not have his cards shown in the deal cards functions
# When it is dealers turn, it should show the hidden card first