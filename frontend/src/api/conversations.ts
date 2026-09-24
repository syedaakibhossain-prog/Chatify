import { api } from "./client";
import type { Conversation } from "../types";

/** Shape the backend returns for a conversation (ConversationResponse) */
export interface ConversationResponse {
  id: string;
  other_username: string;
}

export const conversationApi = {
  /** GET /api/v1/conversation/ → list of ConversationResponse objects */
  list: () => api.get<Conversation[]>("api/v1/conversation/"),

  /** POST /api/v1/conversation/?user_id={userId} → new ConversationResponse */
  create: (userId: string) =>
    api.post<Conversation>(`api/v1/conversation/?user_id=${userId}`),
};
