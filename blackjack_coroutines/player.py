from card import Card, Deck
from blackjack_rules import calculate_hand_value

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
        
    def place_bet(self, amount):
        """
        Attempt to place a bet by deducting chips.
        Args:
            amount (int): The amount to bet.
        Returns:
            None
        """
        if amount > self.chips:
            print(f"{self.name} does not have enough chips to bet {amount}.")
        elif amount <= 0:
            print(f"{self.name} cannot bet {amount}. Bet must be positive.")
        else:
            self.chips -= amount
            print(f"{self.name} bets {amount}. Remaining chips: {self.chips}")
        return amount
        
    def add_card(self, card):
        """
        Add a card to the player's hand.
        Args:
            card (Card): The card to add.
        Returns:
            None
        """
        self.hand.append(card)
        print(f"{self.name} receives {card}. Current hand: {self.calcuate_hand_value()}")
        
        
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
        print(f"{self.name}'s hand has been reset.")

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
        return self.calculate_hand_value() < 17
    
    def show_hidden_card(self):
        """
        Return a string representation of the dealer's hand, hiding the first card.
        Returns:
            str: The dealer's hand with the first card hidden.
        """
        return self.show_hand(hide_first=True)
