'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  data?: unknown;
  [key: string]: unknown;
}

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

/**
 * Hook for consuming WebSocket real-time updates.
 * Handles reconnection, message parsing, and lifecycle management.
 */
export function useWebSocket(
  url: string,
  options: UseWebSocketOptions = {}
) {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectDelay = 3000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    if (isConnecting) {
      return;
    }

    setIsConnecting(true);

    try {
      const resolvedUrl = (() => {
        if (url.startsWith('ws://') || url.startsWith('wss://')) {
          return url;
        }

        if (url.startsWith('http://') || url.startsWith('https://')) {
          return url.replace(/^http/, 'ws');
        }

        const backendUrl = (process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000").replace(/\/+$|\/api\/v1$/, '');
        if (backendUrl && /^https?:\/\//.test(backendUrl)) {
          const webSocketProtocol = backendUrl.startsWith('https://') ? 'wss:' : 'ws:';
          const backendHost = backendUrl.replace(/^https?:/, '');
          return `${webSocketProtocol}${backendHost}${url.startsWith('/') ? url : `/${url}`}`;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}${url.startsWith('/') ? url : `/${url}`}`;
      })();

      console.debug(`Resolved WebSocket URL for ${url}:`, resolvedUrl);
      const ws = new WebSocket(resolvedUrl);

      ws.onopen = () => {
        console.log(`WebSocket connected to ${url}`);
        setIsConnected(true);
        setIsConnecting(false);
        reconnectCountRef.current = 0;
        onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          onMessage?.(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        console.error(`WebSocket error on ${url}:`, error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log(`WebSocket disconnected from ${url}`);
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        // Attempt to reconnect
        if (reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log(`Reconnecting... (attempt ${reconnectCountRef.current}/${reconnectAttempts})`);
            connect();
          }, reconnectDelay);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setIsConnecting(false);
    }
  }, [url, isConnecting, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectDelay]);

  // Connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Send message function
  const send = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Keep-alive ping
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      send({ action: 'ping' });
    }, 30000); // Ping every 30 seconds

    return () => clearInterval(pingInterval);
  }, [isConnected, send]);

  return {
    isConnected,
    isConnecting,
    send,
    ws: wsRef.current,
  };
}
