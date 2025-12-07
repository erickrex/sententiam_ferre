import React, { useState } from 'react';
import './TagSelector.css';

function TagSelector({ taxonomies, selectedTermIds = [], onChange, disabled = false }) {
  const [expandedTaxonomies, setExpandedTaxonomies] = useState(new Set());

  const toggleTaxonomy = (taxonomyId) => {
    setExpandedTaxonomies(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taxonomyId)) {
        newSet.delete(taxonomyId);
      } else {
        newSet.add(taxonomyId);
      }
      return newSet;
    });
  };

  const handleTermToggle = (termId) => {
    if (disabled) return;

    const newSelectedTermIds = selectedTermIds.includes(termId)
      ? selectedTermIds.filter(id => id !== termId)
      : [...selectedTermIds, termId];
    
    onChange(newSelectedTermIds);
  };

  const isTermSelected = (termId) => {
    return selectedTermIds.includes(termId);
  };

  if (!taxonomies || taxonomies.length === 0) {
    return (
      <div className="tag-selector-empty">
        No taxonomies available. Create taxonomies first to tag items.
      </div>
    );
  }

  return (
    <div className="tag-selector">
      {taxonomies.map((taxonomy) => (
        <div key={taxonomy.id} className="taxonomy-section">
          <button
            type="button"
            className="taxonomy-header"
            onClick={() => toggleTaxonomy(taxonomy.id)}
            disabled={disabled}
          >
            <span className="taxonomy-name">{taxonomy.name}</span>
            <span className="taxonomy-toggle">
              {expandedTaxonomies.has(taxonomy.id) ? '▼' : '▶'}
            </span>
          </button>

          {expandedTaxonomies.has(taxonomy.id) && taxonomy.terms && (
            <div className="terms-list">
              {taxonomy.terms.length === 0 ? (
                <div className="terms-empty">No terms in this taxonomy</div>
              ) : (
                taxonomy.terms.map((term) => (
                  <label
                    key={term.id}
                    className={`term-checkbox-label ${disabled ? 'disabled' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={isTermSelected(term.id)}
                      onChange={() => handleTermToggle(term.id)}
                      disabled={disabled}
                      className="term-checkbox"
                    />
                    <span className="term-value">{term.value}</span>
                    {term.attributes?.color && (
                      <span
                        className="term-color-indicator"
                        style={{ backgroundColor: term.attributes.color }}
                      />
                    )}
                  </label>
                ))
              )}
            </div>
          )}
        </div>
      ))}

      {selectedTermIds.length > 0 && (
        <div className="selected-tags-summary">
          <span className="summary-label">Selected:</span>
          <span className="summary-count">{selectedTermIds.length} tag(s)</span>
        </div>
      )}
    </div>
  );
}

export default TagSelector;
