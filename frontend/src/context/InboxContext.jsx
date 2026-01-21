import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import client from '../api/client';

const InboxContext = createContext();

export const useInbox = () => useContext(InboxContext);

export const InboxProvider = ({ children }) => {
  const [unreadCount, setUnreadCount] = useState(0);
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

  useEffect(() => {
    fetchUnreadCount();
    // Optionally, set up an interval to poll for new messages
    const interval = setInterval(fetchUnreadCount, 60000); // every 60 seconds
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

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
