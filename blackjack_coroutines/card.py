import random

class Card:
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self, suit, rank):
        
        self.suit = suit
        self.rank = rank
        if suit not in self.SUITS or rank not in self.RANKS:
            raise ValueError("Invalid suit or rank")
        
    def value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)
        
    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
class Deck:
    def __init__(self):
        # Create and shuffle deck(s)
        self.reset()
    
    def reset(self):
        """Reset the deck with a fresh set of cards."""
        self.cards = [Card(suit, rank) for suit in Card.SUITS for rank in Card.RANKS]
        self.shuffle()
    
    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if not self.cards:
            print("Deck is empty, resetting and reshuffling...")
            self.reset()
        return self.cards.pop()