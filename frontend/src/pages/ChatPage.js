// src/pages/ChatPage.js
import { renderConversationList } from '../components/ConversationList.js';
import { renderMessageThread } from '../components/MessageThread.js';
import { renderMessageComposer } from '../components/MessageComposer.js';
import { createConversation, getMessages, sendMessageRest, deleteMessage } from '../api/messages.js';
import { ChatSocket } from '../api/socket.js';
import { logout } from '../api/auth.js';

export function renderChatPage(container, user, onLogout) {
    let conversations = JSON.parse(localStorage.getItem(`conversations_${user.id}`)) || [];
    let activeConversationId = null;
    let messages = [];
    let socket = null;

    function saveConversations() {
        localStorage.setItem(`conversations_${user.id}`, JSON.stringify(conversations));
    }

    container.innerHTML = `
        <div class="chat-layout">
            <div class="sidebar" id="sidebar"></div>
            <div class="chat-main">
                <div class="chat-header">
                    <div id="chat-title" class="text-md" style="flex:1;">Select a conversation</div>
                    <button id="logout-btn" class="text-sm text-muted" style="background:none;border:none;cursor:pointer;">Logout</button>
                </div>
                <div class="message-thread" id="message-thread">
                    <div class="center-container" style="height: 100%;">
                        <p class="text-muted text-sm">Select a conversation to start chatting.</p>
                    </div>
                </div>
                <div id="message-composer"></div>
            </div>
        </div>
    `;

    const sidebarContainer = document.getElementById('sidebar');
    const threadContainer = document.getElementById('message-thread');
    const composerContainer = document.getElementById('message-composer');
    const titleContainer = document.getElementById('chat-title');

    document.getElementById('logout-btn').addEventListener('click', async () => {
        try { await logout(); } catch (e) {}
        if (socket) socket.close();
        onLogout();
    });

    const updateSidebar = () => {
        renderConversationList(sidebarContainer, conversations, activeConversationId, handleSelectConversation, handleCreateConversation);
    };

    const updateThread = () => {
        if (!activeConversationId) {
            threadContainer.innerHTML = `
                <div class="center-container" style="height: 100%;">
                    <p class="text-muted text-sm">Select a conversation to start chatting.</p>
                </div>
            `;
            composerContainer.innerHTML = '';
            titleContainer.textContent = 'Select a conversation';
        } else {
            const activeConv = conversations.find(c => c.id === activeConversationId);
            titleContainer.textContent = activeConv ? (activeConv.name || 'Chat') : 'Chat';
            
            renderMessageThread(threadContainer, messages, user.id, handleDeleteMessage);
            renderMessageComposer(composerContainer, handleSendMessage);
        }
    };

    const handleCreateConversation = async () => {
        const userId = prompt("Enter the user UUID to chat with:");
        if (userId && userId.trim() !== "") {
            try {
                const res = await createConversation([userId.trim()]);
                const newConv = { id: res.id, name: 'Chat with ' + userId.substring(0,8) };
                
                if (!conversations.find(c => c.id === res.id)) {
                    conversations.push(newConv);
                    saveConversations();
                }
                handleSelectConversation(res.id);
            } catch (err) {
                alert("Failed to create conversation: " + err.message);
            }
        }
    };

    const handleSelectConversation = async (convId) => {
        activeConversationId = convId;
        updateSidebar();
        
        // Disconnect old socket
        if (socket) {
            socket.close();
        }

        try {
            messages = await getMessages(convId);
        } catch (e) {
            alert("Failed to load messages");
            messages = [];
        }
        
        updateThread();

        // Connect new socket
        socket = new ChatSocket(
            convId, 
            user.id, 
            (newMsg) => {
                // Deduplicate optimistic messages if needed, here we just append
                // In a real app we'd match by a local ID. For simplicity, we just push
                if (!messages.find(m => m.id === newMsg.id)) {
                    messages.push(newMsg);
                    updateThread();
                } else {
                    // Update existing optimistic message
                    const idx = messages.findIndex(m => m.id === newMsg.id);
                    messages[idx] = newMsg;
                    updateThread();
                }
            },
            (err) => {
                console.error("Socket error", err);
            }
        );
    };

    const handleSendMessage = (content) => {
        if (socket && activeConversationId) {
            try {
                socket.sendMessage(content);
                // Optimistic UI
                const optMsg = {
                    id: 'temp-' + Date.now(),
                    sender_id: user.id,
                    content: content,
                    created_at: new Date().toISOString(),
                    pending: true
                };
                messages.push(optMsg);
                updateThread();
            } catch (e) {
                // Fallback to REST
                sendMessageRest(activeConversationId, content).then(res => {
                    messages.push(res);
                    updateThread();
                }).catch(err => {
                    alert("Failed to send message: " + err.message);
                });
            }
        }
    };

    const handleDeleteMessage = async (msgId) => {
        try {
            const updated = await deleteMessage(msgId);
            const idx = messages.findIndex(m => m.id === msgId);
            if (idx > -1) {
                messages[idx] = updated;
                updateThread();
            }
        } catch (err) {
            alert("Failed to delete message: " + err.message);
        }
    };

    updateSidebar();
    updateThread();
}
