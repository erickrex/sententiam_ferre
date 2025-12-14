import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { decisionsAPI, itemsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import DecisionDetail from '../components/DecisionDetail';
import ChatView from '../components/ChatView';
import './DecisionDetailPage.css';

// Simple Items Tab component with pagination
function ItemsTab({ items, isAdmin, decisionId }) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;
  
  const totalPages = Math.ceil(items.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = items.slice(startIndex, endIndex);
  
  return (
    <div className="items-tab">
      <div className="tab-header">
        <h2>Items ({items.length})</h2>
        {isAdmin ? (
          <Link 
            to={`/decisions/${decisionId}/items`}
            className="manage-items-button"
          >
            Manage Items
          </Link>
        ) : (
          <button 
            className="manage-items-button"
            disabled
            title="Only admins can manage items"
          >
            Manage Items
          </button>
        )}
      </div>
      
      {items.length === 0 ? (
        <div className="empty-state">
          <p>No items yet.</p>
          {isAdmin && <p>Add items for members to vote on!</p>}
        </div>
      ) : (
        <>
          <ul className="items-simple-list">
            {currentItems.map((item, index) => (
              <li key={item.id} className="item-row">
                <span className="item-number">{startIndex + index + 1}.</span>
                <span className="item-name">{item.label}</span>
              </li>
            ))}
          </ul>
          
          {totalPages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="pagination-btn"
              >
                ← Previous
              </button>
              <span className="pagination-info">
                Page {currentPage} of {totalPages}
              </span>
              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="pagination-btn"
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

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

  const loadDecisionData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      const decisionResponse = await decisionsAPI.get(decisionId);
      // API returns { status: 'success', data: {...} }
      const decisionData = decisionResponse.data.data || decisionResponse.data;
      setDecision(decisionData);
      
      // Check if user is admin (creator or group admin)
      // This is a simplified check - in production, you'd verify group membership
      setIsAdmin(true); // For now, assume user can manage their decisions
      
      // Load items and favourites
      const [itemsResponse, favouritesResponse] = await Promise.all([
        itemsAPI.list(decisionId),
        decisionsAPI.listFavourites(decisionId)
      ]);
      
      // API returns { status: 'success', data: { results: [...], count: 20, ... } }
      const itemsData = itemsResponse.data.data?.results || itemsResponse.data.data || itemsResponse.data.results || itemsResponse.data || [];
      setItems(Array.isArray(itemsData) ? itemsData : []);
      
      // API returns { status: 'success', data: [...] }
      let favouritesData = favouritesResponse.data.data || favouritesResponse.data;
      if (favouritesData && favouritesData.results) {
        favouritesData = favouritesData.results;
      }
      setFavourites(Array.isArray(favouritesData) ? favouritesData : []);
    } catch (err) {
      setError(err.message || 'Failed to load decision data');
    } finally {
      setLoading(false);
    }
  }, [decisionId]);

  useEffect(() => {
    loadDecisionData();
  }, [loadDecisionData]);

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

  // Get the group ID for back navigation
  const groupId = decision?.group?.id || decision?.group_id || decision?.group;

  if (error && !decision) {
    return (
      <div className="error-page">
        <p>{error}</p>
        <button onClick={() => navigate('/groups')} className="back-button">
          ← Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="decision-detail-page">
      <div className="page-header">
        <button onClick={() => navigate(groupId ? `/groups/${groupId}` : '/groups')} className="back-link">
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
          <ItemsTab 
            items={items} 
            isAdmin={isAdmin} 
            decisionId={decisionId} 
          />
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
