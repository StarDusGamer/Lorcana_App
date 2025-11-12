// Game state
let gameState = null;
let playerId = null;
let gameId = null;
let socket = null;

// Initialize game on load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        // Initialize test game
        const response = await fetch('/test_game');
        const data = await response.json();
        
        gameId = data.game_id;
        playerId = data.player_id;
        gameState = data.state;
        
        // Initialize socket connection
        socket = io();
        
        socket.on('connect', () => {
            console.log('Socket connected');
            socket.emit('join_game', { game_id: gameId, player_id: playerId });
        });
        
        socket.on('game_update', (newState) => {
            gameState = newState;
            renderGame();
        });
        
        socket.on('error', (data) => {
            alert(data.message);
        });
        
        // Hide loading and render
        document.getElementById('loading').classList.add('hidden');
        renderGame();
        
    } catch (error) {
        console.error('Error initializing game:', error);
        alert('Failed to load game. Check console for details.');
    }
});

// Render the game state
function renderGame() {
    if (!gameState) return;
    
    const myPlayer = gameState.players[playerId];
    
    // Update turn info
    document.getElementById('turn-number').textContent = gameState.turn_number;
    const currentPlayerName = gameState.players[gameState.current_turn].username;
    document.getElementById('current-player-name').textContent = currentPlayerName;
    
    // Update lore
    document.getElementById('your-lore').textContent = myPlayer.lore;
    
    // Update zone counts
    document.getElementById('deck-count').textContent = myPlayer.zone_counts.deck;
    document.getElementById('mystery-count').textContent = myPlayer.zone_counts.mystery;
    document.getElementById('discard-count').textContent = myPlayer.zone_counts.discard;
    document.getElementById('ink-count').textContent = myPlayer.zone_counts.ink;
    
    // Render zones
    renderZone('hand-zone', myPlayer.zones.hand);
    renderZone('ready-zone', myPlayer.zones.ready);
    renderZone('summoning-zone', myPlayer.zones.summoning);
}

// Render a specific zone
function renderZone(zoneId, cardIds) {
    const zoneElement = document.getElementById(zoneId);
    zoneElement.innerHTML = '';
    
    if (!cardIds) return;
    
    cardIds.forEach(cardId => {
        const card = gameState.my_cards[cardId];
        if (!card) return;
        
        const cardElement = createCardElement(card);
        zoneElement.appendChild(cardElement);
    });
}

// Create a card HTML element
function createCardElement(card) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    cardDiv.dataset.cardId = card.id;
    
    if (card.exerted) {
        cardDiv.classList.add('exerted');
    }
    
    // Add card image
    if (card.image_url) {
        cardDiv.style.backgroundImage = `url(${card.image_url})`;
    } else {
        // Fallback for cards without images
        cardDiv.innerHTML = '<div class="card-back">?</div>';
    }
    
    // Add damage counter if needed
    if (card.damage > 0) {
        const damageCounter = document.createElement('div');
        damageCounter.className = 'damage-counter';
        damageCounter.textContent = card.damage;
        cardDiv.appendChild(damageCounter);
    }
    
    // Add click handler
    cardDiv.addEventListener('click', (e) => {
        e.stopPropagation();
        showCardMenu(card, e.clientX, e.clientY);
    });
    
    return cardDiv;
}

// Show context menu for a card
function showCardMenu(card, x, y) {
    const menu = document.getElementById('context-menu');
    menu.innerHTML = '';
    
    const options = getCardOptions(card);
    
    options.forEach(option => {
        const item = document.createElement('div');
        item.className = 'context-menu-item';
        if (option.disabled) {
            item.classList.add('disabled');
        }
        item.textContent = option.label;
        item.addEventListener('click', () => {
            if (!option.disabled) {
                option.action();
                hideContextMenu();
            }
        });
        menu.appendChild(item);
    });
    
    // Position menu
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.classList.remove('hidden');
}

// Get available options for a card based on its zone and state
function getCardOptions(card) {
    const options = [];
    
    switch (card.zone) {
        case 'hand':
            options.push({ label: 'Play Card', action: () => playCard(card.id) });
            options.push({ label: 'Ink Card', action: () => inkCard(card.id) });
            options.push({ label: 'Discard', action: () => moveCard(card.id, 'discard') });
            break;
            
        case 'ready':
            if (!card.exerted) {
                options.push({ label: 'Quest (+1 Lore)', action: () => quest(card.id) });
                options.push({ label: 'Challenge (Exert)', action: () => exertCard(card.id) });
                options.push({ label: 'Sing (Exert)', action: () => exertCard(card.id) });
                options.push({ label: 'Exert', action: () => exertCard(card.id) });
            } else {
                options.push({ label: 'Ready', action: () => readyCard(card.id) });
            }
            options.push({ label: 'Add Damage', action: () => addDamage(card.id) });
            if (card.damage > 0) {
                options.push({ label: 'Remove Damage', action: () => removeDamage(card.id) });
            }
            options.push({ label: 'Move to Hand', action: () => moveCard(card.id, 'hand') });
            options.push({ label: 'Move to Discard', action: () => moveCard(card.id, 'discard') });
            break;
            
        case 'summoning':
            options.push({ label: 'Move to Ready', action: () => moveCard(card.id, 'ready') });
            options.push({ label: 'Add Damage', action: () => addDamage(card.id) });
            if (card.damage > 0) {
                options.push({ label: 'Remove Damage', action: () => removeDamage(card.id) });
            }
            options.push({ label: 'Move to Hand', action: () => moveCard(card.id, 'hand') });
            options.push({ label: 'Move to Discard', action: () => moveCard(card.id, 'discard') });
            break;
    }
    
    return options;
}

// Card actions
function playCard(cardId) {
    socket.emit('play_card', { card_id: cardId });
}

function inkCard(cardId) {
    socket.emit('ink_card', { card_id: cardId });
}

function moveCard(cardId, toZone) {
    socket.emit('move_card', { card_id: cardId, to_zone: toZone });
}

function exertCard(cardId) {
    socket.emit('exert_card', { card_id: cardId });
}

function readyCard(cardId) {
    socket.emit('ready_card', { card_id: cardId });
}

function addDamage(cardId) {
    socket.emit('add_damage', { card_id: cardId });
}

function removeDamage(cardId) {
    socket.emit('remove_damage', { card_id: cardId });
}

function quest(cardId) {
    // Exert the card and add lore
    socket.emit('exert_card', { card_id: cardId });
    socket.emit('add_lore', { amount: 1 });
}

// Button actions
document.getElementById('draw-btn').addEventListener('click', () => {
    socket.emit('draw_card', {});
});

document.getElementById('shuffle-btn').addEventListener('click', () => {
    socket.emit('shuffle_deck', {});
});

document.getElementById('end-turn-btn').addEventListener('click', () => {
    socket.emit('end_turn', {});
});

// Pile click actions
function showDeckOptions() {
    // For now, just draw a card
    socket.emit('draw_card', {});
}

function showMysteryOptions() {
    if (gameState.turn_number >= 3) {
        if (confirm('Flip and play mystery card?')) {
            socket.emit('flip_mystery_card', {});
        }
    } else {
        alert('Mystery card can only be flipped on turn 3 or later');
    }
}

function showDiscardPile() {
    const myPlayer = gameState.players[playerId];
    const discardCards = myPlayer.zones.discard.map(id => gameState.my_cards[id]);
    showModal('Discard Pile', discardCards);
}

function showInkPile() {
    const myPlayer = gameState.players[playerId];
    const inkCards = myPlayer.zones.ink.map(id => gameState.my_cards[id]);
    showModal('Ink Pile', inkCards);
}

// Modal functions
function showModal(title, cards) {
    const modal = document.getElementById('pile-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalCards = document.getElementById('modal-cards');
    
    modalTitle.textContent = title;
    modalCards.innerHTML = '';
    
    cards.forEach(card => {
        if (card) {
            const cardElement = createCardElement(card);
            modalCards.appendChild(cardElement);
        }
    });
    
    modal.classList.remove('hidden');
}

function closeModal() {
    document.getElementById('pile-modal').classList.add('hidden');
}

// Hide context menu when clicking elsewhere
document.addEventListener('click', hideContextMenu);

function hideContextMenu() {
    document.getElementById('context-menu').classList.add('hidden');
}

// Prevent context menu from hiding when clicking on it
document.getElementById('context-menu').addEventListener('click', (e) => {
    e.stopPropagation();
});
```

---

## 🎉 That's all the files!

Here's your complete file structure:
```
github/
├── backend/
│   ├── app.py
│   ├── game_state.py
│   └── lorcana_api.py
└── UI/
    ├── game.html
    ├── style.css
    └── game.js
