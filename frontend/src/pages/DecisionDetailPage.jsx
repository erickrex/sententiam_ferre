import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { decisionsAPI, itemsAPI, groupsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import DecisionDetail from '../components/DecisionDetail';
import CharacterGallery from '../components/CharacterGallery';
import './DecisionDetailPage.css';

// Helper to extract key parameters from FIBO JSON or attributes
function extractKeyParams(attributes) {
  if (!attributes) return [];
  
  const keyParams = [];
  const fibo = attributes.fibo_json;
  
  if (fibo) {
    // Extract from FIBO structured_prompt
    const sp = fibo.structured_prompt || {};
    if (sp.art_style) keyParams.push({ key: 'Style', value: sp.art_style });
    if (sp.character?.pose) keyParams.push({ key: 'Pose', value: sp.character.pose });
    if (sp.character?.expression) keyParams.push({ key: 'Expression', value: sp.character.expression });
    if (sp.scene?.setting) keyParams.push({ key: 'Setting', value: sp.scene.setting });
    if (sp.colors?.palette) keyParams.push({ key: 'Palette', value: sp.colors.palette });
  } else {
    // Fallback to generation_params
    const params = attributes.generation_params || {};
    if (params.art_style) keyParams.push({ key: 'Style', value: params.art_style });
    if (params.pose) keyParams.push({ key: 'Pose', value: params.pose });
    if (params.expression) keyParams.push({ key: 'Expression', value: params.expression });
    if (params.view_angle) keyParams.push({ key: 'View', value: params.view_angle });
    if (params.color_palette) keyParams.push({ key: 'Palette', value: params.color_palette });
  }
  
  return keyParams.slice(0, 4); // Max 4 params
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
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const loadDecisionData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      
      const decisionResponse = await decisionsAPI.get(decisionId);
      // API returns { status: 'success', data: {...} }
      const decisionData = decisionResponse.data.data || decisionResponse.data;
      setDecision(decisionData);
      
      // Check if user is admin of the group
      try {
        const membersResponse = await groupsAPI.listMembers(decisionData.group);
        const members = membersResponse.data.data || [];
        const currentUserMembership = members.find(m => m.user?.id === user?.id);
        setIsAdmin(currentUserMembership?.role === 'admin');
      } catch (err) {
        console.error('Failed to check admin status:', err);
        setIsAdmin(false);
      }
      
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
  }, [decisionId, user]);

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

  const handleDeleteItem = async (itemId) => {
    try {
      await itemsAPI.delete(itemId);
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error('Failed to delete item:', err);
    }
  };

  // Check if this is a 2D character decision
  const isCharacterDecision = decision?.item_type === '2d_character';

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
              <h2>Items ({items.length})</h2>
              {isAdmin && (
                <Link 
                  to={`/decisions/${decisionId}/items`}
                  className="manage-items-button"
                >
                  + Add Items
                </Link>
              )}
            </div>
            
            {isCharacterDecision ? (
              <CharacterGallery
                decisionId={decisionId}
                onDeleteItem={handleDeleteItem}
                refreshTrigger={refreshTrigger}
                isAdmin={isAdmin}
              />
            ) : (
              items.length === 0 ? (
                <div className="empty-state">
                  <p>No items yet.</p>
                  {isAdmin && <p>Add items for members to vote on!</p>}
                </div>
              ) : (
                <ul className="items-simple-list">
                  {items.map((item, index) => (
                    <li key={item.id} className="item-row">
                      <span className="item-number">{index + 1}.</span>
                      <span className="item-name">{item.label}</span>
                    </li>
                  ))}
                </ul>
              )
            )}
          </div>
        )}

        {activeTab === 'favourites' && (
          <div className="favourites-tab">
            <div className="tab-header">
              <h2>Favourites ({favourites.length})</h2>
              <Link 
                to={`/decisions/${decisionId}/favourites`}
                className="view-all-link"
              >
                Export Options →
              </Link>
            </div>
            <p className="tab-description">
              Characters that have met the approval threshold
            </p>
            
            {favourites.length === 0 ? (
              <div className="empty-state">
                <p>No favourites yet.</p>
                <p>Items will appear here once they meet the approval rule.</p>
              </div>
            ) : (
              <div className="favourites-grid-view">
                {favourites.map((favourite) => {
                  const item = favourite.item || {};
                  const attributes = item.attributes || {};
                  const keyParams = extractKeyParams(attributes);
                  
                  return (
                    <div key={favourite.id} className="favourite-grid-card">
                      {attributes.image_url ? (
                        <img 
                          src={attributes.image_url} 
                          alt={item.label} 
                          className="favourite-grid-image"
                        />
                      ) : (
                        <div className="favourite-grid-placeholder">
                          <span>⭐</span>
                        </div>
                      )}
                      <div className="favourite-grid-content">
                        <h3 className="favourite-grid-label">{item.label || 'Unknown'}</h3>
                        {keyParams.length > 0 && (
                          <div className="favourite-grid-params">
                            {keyParams.map((param, idx) => (
                              <span key={idx} className="param-tag">
                                {param.key}: {param.value}
                              </span>
                            ))}
                          </div>
                        )}
                        <div className="favourite-grid-approval">
                          <span className="approval-badge">
                            ✓ {favourite.snapshot?.approvals || 0}/{favourite.snapshot?.total_members || 0}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

export default DecisionDetailPage;
