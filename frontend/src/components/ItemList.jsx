import React from 'react';
import './ItemList.css';

function ItemList({ items, onEdit, onDelete, isAdmin }) {
  if (!items || items.length === 0) {
    return (
      <div className="item-list-empty">
        <p>No items yet. Add some items to get started!</p>
      </div>
    );
  }

  const formatAttributeValue = (value) => {
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <div className="item-list">
      {items.map((item) => (
        <div key={item.id} className="item-list-card">
          <div className="item-list-header">
            <h3 className="item-list-label">{item.label}</h3>
            {isAdmin && (
              <div className="item-list-actions">
                <button
                  className="item-action-button edit"
                  onClick={() => onEdit(item)}
                  title="Edit item"
                >
                  ✏️
                </button>
                <button
                  className="item-action-button delete"
                  onClick={() => onDelete(item.id)}
                  title="Delete item"
                >
                  🗑️
                </button>
              </div>
            )}
          </div>

          {item.attributes && Object.keys(item.attributes).length > 0 && (
            <div className="item-list-attributes">
              {Object.entries(item.attributes).map(([key, value]) => (
                <div key={key} className="item-list-attribute">
                  <span className="attribute-key">{key}:</span>
                  <span className="attribute-value">
                    {formatAttributeValue(value)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {item.terms && item.terms.length > 0 && (
            <div className="item-list-tags">
              {item.terms.map((term) => (
                <span key={term.id} className="item-tag">
                  {term.taxonomy_name}: {term.value}
                </span>
              ))}
            </div>
          )}

          {item.external_ref && (
            <div className="item-list-ref">
              <span className="ref-label">Ref:</span>
              <span className="ref-value">{item.external_ref}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default ItemList;
