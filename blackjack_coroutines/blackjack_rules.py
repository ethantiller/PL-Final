from card import Card


def calculate_hand_value(cards: list[Card]):
    """
    Calculate the total value of a hand of cards.
    - Aces are counted as 11 unless it would cause the hand to bust, in which case they are counted as 1.
    - Face cards (J, Q, K) are worth 10.
    - Number cards are worth their face value.
    - The total value is adjusted for Aces if the total exceeds 21.
    """
    value = 0
    aces = 0

    # Count the value of face cards, aces, and number cards
    FACES = {'J': 10, 'Q': 10, 'K': 10}
    for card in cards:
      # If the card is a face card, add its value
      if card.rank in FACES:
        value += FACES[card.rank]
      elif card.rank == 'A':
        aces += 1
        value += 11
      else:
        value += int(card.rank)

    while value > 21 and aces:
      value -= 10
      aces -= 1

    return value
  
def is_blackjack(cards: list[Card]):
  """
  Check if the hand is a blackjack (total value of 21 with exactly two cards)
  - A blackjack is defined as having a total value of 21 with exactly two cards
  """
  return calculate_hand_value(cards) == 21 and len(cards) == 2

def is_bust(cards: list[Card]):
  """
  Check if the hand is bust (total value exceeds 21)
  - A hand is bust if the total value exceeds 21
  """
  return calculate_hand_value(cards) > 21

def can_double_down(cards: list[Card]):
  """
  Checks if the player can double down
  - Player can double down if they have exactly two cards and their total value is between 9 and 11
  """
  return len(cards) == 2 and calculate_hand_value(cards) in range(9, 12)

def calculate_payout(bet: int, result: str):
  """
  Calculate the payout based on the game result.
  - Win returns bet * 2
  - Blackjack returns bet * 2.5
  - Push/tie with dealer returns bet
  - Lose returns 0
  """
  if result == 'win':
    return bet * 2
  elif result == 'blackjack':
    return int(bet * 2.5)
  elif result == 'push':
    return bet
  elif result == 'lose':
    return 0
  else:
    raise ValueError("Invalid result. Must be 'win', 'lose', 'blackjack', or 'push'.")
  
def determine_winners(player_hands: list[list[Card]], players: list['Player'], dealer_hand: list[Card]):
  """
  Determine the winners of a blackjack game.
  - Compares the total values of each player's hand and the dealer's hand.
  - Returns a list of results: 'win', 'lose', 'push', or 'blackjack' for each player.
  """
  dealer_value = calculate_hand_value(dealer_hand)
  dealer_bust = is_bust(dealer_hand)
  dealer_blackjack = is_blackjack(dealer_hand)
  results = []

  for player_hand, player in zip(player_hands, players):
    player_value = calculate_hand_value(player_hand)
    player_blackjack = is_blackjack(player_hand)
    
    # Check for blackjack first
    if player_blackjack and not dealer_blackjack:
      results.append('blackjack')
    elif player_blackjack and dealer_blackjack:
      results.append('push')
    elif dealer_blackjack and not player_blackjack:
      results.append('lose')
    # Check for bust
    elif is_bust(player_hand):
      results.append('lose')
    elif dealer_bust:
      results.append('win')
    # Compare values
    elif player_value > dealer_value:
      results.append('win')
    elif player_value < dealer_value:
      results.append('lose')
    else:
      results.append('push')

  return results

def get_valid_actions(player_hand: list[Card], dealer_hand: list[Card]):
  """
  Get the valid actions for the player based on their hand and the dealer's hand.
  - Returns a list of valid actions: 'hit', 'stand', and optionally 'double' if the player can double down.
  """
  actions = ['hit', 'stand']
  if can_double_down(player_hand):
    actions.append('double')
  return actions
