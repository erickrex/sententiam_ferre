import React from 'react';
import { Link } from 'react-router-dom';
import './GroupList.css';

function GroupList({ groups, loading, error }) {
  if (loading) {
    return <div className="loading">Loading groups...</div>;
  }

  if (error) {
    return <div className="error-message">{error}</div>;
  }

  if (!groups || groups.length === 0) {
    return (
      <div className="empty-state">
        <p>You don't have any groups yet.</p>
        <p>Create a group to start collaborating!</p>
      </div>
    );
  }

  return (
    <div className="group-list">
      {groups.map((group) => (
        <Link 
          key={group.id} 
          to={`/groups/${group.id}`} 
          className="group-card"
        >
          <div className="group-card-header">
            <h3 className="group-name">{group.name}</h3>
            {group.role === 'admin' && (
              <span className="admin-badge">Admin</span>
            )}
          </div>
          {group.description && (
            <p className="group-description">{group.description}</p>
          )}
          <div className="group-meta">
            <span className="member-count">
              {group.member_count || 0} {group.member_count === 1 ? 'member' : 'members'}
            </span>
            {group.decision_count !== undefined && (
              <span className="decision-count">
                {group.decision_count} {group.decision_count === 1 ? 'decision' : 'decisions'}
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}

export default GroupList;
