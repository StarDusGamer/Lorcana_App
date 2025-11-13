from flask import Flask, render_template, jsonify, request, session
from flask_socketio import SocketIO, emit, join_room
import uuid
import os
from game_state import GameState
from lorcana_api import LorcanaAPI

app = Flask(__name__, 
            template_folder='../UI',
            static_folder='../UI',
            static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active games
games = {}
lorcana_api = LorcanaAPI()

# Sample deck for testing
SAMPLE_DECK = """2 Rapunzel - Gifted with Healing
3 Stitch - Carefree Surfer
2 Be Our Guest
3 Lantern
2 Maui - Hero to All
1 Te Kā - The Burning One
2 Fan the Flames
2 Rapunzel - Gifted Artist
2 Snow White - Lost in the Forest
2 Snow White - Well Wisher
4 Felicia - Always Hungry
4 Mother Gothel - Withered and Wicked
2 Teeth and Ambitions
2 Dinner Bell
4 Pluto - Determined Defender
4 Pluto - Friendly Pooch
2 Pongo - Determined Father
4 Cleansing Rainwater
2 Heart of Atlantis
3 Maui - Whale
2 Stitch - Little Rocket
2 Divebomb
2 On Your Feet! Now!
2 Maui's Fish Hook"""


@app.route('/')
def index():
    return render_template('game.html')


@app.route('/test_game')
def test_game():
    """Create a test game with sample deck"""
    game_id = str(uuid.uuid4())
    player_id = str(uuid.uuid4())
    
    # Load deck
    print("Loading deck from API...")
    deck_cards = lorcana_api.parse_dreamborn_deck(SAMPLE_DECK)
    print(f"Loaded {len(deck_cards)} cards")
    
    # Create game
    game = GameState(game_id)
    
    # Add main player (you)
    game.add_player(player_id, "You", deck_cards)
    
    # Add 2 more players for testing (3 player game)
    opponent1_id = str(uuid.uuid4())
    opponent1_deck = lorcana_api.parse_dreamborn_deck(SAMPLE_DECK)
    game.add_player(opponent1_id, "Player 2", opponent1_deck)
    
    opponent2_id = str(uuid.uuid4())
    opponent2_deck = lorcana_api.parse_dreamborn_deck(SAMPLE_DECK)
    game.add_player(opponent2_id, "Player 3", opponent2_deck)
    
    # Start game
    game.start_game()
    
    games[game_id] = game
    
    # Store in session
    session['game_id'] = game_id
    session['player_id'] = player_id
    
    return jsonify({
        'game_id': game_id,
        'player_id': player_id,
        'state': game.get_state_for_player(player_id)
    })

@app.route('/game_state')
def get_game_state():
    """Get current game state"""
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if not game_id or game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    return jsonify(game.get_state_for_player(player_id))


@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('join_game')
def handle_join_game(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    
    if game_id in games:
        join_room(game_id)
        emit('game_joined', {'game_id': game_id})


@socketio.on('move_card')
def handle_move_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    card_id = data.get('card_id')
    to_zone = data.get('to_zone')
    face_up = data.get('face_up')
    
    # Validate card belongs to player
    if game.cards[card_id].owner != player_id:
        emit('error', {'message': 'Not your card'})
        return
    
    game.move_card(card_id, to_zone, face_up=face_up)
    
    # Broadcast updated state to all players in game
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('ink_card')
def handle_ink_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    if game.cards[card_id].owner != player_id:
        return
    
    game.ink_card(card_id)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('play_card')
def handle_play_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    if game.cards[card_id].owner != player_id:
        return
    
    game.play_card(card_id)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('exert_card')
def handle_exert_card(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.exert_card(card_id)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('ready_card')
def handle_ready_card(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.ready_card(card_id)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('add_damage')
def handle_add_damage(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.add_damage(card_id, 1)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('remove_damage')
def handle_remove_damage(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.remove_damage(card_id, 1)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('draw_card')
def handle_draw_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.draw_cards(player_id, 1)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('shuffle_deck')
def handle_shuffle_deck(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.shuffle_deck(player_id)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('end_turn')
def handle_end_turn(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.end_turn(player_id)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('add_lore')
def handle_add_lore(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    amount = data.get('amount', 1)
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.add_lore(player_id, amount)
    
    for pid in game.players:
        emit('game_update', game.get_state_for_player(pid), room=game_id)


@socketio.on('flip_mystery_card')
def handle_flip_mystery(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    success = game.flip_mystery_card(player_id)
    
    if success:
        for pid in game.players:
            emit('game_update', game.get_state_for_player(pid), room=game_id)
    else:
        emit('error', {'message': 'Cannot flip mystery card yet (turn 3+)'})


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
