import React, { useState, useEffect, useCallback } from 'react';
import { generationAPI } from '../services/api';
import { PARAMETER_LABELS } from './parameterConstants';
import './VersionNavigator.css';

/**
 * VersionNavigator component displays version information for a character item.
 * Shows version count, enables navigation between parent and child versions,
 * and displays parameter differences from parent.
 * 
 * Requirements: 5.3, 5.5
 */
function VersionNavigator({ 
  item, 
  onClose, 
  onNavigate 
}) {
  const [versionData, setVersionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Fetch version information for the item
  const loadVersionData = useCallback(async () => {
    if (!item?.id) return;
    
    try {
      setLoading(true);
      setError('');
      
      const response = await generationAPI.getItemVersions(item.id);
      const data = response.data.data || response.data;
      setVersionData(data);
    } catch (err) {
      console.error('Failed to load version data:', err);
      setError(err.message || 'Failed to load version information');
    } finally {
      setLoading(false);
    }
  }, [item?.id]);

  useEffect(() => {
    loadVersionData();
  }, [loadVersionData]);

  // Handle clicking outside to close
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose?.();
    }
  };

  // Handle keyboard escape to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose?.();
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Navigate to a different version
  const handleNavigate = (targetItem) => {
    onNavigate?.(targetItem);
    onClose?.();
  };

  // Get parameter label for display
  const getParamLabel = (value) => {
    if (!value) return 'N/A';
    return value.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  // Calculate parameter differences from parent
  const getParamDiff = () => {
    if (!versionData || !item) return [];
    
    const currentParams = item.attributes?.generation_params || {};
    const parentItemId = item.attributes?.parent_item_id;
    
    if (!parentItemId) return [];
    
    // Find parent in version chain
    const parentInChain = versionData.version_chain?.find(
      v => v.id === parentItemId
    );
    
    if (!parentInChain) return [];
    
    const parentParams = parentInChain.attributes?.generation_params || {};
    const diffs = [];
    
    // Compare all parameters
    const allParams = new Set([
      ...Object.keys(currentParams),
      ...Object.keys(parentParams)
    ]);
    
    for (const param of allParams) {
      if (currentParams[param] !== parentParams[param]) {
        diffs.push({
          param,
          label: PARAMETER_LABELS[param] || param,
          oldValue: parentParams[param],
          newValue: currentParams[param],
        });
      }
    }
    
    return diffs;
  };

  const attributes = item?.attributes || {};
  const description = attributes.description || item?.label || 'Character';
  const version = attributes.version || 1;
  const paramDiffs = getParamDiff();

  return (
    <div className="version-navigator-overlay" onClick={handleOverlayClick}>
      <div className="version-navigator" role="dialog" aria-modal="true">
        {/* Header */}
        <div className="version-navigator-header">
          <h2 className="version-navigator-title">
            <span className="title-icon">🔀</span>
            Version History
          </h2>
          <button 
            className="version-navigator-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="version-navigator-content">
          {loading ? (
            <div className="version-navigator-loading">
              <div className="loading-spinner"></div>
              <span>Loading version info...</span>
            </div>
          ) : error ? (
            <div className="version-navigator-error">
              <p>{error}</p>
              <button onClick={loadVersionData}>Try Again</button>
            </div>
          ) : (
            <>
              {/* Current version info */}
              <div className="current-version-info">
                <div className="current-version-label">Current Character</div>
                <div className="current-version-name">{description}</div>
                <span className="current-version-badge">
                  <span>v{version}</span>
                </span>
                
                {versionData && (
                  <div className="version-stats">
                    <div className="version-stat">
                      <span className="stat-icon">📊</span>
                      <span>{versionData.variation_count || 0} variation{versionData.variation_count !== 1 ? 's' : ''}</span>
                    </div>
                    {versionData.parent_item_id && (
                      <div className="version-stat">
                        <span className="stat-icon">👆</span>
                        <span>Has parent</span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Parameter differences from parent */}
              {versionData?.parent_item_id && (
                <div className="param-diff-section">
                  <h3 className="section-title">
                    <span className="section-icon">🔄</span>
                    Changes from Parent
                  </h3>
                  {paramDiffs.length > 0 ? (
                    <div className="param-diff-list">
                      {paramDiffs.map(diff => (
                        <div key={diff.param} className="param-diff-item">
                          <span className="param-diff-name">{diff.label}</span>
                          <div className="param-diff-values">
                            <span className="param-diff-old">
                              {getParamLabel(diff.oldValue)}
                            </span>
                            <span className="param-diff-arrow">→</span>
                            <span className="param-diff-new">
                              {getParamLabel(diff.newValue)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-diff-message">
                      No parameter changes from parent
                    </div>
                  )}
                </div>
              )}

              {/* Version chain (ancestors) */}
              {versionData?.version_chain && versionData.version_chain.length > 0 && (
                <div className="version-chain-section">
                  <h3 className="section-title">
                    <span className="section-icon">📜</span>
                    Version Chain
                  </h3>
                  <div className="version-chain-list">
                    {versionData.version_chain.map((chainItem, index) => {
                      const isRoot = index === 0;
                      const isCurrent = chainItem.id === item.id;
                      
                      return (
                        <div 
                          key={chainItem.id}
                          className={`version-chain-item ${isRoot ? 'root' : ''} ${isCurrent ? 'current' : ''}`}
                          onClick={() => !isCurrent && handleNavigate(chainItem)}
                          role="button"
                          tabIndex={isCurrent ? -1 : 0}
                        >
                          <div className="chain-connector">
                            {index > 0 && <div className="chain-line"></div>}
                            <div className="chain-dot"></div>
                          </div>
                          <div className="chain-info">
                            <div className="chain-label">{chainItem.label}</div>
                            <div className="chain-version">Version {chainItem.version}</div>
                          </div>
                          {isRoot && (
                            <span className="chain-badge root-badge">Original</span>
                          )}
                          {isCurrent && (
                            <span className="chain-badge current-badge">Current</span>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Child variations */}
              {versionData?.children && versionData.children.length > 0 && (
                <div className="variations-section">
                  <h3 className="section-title">
                    <span className="section-icon">🌿</span>
                    Variations ({versionData.children.length})
                  </h3>
                  <div className="variations-list">
                    {versionData.children.map(child => (
                      <div 
                        key={child.id}
                        className="variation-item"
                        onClick={() => handleNavigate(child)}
                        role="button"
                        tabIndex={0}
                      >
                        <span className="variation-icon">↳</span>
                        <div className="variation-info">
                          <div className="variation-label">{child.label}</div>
                          <div className="variation-version">Version {child.version}</div>
                        </div>
                        <span className="variation-arrow">›</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* No variations message */}
              {(!versionData?.children || versionData.children.length === 0) && 
               (!versionData?.version_chain || versionData.version_chain.length <= 1) && (
                <div className="no-variations-message">
                  This is the original character with no variations yet.
                  <br />
                  Use "Create Variation" to make new versions!
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default VersionNavigator;
