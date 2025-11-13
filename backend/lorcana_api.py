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
        self.cache = {}
        self.use_mock = use_mock
        self.all_cards = None
    
    def fetch_all_cards(self):
        """Fetch all cards from the API and cache them"""
        if self.all_cards is not None:
            return self.all_cards
        
        try:
            print("Fetching all cards from Lorcana API...")
            all_cards = []
            page = 1
            pagesize = 1000
            
            while True:
                response = requests.get(
                    f"{self.BASE_URL}/cards/all",
                    params={
                        "pagesize": pagesize,
                        "page": page
                    },
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                all_cards.extend(data)
                print(f"Fetched page {page} ({len(data)} cards)")
                
                if len(data) < pagesize:
                    break
                
                page += 1
                time.sleep(0.5)
            
            self.all_cards = all_cards
            print(f"Successfully cached {len(all_cards)} total cards")
            return all_cards
            
        except Exception as e:
            print(f"Error fetching all cards: {e}")
            self.use_mock = True
            return []
    
    def search_card(self, main_name: str, subtitle: str) -> Optional[Dict]:
        """
        Search for a card by main name and subtitle.
        Returns card data including image URL.
        """
        cache_key = f"{main_name}|{subtitle}".lower()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if not self.use_mock:
            try:
                full_name = f"{main_name} - {subtitle}"
                response = requests.get(
                    f"{self.BASE_URL}/cards/fetch",
                    params={
                        "strict": full_name
                    },
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    card = data[0]
                    
                    # DEBUG: Print all available fields
                    print(f"Card fields for {full_name}: {list(card.keys())}")
                    
                    # Extract image URL - try multiple field names
                    image_url = None
                    for img_field in ['Image', 'image', 'image_url', 'Image_URL', 'card_image', 'art']:
                        if img_field in card and card[img_field]:
                            image_url = card[img_field]
                            print(f"Found image at field '{img_field}': {image_url}")
                            break
                    
                    if not image_url:
                        print(f"WARNING: No image found for {full_name}")
                    
                    card_info = {
                        'name': card.get('Name', main_name),
                        'subtitle': card.get('Subtitle', subtitle),
                        'full_name': f"{main_name} - {subtitle}",
                        'image_url': image_url,
                        'cost': card.get('Cost'),
                        'inkwell': card.get('Inkwell'),
                        'type': card.get('Type'),
                        'classification': card.get('Classifications'),
                        'strength': card.get('Strength'),
                        'willpower': card.get('Willpower'),
                        'lore': card.get('Lore_Value'),
                        'rarity': card.get('Rarity'),
                        'set': card.get('Set_Name'),
                        'card_num': card.get('Card_Num')
                    }
                    
                    self.cache[cache_key] = card_info
                    return card_info
                
            except Exception as e:
                print(f"API error for {main_name} - {subtitle}: {e}")
        
        if not self.use_mock:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/cards/fetch",
                    params={
                        "search": f"name:{main_name}"
                    },
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                
                for card in data:
                    if card.get('Subtitle', '').lower() == subtitle.lower():
                        image_url = card.get('Image') or card.get('image')
                        
                        card_info = {
                            'name': card.get('Name', main_name),
                            'subtitle': card.get('Subtitle', subtitle),
                            'full_name': f"{main_name} - {subtitle}",
                            'image_url': image_url,
                            'cost': card.get('Cost'),
                            'inkwell': card.get('Inkwell'),
                            'type': card.get('Type'),
                            'classification': card.get('Classifications'),
                            'strength': card.get('Strength'),
                            'willpower': card.get('Willpower'),
                            'lore': card.get('Lore_Value'),
                            'rarity': card.get('Rarity'),
                            'set': card.get('Set_Name'),
                            'card_num': card.get('Card_Num')
                        }
                        
                        self.cache[cache_key] = card_info
                        return card_info
                
            except Exception as e:
                print(f"Search API error for {main_name} - {subtitle}: {e}")
                self.use_mock = True
        
        card_type = 'character'
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
    
    def search_card_no_subtitle(self, main_name: str) -> Optional[Dict]:
        """
        Search for a card without subtitle (actions/items).
        """
        cache_key = f"{main_name}|NO_SUBTITLE".lower()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if not self.use_mock:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/cards/fetch",
                    params={
                        "strict": main_name
                    },
                    timeout=5
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    card = data[0]
                    
                    print(f"Card fields for {main_name}: {list(card.keys())}")
                    
                    image_url = None
                    for img_field in ['Image', 'image', 'image_url', 'Image_URL', 'card_image', 'art']:
                        if img_field in card and card[img_field]:
                            image_url = card[img_field]
                            print(f"Found image at field '{img_field}': {image_url}")
                            break
                    
                    card_info = {
                        'name': card.get('Name', main_name),
                        'subtitle': '',
                        'full_name': main_name,
                        'image_url': image_url,
                        'cost': card.get('Cost'),
                        'inkwell': card.get('Inkwell'),
                        'type': card.get('Type'),
                        'classification': card.get('Classifications'),
                        'rarity': card.get('Rarity'),
                        'set': card.get('Set_Name'),
                        'card_num': card.get('Card_Num')
                    }
                    
                    self.cache[cache_key] = card_info
                    return card_info
                    
            except Exception as e:
                print(f"API error for {main_name}: {e}")
                self.use_mock = True
        
        mock_card = {
            'name': main_name,
            'subtitle': '',
            'full_name': main_name,
            'image_url': MOCK_CARD_IMAGES['action'],
            'mock': True
        }
        
        self.cache[cache_key] = mock_card
        return mock_card
    
    def parse_dreamborn_deck(self, deck_text: str) -> List[Dict]:
        """
        Parse a Dreamborn format deck list and fetch card data.
        Format: "3 Aladdin - Street Rat" or "2 Be Our Guest"
        Returns list of card data dictionaries (with duplicates for count).
        """
        cards = []
        lines = deck_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(' ', 1)
            if len(parts) != 2:
                continue
            
            try:
                count = int(parts[0])
                full_name = parts[1]
                
                if ' - ' in full_name:
                    main_name, subtitle = full_name.split(' - ', 1)
                    main_name = main_name.strip()
                    subtitle = subtitle.strip()
                else:
                    main_name = full_name.strip()
                    subtitle = None
                
                if subtitle:
                    card_data = self.search_card(main_name, subtitle)
                else:
                    card_data = self.search_card_no_subtitle(main_name)
                
                if card_data:
                    for _ in range(count):
                        cards.append(card_data)
                    
                    if card_data.get('mock'):
                        print(f"Added {count}x {main_name}" + (f" - {subtitle}" if subtitle else "") + " (MOCK)")
                    else:
                        print(f"Added {count}x {main_name}" + (f" - {subtitle}" if subtitle else ""))
                else:
                    print(f"Could not find card: {main_name}" + (f" - {subtitle}" if subtitle else ""))
                    for _ in range(count):
                        cards.append({
                            'name': main_name,
                            'subtitle': subtitle or '',
                            'image_url': MOCK_CARD_IMAGES['action'],
                            'error': True
                        })
                    
            except ValueError as e:
                print(f"Error parsing line: {line} - {e}")
                continue
        
        return cards


if __name__ == "__main__":
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
        print(f"    Image: {card.get('image_url')}")
```

Now restart your server and **check the terminal output**. Look for lines like:
```
Card fields for Rapunzel - Gifted with Healing: ['Name', 'Subtitle', 'Image', ...]
Found image at field 'Image': https://...
