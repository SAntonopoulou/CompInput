import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import client from '../api/client';

const InboxContext = createContext();

export function useInbox() {
  return useContext(InboxContext);
}

export const InboxProvider = ({ children }) => {
  const [unreadCount, setUnreadCount] = useState(0);
  const ws = useRef(null); // Ref for the global WebSocket
  const token = localStorage.getItem('token');

  const fetchUnreadCount = useCallback(async () => {
    if (!token) {
      setUnreadCount(0);
      return;
    }
    try {
      const response = await client.get('/conversations/summary');
      setUnreadCount(response.data.total_unread_count);
    } catch (error) {
      console.error('Failed to fetch unread message count:', error);
      setUnreadCount(0);
    }
  }, [token]);

  // Global WebSocket for real-time unread count updates
  useEffect(() => {
    if (!token) {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
      return;
    }

    // Close existing connection if token changes or component re-mounts
    if (ws.current) {
      ws.current.close();
    }

    const wsUrl = `ws://${window.location.host.split(':')[0]}:8000/conversations/ws?token=${token}`;
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log("Global Inbox WebSocket connected");
    };

    ws.current.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      if (notification.type === "UNREAD_COUNT_UPDATE") {
        setUnreadCount(notification.unread_count);
      }
    };

    ws.current.onclose = () => {
      console.log("Global Inbox WebSocket disconnected");
      // Attempt to reconnect after a delay if disconnected unexpectedly
      if (token) { // Only reconnect if user is still logged in
        setTimeout(() => {
          console.log("Attempting to reconnect global Inbox WebSocket...");
          // Re-trigger the useEffect by changing a dependency or explicitly calling connect logic
          fetchUnreadCount();
        }, 3000); 
      }
    };

    ws.current.onerror = (error) => {
      console.error("Global Inbox WebSocket error:", error);
    };

    return () => {
      if (ws.current) {
        ws.current.close();
        ws.current = null;
      }
    };
  }, [token, fetchUnreadCount]); // Reconnect if token changes

  // Initial fetch on mount
  useEffect(() => {
    fetchUnreadCount();
  }, [fetchUnreadCount]);

  // Removed setInterval polling as WebSocket will handle real-time updates

  const value = {
    unreadCount,
    fetchUnreadCount,
  };

  return (
    <InboxContext.Provider value={value}>
      {children}
    </InboxContext.Provider>
  );
};
