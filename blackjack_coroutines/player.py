from card import Card, Deck

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
        self.hand = []  # List to hold player's cards
        pass
        
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
        pass
        
    def add_card(self, card):
        """
        Add a card to the player's hand.

        Args:
            card (Card): The card to add.

        Returns:
            None
        """
        self.hand.append(card)
        print(f"{self.name} receives {card}. Current hand: {self.show_hand()}")
        pass
        
    def hand_value(self):
        """
        Calculate the total value of the player's hand, handling Aces as 1 or 11.

        Returns:
            int: The best hand value.
        """
        total = 0
        aces = 0

        for card in self.hand:
            total += card.value()
            if card.rank == 'A':
                aces += 1
        pass

        # Add best Ace handling
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total
        
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
        pass
        
    def has_blackjack(self):
        """
        Check if the player has a natural blackjack (an Ace and a 10-value card).

        Returns:
            bool: True if the player has blackjack, False otherwise.
        """
        if len(self.hand) == 2 and self.hand_value() == 21:
            return True
        pass
        
    def is_bust(self):
        """
        Check if the player's hand value exceeds 21.

        Returns:
            bool: True if the player is bust, False otherwise.
        """
        if self.hand_value() > 21:
            print(f"{self.name} is bust with hand value {self.hand_value()}.")
            return True
        pass
        
    def reset_hand(self):
        """
        Reset the player's hand for a new round.

        Returns:
            None
        """
        self.hand = []
        print(f"{self.name}'s hand has been reset.")
        pass

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
        pass
        
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
        pass
        
    def add_card(self, card):
        """
        Add a card to the player's hand.
        Args:
            card (Card): The card to add.
        Returns:
            None
        """
        self.hand.append(card)
        print(f"{self.name} receives {card}. Current hand: {self.show_hand()}")
        pass
        
    def hand_value(self):
        """
        Calculate the total value of the player's hand, handling Aces as 1 or 11
        Returns:
            int: The best hand value.
        """
        total = 0
        aces = 0

        for card in self.hand:
            total += card.value()
            if card.rank == 'A':
                aces += 1
        pass

        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total
        
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
        pass
        
    def has_blackjack(self):
        """
        Check if the player has a natural blackjack (an Ace and a 10-value card).
        Returns:
            bool: True if the player has blackjack, False otherwise.
        """
        if len(self.hand) == 2 and self.hand_value() == 21:
            return True
        pass
        
    def is_bust(self):
        """
        Check if the player's hand value exceeds 21.
        Returns:
            bool: True if the player is bust, False otherwise.
        """
        if self.hand_value() > 21:
            print(f"{self.name} is bust with hand value {self.hand_value()}.")
            return True
        pass
        
    def reset_hand(self):
        """
        Reset the player's hand for a new round.
        Returns:
            None
        """
        self.hand = []
        print(f"{self.name}'s hand has been reset.")
        pass
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
        return self.hand_value() < 17
        pass
    
    def show_hidden_card(self):
        """
        Return a string representation of the dealer's hand, hiding the first card.
        Returns:
            str: The dealer's hand with the first card hidden.
        """
        return self.show_hand(hide_first=True)
        pass