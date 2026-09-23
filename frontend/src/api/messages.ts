import { api } from "./client";
import type { MessagesResponse } from "../types";

/** GET /api/v1/message/conversations/{conversationId}/messages → { messages: MessageOut[] } */
export const messagesApi = {
  getMessages: (conversationId: string) =>
    api.get<MessagesResponse>(
      `api/v1/message/conversations/${conversationId}/messages`
    ),
};
