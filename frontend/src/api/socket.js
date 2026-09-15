// src/api/socket.js

export class ChatSocket {
    constructor(conversessionId, userId, onMessage, onError) {
        this.conversessionId = conversessionId;
        this.userId = userId;
        this.onMessage = onMessage;
        this.onError = onError;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.connect();
    }

    connect() {
        const wsUrl = `ws://localhost:8000/ws/conversession/${this.conversessionId}?user_id=${this.userId}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'message') {
                    if (this.onMessage) this.onMessage(data.data);
                } else if (data.type === 'error') {
                    if (this.onError) this.onError(data.detail);
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message', e);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error', error);
            // close will be called subsequently
        };
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const timeout = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
            console.log(`Reconnecting in ${timeout}ms...`);
            setTimeout(() => this.connect(), timeout);
        } else {
            console.error('Max reconnect attempts reached.');
        }
    }

    sendMessage(content) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'message', content }));
        } else {
            throw new Error('WebSocket is not connected');
        }
    }

    close() {
        if (this.ws) {
            this.ws.onclose = null; // prevent reconnect
            this.ws.close();
        }
    }
}
