// src/api/messages.js
import { fetchClient } from './client.js';

export async function createConversation(userIds) {
    return fetchClient('/conversations', {
        method: 'POST',
        body: JSON.stringify({ user_ids: userIds })
    });
}

export async function getConversation(conversationId) {
    return fetchClient(`/conversations/${conversationId}`, { method: 'GET' });
}

export async function getMessages(conversationId) {
    // Reversing here so newest is at the bottom (oldest first)
    const messages = await fetchClient(`/messages/conversations/${conversationId}`, { method: 'GET' });
    return messages.reverse();
}

export async function sendMessageRest(conversationId, content) {
    return fetchClient(`/messages/conversations/${conversationId}`, {
        method: 'POST',
        body: JSON.stringify({ content })
    });
}

export async function editMessage(messageId, content) {
    return fetchClient(`/messages/${messageId}`, {
        method: 'PATCH',
        body: JSON.stringify({ content })
    });
}

export async function deleteMessage(messageId) {
    return fetchClient(`/messages/${messageId}`, { method: 'DELETE' });
}
