import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { AuthStore } from "../stroes/authStroes";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const status = AuthStore((s) => s.status);
  const login = AuthStore((s) => s.login);
  const error = AuthStore((s) => s.error);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    try {
      await login(email, password);
    } catch {
      // error is stored in the auth store
    }
  }

  if (status === "authentecated") return <Navigate to="/" replace />;

  return (
    <div className="auth-bg">
      <form className="auth-card" onSubmit={handleSubmit} noValidate>
        <div className="auth-logo">Chatify</div>
        <p className="auth-subtitle">Real-time conversations, instantly.</p>

        <h1 className="auth-title">Sign in</h1>

        {error && <div className="auth-error">{error}</div>}

        <div className="auth-field">
          <label className="auth-label" htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            className="auth-input"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoFocus
            required
          />
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="login-password">Password</label>
          <input
            id="login-password"
            type="password"
            className="auth-input"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          id="login-submit-btn"
          type="submit"
          disabled={status === "loading"}
          className="btn-primary"
        >
          {status === "loading" ? "Signing in…" : "Sign in"}
        </button>

        <p className="auth-footer">
          No account?{" "}
          <Link className="auth-link" to="/register">
            Create one
          </Link>
        </p>
      </form>
    </div>
  );
}
