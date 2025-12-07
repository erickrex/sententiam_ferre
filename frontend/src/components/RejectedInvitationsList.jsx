import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './RejectedInvitationsList.css';

function RejectedInvitationsList({ invitations, onResend, onDelete, onSuccess, onError }) {
  const [loadingAction, setLoadingAction] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

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

  const handleResend = async (invitationId) => {
    setLoadingAction(`resend-${invitationId}`);
    try {
      await onResend(invitationId);
      if (onSuccess) {
        onSuccess('Invitation resent');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to resend invitation');
      }
    } finally {
      setLoadingAction(null);
    }
  };

  const handleDeleteClick = (invitationId) => {
    setShowDeleteConfirm(invitationId);
  };

  const handleDeleteConfirm = async (invitationId) => {
    setLoadingAction(`delete-${invitationId}`);
    try {
      await onDelete(invitationId);
      if (onSuccess) {
        onSuccess('Record deleted successfully');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to delete invitation');
      }
    } finally {
      setLoadingAction(null);
      setShowDeleteConfirm(null);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(null);
  };

  if (!invitations || invitations.length === 0) {
    return (
      <div className="rejected-invitations-list empty">
        <p className="empty-message">No rejected invitations</p>
      </div>
    );
  }

  return (
    <div className="rejected-invitations-list">
      {invitations.map((invitation) => (
        <div key={invitation.id} className="invitation-card">
          <div className="invitation-header">
            <h3 className="username">{invitation.user?.username || 'Unknown User'}</h3>
          </div>
          <div className="invitation-info">
            <span className="invitation-date">
              Rejected {formatDate(invitation.rejected_at)}
            </span>
          </div>
          <div className="invitation-actions">
            {showDeleteConfirm === invitation.id ? (
              <div className="delete-confirm">
                <p className="confirm-message">Are you sure you want to delete this invitation?</p>
                <div className="confirm-buttons">
                  <button
                    className="cancel-button"
                    onClick={handleDeleteCancel}
                    disabled={loadingAction === `delete-${invitation.id}`}
                  >
                    Cancel
                  </button>
                  <button
                    className="confirm-delete-button"
                    onClick={() => handleDeleteConfirm(invitation.id)}
                    disabled={loadingAction === `delete-${invitation.id}`}
                  >
                    {loadingAction === `delete-${invitation.id}` ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            ) : (
              <>
                <button
                  className="resend-button"
                  onClick={() => handleResend(invitation.id)}
                  disabled={loadingAction === `resend-${invitation.id}`}
                >
                  {loadingAction === `resend-${invitation.id}` ? 'Resending...' : 'Resend'}
                </button>
                <button
                  className="delete-button"
                  onClick={() => handleDeleteClick(invitation.id)}
                  disabled={loadingAction}
                >
                  Delete
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

RejectedInvitationsList.propTypes = {
  invitations: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      user: PropTypes.shape({
        username: PropTypes.string,
      }),
      rejected_at: PropTypes.string.isRequired,
    })
  ).isRequired,
  onResend: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  onError: PropTypes.func,
};

export default RejectedInvitationsList;
