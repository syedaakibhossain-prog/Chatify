// src/components/ConversationList.js

export function renderConversationList(container, conversations, activeId, onSelect, onCreateNew) {
    container.innerHTML = `
        <div class="sidebar-header">
            <h1 class="text-md">Chatify</h1>
            <button id="new-chat-btn" class="text-accent" style="background:none;border:none;cursor:pointer;font-size:18px;">+</button>
        </div>
        <div class="conv-list" id="conv-list">
            ${conversations.length === 0 ? `
                <div class="center-container" style="height: 100%;">
                    <p class="text-muted text-sm">No conversations yet</p>
                </div>
            ` : conversations.map(c => `
                <div class="conv-row ${c.id === activeId ? 'active' : ''}" data-id="${c.id}">
                    <div class="text-base">${c.name || c.id.substring(0,8)}</div>
                </div>
            `).join('')}
        </div>
    `;

    document.getElementById('new-chat-btn').addEventListener('click', onCreateNew);

    const rows = document.querySelectorAll('.conv-row');
    rows.forEach(row => {
        row.addEventListener('click', () => {
            onSelect(row.dataset.id);
        });
    });
}
