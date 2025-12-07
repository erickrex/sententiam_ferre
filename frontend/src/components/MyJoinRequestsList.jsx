import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './MyJoinRequestsList.css';

function MyJoinRequestsList({ requests, onResend, onDelete, onSuccess, onError }) {
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

  const handleResend = async (requestId) => {
    setLoadingAction(`resend-${requestId}`);
    try {
      await onResend(requestId);
      if (onSuccess) {
        onSuccess('Request resent');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to resend request');
      }
    } finally {
      setLoadingAction(null);
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
      <div className="my-join-requests-list empty">
        <p className="empty-message">No join requests yet</p>
      </div>
    );
  }

  // Sort: pending first, then rejected by date descending
  const sortedRequests = [...requests].sort((a, b) => {
    if (a.status === 'pending' && b.status !== 'pending') return -1;
    if (a.status !== 'pending' && b.status === 'pending') return 1;
    return new Date(b.rejected_at || b.invited_at) - new Date(a.rejected_at || a.invited_at);
  });

  return (
    <div className="my-join-requests-list">
      {sortedRequests.map((request) => (
        <div key={request.id} className={`request-card ${request.status}`}>
          <div className="request-header">
            <h3 className="group-name">{request.group_name}</h3>
            <span className={`status-badge ${request.status}`}>
              {request.status === 'pending' ? 'Pending' : 'Rejected'}
            </span>
          </div>
          <div className="request-info">
            <span className="request-date">
              {request.status === 'rejected' 
                ? `Rejected ${formatDate(request.rejected_at)}`
                : `Requested ${formatDate(request.invited_at)}`
              }
            </span>
          </div>
          {request.status === 'rejected' && (
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
                <>
                  <button
                    className="resend-button"
                    onClick={() => handleResend(request.id)}
                    disabled={loadingAction === `resend-${request.id}`}
                  >
                    {loadingAction === `resend-${request.id}` ? 'Resending...' : 'Resend'}
                  </button>
                  <button
                    className="delete-button"
                    onClick={() => handleDeleteClick(request.id)}
                    disabled={loadingAction}
                  >
                    Delete
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

MyJoinRequestsList.propTypes = {
  requests: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      group_name: PropTypes.string.isRequired,
      status: PropTypes.string.isRequired,
      invited_at: PropTypes.string.isRequired,
      rejected_at: PropTypes.string,
    })
  ).isRequired,
  onResend: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  onError: PropTypes.func,
};

export default MyJoinRequestsList;
