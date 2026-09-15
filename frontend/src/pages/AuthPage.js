// src/pages/AuthPage.js
import { login, register } from '../api/auth.js';

export function renderAuthPage(container, onLoginSuccess) {
    let isLogin = true;

    function render() {
        container.innerHTML = `
            <div class="center-container">
                <div class="card">
                    <h2 class="text-lg mb-24">${isLogin ? 'Log in' : 'Create account'}</h2>
                    
                    <form id="auth-form">
                        ${!isLogin ? `
                            <input type="text" id="username" placeholder="Username" required minlength="3" maxlength="20">
                        ` : ''}
                        <input type="email" id="email" placeholder="Email" required>
                        <input type="password" id="password" placeholder="Password" required>
                        ${!isLogin ? `
                            <p class="text-xs text-muted mb-16">Password must be at least 8 characters long.</p>
                        ` : ''}
                        
                        <p id="error-msg" class="text-danger text-sm mb-16 hidden"></p>
                        
                        <button type="submit" class="primary mb-16" id="submit-btn">
                            ${isLogin ? 'Log in' : 'Create account'}
                        </button>
                    </form>

                    <div class="center-container" style="height: auto;">
                        <a href="#" id="toggle-auth" class="text-sm">
                            ${isLogin ? "Don't have an account? Create one" : "Already have an account? Log in"}
                        </a>
                    </div>
                </div>
            </div>
        `;

        const form = document.getElementById('auth-form');
        const toggleBtn = document.getElementById('toggle-auth');
        const errorMsg = document.getElementById('error-msg');
        const submitBtn = document.getElementById('submit-btn');

        toggleBtn.addEventListener('click', (e) => {
            e.preventDefault();
            isLogin = !isLogin;
            render();
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            errorMsg.classList.add('hidden');
            submitBtn.disabled = true;

            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                if (isLogin) {
                    const user = await login(email, password);
                    onLoginSuccess(user);
                } else {
                    const username = document.getElementById('username').value;
                    await register(username, email, password);
                    // Automatically log in after registration
                    const user = await login(email, password);
                    onLoginSuccess(user);
                }
            } catch (err) {
                errorMsg.textContent = err.message;
                errorMsg.classList.remove('hidden');
            } finally {
                submitBtn.disabled = false;
            }
        });
    }

    render();
}
