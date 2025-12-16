import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import SwipeCardStack from '../components/SwipeCardStack';
import CharacterWizard from '../components/CharacterWizard';
import Toast from '../components/Toast';
import { itemsAPI, votingAPI, decisionsAPI, generationAPI } from '../services/api';
import './VotingPage.css';

/**
 * VotingPage component for swipe-based voting on decision items.
 * Supports both text-based items and 2D character items with images.
 * 
 * Requirements: 7.1, 7.2, 7.5
 * - Display character image prominently with swipe actions
 * - Show key parameters below the image
 * - Skip characters that are still generating
 */
function VotingPage() {
  const { decisionId } = useParams();
  const navigate = useNavigate();
  
  const [items, setItems] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [decision, setDecision] = useState(null);
  const [voteHistory, setVoteHistory] = useState([]);
  const [toast, setToast] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [showWizard, setShowWizard] = useState(false);
  // eslint-disable-next-line no-unused-vars
  const [isGenerating, setIsGenerating] = useState(false);

  /**
   * Check if an item is ready for voting.
   * For character items (2d_character type), they must have a completed generation
   * with an image_url. Text-based items are always ready.
   * 
   * Requirement 7.5: Skip characters that are still generating
   */
  const isItemReadyForVoting = (item) => {
    const attributes = item.attributes || {};
    
    // If it's a 2D character item, check if generation is complete
    if (attributes.type === '2d_character') {
      // Item must have an image_url to be ready for voting
      return !!attributes.image_url;
    }
    
    // Non-character items are always ready
    return true;
  };

  // Fetch decision and items
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch decision details
        const decisionResponse = await decisionsAPI.get(decisionId);
        const decisionData = decisionResponse.data.data || decisionResponse.data;
        setDecision(decisionData);
        
        // Fetch items for this decision
        const itemsResponse = await itemsAPI.list(decisionId);
        console.log('Items response:', itemsResponse);
        let fetchedItems = itemsResponse.data.data?.results || itemsResponse.data.data || itemsResponse.data.results || itemsResponse.data || [];
        
        // Ensure it's an array
        if (!Array.isArray(fetchedItems)) {
          console.warn('fetchedItems is not an array:', fetchedItems);
          fetchedItems = [];
        }
        
        console.log('Fetched items:', fetchedItems);
        
        // Filter out items that are still generating (Requirement 7.5)
        const readyItems = fetchedItems.filter(isItemReadyForVoting);
        const stillGenerating = fetchedItems.length - readyItems.length;
        setPendingCount(stillGenerating);
        
        if (stillGenerating > 0) {
          console.log(`Skipping ${stillGenerating} items still generating`);
        }
        
        // Filter out items the user has already voted on
        const itemsWithVotes = await Promise.all(
          readyItems.map(async (item) => {
            try {
              const voteResponse = await votingAPI.getMyVote(item.id);
              // API returns { status: 'success', data: null } when no vote exists
              const voteData = voteResponse.data.data;
              if (voteData) {
                return { ...item, hasVoted: true, myVote: voteData };
              }
              return { ...item, hasVoted: false };
            } catch (err) {
              // Error means no vote or access denied
              return { ...item, hasVoted: false };
            }
          })
        );
        
        // Only show items without votes
        const unvotedItems = itemsWithVotes.filter(item => !item.hasVoted);
        console.log('Unvoted items:', unvotedItems);
        setItems(unvotedItems);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message || 'Failed to load voting data');
        setLoading(false);
      }
    };

    fetchData();
  }, [decisionId]);

  // Handle swipe gesture
  const handleSwipe = async (direction, item) => {
    const isLike = direction === 'right';
    await submitVote(item.id, isLike, null);
  };

  // Handle button vote
  const handleButtonVote = async (isLike) => {
    const currentItem = items[currentIndex];
    if (!currentItem) return;
    
    await submitVote(currentItem.id, isLike, null);
  };

  // Submit vote to API
  const submitVote = async (itemId, isLike, rating) => {
    try {
      const voteData = {};
      if (isLike !== null) {
        voteData.is_like = isLike;
      }
      if (rating !== null) {
        voteData.rating = rating;
      }
      
      await votingAPI.castVote(itemId, voteData);
      
      // Add to history for undo functionality
      setVoteHistory([...voteHistory, { itemId, isLike, rating, index: currentIndex }]);
      
      // Show success toast
      const voteType = rating !== null ? `${rating} stars` : (isLike ? 'liked' : 'disliked');
      setToast({ message: `Vote submitted: ${voteType}`, type: 'success' });
      
      // Move to next item
      setCurrentIndex(currentIndex + 1);
    } catch (err) {
      console.error('Error submitting vote:', err);
      setToast({ message: err.message || 'Failed to submit vote', type: 'error' });
    }
  };

  // Handle undo last vote
  const handleUndo = async () => {
    if (voteHistory.length === 0) return;
    
    const lastVote = voteHistory[voteHistory.length - 1];
    
    try {
      // Delete the vote from the database
      await votingAPI.deleteVote(lastVote.itemId);
      
      // Go back to the previous item
      setCurrentIndex(lastVote.index);
      setVoteHistory(voteHistory.slice(0, -1));
      
      setToast({ message: 'Vote undone', type: 'success' });
    } catch (err) {
      console.error('Error undoing vote:', err);
      setToast({ message: err.message || 'Failed to undo vote', type: 'error' });
    }
  };

  // Handle creating a variation from the current item
  const handleCreateVariation = () => {
    setShowWizard(true);
  };

  // Handle wizard generation
  const handleWizardGenerate = async (wizardContext) => {
    setIsGenerating(true);
    try {
      // Create a new character (not a variation, since we want it as a new item)
      const response = await generationAPI.createGeneration(decisionId, wizardContext.apiParams);
      const data = response.data?.data || response.data;
      
      return {
        imageUrl: data?.attributes?.image_url || data?.image_url,
        item: data,
      };
    } catch (err) {
      console.error('Failed to create character:', err);
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle wizard completion - add the new item and navigate to vote on it
  const handleWizardComplete = async (result) => {
    setShowWizard(false);
    
    if (result?.item) {
      // Add the new item to the list and navigate to it
      const newItem = { ...result.item, hasVoted: false };
      
      // Insert the new item right after the current one so user votes on it next
      const newItems = [...items];
      newItems.splice(currentIndex + 1, 0, newItem);
      setItems(newItems);
      
      // Move to the new item
      setCurrentIndex(currentIndex + 1);
      
      setToast({ message: 'Character created! Vote on it now.', type: 'success' });
    } else {
      // Refresh items to get the new one
      setToast({ message: 'Character created!', type: 'success' });
    }
  };

  // Calculate progress
  const totalItems = items.length;
  const votedItems = currentIndex;
  const progressPercentage = totalItems > 0 ? (votedItems / totalItems) * 100 : 0;

  if (loading) {
    return (
      <div className="voting-page">
        <div className="loading-message">Loading items...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="voting-page">
        <div className="error-message">
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={() => navigate(`/decisions/${decisionId}`)}>
            Back to Decision
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="voting-page">
      {/* Header */}
      <div className="voting-header">
        <button 
          className="back-button"
          onClick={() => navigate(`/decisions/${decisionId}`)}
        >
          ← Back
        </button>
        <h1>{decision?.title || 'Vote on Items'}</h1>
      </div>

      {/* Progress indicator */}
      <div className="progress-section">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <div className="progress-text">
          {votedItems} / {totalItems} items voted
          {pendingCount > 0 && (
            <span className="pending-indicator">
              ({pendingCount} still generating)
            </span>
          )}
        </div>
      </div>

      {/* Swipe card stack */}
      <SwipeCardStack
        items={items}
        currentIndex={currentIndex}
        onSwipe={handleSwipe}
      />

      {/* Vote buttons */}
      {currentIndex < items.length && (
        <div className="vote-controls">
          <button 
            className="vote-button vote-button-dislike"
            onClick={() => handleButtonVote(false)}
          >
            <span className="button-icon">✕</span>
            <span className="button-label">Nope</span>
          </button>
          
          <button 
            className="vote-button vote-button-create"
            onClick={handleCreateVariation}
            disabled={isGenerating}
          >
            <span className="button-icon">✨</span>
            <span className="button-label">{isGenerating ? 'Creating...' : 'Create'}</span>
          </button>
          
          <button 
            className="vote-button vote-button-like"
            onClick={() => handleButtonVote(true)}
          >
            <span className="button-icon">♥</span>
            <span className="button-label">Like</span>
          </button>
        </div>
      )}

      {/* Character Wizard for creating new variations */}
      {showWizard && (
        <CharacterWizard
          onGenerate={handleWizardGenerate}
          onComplete={handleWizardComplete}
          onCancel={() => setShowWizard(false)}
          isVariation={false}
          parentItem={null}
          lockedParams={decision?.rules?.locked_params || {}}
        />
      )}

      {/* Undo button - show if there's history, even after all items voted */}
      {voteHistory.length > 0 && (
        <button 
          className="undo-button"
          onClick={handleUndo}
        >
          ↶ Undo
        </button>
      )}

      {/* Toast notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default VotingPage;
