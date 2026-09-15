// src/components/MessageThread.js

export function renderMessageThread(container, messages, currentUserId, onDeleteMessage) {
    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="center-container" style="height:100%;">
                <p class="text-muted text-sm">No messages yet.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = messages.map(msg => {
        const isIncoming = msg.sender_id !== currentUserId;
        const alignClass = isIncoming ? 'incoming' : 'outgoing';
        
        if (msg.is_deleted) {
            return `
                <div class="message-row ${alignClass}">
                    <div class="message-bubble deleted">message deleted</div>
                </div>
            `;
        }

        const date = new Date(msg.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const pendingClass = msg.pending ? 'pending' : '';
        
        return `
            <div class="message-row ${alignClass}">
                <div class="message-bubble ${alignClass} ${pendingClass}">
                    ${escapeHTML(msg.content)}
                    ${!isIncoming && !msg.pending ? `
                        <div class="text-xs" style="text-align:right; margin-top:4px;">
                            <a href="#" class="text-muted delete-msg-btn" data-id="${msg.id}" style="font-size:11px;">delete</a>
                        </div>
                    ` : ''}
                </div>
                <div class="timestamp">${date}</div>
            </div>
        `;
    }).join('');

    const deleteBtns = container.querySelectorAll('.delete-msg-btn');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            // In a real app, maybe inline confirm
            if (confirm('Delete this message?')) {
                onDeleteMessage(btn.dataset.id);
            }
        });
    });

    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}
