import requests
import time
from typing import Optional, Dict, List

# Mock card images for testing (using placeholder service)
MOCK_CARD_IMAGES = {
    'character': 'https://via.placeholder.com/250x350/4A90E2/FFFFFF?text=Character',
    'action': 'https://via.placeholder.com/250x350/E27A3F/FFFFFF?text=Action',
    'item': 'https://via.placeholder.com/250x350/45B7D1/FFFFFF?text=Item',
}

class LorcanaAPI:
    BASE_URL = "https://api.lorcana-api.com"
    
    def __init__(self, use_mock=False):
        self.cache = {}  # Cache cards to avoid repeated API calls
        self.use_mock = use_mock  # Use mock data if API unavailable
    
    def search_card(self, main_name: str, subtitle: str) -> Optional[Dict]:
        """
        Search for a card by main name and subtitle.
        Returns card data including image URL.
        """
        cache_key = f"{main_name}|{subtitle}".lower()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Try API first
        if not self.use_mock:
            try:
                # Search by name
                response = requests.get(
                    f"{self.BASE_URL}/cards/search",
                    params={"q": f"{main_name} - {subtitle}"},
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    card = data[0]  # Take first match
                    self.cache[cache_key] = card
                    return card
                
            except Exception as e:
                print(f"API error for {main_name} - {subtitle}: {e}")
                self.use_mock = True  # Fall back to mock
        
        # Use mock data
        card_type = 'character'  # Default to character
        if any(word in main_name.lower() for word in ['be our', 'fan the', 'cleansing', 'divebomb', 'on your']):
            card_type = 'action'
        elif any(word in main_name.lower() for word in ['lantern', 'hook', 'heart of', 'bell']):
            card_type = 'item'
        
        mock_card = {
            'name': main_name,
            'subtitle': subtitle,
            'full_name': f"{main_name} - {subtitle}",
            'image_url': MOCK_CARD_IMAGES[card_type],
            'mock': True
        }
        
        self.cache[cache_key] = mock_card
        return mock_card
    
    def parse_dreamborn_deck(self, deck_text: str) -> List[Dict]:
        """
        Parse a Dreamborn format deck list and fetch card data.
        Format: "3 Aladdin - Street Rat"
        Returns list of card data dictionaries (with duplicates for count).
        """
        cards = []
        lines = deck_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse "X Card Name - Subtitle"
            parts = line.split(' ', 1)
            if len(parts) != 2:
                continue
            
            try:
                count = int(parts[0])
                full_name = parts[1]
                
                # Split on " - " to get main name and subtitle
                if ' - ' in full_name:
                    main_name, subtitle = full_name.split(' - ', 1)
                    main_name = main_name.strip()
                    subtitle = subtitle.strip()
                    
                    # Fetch card from API
                    card_data = self.search_card(main_name, subtitle)
                    
                    if card_data:
                        # Add card count times
                        for _ in range(count):
                            cards.append(card_data)
                        if card_data.get('mock'):
                            print(f"Added {count}x {main_name} - {subtitle} (MOCK)")
                        else:
                            print(f"Added {count}x {main_name} - {subtitle}")
                    else:
                        print(f"Could not find card: {main_name} - {subtitle}")
                        # Add a placeholder card so deck doesn't break
                        for _ in range(count):
                            cards.append({
                                'name': main_name,
                                'subtitle': subtitle,
                                'image_url': MOCK_CARD_IMAGES['character'],
                                'error': True
                            })
                else:
                    print(f"Invalid format: {line}")
                    
            except ValueError as e:
                print(f"Error parsing line: {line} - {e}")
                continue
        
        return cards


if __name__ == "__main__":
    # Test with your deck
    api = LorcanaAPI()
    
    test_deck = """
2 Rapunzel - Gifted with Healing
3 Stitch - Carefree Surfer
2 Be Our Guest
"""
    
    cards = api.parse_dreamborn_deck(test_deck)
    print(f"\nLoaded {len(cards)} cards")
    for card in cards[:3]:
        print(f"  - {card.get('name')} - {card.get('subtitle', 'N/A')}")
