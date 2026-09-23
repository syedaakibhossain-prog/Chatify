import { create } from "zustand";
import type{ AuthUser } from "../types";
import { authapi } from "../api/auth";

type AuthStatus = "idle" | "loading" | "authentecated" | "unauthenticated";

interface AuthState{
  user: AuthUser | null;
  status: AuthStatus;
  error: string | null;

  bootstrap: () => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthStore = create<AuthState>((set) => ({
  user: null,
  status: "idle",
  error: null,

  bootstrap: async () => {
    set({ status: "loading" });
    try {
      const user = await authapi.me();
      set({ user, status: "authentecated" });
    } catch {
      set({ user: null, status: "unauthenticated" });
    }
  },

  register: async (username: string, email: string, password: string) => {
    set({ status: "loading", error: null });
    try {
      const user = await authapi.register(username, email, password);
      set({ user, status: "authentecated" });
    } catch(err) {
      set({
        status: "unauthenticated",
        error: err instanceof Error ? err.message : "Registration failed"
      });
      throw err;
    }
  },
  login: async (email: string, password: string) => {
    set({ status: "loading", error: null });
    try {
      const user = await authapi.login(email, password);
      set({ user, status: "authentecated" });
    } catch (err) {
      set({
        status: "unauthenticated",
        error: err instanceof Error ? err.message : "Login failed"
      });
      throw err;
    }
  },
  logout: async () => {
    try {
      await authapi.logout();
    } finally {
      set({ user: null, status: "unauthenticated", error: null });
    }
  }

}));
