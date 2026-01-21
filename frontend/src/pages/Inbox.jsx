import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useToast } from '../context/ToastContext';
import { useInbox } from '../context/InboxContext';
import { FaPaperPlane, FaVideo } from 'react-icons/fa';

const Inbox = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { fetchUnreadCount } = useInbox();
  const token = localStorage.getItem('token'); // Get token directly
  const [user, setUser] = useState(null); // State to hold current user info

  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [demoVideoUrl, setDemoVideoUrl] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);

  const messagesEndRef = useRef(null);

  // Fetch current user details
  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const response = await client.get('/users/me');
          setUser(response.data);
        } catch (error) {
          console.error("Failed to fetch user for Inbox", error);
          // Handle token expiration or invalid token
          localStorage.removeItem('token');
          navigate('/login');
        }
      } else {
        navigate('/login');
      }
    };
    fetchUser();
  }, [token, navigate]);


  const fetchConversations = useCallback(async () => {
    if (!token) return; // Don't fetch if no token
    setIsLoadingConversations(true);
    try {
      const response = await client.get('/conversations/');
      setConversations(response.data);
      fetchUnreadCount(); // Update global unread count
    } catch (error) {
      addToast('Failed to load conversations', 'error');
    } finally {
      setIsLoadingConversations(false);
    }
  }, [addToast, fetchUnreadCount, token]);

  const fetchCurrentConversation = useCallback(async () => {
    if (!conversationId || !token) { // Don't fetch if no conversationId or token
      setCurrentConversation(null);
      return;
    }
    setIsLoadingMessages(true);
    try {
      const response = await client.get(`/conversations/${conversationId}`);
      setCurrentConversation(response.data);
      setDemoVideoUrl(response.data.student_demo_video_url || '');
      fetchUnreadCount(); // Update global unread count after marking messages as read
    } catch (error) {
      addToast('Failed to load conversation', 'error');
      setCurrentConversation(null);
    } finally {
      setIsLoadingMessages(false);
    }
  }, [conversationId, addToast, fetchUnreadCount, token]);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  useEffect(() => {
    fetchCurrentConversation();
  }, [fetchCurrentConversation]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [currentConversation?.messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !currentConversation || isSending || !user) return;

    setIsSending(true);
    try {
      await client.post(`/conversations/${currentConversation.id}/messages`, { content: newMessage });
      setNewMessage('');
      fetchCurrentConversation(); // Refresh conversation to show new message
    } catch (error) {
      addToast('Failed to send message', 'error');
    } finally {
      setIsSending(false);
    }
  };

  const handleUpdateDemoVideo = async () => {
    if (!currentConversation || !user || user.id !== currentConversation.student_id) return;
    try {
      await client.patch(`/conversations/${currentConversation.id}/demo-video`, { url: demoVideoUrl });
      addToast('Demo video URL updated', 'success');
      fetchCurrentConversation();
    } catch (error) {
      addToast('Failed to update demo video URL', 'error');
    }
  };

  const handleCloseConversation = async () => {
    if (!currentConversation || !user || user.id !== currentConversation.teacher_id) return;
    if (!window.confirm('Are you sure you want to close this conversation? This action cannot be undone.')) return;

    try {
      await client.post(`/conversations/${currentConversation.id}/close`);
      addToast('Conversation closed', 'success');
      fetchCurrentConversation();
    } catch (error) {
      addToast('Failed to close conversation', 'error');
    }
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (!user) return <div className="p-10 text-center">Loading user data...</div>;

  return (
    <div className="flex h-[calc(100vh-64px)] bg-gray-100">
      {/* Left Column: Conversation List */}
      <div className="w-1/3 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">Inbox</h2>
        </div>
        {isLoadingConversations ? (
          <div className="p-4 text-gray-500">Loading conversations...</div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-gray-500">No conversations yet.</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => navigate(`/messages/${conv.id}`)}
              className={`flex items-center p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${conversationId == conv.id ? 'bg-indigo-50 border-l-4 border-indigo-500' : ''}`}
            >
              <div className="flex-shrink-0 mr-3">
                {conv.other_participant.avatar_url ? (
                  <img className="h-10 w-10 rounded-full object-cover" src={conv.other_participant.avatar_url} alt={conv.other_participant.full_name} />
                ) : (
                  <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">
                    {conv.other_participant.full_name ? conv.other_participant.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : '??'}
                  </div>
                )}
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-center">
                  <p className="text-sm font-medium text-gray-900">
                    {conv.other_participant.full_name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatDateTime(conv.updated_at)}
                  </p>
                </div>
                <p className="text-sm text-gray-600 truncate">
                  {conv.request_title}
                </p>
                {conv.unread_messages_count > 0 && (
                  <span className="text-xs font-semibold text-indigo-600">
                    {conv.unread_messages_count} unread
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Right Column: Chat Window */}
      <div className="flex-1 flex flex-col">
        {currentConversation ? (
          <>
            <div className="bg-white p-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-gray-800">{currentConversation.request_title}</h3>
                <p className="text-sm text-gray-600">
                  {user.id === currentConversation.teacher_id ? `Student: ${currentConversation.student.full_name}` : `Teacher: ${currentConversation.teacher.full_name}`}
                </p>
              </div>
              {currentConversation.status === 'open' && user.id === currentConversation.teacher_id && (
                <button
                  onClick={handleCloseConversation}
                  className="bg-red-500 hover:bg-red-600 text-white text-sm font-medium py-2 px-4 rounded-md"
                >
                  Close Conversation
                </button>
              )}
            </div>

            <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
              {isLoadingMessages ? (
                <div className="text-center text-gray-500">Loading messages...</div>
              ) : currentConversation.messages.length === 0 ? (
                <div className="text-center text-gray-500">No messages yet.</div>
              ) : (
                currentConversation.messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex mb-4 ${message.sender_id === user.id ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow ${
                        message.sender_id === user.id ? 'bg-indigo-500 text-white' : 'bg-gray-300 text-gray-800'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      <span className="block text-xs text-right opacity-75 mt-1">
                        {formatDateTime(message.created_at)}
                      </span>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {currentConversation.status === 'open' ? (
              <div className="bg-white p-4 border-t border-gray-200">
                {user.id === currentConversation.student_id && (
                  <div className="mb-4">
                    <label htmlFor="demoVideo" className="block text-sm font-medium text-gray-700">
                      Demo Video URL (for teacher)
                    </label>
                    <div className="mt-1 flex rounded-md shadow-sm">
                      <input
                        type="url"
                        name="demoVideo"
                        id="demoVideo"
                        className="flex-1 block w-full rounded-none rounded-l-md border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                        placeholder="https://youtube.com/watch?v=..."
                        value={demoVideoUrl}
                        onChange={(e) => setDemoVideoUrl(e.target.value)}
                      />
                      <button
                        type="button"
                        onClick={handleUpdateDemoVideo}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-r-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <FaVideo className="mr-2" /> Update
                      </button>
                    </div>
                    {currentConversation.student_demo_video_url && (
                        <p className="mt-2 text-sm text-gray-500">Current: <a href={currentConversation.student_demo_video_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">{currentConversation.student_demo_video_url}</a></p>
                    )}
                  </div>
                )}
                <form onSubmit={handleSendMessage} className="flex items-center">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    placeholder="Type your message..."
                    className="flex-1 border border-gray-300 rounded-l-md py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={isSending}
                  />
                  <button
                    type="submit"
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-r-md flex items-center justify-center"
                    disabled={isSending}
                  >
                    <FaPaperPlane className="mr-2" /> Send
                  </button>
                </form>
              </div>
            ) : (
              <div className="bg-white p-4 border-t border-gray-200 text-center text-gray-600">
                This conversation is closed.
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Select a conversation to start chatting.
          </div>
        )}
      </div>
    </div>
  );
};

export default Inbox;
