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
        
        # Parse "X Card Name - Subtitle" or "X Card Name"
        parts = line.split(' ', 1)
        if len(parts) != 2:
            continue
        
        try:
            count = int(parts[0])
            full_name = parts[1]
            
            # Check if card has subtitle (character cards) or not (actions/items)
            if ' - ' in full_name:
                # Character card with subtitle
                main_name, subtitle = full_name.split(' - ', 1)
                main_name = main_name.strip()
                subtitle = subtitle.strip()
            else:
                # Action/Item card without subtitle
                main_name = full_name.strip()
                subtitle = None
            
            # Fetch card from API
            if subtitle:
                card_data = self.search_card(main_name, subtitle)
            else:
                card_data = self.search_card_no_subtitle(main_name)
            
            if card_data:
                # Add card count times
                for _ in range(count):
                    cards.append(card_data)
                
                if card_data.get('mock'):
                    print(f"Added {count}x {main_name}" + (f" - {subtitle}" if subtitle else "") + " (MOCK)")
                else:
                    print(f"Added {count}x {main_name}" + (f" - {subtitle}" if subtitle else ""))
            else:
                print(f"Could not find card: {main_name}" + (f" - {subtitle}" if subtitle else ""))
                # Add a placeholder card so deck doesn't break
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

def search_card_no_subtitle(self, main_name: str) -> Optional[Dict]:
    """
    Search for a card without subtitle (actions/items).
    """
    cache_key = f"{main_name}|NO_SUBTITLE".lower()
    
    if cache_key in self.cache:
        return self.cache[cache_key]
    
    # Try API first
    if not self.use_mock:
        try:
            # Search for card by exact name
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
                
                # Extract image URL
                image_url = card.get('Image') or card.get('image')
                
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
    
    # Mock fallback
    mock_card = {
        'name': main_name,
        'subtitle': '',
        'full_name': main_name,
        'image_url': MOCK_CARD_IMAGES['action'],
        'mock': True
    }
    
    self.cache[cache_key] = mock_card
    return mock_card
