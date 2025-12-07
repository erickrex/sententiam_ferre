import React from 'react';
import './MessageBubble.css';

function MessageBubble({ message, isCurrentUser }) {
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    if (isToday) {
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true 
      });
    }
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  return (
    <div className={`message-bubble ${isCurrentUser ? 'current-user' : 'other-user'}`}>
      <div className="message-content">
        {!isCurrentUser && (
          <div className="message-sender">
            {message.sender?.username || 'Unknown User'}
          </div>
        )}
        <div className="message-text">{message.text}</div>
        <div className="message-meta">
          <span className="message-time">{formatTime(message.sent_at)}</span>
          {isCurrentUser && message.is_read && (
            <span className="read-indicator">✓</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;
