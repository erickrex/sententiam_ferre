import React from 'react';
import './GroupDetail.css';

function GroupDetail({ group, members, onInvite, onRemoveMember, onApproveJoinRequest, onRejectJoinRequest, isAdmin }) {
  if (!group) {
    return <div className="loading">Loading group details...</div>;
  }

  const confirmedMembers = members?.filter(m => m.is_confirmed) || [];
  const pendingInvitations = members?.filter(m => !m.is_confirmed && m.membership_type === 'invitation') || [];
  const pendingJoinRequests = members?.filter(m => !m.is_confirmed && m.membership_type === 'request') || [];

  return (
    <div className="group-detail">
      <div className="group-header">
        <div className="group-info">
          <h1 className="group-title">{group.name}</h1>
          {group.description && (
            <p className="group-description">{group.description}</p>
          )}
        </div>
        {isAdmin && (
          <button 
            className="invite-button"
            onClick={onInvite}
          >
            + Invite Member
          </button>
        )}
      </div>

      <div className="members-section">
        <h2 className="section-title">Members ({confirmedMembers.length})</h2>
        <div className="member-list">
          {confirmedMembers.length === 0 ? (
            <p className="empty-message">No confirmed members yet.</p>
          ) : (
            confirmedMembers.map((member) => (
              <div key={member.id} className="member-item">
                <div className="member-info">
                  <span className="member-name">{member.user?.username || 'Unknown'}</span>
                  {member.role === 'admin' && (
                    <span className="role-badge admin">Admin</span>
                  )}
                </div>
                {isAdmin && member.role !== 'admin' && (
                  <button
                    className="remove-button"
                    onClick={() => onRemoveMember(member.user?.id)}
                  >
                    Remove
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {pendingInvitations.length > 0 && (
        <div className="pending-section">
          <h2 className="section-title">Pending Invitations ({pendingInvitations.length})</h2>
          <div className="member-list">
            {pendingInvitations.map((member) => (
              <div key={member.id} className="member-item pending">
                <div className="member-info">
                  <span className="member-name">{member.user?.username || 'Unknown'}</span>
                  <span className="status-badge pending">Pending</span>
                </div>
                {isAdmin && (
                  <button
                    className="remove-button"
                    onClick={() => onRemoveMember(member.user?.id)}
                  >
                    Cancel
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {pendingJoinRequests.length > 0 && (
        <div className="pending-section">
          <h2 className="section-title">Pending Join Requests ({pendingJoinRequests.length})</h2>
          <div className="member-list">
            {pendingJoinRequests.map((member) => (
              <div key={member.id} className="member-item pending">
                <div className="member-info">
                  <span className="member-name">{member.user?.username || 'Unknown'}</span>
                  <span className="status-badge pending">Pending</span>
                </div>
                {isAdmin && (
                  <div className="member-actions">
                    <button
                      className="accept-button"
                      onClick={() => onApproveJoinRequest?.(member.id)}
                    >
                      Accept
                    </button>
                    <button
                      className="remove-button"
                      onClick={() => onRejectJoinRequest?.(member.id)}
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default GroupDetail;
