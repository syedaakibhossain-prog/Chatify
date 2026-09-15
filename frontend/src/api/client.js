// src/api/client.js
import { refreshToken } from './auth.js';

export const API_BASE = 'http://localhost:8000';

export async function fetchClient(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultOptions = {
        credentials: 'include', // Important for cookies
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: { ...defaultOptions.headers, ...options.headers },
    };

    let response = await fetch(url, finalOptions);

    if (response.status === 401 && endpoint !== '/auth/login' && endpoint !== '/auth/refresh') {
        // Try refresh once
        try {
            await refreshToken();
            // Retry original request
            response = await fetch(url, finalOptions);
        } catch (error) {
            // Refresh failed, probably need to login again
            throw new Error('Unauthorized');
        }
    }

    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch (e) {
            errorData = { detail: 'An error occurred' };
        }
        throw new Error(errorData.detail || response.statusText);
    }

    if (response.status === 204) {
        return null; // No content
    }

    return response.json();
}
