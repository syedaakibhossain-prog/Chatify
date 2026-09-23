import { api } from "./client";
import type { Conversation } from "../types";

/** Raw shape the backend returns for a conversation detail */
export interface ConversationOut {
  id: string;
  created_at: string;
  members: { id: string; username: string }[];
}

export const conversationApi = {
  /** GET /api/v1/conversation/ → list of conversation UUIDs */
  list: () => api.get<string[]>("api/v1/conversation/"),

  /** GET /api/v1/conversation/{id} → conversation detail */
  get: (id: string) => api.get<Conversation>(`api/v1/conversation/${id}`),

  /** POST /api/v1/conversation/?user_id={userId} → new conversation */
  create: (userId: string) =>
    api.post<ConversationOut>(`api/v1/conversation/?user_id=${userId}`),
};
