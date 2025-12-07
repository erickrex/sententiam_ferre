import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { decisionsAPI, itemsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import DecisionDetail from '../components/DecisionDetail';
import ChatView from '../components/ChatView';
import './DecisionDetailPage.css';

function DecisionDetailPage() {
  const { decisionId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [decision, setDecision] = useState(null);
  const [items, setItems] = useState([]);
  const [favourites, setFavourites] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    loadDecisionData();
  }, [decisionId, loadDecisionData]);

  const loadDecisionData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const decisionResponse = await decisionsAPI.get(decisionId);
      setDecision(decisionResponse.data);
      
      // Check if user is admin (creator or group admin)
      // This is a simplified check - in production, you'd verify group membership
      setIsAdmin(true); // For now, assume user can manage their decisions
      
      // Load items and favourites
      const [itemsResponse, favouritesResponse] = await Promise.all([
        itemsAPI.list(decisionId),
        decisionsAPI.listFavourites(decisionId)
      ]);
      
      setItems(itemsResponse.data.results || itemsResponse.data || []);
      setFavourites(favouritesResponse.data.results || favouritesResponse.data || []);
    } catch (err) {
      setError(err.message || 'Failed to load decision data');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await decisionsAPI.update(decisionId, { status: newStatus });
      await loadDecisionData();
    } catch (err) {
      setError(err.message || 'Failed to update decision status');
    }
  };

  if (loading) {
    return <div className="loading-page">Loading decision...</div>;
  }

  if (error && !decision) {
    return (
      <div className="error-page">
        <p>{error}</p>
        <button onClick={() => navigate(-1)} className="back-button">
          ← Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="decision-detail-page">
      <div className="page-header">
        <button onClick={() => navigate(-1)} className="back-link">
          ← Back
        </button>
        {decision?.status === 'open' && (
          <Link 
            to={`/decisions/${decisionId}/vote`} 
            className="vote-button"
          >
            Start Voting
          </Link>
        )}
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`tab ${activeTab === 'items' ? 'active' : ''}`}
          onClick={() => setActiveTab('items')}
        >
          Items ({items.length})
        </button>
        <button
          className={`tab ${activeTab === 'favourites' ? 'active' : ''}`}
          onClick={() => setActiveTab('favourites')}
        >
          Favourites ({favourites.length})
        </button>
        <button
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Chat
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && (
          <DecisionDetail
            decision={decision}
            isAdmin={isAdmin}
            onStatusChange={handleStatusChange}
          />
        )}

        {activeTab === 'items' && (
          <div className="items-tab">
            <div className="tab-header">
              <h2>Items</h2>
              {isAdmin && (
                <Link 
                  to={`/decisions/${decisionId}/items`}
                  className="manage-items-button"
                >
                  Manage Items
                </Link>
              )}
            </div>
            
            {items.length === 0 ? (
              <div className="empty-state">
                <p>No items yet.</p>
                {isAdmin && <p>Add items for members to vote on!</p>}
              </div>
            ) : (
              <div className="items-list">
                {items.map((item) => (
                  <div key={item.id} className="item-card">
                    <h3 className="item-label">{item.label}</h3>
                    {item.attributes && Object.keys(item.attributes).length > 0 && (
                      <div className="item-attributes">
                        {Object.entries(item.attributes).map(([key, value]) => (
                          <span key={key} className="attribute">
                            <strong>{key}:</strong> {String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'favourites' && (
          <div className="favourites-tab">
            <div className="tab-header">
              <h2>Favourites</h2>
              <Link 
                to={`/decisions/${decisionId}/favourites`}
                className="view-all-link"
              >
                View Full Page →
              </Link>
            </div>
            <p className="tab-description">
              Items that have met the approval threshold
            </p>
            
            {favourites.length === 0 ? (
              <div className="empty-state">
                <p>No favourites yet.</p>
                <p>Items will appear here once they meet the approval rule.</p>
              </div>
            ) : (
              <div className="favourites-list">
                {favourites.map((favourite) => (
                  <div key={favourite.id} className="favourite-card">
                    <h3 className="favourite-label">
                      {favourite.item?.label || 'Unknown Item'}
                    </h3>
                    {favourite.snapshot && (
                      <div className="favourite-snapshot">
                        <span className="snapshot-item">
                          Approvals: {favourite.snapshot.approvals || 0}
                        </span>
                        <span className="snapshot-item">
                          Total Members: {favourite.snapshot.total_members || 0}
                        </span>
                        {favourite.snapshot.approval_percentage && (
                          <span className="snapshot-item">
                            {Math.round(favourite.snapshot.approval_percentage)}% approved
                          </span>
                        )}
                      </div>
                    )}
                    <div className="favourite-meta">
                      Selected on {new Date(favourite.selected_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="chat-tab">
            <ChatView 
              decisionId={decisionId}
              isClosed={decision?.status === 'closed' || decision?.status === 'archived'}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default DecisionDetailPage;
