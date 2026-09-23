//auth response
export interface AuthUser{
  user_id: string;
  username: string;
  email: string;
}

//response - search
export interface PublicUser{
  id: string;
  username: string;
  email: string;
}

//response - Conversation
export interface Conversation{
  id: string;
  created_at: string;
  members: Pick<PublicUser, "id" | "username">[];
}

//response - single message
export interface Message{
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  type: "text" | "image" | "file" | "system";
  created_st: string;
  is_deleted: boolean;

  pending?: boolean;
  failed?: boolean;
  temp_id?: string;
}

//response - messages list (API envelope)
export interface MessagesResponse{
  messages: Message[];
}

/** @deprecated use Message instead */
export type Messages = MessagesResponse;

//websockets frames
export interface WsReady {
  type: "ready";
  user_id: string;
  conversations: string[];
}
export interface WsPong {
  type: "pong";
}
export interface WsMessageNew {
  type: "message:new";
  message: Message;
}
export interface WsMessageAck {
  type: "message:ack";
  temp_id: string | null;
  message: Message;
}
export interface WsTypingUpdate {
  type: "typing:update";
  conversation_id: string;
  user_id: string;
  username: string;
  is_typing: boolean;
}
export interface WsReadUpdate {
  type: "read:update";
  conversation_id: string;
  user_id: string;
}
export interface WsError {
  type: "error";
  detail: string;
}

export type WsInbound =
  | WsReady
  | WsPong
  | WsMessageNew
  | WsMessageAck
  | WsTypingUpdate
  | WsReadUpdate
  | WsError;
