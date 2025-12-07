import React, { useState, useEffect, useCallback } from 'react';
import { chatAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import './ChatView.css';

function ChatView({ decisionId, isClosed = false }) {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [conversationId, setConversationId] = useState(null);

  const loadMessages = useCallback(async () => {
    try {
      setError('');
      
      // Get or create conversation
      const conversationResponse = await chatAPI.getConversation(decisionId);
      setConversationId(conversationResponse.data.id);
      
      // Load messages
      const messagesResponse = await chatAPI.listMessages(decisionId);
      const messagesList = messagesResponse.data.results || messagesResponse.data || [];
      setMessages(messagesList);
    } catch (err) {
      setError(err.message || 'Failed to load messages');
      console.error('Error loading messages:', err);
    } finally {
      setLoading(false);
    }
  }, [decisionId]);

  useEffect(() => {
    loadMessages();
    
    // Poll for new messages every 5 seconds
    const interval = setInterval(() => {
      loadMessages();
    }, 5000);
    
    return () => clearInterval(interval);
  }, [loadMessages]);

  const handleSendMessage = async (text) => {
    try {
      const response = await chatAPI.sendMessage(decisionId, { text });
      
      // Add the new message to the list
      const newMessage = response.data;
      setMessages(prev => [...prev, newMessage]);
      
      return response;
    } catch (err) {
      setError(err.message || 'Failed to send message');
      throw err;
    }
  };

  return (
    <div className="chat-view">
      {error && (
        <div className="chat-error">
          {error}
          <button onClick={() => setError('')} className="dismiss-error">×</button>
        </div>
      )}
      
      <MessageList
        messages={messages}
        currentUserId={user?.id}
        loading={loading}
      />
      
      <MessageInput
        onSendMessage={handleSendMessage}
        disabled={isClosed}
      />
      
      {isClosed && (
        <div className="chat-closed-notice">
          This decision is closed. You can read messages but cannot send new ones.
        </div>
      )}
    </div>
  );
}

export default ChatView;
