import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { AuthStore } from "../stroes/authStroes";

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const status = AuthStore((s) => s.status);
  const error = AuthStore((s) => s.error);
  const register = AuthStore((s) => s.register);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    try {
      await register(username, email, password);
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

        <h1 className="auth-title">Create account</h1>

        {error && <div className="auth-error">{error}</div>}

        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-username">Username</label>
          <input
            id="reg-username"
            className="auth-input"
            placeholder="cool_username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
            maxLength={20}
          />
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-email">Email</label>
          <input
            id="reg-email"
            type="email"
            className="auth-input"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="auth-field">
          <label className="auth-label" htmlFor="reg-password">Password</label>
          <input
            id="reg-password"
            type="password"
            className="auth-input"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          id="register-submit-btn"
          type="submit"
          disabled={status === "loading"}
          className="btn-primary"
        >
          {status === "loading" ? "Creating account…" : "Create account"}
        </button>

        <p className="auth-footer">
          Already have an account?{" "}
          <Link className="auth-link" to="/login">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
