'use client';
import { useEffect, useRef, useCallback } from 'react';
import { useSystemStore } from '@/store/useSystemStore';
import type { WSMessage } from '@/types';

const WS_URL = typeof window !== 'undefined'
  ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/dashboard`
  : '';

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retries = useRef(0);
  const store = useSystemStore();

  const handleMessage = useCallback((raw: string) => {
    try {
      const msg = JSON.parse(raw) as WSMessage;
      if (msg.type === 'ping') return;

      if (msg.type === 'init' && msg.data) {
        store.applyDashboard(msg.data as Record<string, unknown>);
        return;
      }

      if (msg.type === 'update' && msg.channel && msg.data) {
        if (msg.channel.includes('finance'))     store.setRevenue(msg.data as never);
        if (msg.channel.includes('ceo_status'))  store.applyDashboard(msg.data as Record<string, unknown>);
      }

      if (msg.type === 'activity' && msg.data) {
        store.addActivity(msg.data as never);
      }
    } catch { /* ignore malformed */ }
  }, [store]);

  const connect = useCallback(() => {
    if (!WS_URL || ws.current?.readyState === WebSocket.OPEN) return;

    const socket = new WebSocket(WS_URL);
    ws.current = socket;

    socket.onopen = () => {
      store.setWsConnected(true);
      retries.current = 0;
    };

    socket.onmessage = e => handleMessage(e.data as string);

    socket.onclose = () => {
      store.setWsConnected(false);
      // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
      const delay = Math.min(1000 * Math.pow(2, retries.current++), 30_000);
      reconnectTimer.current = setTimeout(connect, delay);
    };

    socket.onerror = () => socket.close();
  }, [handleMessage, store]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      ws.current?.close();
    };
  }, [connect]);
}
