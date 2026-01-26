import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client from '../api/client';
import { useToast } from '../context/ToastContext';
import { useInbox } from '../context/InboxContext';
import { FaPaperPlane, FaVideo, FaReply, FaTimes, FaDollarSign } from 'react-icons/fa';
import ConfirmationModal from '../components/ConfirmationModal';

const Inbox = () => {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { fetchUnreadCount } = useInbox();
  const token = localStorage.getItem('token');
  const [user, setUser] = useState(null);

  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [newMessage, setNewMessage] = useState('');
  const [demoVideoUrl, setDemoVideoUrl] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [replyingToMessage, setReplyingToMessage] = useState(null);

  const [showOfferModal, setShowOfferModal] = useState(false);
  const [offerDescription, setOfferDescription] = useState('');
  const [offerPrice, setOfferPrice] = useState(0);

  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [modalConfig, setModalConfig] = useState({});

  const messagesContainerRef = useRef(null);
  const ws = useRef(null);

  useEffect(() => {
    const fetchUser = async () => {
      if (token) {
        try {
          const response = await client.get('/users/me');
          setUser(response.data);
        } catch (error) {
          console.error("Failed to fetch user for Inbox", error);
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
    if (!token) return;
    setIsLoadingConversations(true);
    try {
      const response = await client.get('/conversations/');
      setConversations(response.data);
    } catch (error) {
      addToast('Failed to load conversations', 'error');
    } finally {
      setIsLoadingConversations(false);
    }
  }, [addToast, token]);

  const fetchCurrentConversation = useCallback(async () => {
    if (!conversationId || !token) {
      setCurrentConversation(null);
      return;
    }
    setIsLoadingMessages(true);
    try {
      const response = await client.get(`/conversations/${conversationId}`);
      setCurrentConversation(response.data);
      setDemoVideoUrl(response.data.student_demo_video_url || '');
      setConversations(prev => prev.map(conv => 
        conv.id === parseInt(conversationId) ? { ...conv, unread_messages_count: 0 } : conv
      ));
      fetchUnreadCount();
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
    if (!conversationId || !user || !token) return;
    const wsUrl = `ws://${window.location.host.split(':')[0]}:8000/conversations/${conversationId}/ws?token=${token}`;
    ws.current = new WebSocket(wsUrl);
    ws.current.onopen = () => console.log("WebSocket connected");
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket message received:", data); // Add this log
      if (data.type === 'OFFER_ACCEPTED') {
        navigate(`/projects/${data.project_id}`);
      } else if (data.type === 'CONVERSATION_CLOSED') {
        setCurrentConversation(prev => ({ ...prev, status: 'closed' }));
        fetchConversations();
      } else if (data.type === 'MESSAGE_AND_CONVERSATION_CLOSED') {
        console.log("MESSAGE_AND_CONVERSATION_CLOSED data.message:", data.message); // Add this log
        setCurrentConversation(prev => {
          if (prev && prev.id === data.conversation_id) {
            // Ensure data.message is an object before adding
            if (data.message && typeof data.message === 'object') {
              return { ...prev, messages: [...prev.messages, data.message], status: 'closed' };
            } else {
              console.error("Received MESSAGE_AND_CONVERSATION_CLOSED with invalid message:", data.message);
              return { ...prev, status: 'closed' }; // Close without adding malformed message
            }
          }
          return prev;
        });
        let toastMessage = 'Conversation archived.';
        if (data.reason === 'student_left') {
          toastMessage = 'Student left conversation. Conversation archived.';
        } else if (data.reason === 'teacher_left') {
          toastMessage = 'You have left the conversation. It is now archived.';
        } else if (data.reason === 'request_cancelled') {
          toastMessage = 'Request cancelled by student. Conversation archived.';
        }
        addToast(toastMessage, 'info');
        fetchConversations(); // Refresh sidebar to move conversation to archive
      } else {
        setCurrentConversation((prev) => {
          if (prev && prev.id === data.conversation_id) {
            if (ws.current && ws.current.readyState === WebSocket.OPEN) {
              ws.current.send(JSON.stringify({ type: "READ_RECEIPT", message_ids: [data.id] }));
            }
            // Ensure data is an object before adding as a message
            if (data && typeof data === 'object') {
              return { ...prev, messages: [...prev.messages, data] };
            } else {
              console.error("Received regular WebSocket message with invalid data:", data);
              return prev;
            }
          }
          return prev;
        });
        if (data.sender_id !== user.id && data.conversation_id !== parseInt(conversationId)) {
          fetchUnreadCount();
        }
      }
    };
    ws.current.onclose = () => console.log("WebSocket disconnected");
    ws.current.onerror = (error) => console.error("WebSocket error:", error);
    return () => {
      if (ws.current) ws.current.close();
    };
  }, [conversationId, user, token, fetchUnreadCount, navigate, fetchConversations, addToast]);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [currentConversation?.messages]);

  useEffect(() => {
    return () => {
      fetchUnreadCount();
    };
  }, [fetchUnreadCount]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !currentConversation || isSending || !user) return;
    setIsSending(true);
    try {
      const payload = {
        content: newMessage,
        replied_to_message_id: replyingToMessage ? replyingToMessage.id : null,
      };
      await client.post(`/conversations/${currentConversation.id}/messages`, payload);
      setNewMessage('');
      setReplyingToMessage(null);
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

  const handleLeaveConversation = async () => {
    if (!currentConversation || !user || user.id !== currentConversation.student_id) return;
    setModalConfig({
      title: "Leave Conversation",
      message: "Are you sure you want to leave this conversation? This action cannot be undone.",
      onConfirm: executeLeaveConversation,
      isDanger: true,
      confirmText: "Leave"
    });
    setConfirmModalOpen(true);
  };

  const executeLeaveConversation = async () => {
    try {
      await client.post(`/conversations/${currentConversation.id}/leave`);
      addToast('Conversation left', 'success');
      // The WebSocket will handle the display of the message and archiving.
    } catch (error) {
      addToast('Failed to leave conversation', 'error');
    } finally {
      setConfirmModalOpen(false);
    }
  };

  const handleTeacherLeaveConversation = async () => {
    if (!currentConversation || !user || user.id !== currentConversation.teacher_id) return;
    setModalConfig({
      title: "Leave Conversation",
      message: "Are you sure you want to leave this conversation? This will remove the request from your list and archive this chat.",
      onConfirm: executeTeacherLeaveConversation,
      isDanger: true,
      confirmText: "Leave"
    });
    setConfirmModalOpen(true);
  };

  const executeTeacherLeaveConversation = async () => {
    try {
      await client.post(`/conversations/${currentConversation.id}/teacher-leave`);
      addToast('You have left the conversation.', 'success');
      // The WebSocket will handle the display of the message and archiving.
    } catch (error) {
      addToast('Failed to leave conversation', 'error');
    } finally {
      setConfirmModalOpen(false);
    }
  };

  const handleMakeOffer = async () => {
    if (!currentConversation || !user || user.id !== currentConversation.teacher_id) return;
    if (!offerDescription.trim() || offerPrice <= 0) {
      addToast('Please provide a description and a valid price for the offer.', 'error');
      return;
    }
    try {
      await client.post(`/conversations/${currentConversation.id}/offer`, {
        offer_description: offerDescription,
        offer_price: Math.round(offerPrice * 100),
      });
      addToast('Offer sent!', 'success');
      setShowOfferModal(false);
      setOfferDescription('');
      setOfferPrice(0);
    } catch (error) {
      addToast(error.response?.data?.detail || 'Failed to send offer', 'error');
    }
  };

  const handleAcceptOfferClick = (messageId) => {
    setModalConfig({
      title: "Accept Offer",
      message: "Are you sure you want to accept this offer? This will create a project and close all related conversations.",
      onConfirm: () => executeAcceptOffer(messageId),
      confirmText: "Accept"
    });
    setConfirmModalOpen(true);
  };

  const executeAcceptOffer = async (messageId) => {
    try {
      const response = await client.post(`/conversations/messages/${messageId}/accept-offer`);
      addToast('Offer accepted! Project created.', 'success');
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      addToast(error.response?.data?.detail || 'Failed to accept offer', 'error');
    } finally {
      setConfirmModalOpen(false);
    }
  };

  const handleRejectOfferClick = (messageId) => {
    setModalConfig({
      title: "Reject Offer",
      message: "Are you sure you want to reject this offer? This will close the conversation.",
      onConfirm: () => executeRejectOffer(messageId),
      isDanger: true,
      confirmText: "Reject"
    });
    setConfirmModalOpen(true);
  };

  const executeRejectOffer = async (messageId) => {
    try {
      await client.post(`/conversations/messages/${messageId}/reject-offer`);
      addToast('Offer rejected. Conversation closed.', 'info');
      fetchCurrentConversation();
    } catch (error) {
      addToast(error.response?.data?.detail || 'Failed to reject offer', 'error');
    } finally {
      setConfirmModalOpen(false);
    }
  };

  const formatCurrency = (amountInCents) => new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(amountInCents / 100);
  const formatDateTime = (dateString) => new Date(dateString).toLocaleString();

  if (!user) return <div className="p-10 text-center">Loading user data...</div>;

  const hasPendingOffer = currentConversation?.messages
    ?.filter(m => m && typeof m === 'object') // Filter out null/undefined/non-object items
    .some(m => m.message_type === 'offer' && m.offer_status === 'pending');

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="flex h-[calc(100vh-128px)] bg-white shadow-lg rounded-lg">
        <div className="w-1/3 border-r border-gray-200 overflow-y-auto">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-800">Inbox</h2>
          </div>
          {isLoadingConversations ? (
            <div className="p-4 text-gray-500">Loading conversations...</div>
          ) : conversations.length === 0 ? (
            <div className="p-4 text-gray-500">No conversations yet.</div>
          ) : (
            conversations.map((conv) => (
              <div key={conv.id} onClick={() => navigate(`/messages/${conv.id}`)} className={`flex items-center p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${conversationId == conv.id ? 'bg-indigo-50 border-l-4 border-indigo-500' : ''}`}>
                <div className="flex-shrink-0 mr-3">
                  {conv.other_participant.avatar_url ? <img className="h-10 w-10 rounded-full object-cover" src={conv.other_participant.avatar_url} alt={conv.other_participant.full_name} /> : <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-sm">{conv.other_participant.full_name ? conv.other_participant.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) : '??'}</div>}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <p className="text-sm font-medium text-gray-900">{conv.other_participant.full_name}</p>
                    <p className="text-sm text-gray-600 truncate">{conv.request_title}</p>
                  </div>
                  {conv.unread_messages_count > 0 && <span className="text-xs font-semibold text-indigo-600">{conv.unread_messages_count} unread</span>}
                </div>
              </div>
            ))
          )}
          <div className="p-4 border-t border-gray-200">
            <Link to="/messages/archive" className="text-indigo-600 hover:underline">View Previous Conversations</Link>
          </div>
        </div>
        <div className="flex-1 flex flex-col">
          {currentConversation ? (
            <>
              <div className="bg-white p-4 border-b border-gray-200 flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-bold text-gray-800">{currentConversation.request_title}</h3>
                  <p className="text-sm text-gray-600">{user.id === currentConversation.teacher_id ? `Student: ${currentConversation.student.full_name}` : `Teacher: ${currentConversation.teacher.full_name}`}</p>
                </div>
                <div className="flex space-x-2">
                  {currentConversation.status === 'open' && user.id === currentConversation.student_id && <button onClick={handleLeaveConversation} className="bg-gray-500 hover:bg-gray-600 text-white text-sm font-medium py-2 px-4 rounded-md">Leave Conversation</button>}
                  {currentConversation.status === 'open' && user.id === currentConversation.teacher_id && <button onClick={handleTeacherLeaveConversation} className="bg-gray-500 hover:bg-gray-600 text-white text-sm font-medium py-2 px-4 rounded-md">Leave Conversation</button>}
                </div>
              </div>
              <div ref={messagesContainerRef} className="flex-1 p-4 overflow-y-auto bg-gray-50 min-h-0">
                {isLoadingMessages ? <div className="text-center text-gray-500">Loading messages...</div> : currentConversation.messages.length === 0 ? <div className="text-center text-gray-500">No messages yet.</div> : currentConversation.messages.map((message) => (
                  <div key={message.id} className={`flex mb-4 ${message.sender_id === user.id ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow relative ${message.sender_id === user.id ? 'bg-indigo-500 text-white' : 'bg-gray-300 text-gray-800'}`}>
                      {message.replied_to_message_id && <div className={`mb-2 p-2 rounded-md border-l-4 ${message.sender_id === user.id ? 'border-indigo-300 bg-indigo-600' : 'border-gray-400 bg-gray-200'}`}><p className={`text-xs font-semibold ${message.sender_id === user.id ? 'text-indigo-100' : 'text-gray-700'}`}>{message.replied_to_sender_name || 'Deleted User'}</p><p className={`text-xs italic ${message.sender_id === user.id ? 'text-indigo-200' : 'text-gray-600'} truncate`}>{message.replied_to_message_content}</p></div>}
                      {message.message_type === 'offer' ? <div className="p-3 rounded-md bg-yellow-100 border border-yellow-300 text-yellow-800"><p className="font-bold">Offer from {message.sender_full_name}:</p><p>{message.offer_description}</p><p className="font-bold">{formatCurrency(message.offer_price)}</p>{message.offer_status === 'pending' && user.id === currentConversation.student_id && <div className="mt-2 flex space-x-2"><button onClick={() => handleAcceptOfferClick(message.id)} className="bg-green-600 hover:bg-green-700 text-white text-xs font-medium py-1 px-2 rounded-md">Accept Offer</button><button onClick={() => handleRejectOfferClick(message.id)} className="bg-red-600 hover:bg-red-700 text-white text-xs font-medium py-1 px-2 rounded-md">Reject Offer</button></div>}{message.offer_status === 'accepted' && <span className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Offer Accepted</span>}{message.offer_status === 'rejected' && <span className="mt-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Offer Rejected</span>}</div> : <p className="text-sm">{message.content}</p>}
                      <span className="block text-xs text-right opacity-75 mt-1">{formatDateTime(message.created_at)}</span>
                      {message.message_type === 'text' && currentConversation.status === 'open' && <button onClick={() => setReplyingToMessage(message)} className={`absolute -bottom-2 ${message.sender_id === user.id ? '-left-8' : '-right-8'} p-1 rounded-full bg-gray-200 text-gray-600 hover:bg-gray-300`} title="Reply"><FaReply size={12} /></button>}
                    </div>
                  </div>
                ))}
              </div>
              {currentConversation.status === 'open' ? <div className="bg-white p-4 border-t border-gray-200">{replyingToMessage && <div className="mb-2 p-2 rounded-md bg-gray-100 border-l-4 border-indigo-500 flex justify-between items-center"><div><p className="text-sm font-semibold text-gray-700">Replying to {replyingToMessage.sender_full_name}</p><p className="text-sm text-gray-600 truncate">{replyingToMessage.content}</p></div><button onClick={() => setReplyingToMessage(null)} className="text-gray-500 hover:text-gray-700"><FaTimes /></button></div>}{user.id === currentConversation.student_id && <div className="mb-4"><label htmlFor="demoVideo" className="block text-sm font-medium text-gray-700">Demo Video URL (for teacher)</label><div className="mt-1 flex rounded-md shadow-sm"><input type="url" name="demoVideo" id="demoVideo" className="flex-1 block w-full rounded-none rounded-l-md border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" placeholder="https://youtube.com/watch?v=..." value={demoVideoUrl} onChange={(e) => setDemoVideoUrl(e.target.value)} /><button type="button" onClick={handleUpdateDemoVideo} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-r-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"><FaVideo className="mr-2" /> Update</button></div>{currentConversation.student_demo_video_url && <p className="mt-2 text-sm text-gray-500">Current: <a href={currentConversation.student_demo_video_url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">{currentConversation.student_demo_video_url}</a></p>}</div>}<form onSubmit={handleSendMessage} className="flex items-center">{user.id === currentConversation.teacher_id && <button type="button" onClick={() => {setShowOfferModal(true); setOfferDescription(currentConversation.request_title); setOfferPrice(currentConversation.request.budget / 100);}} className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-l-md flex items-center justify-center mr-1" disabled={hasPendingOffer}><FaDollarSign className="mr-2" /> Make Offer</button>}<input type="text" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} placeholder="Type your message..." className="flex-1 border border-gray-300 rounded-l-md py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" disabled={isSending} /><button type="submit" className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-r-md flex items-center justify-center" disabled={isSending}><FaPaperPlane className="mr-2" /> Send</button></form></div> : <div className="bg-white p-4 border-t border-gray-200 text-center text-gray-600">This conversation is closed.</div>}
            </>
          ) : <div className="flex-1 flex items-center justify-center text-gray-500">Select a conversation to start chatting.</div>}
        </div>
      </div>
      {showOfferModal && <div className="fixed z-10 inset-0 overflow-y-auto"><div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0"><div className="fixed inset-0 transition-opacity" aria-hidden="true"><div className="absolute inset-0 bg-gray-500 opacity-75"></div></div><span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span><div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"><div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4"><h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Make Project Offer</h3><div className="space-y-4"><div><label htmlFor="offerDescription" className="block text-sm font-medium text-gray-700">Project Description</label><textarea id="offerDescription" rows="3" className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={offerDescription} onChange={(e) => setOfferDescription(e.target.value)}></textarea></div><div><label htmlFor="offerPrice" className="block text-sm font-medium text-gray-700">Offer Price (EUR)</label><input type="number" id="offerPrice" min="0" className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" value={offerPrice} onChange={(e) => setOfferPrice(parseFloat(e.target.value))} /></div></div></div><div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse"><button type="button" onClick={handleMakeOffer} className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm">Send Offer</button><button type="button" onClick={() => setShowOfferModal(false)} className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">Cancel</button></div></div></div></div>}
      <ConfirmationModal isOpen={confirmModalOpen} onClose={() => setConfirmModalOpen(false)} onConfirm={modalConfig.onConfirm} title={modalConfig.title} message={modalConfig.message} confirmText={modalConfig.confirmText} isDanger={modalConfig.isDanger} />
    </div>
  );
};

export default Inbox;
