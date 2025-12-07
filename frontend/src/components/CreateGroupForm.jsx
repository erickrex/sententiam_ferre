import React, { useState } from 'react';
import './CreateGroupForm.css';

function CreateGroupForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Group name is required';
    } else if (formData.name.trim().length < 3) {
      newErrors.name = 'Group name must be at least 3 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        name: formData.name.trim(),
        description: formData.description.trim(),
      });
      
      // Reset form on success
      setFormData({ name: '', description: '' });
      setErrors({});
    } catch (error) {
      setErrors({ submit: error.message || 'Failed to create group' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="create-group-form" onSubmit={handleSubmit}>
      <h2 className="form-title">Create New Group</h2>
      
      <div className="form-group">
        <label htmlFor="name">Group Name *</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className={errors.name ? 'error' : ''}
          disabled={isSubmitting}
          placeholder="Enter group name"
          maxLength={100}
        />
        {errors.name && <span className="error-message">{errors.name}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="description">Description (optional)</label>
        <textarea
          id="description"
          name="description"
          value={formData.description}
          onChange={handleChange}
          disabled={isSubmitting}
          placeholder="What is this group about?"
          rows={4}
          maxLength={500}
        />
        <span className="char-count">
          {formData.description.length}/500
        </span>
      </div>

      {errors.submit && (
        <div className="form-error">
          {errors.submit}
        </div>
      )}

      <div className="form-actions">
        {onCancel && (
          <button 
            type="button" 
            className="cancel-button" 
            onClick={onCancel}
            disabled={isSubmitting}
          >
            Cancel
          </button>
        )}
        <button 
          type="submit" 
          className="submit-button" 
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Creating...' : 'Create Group'}
        </button>
      </div>
    </form>
  );
}

export default CreateGroupForm;
