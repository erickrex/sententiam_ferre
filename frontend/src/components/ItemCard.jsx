import React from 'react';
import { PARAMETER_LABELS } from './parameterConstants';
import './ItemCard.css';

/**
 * ItemCard component displays an item for voting.
 * Supports both text-based items and 2D character items with images.
 * 
 * Requirements: 7.1, 7.2 - Display character image prominently with parameters
 */
function ItemCard({ item, style }) {
  // Extract attributes from the item
  const attributes = item.attributes || {};
  const isCharacterItem = attributes.type === '2d_character';
  const generationParams = attributes.generation_params || {};
  const imageUrl = attributes.image_url;
  const description = attributes.description || item.label;
  
  // Key parameters to display for character items
  const displayParams = ['art_style', 'pose', 'expression'];
  
  // Convert snake_case to Title Case
  const formatParamValue = (value) => {
    if (!value) return 'N/A';
    return value.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };
  
  // Render character item with image and parameters
  if (isCharacterItem) {
    return (
      <div className="item-card item-card-character" style={style}>
        <div className="item-card-content">
          {/* Character image - displayed prominently */}
          {imageUrl ? (
            <div className="item-card-image-wrapper">
              <img 
                src={imageUrl} 
                alt={description} 
                className="item-card-image item-card-character-image"
              />
            </div>
          ) : (
            <div className="item-card-image-placeholder item-card-character-placeholder">
              <span className="placeholder-icon">🎭</span>
              <span className="item-card-label-large">{description}</span>
            </div>
          )}
          
          {/* Character info */}
          <div className="item-card-info item-card-character-info">
            <h2 className="item-card-label">{description}</h2>
            
            {/* Generation parameters displayed as tags */}
            <div className="item-card-params">
              {displayParams.map(param => (
                generationParams[param] && (
                  <div key={param} className="item-card-param-tag">
                    <span className="param-label">{PARAMETER_LABELS[param] || param}:</span>
                    <span className="param-value">{formatParamValue(generationParams[param])}</span>
                  </div>
                )
              ))}
            </div>
            
            {/* Additional parameters if present */}
            {generationParams.view_angle && (
              <div className="item-card-secondary-params">
                <span className="secondary-param">
                  {PARAMETER_LABELS.view_angle}: {formatParamValue(generationParams.view_angle)}
                </span>
                {generationParams.color_palette && (
                  <span className="secondary-param">
                    {PARAMETER_LABELS.color_palette}: {formatParamValue(generationParams.color_palette)}
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }
  
  // Render standard text-based item
  return (
    <div className="item-card" style={style}>
      <div className="item-card-content">
        {/* Image placeholder or actual image if available */}
        {imageUrl ? (
          <img 
            src={imageUrl} 
            alt={item.label} 
            className="item-card-image"
          />
        ) : (
          <div className="item-card-image-placeholder">
            <span className="item-card-label-large">{item.label}</span>
          </div>
        )}
        
        {/* Item label */}
        <div className="item-card-info">
          <h2 className="item-card-label">{item.label}</h2>
          
          {/* Display attributes */}
          {Object.keys(attributes).length > 0 && (
            <div className="item-card-attributes">
              {Object.entries(attributes)
                .filter(([key]) => !['image_url', 'type', 'generation_params', 'description', 'parent_item_id', 'version'].includes(key))
                .map(([key, value]) => (
                  <div key={key} className="item-card-attribute">
                    <span className="attribute-key">{key}:</span>
                    <span className="attribute-value">{String(value)}</span>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ItemCard;
