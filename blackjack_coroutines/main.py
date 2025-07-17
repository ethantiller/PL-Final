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
    print("\nDeck shuffled!")
    
    # Deal a few cards to show it works
    print("\nDealing 5 cards:")
    for i in range(5):
        card = deck.deal_card()
        print(f"Card {i+1}: {card}")
    
    print(f"\nCards remaining in deck: {len(deck.cards)}")
    

if __name__ == "__main__":
    start_game()
    # This will be the main entry point for the game