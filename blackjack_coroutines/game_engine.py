import asyncio
from player import Player, Dealer
from blackjack_rules import *
from card import Card, Deck

def initial_deal(deck: Deck, players: list[Player], dealer: Dealer):
    """
    Deal two cards to each player and the dealer.
    - Players receive two cards each.
    - Dealer receives one card face up and one card face down.
    """
    for player in players:
        for _ in range(2):
            card = deck.deal_card()
            player.add_card(card)
    
    # Dealer gets one card face up
    dealer.add_card(deck.deal_card())
    
    # Dealer gets one card face down (not shown to players)
    dealer.add_card(deck.deal_card())

class GameEngine:
    def __init__(self):
        # Initialize the game engine with necessary components
        self.players: list[Player] = []
        self.dealer = Dealer()
        self.deck = Deck()
        self.current_round = 0
    
    def create_players(self, player_names: list[str]):
        """
        Create player instances from a list of names.
        - Receives a list of player names.
        - Initializes each player with a default chip count of 1000.
        - Returns a list of Player instances.
        """

        if not player_names:
            print("No player names provided.")
            return []
        
        if len(player_names) < 1:
            print("At least one player is required to start the game.")
            return []
        elif len(player_names) > 3:
            print("Maximum of 3 players allowed. Truncating to first 3 names.")
            player_names = player_names[:3]
        
        self.players = [Player(name) for name in player_names]
        print(f"Players created: {[player.name for player in self.players]}")
        return self.players

    def collect_bets(self):
        """Collect bets from all players before dealing cards."""
        for player in self.players:
            while True:
                try:
                    bet_amount = int(input(f"{player.name}, place your bet (1-{player.chips}): "))
                    placed = player.place_bet(bet_amount)
                    if placed and 1 <= bet_amount <= player.chips + bet_amount:
                        break
                except ValueError:
                    print("Please enter a valid number.")

    def display_game_state(self, hide_dealer_card=False):
        """
        Display the current game state, showing players' hands and the dealer's hand.
        - If hide_dealer_card is True, the dealer's first card is hidden.
        """

        print("\nCurrent Game State:")
        for player in self.players:
            print(f"{player.name}'s hand: {player.show_hand()}")
        
        if hide_dealer_card:
            print(f"Dealer's hand: {self.dealer.show_hand(hide_first=True)}")
        else:
            print(f"Dealer's hand: {self.dealer.show_hand()}")

    def check_natural_blackjacks(self):
        """
        Check if any player or the dealer has a natural blackjack (21 with two cards).
        - If a player has a blackjack, they win immediately.
        """
        for player in self.players:
            if is_blackjack(player.hand):
                print(f"{player.name} has a natural blackjack! They win!")
                player.chips += calculate_payout(player.place_bet(0), 'blackjack')
        
        if is_blackjack(self.dealer.hand):
            print("Dealer has a natural blackjack! All players lose their bets.")
            for player in self.players:
                player.chips -= player.place_bet(0)
        
        self.display_game_state(hide_dealer_card=True)

    def start_game(self, player_names: list[str]):
        print("Starting the Blackjack game...")
        
        if not player_names:
            print("No players provided. Game cannot start.")
            return
        
        # Shuffle the deck
        self.deck.shuffle()
        print("Deck shuffled.")

        # Create players using the dedicated method
        self.create_players(player_names)
        
        # Betting phase - each player places their bet
        self.collect_bets()
        
        # Deal initial cards to players and dealer
        initial_deal(self.deck, self.players, self.dealer)
        print("Initial cards dealt.")
        
        # Display initial game state
        self.display_game_state(hide_dealer_card=True)
        
        # Check for natural blackjacks
        self.check_natural_blackjacks()
        
        # Set up for player turns
        self.current_round += 1
        print(f"Round {self.current_round} begins!")