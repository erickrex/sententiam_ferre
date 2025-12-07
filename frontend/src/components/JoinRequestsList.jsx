import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './JoinRequestsList.css';

function JoinRequestsList({ requests, onApprove, onReject, onSuccess, onError }) {
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

  const handleApprove = async (requestId) => {
    setLoadingAction(`approve-${requestId}`);
    try {
      await onApprove(requestId);
      if (onSuccess) {
        onSuccess('Request approved');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to approve request');
      }
    } finally {
      setLoadingAction(null);
    }
  };

  const handleReject = async (requestId) => {
    setLoadingAction(`reject-${requestId}`);
    try {
      await onReject(requestId);
      if (onSuccess) {
        onSuccess('Request rejected');
      }
    } catch (err) {
      if (onError) {
        onError(err.message || 'Failed to reject request');
      }
    } finally {
      setLoadingAction(null);
    }
  };

  if (!requests || requests.length === 0) {
    return (
      <div className="join-requests-list empty">
        <p className="empty-message">No pending join requests</p>
      </div>
    );
  }

  return (
    <div className="join-requests-list">
      {requests.map((request) => (
        <div key={request.id} className="request-card">
          <div className="request-header">
            <h3 className="username">{request.user?.username || 'Unknown User'}</h3>
          </div>
          <div className="request-info">
            <span className="request-date">
              Requested {formatDate(request.invited_at)}
            </span>
          </div>
          <div className="request-actions">
            <button
              className="approve-button"
              onClick={() => handleApprove(request.id)}
              disabled={loadingAction === `approve-${request.id}`}
            >
              {loadingAction === `approve-${request.id}` ? 'Approving...' : 'Approve'}
            </button>
            <button
              className="reject-button"
              onClick={() => handleReject(request.id)}
              disabled={loadingAction === `reject-${request.id}`}
            >
              {loadingAction === `reject-${request.id}` ? 'Rejecting...' : 'Reject'}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

JoinRequestsList.propTypes = {
  requests: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      user: PropTypes.shape({
        username: PropTypes.string,
      }),
      invited_at: PropTypes.string.isRequired,
    })
  ).isRequired,
  onApprove: PropTypes.func.isRequired,
  onReject: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  onError: PropTypes.func,
};

export default JoinRequestsList;
