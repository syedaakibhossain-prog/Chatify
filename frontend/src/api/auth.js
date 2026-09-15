// src/api/auth.js
import { fetchClient, API_BASE } from './client.js';

export async function login(email, password) {
    return fetchClient('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
    });
}

export async function register(username, email, password) {
    return fetchClient('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
    });
}

export async function logout() {
    return fetchClient('/auth/logout', { method: 'POST' });
}

export async function getMe() {
    return fetchClient('/auth/me', { method: 'GET' });
}

export async function refreshToken() {
    // Explicitly using fetch instead of fetchClient to avoid infinite retry loops
    const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
    });
    
    if (!response.ok) {
        throw new Error('Refresh failed');
    }
    
    return response.json();
}
