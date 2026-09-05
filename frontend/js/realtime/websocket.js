/**
 * DealFlow360 — Real-Time WebSocket Manager
 * Handles resilient WebSocket connectivity, token authentication,
 * bounded exponential-backoff reconnects, quote room subscriptions, and event dispatching.
 */
(function (global) {
  'use strict';

  class WebSocketManager {
    constructor() {
      this.socket = null;
      this.isConnected = false;
      this.isConnecting = false;
      this.reconnectAttempts = 0;
      this.maxReconnectDelay = 10000; // 10s max
      this.reconnectTimer = null;
      this.listeners = new Map();
      this.subscribedQuotes = new Set();
      this.heartbeatTimer = null;
    }

    /**
     * Build the WebSocket endpoint URL dynamically from current API configuration.
     */
    getWsUrl() {
      const baseUrl = global.DealFlowConfig?.API_BASE_URL || 'http://127.0.0.1:8000';
      const wsProtocol = baseUrl.startsWith('https') ? 'wss:' : 'ws:';
      const host = baseUrl.replace(/^https?:\/\//, '');
      const token = global.DealFlowAuth?.getAccessToken() || '';
      return `${wsProtocol}//${host}/api/v1/ws?token=${encodeURIComponent(token)}`;
    }

    /**
     * Establish WebSocket connection.
     */
    connect() {
      if (!global.DealFlowAuth?.hasToken()) {
        return;
      }

      if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
        return;
      }

      this.isConnecting = true;
      const url = this.getWsUrl();

      try {
        this.socket = new WebSocket(url);

        this.socket.onopen = () => {
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.resubscribeQuotes();
          this.dispatch('connection.status', { status: 'CONNECTED' });
        };

        this.socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleIncomingEvent(data);
          } catch (e) {
            console.warn('[WS] Failed to parse message:', event.data);
          }
        };

        this.socket.onclose = (event) => {
          this.isConnected = false;
          this.isConnecting = false;
          this.stopHeartbeat();
          this.dispatch('connection.status', { status: 'DISCONNECTED', code: event.code });

          // Only reconnect if user is still authenticated and it wasn't a clean deliberate closure
          if (global.DealFlowAuth?.hasToken() && event.code !== 1000 && event.code !== 1008) {
            this.scheduleReconnect();
          }
        };

        this.socket.onerror = () => {
          this.isConnecting = false;
          // Disconnect event will trigger reconnect
        };
      } catch (err) {
        this.isConnecting = false;
        this.scheduleReconnect();
      }
    }

    /**
     * Bounded exponential-backoff reconnect strategy (1s, 2s, 5s, 10s).
     */
    scheduleReconnect() {
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
      this.reconnectAttempts++;

      const delays = [1000, 2000, 5000, 10000];
      const delay = delays[Math.min(this.reconnectAttempts - 1, delays.length - 1)];

      this.dispatch('connection.status', { status: 'RECONNECTING', attempt: this.reconnectAttempts, delay });

      this.reconnectTimer = setTimeout(() => {
        this.connect();
      }, delay);
    }

    /**
     * Subscribe to real-time events for a specific quotation.
     * @param {number} quotationId
     */
    subscribeQuotation(quotationId) {
      if (!quotationId) return;
      this.subscribedQuotes.add(quotationId);

      if (this.isConnected && this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          action: 'subscribe',
          quotation_id: quotationId
        }));
      }
    }

    /**
     * Alias for subscribeQuotation
     * @param {number} quotationId
     */
    subscribe(quotationId) {
      return this.subscribeQuotation(quotationId);
    }

    /**
     * Re-subscribe active quote rooms upon reconnection.
     */
    resubscribeQuotes() {
      this.subscribedQuotes.forEach(qId => {
        this.subscribeQuotation(qId);
      });
    }

    /**
     * Heartbeat ping to keep connection alive.
     */
    startHeartbeat() {
      this.stopHeartbeat();
      this.heartbeatTimer = setInterval(() => {
        if (this.isConnected && this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ action: 'ping' }));
        }
      }, 30000);
    }

    stopHeartbeat() {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    }

    /**
     * Disconnect gracefully (e.g. on logout).
     */
    disconnect() {
      this.stopHeartbeat();
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
      this.subscribedQuotes.clear();

      if (this.socket) {
        this.socket.close(1000, 'User Logged Out');
        this.socket = null;
      }
      this.isConnected = false;
      this.isConnecting = false;
    }

    /**
     * Distribute incoming WebSocket events to registered listeners.
     */
    handleIncomingEvent(msg) {
      const eventName = msg.event || 'message';
      this.dispatch(eventName, msg);
      this.dispatch('*', msg);
    }

    /**
     * Register an event listener.
     * @param {string} event
     * @param {function} callback
     */
    on(event, callback) {
      if (!this.listeners.has(event)) {
        this.listeners.set(event, new Set());
      }
      this.listeners.get(event).add(callback);
    }

    /**
     * Remove an event listener.
     * @param {string} event
     * @param {function} callback
     */
    off(event, callback) {
      if (this.listeners.has(event)) {
        this.listeners.get(event).delete(callback);
      }
    }

    /**
     * Internal event dispatcher.
     */
    dispatch(event, payload) {
      if (this.listeners.has(event)) {
        this.listeners.get(event).forEach(cb => {
          try {
            cb(payload);
          } catch (e) {
            console.error('[WS] Error in event handler for', event, e);
          }
        });
      }
    }
  }

  global.DealFlowWS = new WebSocketManager();
})(typeof window !== 'undefined' ? window : this);
