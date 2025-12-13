import React, { useState, useEffect } from 'react';
import { decisionsAPI } from '../services/api';
import FavouriteCard from './FavouriteCard';
import './FavouritesList.css';

function FavouritesList({ decisionId, autoRefresh = false, refreshInterval = 5000 }) {
  const [favourites, setFavourites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortBy, setSortBy] = useState('date'); // 'date', 'approval'
  const [filterMinApproval, setFilterMinApproval] = useState(0);

  useEffect(() => {
    loadFavourites();
    
    // Set up auto-refresh if enabled
    let intervalId;
    if (autoRefresh) {
      intervalId = setInterval(() => {
        loadFavourites(true); // Silent refresh
      }, refreshInterval);
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [decisionId, autoRefresh, refreshInterval]);

  const loadFavourites = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
        setError('');
      }
      
      const response = await decisionsAPI.listFavourites(decisionId);
      // API returns { status: 'success', data: [...] } or { status: 'success', data: { results: [...] } }
      let data = response.data.data || response.data;
      if (data && data.results) {
        data = data.results;
      }
      setFavourites(Array.isArray(data) ? data : []);
    } catch (err) {
      if (!silent) {
        setError(err.message || 'Failed to load favourites');
      }
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const getSortedAndFilteredFavourites = () => {
    let filtered = [...favourites];
    
    // Apply approval filter
    if (filterMinApproval > 0) {
      filtered = filtered.filter(fav => {
        const approvalPercentage = fav.snapshot?.approval_percentage || 0;
        return approvalPercentage >= filterMinApproval;
      });
    }
    
    // Apply sorting
    filtered.sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.selected_at) - new Date(a.selected_at);
      } else if (sortBy === 'approval') {
        const aPercentage = a.snapshot?.approval_percentage || 0;
        const bPercentage = b.snapshot?.approval_percentage || 0;
        return bPercentage - aPercentage;
      }
      return 0;
    });
    
    return filtered;
  };

  const handleRefresh = () => {
    loadFavourites();
  };

  if (loading) {
    return (
      <div className="favourites-list-loading">
        <div className="spinner"></div>
        <p>Loading favourites...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="favourites-list-error">
        <p>{error}</p>
        <button onClick={handleRefresh} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }

  const sortedFavourites = getSortedAndFilteredFavourites();

  return (
    <div className="favourites-list">
      <div className="favourites-controls">
        <div className="control-group">
          <label htmlFor="sort-by">Sort by:</label>
          <select
            id="sort-by"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="sort-select"
          >
            <option value="date">Most Recent</option>
            <option value="approval">Highest Approval</option>
          </select>
        </div>
        
        <div className="control-group">
          <label htmlFor="min-approval">Min Approval %:</label>
          <input
            id="min-approval"
            type="number"
            min="0"
            max="100"
            value={filterMinApproval}
            onChange={(e) => setFilterMinApproval(Number(e.target.value))}
            className="filter-input"
          />
        </div>
        
        <button onClick={handleRefresh} className="refresh-button" title="Refresh">
          ↻ Refresh
        </button>
      </div>

      {sortedFavourites.length === 0 ? (
        <div className="favourites-empty">
          {favourites.length === 0 ? (
            <>
              <p>No favourites yet.</p>
              <p>Items will appear here once they meet the approval rule.</p>
            </>
          ) : (
            <p>No favourites match the current filter.</p>
          )}
        </div>
      ) : (
        <div className="favourites-grid">
          {sortedFavourites.map((favourite) => (
            <FavouriteCard key={favourite.id} favourite={favourite} />
          ))}
        </div>
      )}
      
      {autoRefresh && (
        <div className="auto-refresh-indicator">
          <span className="refresh-dot"></span>
          Auto-refreshing every {refreshInterval / 1000}s
        </div>
      )}
    </div>
  );
}

export default FavouritesList;
