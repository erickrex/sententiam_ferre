import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import './MessageList.css';

function MessageList({ messages, currentUserId, loading = false }) {
  const messagesEndRef = useRef(null);
  const containerRef = useRef(null);

  const scrollToBottom = (behavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    // Scroll to bottom when messages change
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Scroll to bottom immediately on mount
    scrollToBottom('auto');
  }, []);

  if (loading) {
    return (
      <div className="message-list loading">
        <div className="loading-spinner">Loading messages...</div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="message-list empty">
        <div className="empty-state">
          <p>No messages yet</p>
          <p className="empty-hint">Start the conversation!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="message-list" ref={containerRef}>
      <div className="messages-container">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            isCurrentUser={message.sender?.id === currentUserId || message.sender_id === currentUserId}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

export default MessageList;
