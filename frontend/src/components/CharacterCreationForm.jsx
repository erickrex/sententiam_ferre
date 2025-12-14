import React, { useState } from 'react';
import ParameterControls from './ParameterControls';
import { PARAMETER_OPTIONS, PARAMETER_LABELS, DEFAULT_PARAMETERS } from './parameterConstants';
import './CharacterCreationForm.css';

function CharacterCreationForm({ 
  lockedParams = {}, 
  onSubmit, 
  onCancel,
  isSubmitting = false 
}) {
  const [description, setDescription] = useState('');
  const [parameters, setParameters] = useState({
    ...DEFAULT_PARAMETERS,
    ...lockedParams, // Apply locked params as initial values
  });
  const [showSummary, setShowSummary] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    
    if (!description.trim()) {
      newErrors.description = 'Character description is required';
    } else if (description.trim().length < 3) {
      newErrors.description = 'Description must be at least 3 characters';
    } else if (description.trim().length > 500) {
      newErrors.description = 'Description must be less than 500 characters';
    }

    // Validate required parameters
    if (!parameters.art_style) {
      newErrors.art_style = 'Art style is required';
    }
    if (!parameters.view_angle) {
      newErrors.view_angle = 'View angle is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };


  const handleDescriptionChange = (e) => {
    setDescription(e.target.value);
    if (errors.description) {
      setErrors(prev => ({ ...prev, description: '' }));
    }
  };

  const handleParametersChange = (newParams) => {
    setParameters(newParams);
    // Clear any parameter-related errors
    setErrors(prev => {
      const updated = { ...prev };
      delete updated.art_style;
      delete updated.view_angle;
      return updated;
    });
  };

  const handleReviewClick = () => {
    if (validate()) {
      setShowSummary(true);
    }
  };

  const handleBackToEdit = () => {
    setShowSummary(false);
  };

  const handleSubmit = async () => {
    if (!validate()) {
      setShowSummary(false);
      return;
    }

    try {
      await onSubmit({
        description: description.trim(),
        ...parameters,
      });
    } catch (err) {
      setErrors({ submit: err.message || 'Failed to create character' });
      setShowSummary(false);
    }
  };

  const getOptionLabel = (paramName, value) => {
    const options = PARAMETER_OPTIONS[paramName];
    const option = options?.find(opt => opt.value === value);
    return option?.label || value;
  };

  const renderSummary = () => {
    return (
      <div className="creation-summary">
        <h3 className="summary-title">Review Your Character</h3>
        
        <div className="summary-section">
          <h4>Description</h4>
          <p className="summary-description">{description}</p>
        </div>

        <div className="summary-section">
          <h4>Parameters</h4>
          <div className="summary-params">
            {Object.entries(parameters).map(([key, value]) => (
              <div key={key} className="summary-param">
                <span className="param-name">{PARAMETER_LABELS[key]}:</span>
                <span className="param-value">
                  {getOptionLabel(key, value)}
                  {lockedParams[key] !== undefined && (
                    <span className="locked-badge">🔒 Locked</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="summary-actions">
          <button
            type="button"
            onClick={handleBackToEdit}
            className="back-button"
            disabled={isSubmitting}
          >
            Back to Edit
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            className="generate-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Generating...' : 'Generate Character'}
          </button>
        </div>
      </div>
    );
  };


  const renderForm = () => {
    return (
      <>
        {errors.submit && (
          <div className="error-message">{errors.submit}</div>
        )}

        <div className="form-section">
          <label htmlFor="description" className="form-label">
            Character Description <span className="required">*</span>
          </label>
          <textarea
            id="description"
            value={description}
            onChange={handleDescriptionChange}
            className={`description-input ${errors.description ? 'error' : ''}`}
            placeholder="Describe your character (e.g., 'friendly robot sidekick with antenna' or 'angry vegetable villain with leafy hair')"
            rows={3}
            disabled={isSubmitting}
          />
          {errors.description && (
            <span className="field-error">{errors.description}</span>
          )}
          <span className="character-count">
            {description.length}/500 characters
          </span>
        </div>

        <div className="form-section">
          <h3 className="section-title">Style Parameters</h3>
          <ParameterControls
            parameters={parameters}
            lockedParams={lockedParams}
            onChange={handleParametersChange}
            disabled={isSubmitting}
          />
          {(errors.art_style || errors.view_angle) && (
            <span className="field-error">
              {errors.art_style || errors.view_angle}
            </span>
          )}
        </div>

        <div className="form-actions">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="cancel-button"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="button"
            onClick={handleReviewClick}
            className="review-button"
            disabled={isSubmitting}
          >
            Review & Generate
          </button>
        </div>
      </>
    );
  };

  return (
    <div className="character-creation-form">
      <h2 className="form-title">Create New Character</h2>
      {showSummary ? renderSummary() : renderForm()}
    </div>
  );
}

export default CharacterCreationForm;
