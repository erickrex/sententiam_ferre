import React from 'react';
import './ItemCard.css';

function ItemCard({ item, style }) {
  // Extract attributes from the item
  const attributes = item.attributes || {};
  
  return (
    <div className="item-card" style={style}>
      <div className="item-card-content">
        {/* Image placeholder or actual image if available */}
        {attributes.image_url ? (
          <img 
            src={attributes.image_url} 
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
                .filter(([key]) => key !== 'image_url')
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
