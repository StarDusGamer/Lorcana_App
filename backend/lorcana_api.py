import requests
import time
from typing import Optional, Dict, List

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
    
    def search_card(self, main_name: str, subtitle: str) -> Optional[Dict]:
        cache_key = f"{main_name}|{subtitle}".lower()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if not self.use_mock:
            try:
                full_name = f"{main_name} - {subtitle}"
                response = requests.get(
                    f"{self.BASE_URL}/cards/fetch",
                    params={"strict": full_name},
                    timeout=3
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    card = data[0]
                    
                    image_url = card.get('Image')
                    
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
                self.use_mock = True
        
        card_type = 'character'
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
        cache_key = f"{main_name}|NO_SUBTITLE".lower()
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        if not self.use_mock:
            try:
                response = requests.get(
                    f"{self.BASE_URL}/cards/fetch",
                    params={"strict": main_name},
                    timeout=3
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    card = data[0]
                    
                    image_url = card.get('Image')
                    
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
