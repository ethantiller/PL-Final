from card import Card, Deck

def start_game():
    print("Starting the Blackjack game...")
    
    # Initialize a new deck
    deck = Deck()
    
    # Print all cards in the deck
    print("Deck contains:")
    for i, card in enumerate(deck.cards, 1):
        print(f"{i:2d}. {card}")
    
    print(f"\nTotal cards in deck: {len(deck.cards)}")
    
    # Shuffle the deck
    deck.shuffle()
    print("Deck contains: ")
    for i, card in enumerate(deck.cards, 1):
        print(f"{i:2d}. {card}")
    

if __name__ == "__main__":
    start_game()
    