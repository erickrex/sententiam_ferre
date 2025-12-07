import React from 'react';
import { Link } from 'react-router-dom';
import './DecisionList.css';

function DecisionList({ decisions, groupId, isAdmin }) {
  if (!decisions || decisions.length === 0) {
    return (
      <div className="empty-state">
        <p>No decisions yet.</p>
        {isAdmin && <p>Create a decision to get started!</p>}
      </div>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      draft: 'gray',
      open: 'green',
      closed: 'blue',
      archived: 'purple'
    };
    return colors[status] || 'gray';
  };

  const getRuleDisplay = (rules) => {
    if (!rules) return 'No rules';
    if (rules.type === 'unanimous') return 'Unanimous';
    if (rules.type === 'threshold') return `${Math.round(rules.value * 100)}% threshold`;
    return 'Unknown rule';
  };

  return (
    <div className="decision-list">
      {decisions.map((decision) => (
        <Link 
          key={decision.id} 
          to={`/decisions/${decision.id}`}
          className="decision-card"
        >
          <div className="decision-card-header">
            <h3 className="decision-title">{decision.title}</h3>
            <span className={`status-badge status-${decision.status}`}>
              {decision.status}
            </span>
          </div>
          
          {decision.description && (
            <p className="decision-description">{decision.description}</p>
          )}
          
          <div className="decision-meta">
            <span className="meta-item">
              <span className="meta-label">Type:</span> {decision.item_type}
            </span>
            <span className="meta-item">
              <span className="meta-label">Rule:</span> {getRuleDisplay(decision.rules)}
            </span>
            {decision.item_count !== undefined && (
              <span className="meta-item">
                <span className="meta-label">Items:</span> {decision.item_count}
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

export default DecisionList;
