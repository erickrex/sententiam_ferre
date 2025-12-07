import React from 'react';
import './FavouriteCard.css';

function FavouriteCard({ favourite }) {
  const item = favourite.item || {};
  const snapshot = favourite.snapshot || {};
  const attributes = item.attributes || {};
  
  // Calculate approval percentage if not in snapshot
  const approvalPercentage = snapshot.approval_percentage || 
    (snapshot.total_members > 0 
      ? Math.round((snapshot.approvals / snapshot.total_members) * 100)
      : 0);
  
  // Format date
  const selectedDate = new Date(favourite.selected_at);
  const formattedDate = selectedDate.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
  const formattedTime = selectedDate.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  });

  return (
    <div className="favourite-card">
      {/* Item Image or Placeholder */}
      {attributes.image_url ? (
        <img 
          src={attributes.image_url} 
          alt={item.label} 
          className="favourite-card-image"
        />
      ) : (
        <div className="favourite-card-image-placeholder">
          <span className="favourite-icon">⭐</span>
        </div>
      )}
      
      {/* Item Label */}
      <div className="favourite-card-content">
        <h3 className="favourite-card-label">
          {item.label || 'Unknown Item'}
        </h3>
        
        {/* Vote Snapshot */}
        <div className="favourite-card-snapshot">
          <div className="snapshot-row">
            <div className="snapshot-stat">
              <span className="stat-label">Approvals</span>
              <span className="stat-value">{snapshot.approvals || 0}</span>
            </div>
            <div className="snapshot-stat">
              <span className="stat-label">Total Members</span>
              <span className="stat-value">{snapshot.total_members || 0}</span>
            </div>
          </div>
          
          {/* Approval Percentage Bar */}
          <div className="approval-bar-container">
            <div className="approval-bar-label">
              <span>Approval Rate</span>
              <span className="approval-percentage">{approvalPercentage}%</span>
            </div>
            <div className="approval-bar">
              <div 
                className="approval-bar-fill" 
                style={{ width: `${approvalPercentage}%` }}
              ></div>
            </div>
          </div>
          
          {/* Rule Information */}
          {snapshot.rule && (
            <div className="snapshot-rule">
              <span className="rule-label">Rule:</span>
              <span className="rule-value">
                {snapshot.rule.type === 'unanimous' 
                  ? 'Unanimous' 
                  : `${Math.round(snapshot.rule.value * 100)}% Threshold`}
              </span>
            </div>
          )}
        </div>
        
        {/* Item Attributes */}
        {Object.keys(attributes).length > 0 && (
          <div className="favourite-card-attributes">
            {Object.entries(attributes)
              .filter(([key]) => key !== 'image_url')
              .slice(0, 3) // Show only first 3 attributes
              .map(([key, value]) => (
                <div key={key} className="favourite-attribute">
                  <span className="attribute-key">{key}:</span>
                  <span className="attribute-value">{String(value)}</span>
                </div>
              ))}
          </div>
        )}
        
        {/* Selected Date */}
        <div className="favourite-card-meta">
          <span className="meta-icon">📅</span>
          <span className="meta-text">
            Selected on {formattedDate} at {formattedTime}
          </span>
        </div>
      </div>
    </div>
  );
}

export default FavouriteCard;
