import React, { useState, useEffect, useCallback, useRef } from 'react';
import { itemsAPI, generationAPI } from '../services/api';
import CharacterCard from './CharacterCard';
import Toast from './Toast';
import './CharacterGallery.css';

/**
 * CharacterGallery component displays a grid of generated characters with status tracking.
 * Implements polling for pending generation jobs and auto-refresh on completion.
 * Handles timeout for stale jobs (40 seconds) by deleting them and notifying the user.
 * 
 * Requirements: 2.4, 8.1, 8.3, 8.4
 */

// Timeout threshold in milliseconds (40 seconds)
const GENERATION_TIMEOUT_MS = 40000;

function CharacterGallery({ 
  decisionId, 
  onCreateVariation,
  onViewDetails,
  onNavigateToVersion,
  refreshTrigger = 0,
  pollInterval = 5000
}) {
  const [items, setItems] = useState([]);
  const [generationJobs, setGenerationJobs] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ pending: 0, completed: 0, failed: 0 });
  const [filter, setFilter] = useState('all'); // 'all', 'completed', 'pending', 'failed'
  const [toastMessage, setToastMessage] = useState(null);
  
  const pollIntervalRef = useRef(null);
  const isMountedRef = useRef(true);

  // Load items and their generation jobs
  const loadItems = useCallback(async (silent = false) => {
    if (!decisionId) return;
    
    try {
      if (!silent) {
        setLoading(true);
        setError('');
      }
      
      // Fetch items for this decision
      const itemsResponse = await itemsAPI.list(decisionId);
      let itemsData = itemsResponse.data.data || itemsResponse.data;
      if (itemsData && itemsData.results) {
        itemsData = itemsData.results;
      }
      
      // Filter to only 2d_character items
      const characterItems = (Array.isArray(itemsData) ? itemsData : [])
        .filter(item => item.attributes?.type === '2d_character');
      
      if (isMountedRef.current) {
        setItems(characterItems);
      }
      
      // Fetch generation jobs for this decision
      try {
        const jobsResponse = await generationAPI.listDecisionJobs(decisionId);
        let jobsData = jobsResponse.data.data || jobsResponse.data;
        if (jobsData && jobsData.results) {
          jobsData = jobsData.results;
        }
        
        // Create a map of item_id -> latest job
        const jobsMap = {};
        (Array.isArray(jobsData) ? jobsData : []).forEach(job => {
          const itemId = job.item_id || job.item;
          if (!jobsMap[itemId] || new Date(job.created_at) > new Date(jobsMap[itemId].created_at)) {
            jobsMap[itemId] = job;
          }
        });
        
        if (isMountedRef.current) {
          setGenerationJobs(jobsMap);
          
          // Calculate stats
          const jobsList = Object.values(jobsMap);
          setStats({
            pending: jobsList.filter(j => j.status === 'pending' || j.status === 'processing').length,
            completed: jobsList.filter(j => j.status === 'completed').length,
            failed: jobsList.filter(j => j.status === 'failed').length,
          });
        }
      } catch (jobsErr) {
        // Jobs endpoint might not exist yet, continue without jobs
        console.warn('Could not fetch generation jobs:', jobsErr);
      }
      
    } catch (err) {
      if (!silent && isMountedRef.current) {
        setError(err.message || 'Failed to load characters');
      }
    } finally {
      if (!silent && isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [decisionId]);

  // Check if a job has timed out (older than 40 seconds)
  const isJobTimedOut = useCallback((job) => {
    if (!job.created_at) return false;
    const createdAt = new Date(job.created_at).getTime();
    const now = Date.now();
    return (now - createdAt) > GENERATION_TIMEOUT_MS;
  }, []);

  // Handle timeout for a stale job
  const handleJobTimeout = useCallback(async (job) => {
    try {
      const response = await generationAPI.timeoutJob(job.id);
      const data = response.data.data || response.data;
      const description = data.item_description || 'Unknown character';
      
      // Show toast notification
      setToastMessage({
        type: 'error',
        message: `Image "${description}" failed to be generated. Please try again.`,
      });
      
      // Remove the item from local state
      const itemId = job.item_id || job.item;
      setItems(prev => prev.filter(item => item.id !== itemId));
      setGenerationJobs(prev => {
        const newJobs = { ...prev };
        delete newJobs[itemId];
        return newJobs;
      });
      
      return true;
    } catch (err) {
      console.error(`Failed to timeout job ${job.id}:`, err);
      return false;
    }
  }, []);

  // Poll for pending job status updates
  const pollPendingJobs = useCallback(async () => {
    const pendingJobs = Object.values(generationJobs).filter(
      job => job.status === 'pending' || job.status === 'processing'
    );
    
    if (pendingJobs.length === 0) return;
    
    let hasUpdates = false;
    
    for (const job of pendingJobs) {
      // Check if job has timed out
      if (isJobTimedOut(job)) {
        const timedOut = await handleJobTimeout(job);
        if (timedOut) {
          hasUpdates = true;
          continue;
        }
      }
      
      try {
        const response = await generationAPI.getGenerationStatus(job.id);
        const updatedJob = response.data.data || response.data;
        
        if (updatedJob.status !== job.status) {
          hasUpdates = true;
          setGenerationJobs(prev => ({
            ...prev,
            [job.item_id || job.item]: updatedJob,
          }));
          
          // If completed, update the item's image_url
          if (updatedJob.status === 'completed' && updatedJob.image_url) {
            setItems(prev => prev.map(item => {
              if (item.id === (job.item_id || job.item)) {
                return {
                  ...item,
                  attributes: {
                    ...item.attributes,
                    image_url: updatedJob.image_url,
                  },
                };
              }
              return item;
            }));
          }
        }
      } catch (err) {
        console.warn(`Failed to poll job ${job.id}:`, err);
      }
    }
    
    // Refresh stats if there were updates
    if (hasUpdates) {
      loadItems(true);
    }
  }, [generationJobs, loadItems, isJobTimedOut, handleJobTimeout]);

  // Initial load
  useEffect(() => {
    isMountedRef.current = true;
    loadItems();
    
    return () => {
      isMountedRef.current = false;
    };
  }, [loadItems]);

  // Refresh when trigger changes
  useEffect(() => {
    if (refreshTrigger > 0) {
      loadItems();
    }
  }, [refreshTrigger, loadItems]);

  // Set up polling for pending jobs
  useEffect(() => {
    const hasPendingJobs = Object.values(generationJobs).some(
      job => job.status === 'pending' || job.status === 'processing'
    );
    
    if (hasPendingJobs) {
      pollIntervalRef.current = setInterval(pollPendingJobs, pollInterval);
    }
    
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [generationJobs, pollPendingJobs, pollInterval]);

  // Handle retry
  const handleRetry = async (jobId) => {
    try {
      await generationAPI.retryGeneration(jobId);
      loadItems();
    } catch (err) {
      console.error('Failed to retry generation:', err);
    }
  };

  // Filter items
  const getFilteredItems = () => {
    if (filter === 'all') return items;
    
    return items.filter(item => {
      const job = generationJobs[item.id];
      const status = job?.status || (item.attributes?.image_url ? 'completed' : 'pending');
      
      if (filter === 'pending') {
        return status === 'pending' || status === 'processing';
      }
      return status === filter;
    });
  };

  const filteredItems = getFilteredItems();

  if (loading) {
    return (
      <div className="character-gallery-loading">
        <div className="spinner"></div>
        <p>Loading characters...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="character-gallery-error">
        <p>{error}</p>
        <button onClick={() => loadItems()} className="retry-button">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="character-gallery">
      {/* Stats bar */}
      <div className="gallery-stats">
        <div className="stat-item">
          <span className="stat-count">{items.length}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="stat-item completed">
          <span className="stat-count">{stats.completed}</span>
          <span className="stat-label">Ready</span>
        </div>
        <div className="stat-item pending">
          <span className="stat-count">{stats.pending}</span>
          <span className="stat-label">Generating</span>
        </div>
        <div className="stat-item failed">
          <span className="stat-count">{stats.failed}</span>
          <span className="stat-label">Failed</span>
        </div>
      </div>

      {/* Filter controls */}
      <div className="gallery-controls">
        <div className="filter-buttons">
          <button 
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={`filter-btn ${filter === 'completed' ? 'active' : ''}`}
            onClick={() => setFilter('completed')}
          >
            Ready
          </button>
          <button 
            className={`filter-btn ${filter === 'pending' ? 'active' : ''}`}
            onClick={() => setFilter('pending')}
          >
            Generating
          </button>
          <button 
            className={`filter-btn ${filter === 'failed' ? 'active' : ''}`}
            onClick={() => setFilter('failed')}
          >
            Failed
          </button>
        </div>
        
        <button onClick={() => loadItems()} className="refresh-btn" title="Refresh">
          ↻ Refresh
        </button>
      </div>

      {/* Gallery grid */}
      {filteredItems.length === 0 ? (
        <div className="gallery-empty">
          {items.length === 0 ? (
            <>
              <span className="empty-icon">🎨</span>
              <p>No characters yet.</p>
              <p className="empty-hint">Create your first character to get started!</p>
            </>
          ) : (
            <p>No characters match the current filter.</p>
          )}
        </div>
      ) : (
        <div className="gallery-grid">
          {filteredItems.map((item) => (
            <CharacterCard
              key={item.id}
              item={item}
              generationJob={generationJobs[item.id]}
              onCreateVariation={onCreateVariation}
              onViewDetails={onViewDetails}
              onRetry={handleRetry}
              onNavigateToVersion={onNavigateToVersion}
            />
          ))}
        </div>
      )}

      {/* Polling indicator */}
      {stats.pending > 0 && (
        <div className="polling-indicator">
          <span className="polling-dot"></span>
          Auto-refreshing pending generations...
        </div>
      )}
      
      {/* Toast notification for timeouts */}
      {toastMessage && (
        <Toast
          type={toastMessage.type}
          message={toastMessage.message}
          onClose={() => setToastMessage(null)}
          duration={6000}
        />
      )}
    </div>
  );
}

export default CharacterGallery;
