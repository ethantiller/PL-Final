from player import Player, Dealer
from blackjack_rules import *
from card import Deck

def check_natural_blackjacks(players: list[Player], dealer: Dealer):
    """
    Check if any player or the dealer has a natural blackjack (21 with two cards).
    - If a player has a blackjack, they win immediately.
    """
    dealer_has_blackjack = is_blackjack(dealer.hand)
    
    for player in players:
        if is_blackjack(player.hand):
            if dealer_has_blackjack:
                # Push - return bet
                payout = calculate_payout(player.current_bet, 'push')
                player.chips += payout
                print(f"{player.name} has blackjack, but dealer also has blackjack. Push!")
            else:
                # Player blackjack wins
                payout = calculate_payout(player.current_bet, 'blackjack')
                player.chips += payout
                print(f"{player.name} has a natural blackjack! Wins {payout} chips!")
        elif dealer_has_blackjack:
            # Dealer blackjack, player loses (bet already deducted)
            print(f"{player.name} loses to dealer's blackjack.")
    
    if dealer_has_blackjack:
        print("Dealer has a natural blackjack!")

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

def create_players(player_names: list[str]):
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
    
    players = [Player(name) for name in player_names]
    print(f"Players created: {[player.name for player in players]}")
    return players

def collect_bets(players: list[Player]):
    """Collect bets from all players before dealing cards."""
    for player in players:
        while True:
            try:
                bet_amount = int(input(f"{player.name}, place your bet (1-{player.chips}): "))
                if player.place_bet(bet_amount):
                    break
            except ValueError:
                print("Please enter a valid number.")

def display_game_state(players: list[Player], dealer: Dealer, hide_dealer_card=False):
    """
    Display the current game state, showing players' hands and the dealer's hand.
    - If hide_dealer_card is True, the dealer's first card is hidden.
    """

    print("\nCurrent Game State:")
    for player in players:
        print(f"{player.name}'s hand: {player.show_hand()}")
    
    if hide_dealer_card:
        print(f"Dealer's hand: {dealer.show_hand(hide_first=True)}")
    else:
        print(f"Dealer's hand: {dealer.show_hand()}")

def select_first_player(players: list[Player]):
    """
    Select the first player to act based on the order of players.
    - Returns the first player in the list.
    """
    if not players:
        print("No players available to select.")
        return None
    return players[0]

def get_player_action(player: Player, valid_actions: list[str]):
    """
    Get the player's action based on valid actions.
    - Valid actions include 'hit', 'stand', or 'double' if applicable.
    - Returns the player's chosen action.
    """
    while True:
        action = input(f"{player.name}, choose your action ({', '.join(valid_actions)}): ").strip().lower()
        if action in valid_actions:
            return action
        else:
            print(f"Invalid action. Please choose from {', '.join(valid_actions)}.")
            
def player_turn(player: Player, dealer: Dealer, deck: Deck):
    """
    Handle the player's turn by allowing them to hit, stand, or double down.
    - Continues until the player stands or goes bust.
    """
    valid_actions = get_valid_actions(player.hand, dealer.hand)
    while not player.mustStand:
        action = get_player_action(player, valid_actions)
        
        if action == 'hit':
            player.handle_hit(deck)
            if is_bust(player.hand):
                print(f"{player.name} is bust! They lose this round.")
                player.mustStand = True
        elif action == 'stand':
            player.handle_stand()
            break
        elif action == 'double':
            player.handle_double_down(deck)
            if is_bust(player.hand):
                print(f"{player.name} is bust after doubling down! They lose this round.")
                player.mustStand = True
                
def dealer_turn(dealer: Dealer, deck: Deck):
    """
    Handle the dealer's turn based on standard Blackjack rules.
    - Dealer hits until their hand value is 17 or higher.
    """
    while dealer.should_hit():
        dealer.handle_hit(deck)
        print(f"Dealer hits: {dealer.show_hand()}")
    print(f"Dealer stands with hand: {dealer.show_hand()}")
    
def payout_winner(players: list[Player], dealer: Dealer):
    """
    Determine the winner of the round and payout accordingly.
    - Compares each player's hand against the dealer's hand.
    - Updates player chips based on the game result.
    """
    results = determine_winners([player.hand for player in players], players, dealer.hand)
    
    for player, result in zip(players, results):
        payout = calculate_payout(player.current_bet, result)
        player.chips += payout
        
        if result == 'win':
            print(f"{player.name} wins! Receives {payout} chips.")
        elif result == 'blackjack':
            print(f"{player.name} has blackjack! Receives {payout} chips.")
        elif result == 'push':
            print(f"{player.name} pushes. Receives {payout} chips back.")
        elif result == 'lose':
            print(f"{player.name} loses. No payout.")
        
        print(f"{player.name} now has {player.chips} chips.")

def reset_for_new_round(players: list[Player], dealer: Dealer):
    """
    Reset hands and prepare for a new round.
    """
    for player in players:
        player.reset_hand()
    dealer.reset_hand()
    print("All hands reset for new round.")

class GameEngine:
    def __init__(self):
        # Initialize the game engine with necessary components
        self.players: list[Player] = []
        self.dealer = Dealer()
        self.deck = Deck()
        self.current_round = 0
    
    def start_game(self, player_names: list[str]):
        print("Starting the Blackjack game...")
        
        if not player_names:
            print("No players provided. Game cannot start.")
            return
        
        # Shuffle the deck
        self.deck.shuffle()
        print("Deck shuffled.")

        # Create players using the dedicated method
        self.players = create_players(player_names)
        
        # Betting phase - each player places their bet
        collect_bets(self.players)
        
        # Deal initial cards to players and dealer
        initial_deal(self.deck, self.players, self.dealer)
        print("Initial cards dealt.")
        
        # Display initial game state
        display_game_state(self.players, self.dealer, hide_dealer_card=True)
        
        # Check for natural blackjacks
        check_natural_blackjacks(self.players, self.dealer)
        
        # Set up for player turns
        self.current_round += 1
        print(f"Round {self.current_round} begins!")