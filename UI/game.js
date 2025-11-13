let gameState = null;
let playerId = null;
let gameId = null;
let socket = null;

window.addEventListener('DOMContentLoaded', async () => {
    try {
        console.log('Fetching test game...');
        
        const response = await fetch('/test_game');
        
        if (!response.ok) {
            throw new Error('Failed to fetch test game: ' + response.status);
        }
        
        const data = await response.json();
        console.log('Test game data received:', data);
        
        gameId = data.game_id;
        playerId = data.player_id;
        gameState = data.state;
        
        console.log('Game ID:', gameId);
        console.log('Player ID:', playerId);
        
        socket = io();
        
        socket.on('connect', () => {
            console.log('Socket connected');
            socket.emit('join_game', { game_id: gameId, player_id: playerId });
        });
        
        socket.on('game_joined', () => {
            console.log('Successfully joined game');
        });
        
        socket.on('game_update', (newState) => {
            console.log('Game update received');
            gameState = newState;
            renderGame();
        });
        
        socket.on('error', (data) => {
            console.error('Game error:', data);
            alert(data.message);
        });
        
        document.getElementById('loading').classList.add('hidden');
        renderGame();
        
    } catch (error) {
        console.error('Error initializing game:', error);
        document.getElementById('loading').innerHTML = '<h2>Error Loading Game</h2><p style="color: #f44336;">' + error.message + '</p><p>Check the console for details (F12)</p>';
    }
});

function renderGame() {
    if (!gameState) return;
    
    const numPlayers = Object.keys(gameState.players).length;
    const gameLayout = document.getElementById('game-layout');
    gameLayout.className = 'players-' + numPlayers;
    
    document.getElementById('turn-number').textContent = gameState.turn_number;
    const currentPlayerName = gameState.players[gameState.current_turn].username;
    document.getElementById('current-player-name').textContent = currentPlayerName;
    
    renderYourBoard();
    renderOpponentBoards();
}

function renderYourBoard() {
    const yourArea = document.getElementById('your-area');
    const myPlayer = gameState.players[playerId];
    
    // Always rebuild to avoid state issues
    yourArea.innerHTML = '<div class="player-header"><h2>' + myPlayer.username + '</h2><div class="lore-counter">Lore: <span id="your-lore">' + myPlayer.lore + '</span> / 20</div></div><div class="zones-container"><div class="zone-container"><div class="zone-label">Ready Characters</div><div id="ready-zone" class="card-zone ready-zone"></div></div><div class="zone-container"><div class="zone-label">Summoning (Drying)</div><div id="summoning-zone" class="card-zone summoning-zone"></div></div><div id="piles-area"></div><div class="zone-container"><div class="zone-label">Your Hand</div><div id="hand-zone" class="card-zone hand-zone"></div></div></div>';
    
    // Build piles area
    const pilesArea = document.getElementById('piles-area');
    pilesArea.innerHTML = '<div class="pile"><div class="pile-label">Deck</div><div class="pile-count">' + myPlayer.zone_counts.deck + '</div><div class="card-back"></div></div><div class="pile"><div class="pile-label">Mystery</div><div class="pile-count">' + myPlayer.zone_counts.mystery + '</div><div class="card-back"></div></div><div class="pile"><div class="pile-label">Discard</div><div class="pile-count">' + myPlayer.zone_counts.discard + '</div><div class="card-back discard-back"></div></div><div class="pile"><div class="pile-label">Ink</div><div class="pile-count">' + myPlayer.zone_counts.ink + '</div><div class="card-back ink-back"></div></div>';
    
    // Add click handlers to piles
    pilesArea.children[0].onclick = showDeckOptions;
    pilesArea.children[1].onclick = showMysteryOptions;
    pilesArea.children[2].onclick = showDiscardPile;
    pilesArea.children[3].onclick = showInkPile;
    
    // Render zones
    renderZone('hand-zone', myPlayer.zones.hand, true);
    renderZone('ready-zone', myPlayer.zones.ready, true);
    renderZone('summoning-zone', myPlayer.zones.summoning, true);
}
function renderOpponentBoards() {
    const opponentsArea = document.getElementById('opponents-area');
    opponentsArea.innerHTML = '';
    
    const opponentIds = Object.keys(gameState.players).filter(pid => pid !== playerId);
    
    opponentIds.forEach(opponentId => {
        const opponent = gameState.players[opponentId];
        const opponentDiv = document.createElement('div');
        opponentDiv.className = 'player-area opponent';
        opponentDiv.id = 'opponent-' + opponentId;
        
        opponentDiv.innerHTML = '<div class="player-header"><h2>' + opponent.username + '</h2><div class="lore-counter">Lore: ' + opponent.lore + ' / 20</div></div><div class="zones-container"><div class="zone-container"><div class="zone-label">Ready Characters</div><div id="opponent-ready-' + opponentId + '" class="card-zone ready-zone"></div></div><div class="zone-container"><div class="zone-label">Summoning (Drying)</div><div id="opponent-summoning-' + opponentId + '" class="card-zone summoning-zone"></div></div><div class="piles-area"><div class="pile"><div class="pile-label">Deck</div><div class="pile-count">' + opponent.zone_counts.deck + '</div><div class="card-back"></div></div><div class="pile"><div class="pile-label">Mystery</div><div class="pile-count">' + opponent.zone_counts.mystery + '</div><div class="card-back"></div></div><div class="pile" onclick="showOpponentDiscard(\'' + opponentId + '\')"><div class="pile-label">Discard</div><div class="pile-count">' + opponent.zone_counts.discard + '</div><div class="card-back discard-back"></div></div><div class="pile" onclick="showOpponentInk(\'' + opponentId + '\')"><div class="pile-label">Ink</div><div class="pile-count">' + opponent.zone_counts.ink + '</div><div class="card-back ink-back"></div></div></div><div class="zone-container"><div class="zone-label">Hand</div><div id="opponent-hand-' + opponentId + '" class="card-zone hand-zone"></div></div></div>';
        
        opponentsArea.appendChild(opponentDiv);
        
        renderOpponentZone('opponent-ready-' + opponentId, opponentId, 'ready');
        renderOpponentZone('opponent-summoning-' + opponentId, opponentId, 'summoning');
        renderOpponentHand('opponent-hand-' + opponentId, opponent.zone_counts.hand);
    });
}

function renderZone(zoneId, cardIds, isYourCard) {
    const zoneElement = document.getElementById(zoneId);
    if (!zoneElement) {
        console.error('Zone element not found:', zoneId);
        return;
    }
    
    zoneElement.innerHTML = '';
    
    console.log('Rendering zone:', zoneId, 'with cards:', cardIds);
    
    if (!cardIds) {
        console.warn('No cardIds provided for zone:', zoneId);
        return;
    }
    
    if (!Array.isArray(cardIds)) {
        console.error('cardIds is not an array for zone:', zoneId, 'got:', typeof cardIds, cardIds);
        return;
    }
    
    cardIds.forEach(cardId => {
        const card = gameState.my_cards[cardId];
        if (!card) {
            console.warn('Card not found in my_cards:', cardId);
            return;
        }
        
        const cardElement = createCardElement(card, isYourCard);
        zoneElement.appendChild(cardElement);
    });
    
    console.log('Zone', zoneId, 'rendered with', zoneElement.children.length, 'cards');
}

function renderOpponentZone(zoneId, opponentId, zoneName) {
    const zoneElement = document.getElementById(zoneId);
    if (!zoneElement) return;
    
    zoneElement.innerHTML = '';
    
    const visibleCards = Object.values(gameState.visible_cards || {}).filter(card => 
        card.owner === opponentId && card.zone === zoneName
    );
    
    visibleCards.forEach(card => {
        const cardElement = createCardElement(card, false);
        zoneElement.appendChild(cardElement);
    });
}

function renderOpponentHand(zoneId, cardCount) {
    const zoneElement = document.getElementById(zoneId);
    if (!zoneElement) return;
    
    zoneElement.innerHTML = '';
    
    for (let i = 0; i < cardCount; i++) {
        const cardBack = document.createElement('div');
        cardBack.className = 'card';
        cardBack.innerHTML = '<div class="card-back">?</div>';
        zoneElement.appendChild(cardBack);
    }
}

function createCardElement(card, isYourCard) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card';
    cardDiv.dataset.cardId = card.id;
    
    if (card.exerted) {
        cardDiv.classList.add('exerted');
    }
    
    if (card.image_url) {
        cardDiv.style.backgroundImage = 'url(' + card.image_url + ')';
    } else {
        cardDiv.innerHTML = '<div class="card-back">?</div>';
    }
    
    if (card.damage > 0) {
        const damageCounter = document.createElement('div');
        damageCounter.className = 'damage-counter';
        damageCounter.textContent = card.damage;
        cardDiv.appendChild(damageCounter);
    }
    
    if (isYourCard) {
        cardDiv.addEventListener('click', (e) => {
            e.stopPropagation();
            showCardMenu(card, e.clientX, e.clientY);
        });
    }
    
    return cardDiv;
}

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
    
    menu.style.left = x + 'px';
    menu.style.top = y + 'px';
    menu.classList.remove('hidden');
}

function getCardOptions(card) {
    const options = [];
    const myPlayer = gameState.players[playerId];
    
    switch (card.zone) {
        case 'hand':
            options.push({ label: 'Play Card', action: () => playCard(card.id) });
            
            if (!myPlayer.has_inked_this_turn) {
                options.push({ label: 'Ink Card', action: () => inkCard(card.id) });
            }
            
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
    socket.emit('exert_card', { card_id: cardId });
    socket.emit('add_lore', { amount: 1 });
}

document.getElementById('draw-btn').addEventListener('click', () => {
    socket.emit('draw_card', {});
});

document.getElementById('shuffle-btn').addEventListener('click', () => {
    socket.emit('shuffle_deck', {});
});

document.getElementById('end-turn-btn').addEventListener('click', () => {
    socket.emit('end_turn', {});
});

function showDeckOptions() {
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

function showOpponentDiscard(opponentId) {
    const visibleCards = Object.values(gameState.visible_cards || {}).filter(card => 
        card.owner === opponentId && card.zone === 'discard'
    );
    const opponent = gameState.players[opponentId];
    showModal(opponent.username + "'s Discard Pile", visibleCards);
}

function showOpponentInk(opponentId) {
    const visibleCards = Object.values(gameState.visible_cards || {}).filter(card => 
        card.owner === opponentId && card.zone === 'ink' && card.face_up
    );
    const opponent = gameState.players[opponentId];
    showModal(opponent.username + "'s Ink Pile", visibleCards);
}

function showModal(title, cards) {
    const modal = document.getElementById('pile-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalCards = document.getElementById('modal-cards');
    
    modalTitle.textContent = title;
    modalCards.innerHTML = '';
    
    cards.forEach(card => {
        if (card) {
            const cardElement = createCardElement(card, false);
            modalCards.appendChild(cardElement);
        }
    });
    
    modal.classList.remove('hidden');
}

function closeModal() {
    document.getElementById('pile-modal').classList.add('hidden');
}

document.addEventListener('click', hideContextMenu);

function hideContextMenu() {
    document.getElementById('context-menu').classList.add('hidden');
}

document.getElementById('context-menu').addEventListener('click', (e) => {
    e.stopPropagation();
});
