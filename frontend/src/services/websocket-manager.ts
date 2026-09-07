const WS_URL = `${location.protocol === 'https:' ? 'wss:' : 'ws:'}//${location.host}/api/v1/ws/stream`;

type MessageHandler = (data: unknown) => void;

class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private subscribedTopics = new Set<string>();
  private handlers = new Map<string, Set<MessageHandler>>();
  private _isConnected = false;
  private intentionalClose = false;
  private reconnectDelay = 3000;      // starts at 3s
  private readonly maxReconnectDelay = 60000;  // caps at 60s
  private missedHeartbeats = 0;

  get isConnected() {
    return this._isConnected;
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.intentionalClose = false;

    let connectionUrl = WS_URL;
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
        connectionUrl += `?token=${token}`;
    }

    try {
      this.ws = new WebSocket(connectionUrl);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._isConnected = true;
      this.missedHeartbeats = 0;
      this.reconnectDelay = 3000;  // reset backoff on successful connection
      this.resubscribeAll();
      this.startHeartbeat();
      this.emit('connection_state', { connected: true });
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.event === 'pong') {
          this.missedHeartbeats = 0;
          return;
        }
        const handlers = this.handlers.get(msg.event);
        if (handlers) {
          handlers.forEach((h) => h(msg.data));
        }
        const wildcard = this.handlers.get('*');
        if (wildcard) {
          wildcard.forEach((h) => h(msg));
        }
      } catch {
        // ignore parse errors
      }
    };

    this.ws.onclose = () => {
      this._isConnected = false;
      this.stopHeartbeat();
      this.emit('connection_state', { connected: false });
      if (!this.intentionalClose) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  emit(event: string, data: unknown) {
    const handlers = this.handlers.get(event);
    if (handlers) {
      handlers.forEach((h) => h(data));
    }
  }

  disconnect() {
    this.intentionalClose = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
    this._isConnected = false;
  }

  subscribe(topic: string) {
    this.subscribedTopics.add(topic);
    this.send({ action: 'subscribe', topic });
  }

  unsubscribe(topic: string) {
    this.subscribedTopics.delete(topic);
    this.send({ action: 'unsubscribe', topic });
  }

  on(event: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event)!.add(handler);
    return () => {
      this.handlers.get(event)?.delete(handler);
    };
  }

  off(event: string, handler: MessageHandler) {
    this.handlers.get(event)?.delete(handler);
  }

  private send(data: unknown) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private resubscribeAll() {
    this.subscribedTopics.forEach((topic) => {
      this.send({ action: 'subscribe', topic });
    });
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      this.missedHeartbeats++;
      if (this.missedHeartbeats >= 3) {
        this.ws?.close();
        return;
      }
      this.send({ action: 'ping' });
    }, 15000);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect() {
    if (this.intentionalClose) return;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = setTimeout(() => this.connect(), this.reconnectDelay);
    // Exponential backoff: double delay each attempt, cap at maxReconnectDelay
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
  }
}

export const wsManager = new WebSocketManager();