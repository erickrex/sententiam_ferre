import React, { useState } from 'react';
import './ItemFilter.css';

function ItemFilter({ taxonomies, onFilterChange, disabled = false }) {
  const [selectedTags, setSelectedTags] = useState([]);
  const [attributeFilters, setAttributeFilters] = useState([]);
  const [newAttributeKey, setNewAttributeKey] = useState('');
  const [newAttributeValue, setNewAttributeValue] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  const handleTagToggle = (taxonomyName, termValue, termId) => {
    const tagKey = `${taxonomyName}:${termValue}`;
    const isSelected = selectedTags.some(tag => tag.key === tagKey);

    let newSelectedTags;
    if (isSelected) {
      newSelectedTags = selectedTags.filter(tag => tag.key !== tagKey);
    } else {
      newSelectedTags = [...selectedTags, { key: tagKey, termId, taxonomyName, termValue }];
    }

    setSelectedTags(newSelectedTags);
    notifyFilterChange(newSelectedTags, attributeFilters);
  };

  const handleAddAttributeFilter = () => {
    if (!newAttributeKey.trim() || !newAttributeValue.trim()) {
      return;
    }

    const newFilter = {
      key: newAttributeKey,
      value: newAttributeValue
    };

    const newAttributeFilters = [...attributeFilters, newFilter];
    setAttributeFilters(newAttributeFilters);
    setNewAttributeKey('');
    setNewAttributeValue('');
    notifyFilterChange(selectedTags, newAttributeFilters);
  };

  const handleRemoveAttributeFilter = (index) => {
    const newAttributeFilters = attributeFilters.filter((_, i) => i !== index);
    setAttributeFilters(newAttributeFilters);
    notifyFilterChange(selectedTags, newAttributeFilters);
  };

  const handleClearAll = () => {
    setSelectedTags([]);
    setAttributeFilters([]);
    notifyFilterChange([], []);
  };

  const notifyFilterChange = (tags, attributes) => {
    const filters = {
      tags: tags.map(tag => tag.termId),
      attributes: attributes.reduce((acc, filter) => {
        acc[filter.key] = filter.value;
        return acc;
      }, {})
    };
    onFilterChange(filters);
  };

  const hasActiveFilters = selectedTags.length > 0 || attributeFilters.length > 0;

  return (
    <div className="item-filter">
      <div className="filter-header">
        <button
          type="button"
          className="filter-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
          disabled={disabled}
        >
          <span className="filter-icon">🔍</span>
          <span className="filter-title">Filters</span>
          {hasActiveFilters && (
            <span className="filter-badge">{selectedTags.length + attributeFilters.length}</span>
          )}
          <span className="filter-arrow">{isExpanded ? '▼' : '▶'}</span>
        </button>

        {hasActiveFilters && (
          <button
            type="button"
            className="clear-filters-button"
            onClick={handleClearAll}
            disabled={disabled}
          >
            Clear All
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="filter-content">
          {/* Tag Filters */}
          {taxonomies && taxonomies.length > 0 && (
            <div className="filter-section">
              <h4 className="filter-section-title">Filter by Tags</h4>
              {taxonomies.map((taxonomy) => (
                <div key={taxonomy.id} className="taxonomy-filter">
                  <div className="taxonomy-filter-name">{taxonomy.name}</div>
                  {taxonomy.terms && taxonomy.terms.length > 0 && (
                    <div className="terms-filter-list">
                      {taxonomy.terms.map((term) => {
                        const tagKey = `${taxonomy.name}:${term.value}`;
                        const isSelected = selectedTags.some(tag => tag.key === tagKey);
                        
                        return (
                          <button
                            key={term.id}
                            type="button"
                            className={`term-filter-button ${isSelected ? 'selected' : ''}`}
                            onClick={() => handleTagToggle(taxonomy.name, term.value, term.id)}
                            disabled={disabled}
                          >
                            {term.value}
                            {term.attributes?.color && (
                              <span
                                className="term-color-dot"
                                style={{ backgroundColor: term.attributes.color }}
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Attribute Filters */}
          <div className="filter-section">
            <h4 className="filter-section-title">Filter by Attributes</h4>
            
            {attributeFilters.length > 0 && (
              <div className="active-attribute-filters">
                {attributeFilters.map((filter, index) => (
                  <div key={index} className="attribute-filter-item">
                    <span className="attribute-filter-text">
                      {filter.key}: {filter.value}
                    </span>
                    <button
                      type="button"
                      className="remove-filter-button"
                      onClick={() => handleRemoveAttributeFilter(index)}
                      disabled={disabled}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="attribute-filter-input">
              <input
                type="text"
                value={newAttributeKey}
                onChange={(e) => setNewAttributeKey(e.target.value)}
                placeholder="Attribute key"
                className="attribute-filter-key"
                disabled={disabled}
              />
              <input
                type="text"
                value={newAttributeValue}
                onChange={(e) => setNewAttributeValue(e.target.value)}
                placeholder="Value"
                className="attribute-filter-value"
                disabled={disabled}
              />
              <button
                type="button"
                onClick={handleAddAttributeFilter}
                className="add-filter-button"
                disabled={disabled || !newAttributeKey.trim() || !newAttributeValue.trim()}
              >
                Add
              </button>
            </div>
            <div className="filter-hint">
              Add custom attribute filters (e.g., price: 25, color: red)
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ItemFilter;
