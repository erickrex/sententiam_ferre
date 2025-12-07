import React, { useState } from 'react';
import './MessageInput.css';

function MessageInput({ onSendMessage, disabled = false }) {
  const [text, setText] = useState('');
  const [isSending, setIsSending] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const trimmedText = text.trim();
    if (!trimmedText || isSending) return;

    setIsSending(true);
    try {
      await onSendMessage(trimmedText);
      setText('');
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="message-input" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Type a message..."
        disabled={disabled || isSending}
        rows="1"
        className="message-textarea"
      />
      <button
        type="submit"
        disabled={!text.trim() || disabled || isSending}
        className="send-button"
      >
        {isSending ? '...' : '➤'}
      </button>
    </form>
  );
}

export default MessageInput;
