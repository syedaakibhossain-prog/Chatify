import type { WsInbound } from "../types";

type Listener = (msg: WsInbound) => void;

/**
 * Singleton WebSocket client for the Chatify realtime channel.
 *
 * Connect via ws://127.0.0.1:5173/v1/realtime/ws (proxied by Vite to the backend).
 * Auth is done via HTTP-only cookies set at login — no token in the URL needed.
 */
class ChatSocket {
  private ws: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = false;
  private reconnectDelay = 2000;

  connect(): void {
    if (this.ws && this.ws.readyState <= WebSocket.OPEN) return;

    this.shouldReconnect = true;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/v1/realtime/ws`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectDelay = 2000;
      this._startPing();
    };

    this.ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data) as WsInbound;
        this.listeners.forEach((fn) => fn(msg));
      } catch {
        // ignore malformed frames
      }
    };

    this.ws.onclose = () => {
      this._stopPing();
      if (this.shouldReconnect) {
        this.reconnectTimeout = setTimeout(() => {
          this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 15000);
          this.connect();
        }, this.reconnectDelay);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    if (this.reconnectTimeout) clearTimeout(this.reconnectTimeout);
    this._stopPing();
    this.ws?.close();
    this.ws = null;
  }

  send(payload: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  sendMessage(conversationId: string, content: string, tempId: string): void {
    this.send({
      type: "message:send",
      conversation_id: conversationId,
      content,
      temp_id: tempId,
    });
  }

  sendTypingStart(conversationId: string): void {
    this.send({ type: "typing:start", conversation_id: conversationId });
  }

  sendTypingStop(conversationId: string): void {
    this.send({ type: "typing:stop", conversation_id: conversationId });
  }

  sendMessageRead(conversationId: string): void {
    this.send({ type: "message:read", conversation_id: conversationId });
  }

  subscribe(fn: Listener): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private _startPing(): void {
    this._stopPing();
    this.pingInterval = setInterval(() => {
      this.send({ type: "ping" });
    }, 25_000);
  }

  private _stopPing(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

export const chatSocket = new ChatSocket();
