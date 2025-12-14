import React, { useState } from 'react';
import { PARAMETER_LABELS } from './parameterConstants';
import VersionNavigator from './VersionNavigator';
import './CharacterCard.css';

/**
 * CharacterCard component displays a generated character with its status and parameters.
 * Supports pending, completed, and failed generation states.
 * Includes version indicator that opens VersionNavigator on click.
 * 
 * Requirements: 2.4, 5.1, 5.3
 */
function CharacterCard({ 
  item, 
  generationJob,
  onCreateVariation,
  onViewDetails,
  onRetry,
  onNavigateToVersion,
  showActions = true
}) {
  const [showVersionNavigator, setShowVersionNavigator] = useState(false);
  
  const attributes = item.attributes || {};
  const generationParams = attributes.generation_params || {};
  const imageUrl = attributes.image_url;
  const description = attributes.description || item.label;
  const version = attributes.version || 1;
  const hasParent = !!attributes.parent_item_id;
  const variationCount = item.variation_count || 0;
  
  // Determine status from generation job or item state
  const status = generationJob?.status || (imageUrl ? 'completed' : 'pending');
  const errorMessage = generationJob?.error_message;

  // Key parameters to display
  const displayParams = ['art_style', 'pose', 'expression'];

  const getStatusIndicator = () => {
    switch (status) {
      case 'pending':
      case 'processing':
        return (
          <div className="character-status pending">
            <span className="status-spinner"></span>
            <span className="status-text">Generating...</span>
          </div>
        );
      case 'failed':
        return (
          <div className="character-status failed">
            <span className="status-icon">⚠️</span>
            <span className="status-text">Failed</span>
          </div>
        );
      case 'completed':
        return (
          <div className="character-status completed">
            <span className="status-icon">✓</span>
            <span className="status-text">Ready</span>
          </div>
        );
      default:
        return null;
    }
  };

  const renderImage = () => {
    if (status === 'pending' || status === 'processing') {
      return (
        <div className="character-card-image-placeholder generating">
          <div className="generating-animation">
            <div className="pulse-ring"></div>
            <span className="generating-icon">🎨</span>
          </div>
          <span className="generating-text">Creating character...</span>
        </div>
      );
    }

    if (status === 'failed') {
      return (
        <div className="character-card-image-placeholder error">
          <span className="error-icon">❌</span>
          <span className="error-text">Generation failed</span>
          {errorMessage && (
            <span className="error-message">{errorMessage}</span>
          )}
        </div>
      );
    }

    if (imageUrl) {
      return (
        <img 
          src={imageUrl} 
          alt={description} 
          className="character-card-image"
          loading="lazy"
        />
      );
    }

    return (
      <div className="character-card-image-placeholder">
        <span className="placeholder-icon">🎭</span>
      </div>
    );
  };

  const getParamLabel = (value) => {
    // Convert snake_case to Title Case
    if (!value) return 'N/A';
    return value.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className={`character-card status-${status}`}>
      {/* Status indicator */}
      {getStatusIndicator()}
      
      {/* Version badge - clickable to open version navigator */}
      {(version > 1 || variationCount > 0) && (
        <button 
          className="version-badge clickable" 
          title={`${hasParent ? 'Variation' : 'Version'} - Click to view version history`}
          onClick={(e) => {
            e.stopPropagation();
            setShowVersionNavigator(true);
          }}
        >
          v{version}
          {variationCount > 0 && (
            <span className="variation-count">+{variationCount}</span>
          )}
        </button>
      )}
      
      {/* Character image or placeholder */}
      <div className="character-card-image-container">
        {renderImage()}
      </div>
      
      {/* Character info */}
      <div className="character-card-content">
        <h3 className="character-card-title" title={description}>
          {description}
        </h3>
        
        {/* Key parameters */}
        <div className="character-card-params">
          {displayParams.map(param => (
            generationParams[param] && (
              <div key={param} className="param-tag">
                <span className="param-label">{PARAMETER_LABELS[param]}:</span>
                <span className="param-value">{getParamLabel(generationParams[param])}</span>
              </div>
            )
          ))}
        </div>
        
        {/* Actions */}
        {showActions && (
          <div className="character-card-actions">
            {status === 'completed' && (
              <>
                <button 
                  className="action-btn primary"
                  onClick={() => onCreateVariation?.(item)}
                  title="Create a variation of this character"
                >
                  <span className="btn-icon">🔄</span>
                  Create Variation
                </button>
                <button 
                  className="action-btn secondary"
                  onClick={() => onViewDetails?.(item)}
                  title="View full details"
                >
                  <span className="btn-icon">👁️</span>
                  Details
                </button>
              </>
            )}
            {status === 'failed' && onRetry && (
              <button 
                className="action-btn retry"
                onClick={() => onRetry?.(generationJob?.id || item.id)}
                title="Retry generation"
              >
                <span className="btn-icon">🔁</span>
                Retry
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Version Navigator Modal */}
      {showVersionNavigator && (
        <VersionNavigator
          item={item}
          onClose={() => setShowVersionNavigator(false)}
          onNavigate={(targetItem) => {
            setShowVersionNavigator(false);
            onNavigateToVersion?.(targetItem);
          }}
        />
      )}
    </div>
  );
}

export default CharacterCard;
