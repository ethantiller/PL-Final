from card import Card, Deck
from blackjack_rules import calculate_hand_value
import time

class Player:
    def __init__(self, name, chips=1000):
        """
        Initialize a Player instance.
        Args:
            name (str): The player's name.
            chips (int, optional): The starting number of chips. Defaults to 1000.
        """
        self.name = name
        self.chips = chips
        self.hand = []
        self.mustStand = False
        self.current_bet = 0
        
    def place_bet(self, amount):
        """
        Attempt to place a bet by deducting chips.
        Args:
            amount (int): The amount to bet.
        Returns:
            bool: True if bet was placed successfully, False otherwise.
        """
        if amount > self.chips:
            print(f"{self.name} does not have enough chips to bet {amount}.")
            return False
        elif amount <= 0:
            print(f"{self.name} cannot bet {amount}. Bet must be positive.")
            return False
        else:
            self.chips -= amount
            self.current_bet = amount
            print(f"{self.name} bets {amount}. Remaining chips: {self.chips}")
            return True
        
    def add_card(self, card):
        """
        Add a card to the player's hand.
        Args:
            card (Card): The card to add.
        Returns:
            None
        """
        self.hand.append(card)
        
        # Simulate a delay for realism
        time.sleep(0.5)
        print(f"{self.name} receives card: {card}. Current hand: {self.show_hand()}, value: {calculate_hand_value(self.hand)}")
        
    def show_hand(self, hide_first=False):
        """
        Return a string representation of the player's hand.
        Args:
            hide_first (bool, optional): If True, hides the first card (for dealer). Defaults to False.
        Returns:
            str: The hand as a string.
        """
        if hide_first and self.hand:
            return f"[Hidden], {', '.join(str(card) for card in self.hand[1:])}"
        else:
            return ', '.join(str(card) for card in self.hand)
        
    def reset_hand(self):
        """
        Reset the player's hand for a new round.
        Returns:
            None
        """
        self.hand = []
        self.mustStand = False
        self.current_bet = 0
        print(f"{self.name}'s hand has been reset.")
        
    def handle_hit(self, deck: Deck):
        """
        Handle the player's action to hit (draw a card).
        """
        card = deck.deal_card()
        if card:
            self.add_card(card)
        else:
            print("No more cards to deal.")
    
    def handle_stand(self):
        """
        Handle the player's action to stand (no more cards).
        """
        print(f"{self.name} stands with hand value: {calculate_hand_value(self.hand)}")
    
    def handle_double_down(self, deck: Deck):
        """
        Handle the player's action to double down.
        - Doubles the bet and takes exactly one more card.
        """
        if self.chips >= self.current_bet:
            self.chips -= self.current_bet
            self.current_bet *= 2
            print(f"{self.name} doubles down! New bet: {self.current_bet}")
            card = deck.deal_card()
            if card:
                self.add_card(card)
                self.mustStand = True
                print(f"{self.name} receives one card and must stand.")
            else:
                print("No more cards to deal.")
        else:
            print(f"{self.name} doesn't have enough chips to double down.")
            
    def zero_chips(self):
        """
        If the player has no chips left, it will add 100 chips to keep them in the game.
        """
        if self.chips == 0:
            self.chips += 100
            print(f"{self.name} is out of chips! Adding 100 chips to keep playing.")

class Dealer(Player):

    def __init__(self):
        super().__init__(name="Dealer")
        self.hand = []
    
    def should_hit(self):
        """
        Determine if the dealer should hit based on standard Blackjack rules.
        Returns:
            bool: True if the dealer should hit, False otherwise.
        """
        return calculate_hand_value(self.hand) <= 17
    
    def add_hidden_card(self, card):
        self.hand.append(card)
        
        # Simulate a delay for realism
        time.sleep(0.5)
        print("Dealer receives a hidden card.")
    
    def show_hidden_card(self):
        """
        Return a string representation of the dealer's hand, hiding the first card.
        Returns:
            str: The dealer's hand with the first card hidden.
        """
        return self.show_hand(hide_first=True)
