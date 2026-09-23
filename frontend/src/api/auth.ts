import { api } from "./client";
import type { AuthUser } from "../types";

export const authapi = {
  register: (username: string, email: string, password: string) =>
    api.post<AuthUser>(
      "api/v1/auth/register",
      {
        username,
        email,
        password
      }
    ),

  login: (email: string, password: string) =>
    api.post<AuthUser>(
      "api/v1/auth/login",
      {
        email,
        password
      }
    ),
  logout: () => api.post<void>("api/v1/auth/logout"),
  me: () => api.get<AuthUser>("api/v1/auth/me")
}
