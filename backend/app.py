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

games = {}
lorcana_api = LorcanaAPI()

player_sessions = {}

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
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lorcana TCG Simulator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
            }
            .container {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 40px;
                text-align: center;
            }
            h1 {
                font-size: 48px;
                margin-bottom: 10px;
            }
            .subtitle {
                font-size: 20px;
                color: #aaa;
                margin-bottom: 40px;
            }
            .button {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 15px 30px;
                margin: 10px;
                text-decoration: none;
                border-radius: 8px;
                font-size: 18px;
                transition: background 0.3s;
            }
            .button:hover {
                background: #45a049;
            }
            .info {
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid rgba(255, 255, 255, 0.2);
                font-size: 14px;
                color: #ccc;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎴 Lorcana TCG Simulator</h1>
            <div class="subtitle">Disney Lorcana Multiplayer Virtual Tabletop</div>
            
            <a href="/game" class="button">🚀 Launch Game (3 Players)</a>
            
            <div class="info">
                <p><strong>Quick Start:</strong></p>
                <p>Click "Launch Game" to immediately start a 3-player game with sample decks</p>
                <br>
                <p><strong>Features:</strong></p>
                <p>✓ Real-time multiplayer (2-4 players) • ✓ Full game mechanics<br>
                ✓ Card images from Lorcana API • ✓ Interactive UI</p>
            </div>
        </div>
    </body>
    </html>
    """


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/test_game')
def test_game():
    try:
        game_id = str(uuid.uuid4())
        player_id = str(uuid.uuid4())
        
        print("Loading deck from API...")
        deck_cards = lorcana_api.parse_dreamborn_deck(SAMPLE_DECK)
        print(f"Loaded {len(deck_cards)} cards for player 1")
        
        game = GameState(game_id)
        
        print("Adding main player...")
        game.add_player(player_id, "You", deck_cards)
        
        print("Adding opponent 1...")
        opponent1_id = str(uuid.uuid4())
        opponent1_deck = lorcana_api.parse_dreamborn_deck(SAMPLE_DECK)
        print(f"Loaded {len(opponent1_deck)} cards for player 2")
        game.add_player(opponent1_id, "Player 2", opponent1_deck)
        
        print("Adding opponent 2...")
        opponent2_id = str(uuid.uuid4())
        opponent2_deck = lorcana_api.parse_dreamborn_deck(SAMPLE_DECK)
        print(f"Loaded {len(opponent2_deck)} cards for player 3")
        game.add_player(opponent2_id, "Player 3", opponent2_deck)
        
        print("Starting game...")
        game.start_game()
        
        games[game_id] = game
        
        session['game_id'] = game_id
        session['player_id'] = player_id
        
        print("Game initialized successfully!")
        
        return jsonify({
            'game_id': game_id,
            'player_id': player_id,
            'state': game.get_state_for_player(player_id)
        })
        
    except Exception as e:
        print(f"ERROR in test_game: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/game_state')
def get_game_state():
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if not game_id or game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    return jsonify(game.get_state_for_player(player_id))


def broadcast_game_update(game, game_id):
    for pid in game.players:
        if pid in player_sessions:
            socketio.emit('game_update', 
                         game.get_state_for_player(pid), 
                         room=player_sessions[pid])


@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')


@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    for pid, sid in list(player_sessions.items()):
        if sid == request.sid:
            del player_sessions[pid]
            print(f'Removed player session: {pid}')


@socketio.on('join_game')
def handle_join_game(data):
    game_id = data.get('game_id')
    player_id = data.get('player_id')
    
    if game_id in games:
        join_room(game_id)
        player_sessions[player_id] = request.sid
        print(f'Player {player_id} joined with session {request.sid}')
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
    
    if game.cards[card_id].owner != player_id:
        emit('error', {'message': 'Not your card'})
        return
    
    game.move_card(card_id, to_zone, face_up=face_up)
    broadcast_game_update(game, game_id)


@socketio.on('ink_card')
def handle_ink_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    if game.cards[card_id].owner != player_id:
        emit('error', {'message': 'Not your card'})
        return
    
    success, error_msg = game.ink_card(card_id)
    
    if success:
        broadcast_game_update(game, game_id)
    else:
        emit('error', {'message': error_msg})


@socketio.on('play_card')
def handle_play_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    if game.cards[card_id].owner != player_id:
        emit('error', {'message': 'Not your card'})
        return
    
    can_play, error_msg = game.can_play_card(card_id)
    if not can_play:
        emit('error', {'message': error_msg})
        return
    
    game.play_card(card_id)
    broadcast_game_update(game, game_id)


@socketio.on('exert_card')
def handle_exert_card(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.exert_card(card_id)
    broadcast_game_update(game, game_id)


@socketio.on('ready_card')
def handle_ready_card(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.ready_card(card_id)
    broadcast_game_update(game, game_id)


@socketio.on('add_damage')
def handle_add_damage(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.add_damage(card_id, 1)
    broadcast_game_update(game, game_id)


@socketio.on('remove_damage')
def handle_remove_damage(data):
    game_id = session.get('game_id')
    card_id = data.get('card_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.remove_damage(card_id, 1)
    broadcast_game_update(game, game_id)


@socketio.on('draw_card')
def handle_draw_card(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.draw_cards(player_id, 1)
    broadcast_game_update(game, game_id)


@socketio.on('shuffle_deck')
def handle_shuffle_deck(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.shuffle_deck(player_id)
    broadcast_game_update(game, game_id)


@socketio.on('end_turn')
def handle_end_turn(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.end_turn(player_id)
    broadcast_game_update(game, game_id)


@socketio.on('add_lore')
def handle_add_lore(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    amount = data.get('amount', 1)
    
    if game_id not in games:
        return
    
    game = games[game_id]
    game.add_lore(player_id, amount)
    broadcast_game_update(game, game_id)


@socketio.on('flip_mystery_card')
def handle_flip_mystery(data):
    game_id = session.get('game_id')
    player_id = session.get('player_id')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    success = game.flip_mystery_card(player_id)
    
    if success:
        broadcast_game_update(game, game_id)
    else:
        emit('error', {'message': 'Cannot flip mystery card yet (turn 3+)'})


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
