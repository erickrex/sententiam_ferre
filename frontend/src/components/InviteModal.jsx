import React, { useState } from 'react';
import './InviteModal.css';

function InviteModal({ isOpen, onClose, onInvite, groupName }) {
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!username.trim()) {
      setError('Username is required');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await onInvite(username.trim());
      setUsername('');
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to send invitation');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setUsername('');
      setError('');
      onClose();
    }
  };

  const handleChange = (e) => {
    setUsername(e.target.value);
    if (error) {
      setError('');
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Invite Member</h2>
          <button 
            className="close-button" 
            onClick={handleClose}
            disabled={isSubmitting}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <p className="invite-description">
              Invite a user to join <strong>{groupName}</strong>
            </p>

            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                type="text"
                id="username"
                value={username}
                onChange={handleChange}
                className={error ? 'error' : ''}
                disabled={isSubmitting}
                placeholder="Enter username"
                autoFocus
              />
              {error && <span className="error-message">{error}</span>}
            </div>
          </div>

          <div className="modal-footer">
            <button 
              type="button" 
              className="cancel-button" 
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="submit-button" 
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Sending...' : 'Send Invitation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default InviteModal;
