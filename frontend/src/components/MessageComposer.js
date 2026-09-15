// src/components/MessageComposer.js

export function renderMessageComposer(container, onSendMessage) {
    container.innerHTML = `
        <div class="composer">
            <textarea id="msg-input" placeholder="Message..."></textarea>
            <button id="send-btn" class="primary" style="width: auto;" disabled>Send &rarr;</button>
        </div>
    `;

    const input = document.getElementById('msg-input');
    const sendBtn = document.getElementById('send-btn');

    input.addEventListener('input', () => {
        sendBtn.disabled = input.value.trim() === '';
        
        // Auto-resize
        input.style.height = 'auto';
        input.style.height = (input.scrollHeight) + 'px';
    });

    const send = () => {
        const val = input.value.trim();
        if (val) {
            onSendMessage(val);
            input.value = '';
            input.style.height = 'auto';
            sendBtn.disabled = true;
        }
    };

    sendBtn.addEventListener('click', send);

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            send();
        }
    });
}
