import React from 'react';
import './DecisionDetail.css';

function DecisionDetail({ decision, isAdmin, onStatusChange }) {
  if (!decision) {
    return <div className="loading">Loading decision details...</div>;
  }

  const getRuleDisplay = (rules) => {
    if (!rules) return 'No rules configured';
    if (rules.type === 'unanimous') {
      return 'All members must approve for items to become favourites';
    }
    if (rules.type === 'threshold') {
      return `${Math.round(rules.value * 100)}% of members must approve for items to become favourites`;
    }
    return 'Unknown rule type';
  };

  const getStatusColor = (status) => {
    const colors = {
      draft: 'gray',
      open: 'green',
      closed: 'blue',
      archived: 'purple'
    };
    return colors[status] || 'gray';
  };

  const canTransitionTo = (currentStatus, targetStatus) => {
    const validTransitions = {
      draft: ['open'],
      open: ['closed'],
      closed: ['archived'],
      archived: []
    };
    return validTransitions[currentStatus]?.includes(targetStatus) || false;
  };

  const handleStatusChange = (newStatus) => {
    if (window.confirm(`Are you sure you want to change the status to "${newStatus}"?`)) {
      onStatusChange(newStatus);
    }
  };

  return (
    <div className="decision-detail">
      <div className="decision-header">
        <div className="decision-info">
          <h1 className="decision-title">{decision.title}</h1>
          <span className={`status-badge status-${decision.status}`}>
            {decision.status}
          </span>
        </div>
        
        {decision.description && (
          <p className="decision-description">{decision.description}</p>
        )}
      </div>

      <div className="decision-details-grid">
        <div className="detail-section">
          <h3 className="detail-label">Item Type</h3>
          <p className="detail-value">{decision.item_type}</p>
        </div>

        <div className="detail-section">
          <h3 className="detail-label">Approval Rule</h3>
          <p className="detail-value">{getRuleDisplay(decision.rules)}</p>
        </div>

        <div className="detail-section">
          <h3 className="detail-label">Created</h3>
          <p className="detail-value">
            {decision.created_at 
              ? new Date(decision.created_at).toLocaleDateString()
              : 'N/A'}
          </p>
        </div>

        {decision.updated_at && (
          <div className="detail-section">
            <h3 className="detail-label">Last Updated</h3>
            <p className="detail-value">
              {decision.updated_at 
                ? new Date(decision.updated_at).toLocaleDateString()
                : 'N/A'}
            </p>
          </div>
        )}
      </div>

      {isAdmin && onStatusChange && (
        <div className="status-controls">
          <h3 className="controls-label">Status Controls</h3>
          <div className="status-buttons">
            {canTransitionTo(decision.status, 'open') && (
              <button
                className="status-button open"
                onClick={() => handleStatusChange('open')}
              >
                Open Decision
              </button>
            )}
            {canTransitionTo(decision.status, 'closed') && (
              <button
                className="status-button closed"
                onClick={() => handleStatusChange('closed')}
              >
                Close Decision
              </button>
            )}
            {canTransitionTo(decision.status, 'archived') && (
              <button
                className="status-button archived"
                onClick={() => handleStatusChange('archived')}
              >
                Archive Decision
              </button>
            )}
          </div>
          {decision.status === 'closed' && (
            <p className="status-note">
              Closed decisions cannot accept new votes, but chat and favourites remain accessible.
            </p>
          )}
          {decision.status === 'archived' && (
            <p className="status-note">
              Archived decisions are read-only.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default DecisionDetail;
