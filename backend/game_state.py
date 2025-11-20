import random
import uuid
from typing import Dict, List, Optional, Set
from copy import deepcopy

class Card:
    """Represents a single card instance in the game"""
    def __init__(self, card_data: Dict, owner_id: str):
        self.id = str(uuid.uuid4())
        self.card_data = card_data
        self.owner = owner_id
        self.zone = 'deck'
        self.face_up = False
        self.exerted = False
        self.damage = 0
        self.position = 0
    
    def to_dict(self, viewer_id: str = None) -> Dict:
        """Convert to dictionary for JSON serialization"""
        can_see_face = self.face_up or (viewer_id == self.owner and self.zone == 'hand')
        
        return {
            'id': self.id,
            'owner': self.owner,
            'zone': self.zone,
            'face_up': self.face_up,
            'exerted': self.exerted,
            'damage': self.damage,
            'position': self.position,
            'card_data': self.card_data if can_see_face else None,
            'image_url': self.card_data.get('image_url') if can_see_face else None
        }


class Player:
    """Represents a player's state"""
    def __init__(self, player_id: str, username: str):
        self.id = player_id
        self.username = username
        self.lore = 0
        self.has_inked_this_turn = False
        self.zones = {
            'deck': [],
            'hand': [],
            'discard': [],
            'ink': [],
            'summoning': [],
            'ready': [],
            'mystery': []
        }
    
    def to_dict(self, viewer_id: str = None) -> Dict:
        """Convert to dictionary, hiding private info from other players"""
        is_owner = viewer_id == self.id
        
        return {
            'id': self.id,
            'username': self.username,
            'lore': self.lore,
            'has_inked_this_turn': self.has_inked_this_turn,
            'zone_counts': {
                zone: len(cards) for zone, cards in self.zones.items()
            },
            'zones': self.zones if is_owner else {}
        }


class GameState:
    """Main game state manager"""
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.players: Dict[str, Player] = {}
        self.cards: Dict[str, Card] = {}
        self.current_turn: Optional[str] = None
        self.turn_number = 1
        self.player_order: List[str] = []
    
    def add_player(self, player_id: str, username: str, deck_data: List[Dict]):
        """Add a player with their deck"""
        player = Player(player_id, username)
        self.players[player_id] = player
        self.player_order.append(player_id)
        
        for card_data in deck_data:
            card = Card(card_data, player_id)
            self.cards[card.id] = card
            player.zones['deck'].append(card.id)
        
        return player
    
    def start_game(self):
        """Initialize game - shuffle, set mystery card, draw hands"""
        random.shuffle(self.player_order)
        self.current_turn = self.player_order[0]
        
        for player_id in self.player_order:
            player = self.players[player_id]
            
            random.shuffle(player.zones['deck'])
            
            if player.zones['deck']:
                mystery_card_id = player.zones['deck'].pop(0)
                player.zones['mystery'] = [mystery_card_id]
                self.cards[mystery_card_id].zone = 'mystery'
            
            for _ in range(7):
                if player.zones['deck']:
                    card_id = player.zones['deck'].pop(0)
                    player.zones['hand'].append(card_id)
                    self.cards[card_id].zone = 'hand'
                    self.cards[card_id].face_up = True
    
    def mulligan(self, player_id: str, card_ids: List[str]):
        """Mulligan specific cards - put back in deck, shuffle, redraw"""
        player = self.players[player_id]
        
        for card_id in card_ids:
            if card_id in player.zones['hand']:
                player.zones['hand'].remove(card_id)
                player.zones['deck'].append(card_id)
                self.cards[card_id].zone = 'deck'
                self.cards[card_id].face_up = False
        
        random.shuffle(player.zones['deck'])
        
        for _ in range(len(card_ids)):
            if player.zones['deck']:
                card_id = player.zones['deck'].pop(0)
                player.zones['hand'].append(card_id)
                self.cards[card_id].zone = 'hand'
                self.cards[card_id].face_up = True
    
    def move_card(self, card_id: str, to_zone: str, position: Optional[int] = None, 
                  face_up: Optional[bool] = None):
        """Move a card between zones"""
        card = self.cards[card_id]
        player = self.players[card.owner]
        
        if card_id in player.zones[card.zone]:
            player.zones[card.zone].remove(card_id)
        
        if position is not None and position < len(player.zones[to_zone]):
            player.zones[to_zone].insert(position, card_id)
        else:
            player.zones[to_zone].append(card_id)
        
        card.zone = to_zone
        if face_up is not None:
            card.face_up = face_up
        
        if to_zone in ['hand', 'deck', 'discard', 'ink']:
            card.exerted = False
    
    def can_ink_card(self, card_id: str):
        """Check if a card can be inked. Returns (can_ink, error_message)"""
        card = self.cards[card_id]
        player = self.players[card.owner]
        
        if player.has_inked_this_turn:
            return False, "Already inked a card this turn"
        
        if card.zone != 'hand':
            return False, "Card must be in hand to ink"
        
        inkwell = card.card_data.get('inkwell')
        
        has_inkwell = False
        if isinstance(inkwell, bool):
            has_inkwell = inkwell
        elif isinstance(inkwell, str):
            has_inkwell = inkwell.lower() in ['true', 'yes', '1']
        elif isinstance(inkwell, int):
            has_inkwell = inkwell == 1
        
        if not has_inkwell:
            return False, "This card cannot be inked (no inkwell)"
        
        return True, ""
    
    def ink_card(self, card_id: str):
        """Ink a card - move to ink zone face down (dried)"""
        can_ink, error_msg = self.can_ink_card(card_id)
        
        if not can_ink:
            return False, error_msg
        
        card = self.cards[card_id]
        player = self.players[card.owner]
        
        self.move_card(card_id, 'ink', face_up=False)
        player.has_inked_this_turn = True
        return True, ""
    
    def can_play_card(self, card_id: str):
        """Check if a card can be played. Returns (can_play, error_message)"""
        card = self.cards[card_id]
        player = self.players[card.owner]
        
        if card.zone != 'hand':
            return False, "Card must be in hand to play"
        
        cost = card.card_data.get('cost')
        if cost is None:
            cost = 0
        
        available_ink = sum(1 for ink_card_id in player.zones['ink'] 
                           if not self.cards[ink_card_id].face_up)
        
        if available_ink < cost:
            return False, f"Not enough ink. Need {cost}, have {available_ink}"
        
        return True, ""
    
    def spend_ink(self, player_id: str, amount: int):
        """Spend (flip face-up) ink cards"""
        player = self.players[player_id]
        spent = 0
        
        for ink_card_id in player.zones['ink']:
            if spent >= amount:
                break
            if not self.cards[ink_card_id].face_up:
                self.cards[ink_card_id].face_up = True
                spent += 1
    
    def play_card(self, card_id: str):
        """Play a card from hand - goes to appropriate zone based on type"""
        card = self.cards[card_id]
        card_type = card.card_data.get('type', '').lower()
        cost = card.card_data.get('cost', 0) or 0
        
        self.spend_ink(card.owner, cost)
        
        if card_type == 'action':
            self.move_card(card_id, 'discard', face_up=True)
        elif card_type == 'item' or card_type == 'location':
            self.move_card(card_id, 'ready', face_up=True)
            self.cards[card_id].exerted = False
        else:
            self.move_card(card_id, 'summoning', face_up=True)
            self.cards[card_id].exerted = False
    
    def exert_card(self, card_id: str):
        """Exert (tap) a card"""
        self.cards[card_id].exerted = True
    
    def ready_card(self, card_id: str):
        """Ready (untap) a card"""
        self.cards[card_id].exerted = False
    
    def add_damage(self, card_id: str, amount: int = 1):
        """Add damage to a card"""
        self.cards[card_id].damage += amount
    
    def remove_damage(self, card_id: str, amount: int = 1):
        """Remove damage from a card"""
        self.cards[card_id].damage = max(0, self.cards[card_id].damage - amount)
    
    def shuffle_deck(self, player_id: str):
        """Shuffle a player's deck"""
        player = self.players[player_id]
        random.shuffle(player.zones['deck'])
    
    def draw_cards(self, player_id: str, count: int = 1):
        """Draw cards from deck to hand"""
        player = self.players[player_id]
        for _ in range(count):
            if player.zones['deck']:
                card_id = player.zones['deck'].pop(0)
                player.zones['hand'].append(card_id)
                self.cards[card_id].zone = 'hand'
                self.cards[card_id].face_up = True
    
    def flip_mystery_card(self, player_id: str):
        """Flip and play mystery card (turn 3+, free, ready immediately)"""
        if self.turn_number < 3:
            return False
        
        player = self.players[player_id]
        if player.zones['mystery']:
            card_id = player.zones['mystery'][0]
            self.move_card(card_id, 'ready', face_up=True)
            self.cards[card_id].exerted = False
            return True
        return False
    
    def end_turn(self, player_id: str):
        """End current player's turn - dry ink, move to next player"""
        if self.current_turn != player_id:
            return False
        
        player = self.players[player_id]
        
        for card_id in player.zones['ink']:
            self.cards[card_id].face_up = False
        
        player.has_inked_this_turn = False
        
        current_idx = self.player_order.index(player_id)
        next_idx = (current_idx + 1) % len(self.player_order)
        self.current_turn = self.player_order[next_idx]
        
        if next_idx == 0:
            self.turn_number += 1
        
        return True
    
    def add_lore(self, player_id: str, amount: int):
        """Add lore to a player"""
        self.players[player_id].lore += amount
    
    def get_state_for_player(self, viewer_id: str) -> Dict:
        """Get game state from a specific player's perspective"""
        return {
            'game_id': self.game_id,
            'current_turn': self.current_turn,
            'turn_number': self.turn_number,
            'player_order': self.player_order,
            'players': {
                pid: player.to_dict(viewer_id) 
                for pid, player in self.players.items()
            },
            'my_cards': {
                cid: card.to_dict(viewer_id)
                for cid, card in self.cards.items()
                if card.owner == viewer_id
            },
            'visible_cards': {
                cid: card.to_dict(viewer_id)
                for cid, card in self.cards.items()
                if card.owner != viewer_id and card.face_up
            }
        }
