import React, { useState, useEffect } from 'react';
import { groupsAPI } from '../services/api';
import './InviteUserForm.css';

function InviteUserForm({ onSuccess, onError }) {
  const [myAdminGroups, setMyAdminGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadAdminGroups();
  }, []);

  const loadAdminGroups = async () => {
    try {
      setLoading(true);
      const response = await groupsAPI.list();
      const groupsData = response.data.data || response.data.results || response.data;
      const groups = Array.isArray(groupsData) ? groupsData : [];
      
      // Filter to only groups where user is admin
      const adminGroups = groups.filter(g => g.role === 'admin' || g.created_by);
      setMyAdminGroups(adminGroups);
      
      // Auto-select first group if available
      if (adminGroups.length > 0) {
        setSelectedGroupId(adminGroups[0].id);
      }
    } catch (err) {
      console.error('Failed to load admin groups:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!selectedGroupId) {
      if (onError) onError('Please select a group');
      return;
    }
    
    if (!username.trim()) {
      if (onError) onError('Please enter a username');
      return;
    }

    setSubmitting(true);
    try {
      await groupsAPI.inviteMember(selectedGroupId, { username: username.trim() });
      if (onSuccess) onSuccess('Invitation sent successfully');
      setUsername('');
    } catch (err) {
      if (onError) onError(err.message || 'Failed to send invitation');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="invite-user-form">
        <p className="loading-text">Loading your groups...</p>
      </div>
    );
  }

  if (myAdminGroups.length === 0) {
    return (
      <div className="invite-user-form empty">
        <p className="empty-message">
          You need to be an admin of a group to send invitations.
        </p>
        <p className="empty-hint">
          Create a group first, then you can invite users to join!
        </p>
      </div>
    );
  }

  return (
    <div className="invite-user-form">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="group-select">Select Group</label>
          <select
            id="group-select"
            value={selectedGroupId}
            onChange={(e) => setSelectedGroupId(e.target.value)}
            disabled={submitting}
            className="form-select"
          >
            {myAdminGroups.map((group) => (
              <option key={group.id} value={group.id}>
                {group.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="username-input">Username to Invite</label>
          <input
            type="text"
            id="username-input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter username"
            disabled={submitting}
            className="form-input"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !username.trim()}
          className="submit-button"
        >
          {submitting ? 'Sending...' : 'Send Invitation'}
        </button>
      </form>
    </div>
  );
}

export default InviteUserForm;
