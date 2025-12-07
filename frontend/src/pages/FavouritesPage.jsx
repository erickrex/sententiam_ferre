import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { decisionsAPI } from '../services/api';
import FavouritesList from '../components/FavouritesList';
import './FavouritesPage.css';

function FavouritesPage() {
  const { decisionId } = useParams();
  const navigate = useNavigate();
  const [decision, setDecision] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDecision();
  }, [decisionId, loadDecision]);

  const loadDecision = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await decisionsAPI.get(decisionId);
      setDecision(response.data);
    } catch (err) {
      setError(err.message || 'Failed to load decision');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="favourites-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="favourites-page">
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button onClick={() => navigate(-1)} className="back-button">
            ← Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="favourites-page">
      <div className="page-header">
        <button onClick={() => navigate(-1)} className="back-link">
          ← Back
        </button>
        <Link to={`/decisions/${decisionId}`} className="view-decision-link">
          View Decision
        </Link>
      </div>

      <div className="page-title-section">
        <h1 className="page-title">Favourites</h1>
        {decision && (
          <p className="page-subtitle">
            {decision.title}
          </p>
        )}
        <p className="page-description">
          Items that have met the approval threshold and been selected by the group
        </p>
      </div>

      {decision && (
        <div className="decision-info-card">
          <div className="info-item">
            <span className="info-label">Status:</span>
            <span className={`status-badge status-${decision.status}`}>
              {decision.status}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Approval Rule:</span>
            <span className="info-value">
              {decision.rules?.type === 'unanimous' 
                ? 'Unanimous (100%)' 
                : `${Math.round((decision.rules?.value || 0) * 100)}% Threshold`}
            </span>
          </div>
        </div>
      )}

      <div className="favourites-content">
        <FavouritesList 
          decisionId={decisionId} 
          autoRefresh={decision?.status === 'open'}
          refreshInterval={5000}
        />
      </div>
    </div>
  );
}

export default FavouritesPage;
