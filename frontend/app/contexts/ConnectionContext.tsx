"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { API_CONFIG, apiCall } from '@/app/config/api';
import { useUser } from './UserContext';

interface SSHConnection {
  connection_id: string;
  hostname: string;
  username: string;
  port: number;
  status: string;
  alive: boolean;
  connected_at?: string;
}

interface ConnectionContextType {
  activeConnection: SSHConnection | null;
  isLoading: boolean;
  error: string | null;
  refreshConnection: () => Promise<void>;
  setActiveConnection: (connection: SSHConnection | null) => void;
}

const ConnectionContext = createContext<ConnectionContextType | undefined>(undefined);

interface ConnectionProviderProps {
  children: ReactNode;
}

export function ConnectionProvider({ children }: ConnectionProviderProps) {
  const { userId, isAuthenticated } = useUser();
  const [activeConnection, setActiveConnection] = useState<SSHConnection | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // SESSION-BASED: Disconnect when user leaves the site
  const disconnectSession = useCallback(async () => {
    if (!isAuthenticated || !userId || !activeConnection) return;
    
    try {
      console.log('[ConnectionContext] Disconnecting session due to user leaving site');
      await apiCall(
        API_CONFIG.ENDPOINTS.SSH.DISCONNECT, 
        { method: 'POST' }, 
        userId
      );
      setActiveConnection(null);
      console.log('[ConnectionContext] Session disconnected successfully');
    } catch (error) {
      console.error('[ConnectionContext] Failed to disconnect session:', error);
      // Still clear the connection locally even if API call fails
      setActiveConnection(null);
    }
  }, [isAuthenticated, userId, activeConnection]);

  const refreshConnection = useCallback(async () => {
    if (!isAuthenticated || !userId) {
      setActiveConnection(null);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const data: { connections: Record<string, SSHConnection> } = await apiCall<{ connections: Record<string, SSHConnection> }>(
        API_CONFIG.ENDPOINTS.SSH.STATUS, 
        { method: 'GET' }, 
        userId
      );
      
      // Find active connection and add the connection_id from the key
      const connectionEntries = Object.entries(data.connections || {});
      const activeEntry = connectionEntries.find(
        ([, conn]: [string, SSHConnection]) => conn.status === 'connected' && conn.alive
      );
      
      if (activeEntry) {
        const [connectionId, connection] = activeEntry;
        const activeConnectionWithId = {
          ...connection,
          connection_id: connectionId // Add the connection_id from the key
        };
        setActiveConnection(activeConnectionWithId);
      } else {
        setActiveConnection(null);
      }
    } catch (error) {
      console.error('Failed to fetch connection status:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch connection status');
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated, userId]);

  // Refresh connection when user changes or authentication state changes
  useEffect(() => {
    refreshConnection();
  }, [refreshConnection]);

  // Set up polling for connection status
  useEffect(() => {
    if (!isAuthenticated || !userId) return;

    const interval = setInterval(refreshConnection, API_CONFIG.POLLING.CONNECTION_STATUS);
    return () => clearInterval(interval);
  }, [userId, isAuthenticated, refreshConnection]);

  // SESSION-BASED: Auto-disconnect when user leaves site
  useEffect(() => {
    if (!isAuthenticated || !userId) return;

        const handleBeforeUnload = () => {
      // Use sendBeacon for reliable disconnect on page unload
      if (activeConnection) {
        const url = `${API_CONFIG.PING_BACKEND_URL}${API_CONFIG.ENDPOINTS.SSH.DISCONNECT}`;
        const data = JSON.stringify({});
        
        // Use sendBeacon for better reliability on page unload
        if (navigator.sendBeacon) {
          const blob = new Blob([data], { type: 'application/json' });
          navigator.sendBeacon(url, blob);
        } else {
          // Fallback for older browsers
          disconnectSession();
        }
        console.log('[ConnectionContext] Page unload: Disconnecting session');
      }
    };

        const handleVisibilityChange = () => {
          // REMOVED: Aggressive disconnect on tab blur was causing execution failures
          // Keep connection alive for better UX - server will timeout after 60 minutes
          if (document.visibilityState === 'hidden') {
            console.log('[ConnectionContext] Page hidden: Keeping connection alive (no auto-disconnect)');
          }
        };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isAuthenticated, userId, activeConnection, disconnectSession]);

  const value: ConnectionContextType = {
    activeConnection,
    isLoading,
    error,
    refreshConnection,
    setActiveConnection,
  };

  return (
    <ConnectionContext.Provider value={value}>
      {children}
    </ConnectionContext.Provider>
  );
}

export function useConnection() {
  const context = useContext(ConnectionContext);
  if (context === undefined) {
    throw new Error('useConnection must be used within a ConnectionProvider');
  }
  return context;
}