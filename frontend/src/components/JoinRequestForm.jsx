import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './JoinRequestForm.css';

function JoinRequestForm({ onSubmit, onSuccess, onError }) {
  const [groupName, setGroupName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate group name is not empty
    if (!groupName.trim()) {
      setError('Group name is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await onSubmit(groupName.trim());
      setGroupName('');
      if (onSuccess) {
        onSuccess('Join request sent successfully');
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to send join request';
      setError(errorMessage);
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="join-request-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="group-name">Group Name</label>
        <input
          id="group-name"
          type="text"
          value={groupName}
          onChange={(e) => setGroupName(e.target.value)}
          placeholder="Enter group name..."
          disabled={loading}
          className={error ? 'error' : ''}
        />
        {error && <span className="error-message">{error}</span>}
      </div>
      <button 
        type="submit" 
        className="submit-button"
        disabled={loading || !groupName.trim()}
      >
        {loading ? 'Sending...' : 'Request to Join'}
      </button>
    </form>
  );
}

JoinRequestForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  onSuccess: PropTypes.func,
  onError: PropTypes.func,
};

export default JoinRequestForm;
