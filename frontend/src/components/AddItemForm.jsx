import React, { useState, useEffect } from 'react';
import TagSelector from './TagSelector';
import './AddItemForm.css';

function AddItemForm({ onSubmit, onCancel, initialData, taxonomies }) {
  const [formData, setFormData] = useState({
    label: '',
    external_ref: '',
    attributes: {},
    term_ids: []
  });
  const [attributeKey, setAttributeKey] = useState('');
  const [attributeValue, setAttributeValue] = useState('');
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        label: initialData.label || '',
        external_ref: initialData.external_ref || '',
        attributes: initialData.attributes || {},
        term_ids: initialData.terms?.map(t => t.id) || []
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleAddAttribute = () => {
    if (!attributeKey.trim()) {
      setErrors(prev => ({ ...prev, attribute: 'Attribute key is required' }));
      return;
    }

    // Try to parse value as JSON, otherwise use as string
    let parsedValue = attributeValue;
    try {
      // Check if it looks like a number
      if (!isNaN(attributeValue) && attributeValue.trim() !== '') {
        parsedValue = Number(attributeValue);
      } else if (attributeValue.toLowerCase() === 'true') {
        parsedValue = true;
      } else if (attributeValue.toLowerCase() === 'false') {
        parsedValue = false;
      } else if (attributeValue.startsWith('{') || attributeValue.startsWith('[')) {
        parsedValue = JSON.parse(attributeValue);
      }
    } catch (e) {
      // Keep as string if parsing fails
    }

    setFormData(prev => ({
      ...prev,
      attributes: {
        ...prev.attributes,
        [attributeKey]: parsedValue
      }
    }));

    setAttributeKey('');
    setAttributeValue('');
    setErrors(prev => ({ ...prev, attribute: '' }));
  };

  const handleRemoveAttribute = (key) => {
    setFormData(prev => {
      const newAttributes = { ...prev.attributes };
      delete newAttributes[key];
      return {
        ...prev,
        attributes: newAttributes
      };
    });
  };

  const handleTagsChange = (selectedTermIds) => {
    setFormData(prev => ({
      ...prev,
      term_ids: selectedTermIds
    }));
  };

  const validate = () => {
    const newErrors = {};
    
    if (!formData.label.trim()) {
      newErrors.label = 'Label is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    
    if (!validate()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      await onSubmit(formData);
    } catch (err) {
      setErrors({ submit: err.message || 'Failed to save item' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatAttributeValue = (value) => {
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  };

  return (
    <form className="add-item-form" onSubmit={handleSubmit}>
      <h2 className="form-title">
        {initialData ? 'Edit Item' : 'Add New Item'}
      </h2>
      
      {errors.submit && (
        <div className="error-message">{errors.submit}</div>
      )}
      
      <div className="form-group">
        <label htmlFor="label" className="form-label">
          Label <span className="required">*</span>
        </label>
        <input
          type="text"
          id="label"
          name="label"
          value={formData.label}
          onChange={handleChange}
          className={`form-input ${errors.label ? 'error' : ''}`}
          placeholder="e.g., Italian Restaurant Downtown"
          disabled={isSubmitting}
        />
        {errors.label && <span className="field-error">{errors.label}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="external_ref" className="form-label">
          External Reference
        </label>
        <input
          type="text"
          id="external_ref"
          name="external_ref"
          value={formData.external_ref}
          onChange={handleChange}
          className="form-input"
          placeholder="e.g., yelp-12345"
          disabled={isSubmitting}
        />
        <span className="field-hint">
          Optional unique identifier from external system
        </span>
      </div>
      
      <div className="form-group">
        <label className="form-label">Attributes</label>
        
        {Object.keys(formData.attributes).length > 0 && (
          <div className="attributes-list">
            {Object.entries(formData.attributes).map(([key, value]) => (
              <div key={key} className="attribute-item">
                <span className="attribute-display">
                  <strong>{key}:</strong> {formatAttributeValue(value)}
                </span>
                <button
                  type="button"
                  onClick={() => handleRemoveAttribute(key)}
                  className="remove-attribute-button"
                  disabled={isSubmitting}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
        
        <div className="attribute-input-group">
          <input
            type="text"
            value={attributeKey}
            onChange={(e) => setAttributeKey(e.target.value)}
            className="attribute-key-input"
            placeholder="Key (e.g., price)"
            disabled={isSubmitting}
          />
          <input
            type="text"
            value={attributeValue}
            onChange={(e) => setAttributeValue(e.target.value)}
            className="attribute-value-input"
            placeholder="Value (e.g., 25)"
            disabled={isSubmitting}
          />
          <button
            type="button"
            onClick={handleAddAttribute}
            className="add-attribute-button"
            disabled={isSubmitting}
          >
            Add
          </button>
        </div>
        {errors.attribute && <span className="field-error">{errors.attribute}</span>}
        <span className="field-hint">
          Add custom attributes as key-value pairs. Numbers and booleans will be auto-detected.
        </span>
      </div>
      
      {taxonomies && taxonomies.length > 0 && (
        <div className="form-group">
          <label className="form-label">Tags</label>
          <TagSelector
            taxonomies={taxonomies}
            selectedTermIds={formData.term_ids}
            onChange={handleTagsChange}
            disabled={isSubmitting}
          />
        </div>
      )}
      
      <div className="form-actions">
        <button
          type="button"
          onClick={onCancel}
          className="cancel-button"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="submit-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : (initialData ? 'Update Item' : 'Add Item')}
        </button>
      </div>
    </form>
  );
}

export default AddItemForm;
