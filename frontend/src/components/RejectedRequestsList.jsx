import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './RejectedRequestsList.css';

function RejectedRequestsList({ requests, onDelete, onSuccess, onError }) {
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

  const handleDeleteClick = (requestId) => {
    setShowDeleteConfirm(requestId);
  };

  const handleDeleteConfirm = async (requestId) => {
    setLoadingAction(`delete-${requestId}`);
    try {
      await onDelete(requestId);
      if (onSuccess) {
        onSuccess('Record deleted successfully');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to delete request');
      }
    } finally {
      setLoadingAction(null);
      setShowDeleteConfirm(null);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(null);
  };

  if (!requests || requests.length === 0) {
    return (
      <div className="rejected-requests-list empty">
        <p className="empty-message">No rejected requests</p>
      </div>
    );
  }

  return (
    <div className="rejected-requests-list">
      {requests.map((request) => (
        <div key={request.id} className="request-card">
          <div className="request-header">
            <h3 className="username">{request.user?.username || 'Unknown User'}</h3>
          </div>
          <div className="request-info">
            <span className="request-date">
              Rejected {formatDate(request.rejected_at)}
            </span>
          </div>
          <div className="request-actions">
            {showDeleteConfirm === request.id ? (
              <div className="delete-confirm">
                <p className="confirm-message">Are you sure you want to delete this request?</p>
                <div className="confirm-buttons">
                  <button
                    className="cancel-button"
                    onClick={handleDeleteCancel}
                    disabled={loadingAction === `delete-${request.id}`}
                  >
                    Cancel
                  </button>
                  <button
                    className="confirm-delete-button"
                    onClick={() => handleDeleteConfirm(request.id)}
                    disabled={loadingAction === `delete-${request.id}`}
                  >
                    {loadingAction === `delete-${request.id}` ? 'Deleting...' : 'Delete'}
                  </button>
                </div>
              </div>
            ) : (
              <button
                className="delete-button"
                onClick={() => handleDeleteClick(request.id)}
                disabled={loadingAction}
              >
                Delete
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

RejectedRequestsList.propTypes = {
  requests: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      user: PropTypes.shape({
        username: PropTypes.string,
      }),
      rejected_at: PropTypes.string.isRequired,
    })
  ).isRequired,
  onDelete: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  onError: PropTypes.func,
};

export default RejectedRequestsList;
