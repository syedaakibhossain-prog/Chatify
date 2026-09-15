// src/main.js
import { getMe } from './api/auth.js';
import { renderAuthPage } from './pages/AuthPage.js';
import { renderChatPage } from './pages/ChatPage.js';

const appContainer = document.getElementById('app');

async function init() {
    try {
        const user = await getMe();
        if (user) {
            renderChatPage(appContainer, user, handleLogout);
    } catch (err) {
        // Not logged in or token expired
        renderAuthPage(appContainer, handleLoginSuccess);
    }
}

function handleLoginSuccess(user) {
    renderChatPage(appContainer, user, handleLogout);
}

function handleLogout() {
    renderAuthPage(appContainer, handleLoginSuccess);
}

document.addEventListener('DOMContentLoaded', init);
