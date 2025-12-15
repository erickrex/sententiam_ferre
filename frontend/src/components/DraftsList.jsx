import React, { useState, useEffect, useCallback } from 'react';
import { generationAPI } from '../services/api';
import Toast from './Toast';
import './DraftsList.css';

/**
 * DraftsList component displays the user's draft variations
 * that haven't been published yet.
 */
function DraftsList({ onEditDraft, onRefresh }) {
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [toastMessage, setToastMessage] = useState(null);
  const [actionLoading, setActionLoading] = useState({});

  const loadDrafts = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const response = await generationAPI.getMyDrafts();
      const data = response.data.data || response.data;
      setDrafts(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to load drafts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDrafts();
  }, [loadDrafts]);

  const handlePublish = async (draftId) => {
    setActionLoading(prev => ({ ...prev, [draftId]: 'publish' }));
    try {
      await generationAPI.publishItem(draftId);
      setToastMessage({
        type: 'success',
        message: 'Draft published! It\'s now visible to your group.',
      });
      loadDrafts();
      onRefresh?.();
    } catch (err) {
      setToastMessage({
        type: 'error',
        message: err.response?.data?.message || 'Failed to publish',
      });
    } finally {
      setActionLoading(prev => ({ ...prev, [draftId]: null }));
    }
  };

  const handleDiscard = async (draftId) => {
    if (!window.confirm('Are you sure you want to discard this draft?')) return;
    
    setActionLoading(prev => ({ ...prev, [draftId]: 'discard' }));
    try {
      await generationAPI.discardDraft(draftId);
      setToastMessage({
        type: 'info',
        message: 'Draft discarded',
      });
      loadDrafts();
    } catch (err) {
      setToastMessage({
        type: 'error',
        message: err.response?.data?.message || 'Failed to discard',
      });
    } finally {
      setActionLoading(prev => ({ ...prev, [draftId]: null }));
    }
  };

  if (loading) {
    return (
      <div className="drafts-list-loading">
        <div className="spinner"></div>
        <span>Loading drafts...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="drafts-list-error">
        <p>{error}</p>
        <button onClick={loadDrafts}>Try Again</button>
      </div>
    );
  }

  if (drafts.length === 0) {
    return null; // Don't show anything if no drafts
  }

  return (
    <div className="drafts-list">
      <div className="drafts-header">
        <h3>📝 Your Drafts</h3>
        <span className="drafts-count">{drafts.length}</span>
      </div>
      
      <div className="drafts-grid">
        {drafts.map(draft => {
          const imageUrl = draft.attributes?.image_url;
          const description = draft.attributes?.description || draft.label;
          const isGenerating = !imageUrl;
          const isActionLoading = actionLoading[draft.id];
          
          return (
            <div key={draft.id} className="draft-card">
              <div className="draft-image-container">
                {isGenerating ? (
                  <div className="draft-generating">
                    <div className="spinner"></div>
                    <span>Generating...</span>
                  </div>
                ) : (
                  <img src={imageUrl} alt={description} className="draft-image" />
                )}
              </div>
              
              <div className="draft-info">
                <p className="draft-description" title={description}>
                  {description}
                </p>
              </div>
              
              <div className="draft-actions">
                <button
                  className="draft-btn edit"
                  onClick={() => onEditDraft?.(draft)}
                  disabled={isActionLoading}
                  title="Edit this draft"
                >
                  ✏️ Edit
                </button>
                <button
                  className="draft-btn publish"
                  onClick={() => handlePublish(draft.id)}
                  disabled={isGenerating || isActionLoading}
                  title={isGenerating ? 'Wait for generation to complete' : 'Publish to group'}
                >
                  {isActionLoading === 'publish' ? '...' : '✓ Publish'}
                </button>
                <button
                  className="draft-btn discard"
                  onClick={() => handleDiscard(draft.id)}
                  disabled={isActionLoading}
                  title="Discard this draft"
                >
                  {isActionLoading === 'discard' ? '...' : '✕'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
      
      {toastMessage && (
        <Toast
          type={toastMessage.type}
          message={toastMessage.message}
          onClose={() => setToastMessage(null)}
          duration={4000}
        />
      )}
    </div>
  );
}

export default DraftsList;
