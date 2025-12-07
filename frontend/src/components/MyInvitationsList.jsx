import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './MyInvitationsList.css';

function MyInvitationsList({ invitations, onAccept, onReject, onSuccess, onError }) {
  const [loadingAction, setLoadingAction] = useState(null);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const handleAccept = async (invitationId) => {
    setLoadingAction(`accept-${invitationId}`);
    try {
      await onAccept(invitationId);
      if (onSuccess) {
        onSuccess('Invitation accepted');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to accept invitation');
      }
    } finally {
      setLoadingAction(null);
    }
  };

  const handleReject = async (invitationId) => {
    setLoadingAction(`reject-${invitationId}`);
    try {
      await onReject(invitationId);
      if (onSuccess) {
        onSuccess('Invitation declined');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to reject invitation');
      }
    } finally {
      setLoadingAction(null);
    }
  };

  if (!invitations || invitations.length === 0) {
    return (
      <div className="my-invitations-list empty">
        <p className="empty-message">No invitations yet</p>
      </div>
    );
  }

  return (
    <div className="my-invitations-list">
      {invitations.map((invitation) => (
        <div key={invitation.id} className={`invitation-card ${invitation.status}`}>
          <div className="invitation-header">
            <h3 className="group-name">{invitation.group_name}</h3>
            <span className={`status-badge ${invitation.status}`}>
              {invitation.status === 'pending' ? 'Pending' : 'Rejected'}
            </span>
          </div>
          <div className="invitation-info">
            <span className="invitation-date">
              {invitation.status === 'rejected' 
                ? `Rejected ${formatDate(invitation.rejected_at)}`
                : `Invited ${formatDate(invitation.invited_at)}`
              }
            </span>
          </div>
          {invitation.status === 'pending' && (
            <div className="invitation-actions">
              <button
                className="accept-button"
                onClick={() => handleAccept(invitation.id)}
                disabled={loadingAction === `accept-${invitation.id}`}
              >
                {loadingAction === `accept-${invitation.id}` ? 'Accepting...' : 'Accept'}
              </button>
              <button
                className="reject-button"
                onClick={() => handleReject(invitation.id)}
                disabled={loadingAction === `reject-${invitation.id}`}
              >
                {loadingAction === `reject-${invitation.id}` ? 'Rejecting...' : 'Reject'}
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

MyInvitationsList.propTypes = {
  invitations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      group_name: PropTypes.string.isRequired,
      status: PropTypes.string.isRequired,
      invited_at: PropTypes.string.isRequired,
      rejected_at: PropTypes.string,
    })
  ).isRequired,
  onAccept: PropTypes.func.isRequired,
  onReject: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  onError: PropTypes.func,
};

export default MyInvitationsList;
