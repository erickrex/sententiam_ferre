import React, { useState, useEffect } from 'react';
import { PARAMETER_OPTIONS, PARAMETER_LABELS, DEFAULT_PARAMETERS } from './parameterConstants';
import './VariationEditor.css';

/**
 * VariationEditor component allows users to adjust character parameters
 * and create variations with a preview before publishing.
 * 
 * Supports draft workflow: Preview → Regenerate → Publish/Discard
 */
function VariationEditor({
  parentItem,
  draftItem,
  generationJob,
  lockedParams = {},
  onCreateVariation,
  onRegenerate,
  onPublish,
  onDiscard,
  onClose,
  isLoading = false,
}) {
  // Get parent's parameters as starting point
  const parentAttributes = parentItem?.attributes || {};
  const parentParams = parentAttributes.generation_params || {};
  const parentDescription = parentAttributes.description || parentItem?.label || '';
  
  // Get draft's current parameters if exists
  const draftAttributes = draftItem?.attributes || {};
  const draftParams = draftAttributes.generation_params || {};
  const draftImageUrl = draftAttributes.image_url;
  
  // Initialize parameters from draft (if exists) or parent
  const [parameters, setParameters] = useState(() => {
    const source = draftItem ? draftParams : parentParams;
    return {
      description: draftItem ? draftAttributes.description : parentDescription,
      art_style: source.art_style || DEFAULT_PARAMETERS.art_style,
      view_angle: source.view_angle || DEFAULT_PARAMETERS.view_angle,
      pose: source.pose || DEFAULT_PARAMETERS.pose,
      expression: source.expression || DEFAULT_PARAMETERS.expression,
      background: source.background || DEFAULT_PARAMETERS.background,
      color_palette: source.color_palette || DEFAULT_PARAMETERS.color_palette,
    };
  });

  // Track if parameters have changed from the draft
  const [hasChanges, setHasChanges] = useState(false);
  
  // Generation status
  const jobStatus = generationJob?.status;
  const isGenerating = jobStatus === 'pending' || jobStatus === 'processing';
  const hasFailed = jobStatus === 'failed';
  const isComplete = draftImageUrl && !isGenerating;

  useEffect(() => {
    if (draftItem) {
      // Check if current parameters differ from draft
      const draftParamsStr = JSON.stringify({
        description: draftAttributes.description,
        ...draftParams,
      });
      const currentParamsStr = JSON.stringify(parameters);
      setHasChanges(draftParamsStr !== currentParamsStr);
    }
  }, [parameters, draftItem, draftAttributes, draftParams]);

  const handleParameterChange = (paramName, value) => {
    // Don't allow changes to locked parameters
    if (lockedParams[paramName] !== undefined) return;
    
    setParameters(prev => ({
      ...prev,
      [paramName]: value,
    }));
  };

  const handleDescriptionChange = (e) => {
    setParameters(prev => ({
      ...prev,
      description: e.target.value,
    }));
  };

  const handleCreateOrRegenerate = () => {
    if (draftItem) {
      // Regenerate existing draft
      onRegenerate?.(draftItem.id, parameters);
    } else {
      // Create new draft variation
      onCreateVariation?.(parentItem.id, parameters);
    }
  };

  const handlePublish = () => {
    if (draftItem) {
      onPublish?.(draftItem.id);
    }
  };

  const handleDiscard = () => {
    if (draftItem) {
      onDiscard?.(draftItem.id);
    } else {
      onClose?.();
    }
  };

  const isLocked = (paramName) => lockedParams[paramName] !== undefined;
  
  const getEffectiveValue = (paramName) => {
    if (isLocked(paramName)) return lockedParams[paramName];
    return parameters[paramName];
  };

  const renderParameterSlider = (paramName) => {
    const options = PARAMETER_OPTIONS[paramName];
    const label = PARAMETER_LABELS[paramName];
    const locked = isLocked(paramName);
    const currentValue = getEffectiveValue(paramName);
    const currentIndex = options.findIndex(opt => opt.value === currentValue);

    return (
      <div key={paramName} className={`parameter-slider-group ${locked ? 'locked' : ''}`}>
        <div className="parameter-slider-header">
          <label className="parameter-slider-label">
            {label}
            {locked && <span className="lock-icon" title="Locked by decision">🔒</span>}
          </label>
          <span className="parameter-current-value">
            {options.find(o => o.value === currentValue)?.label || currentValue}
          </span>
        </div>
        
        <div className="parameter-slider-container">
          <input
            type="range"
            min="0"
            max={options.length - 1}
            value={currentIndex >= 0 ? currentIndex : 0}
            onChange={(e) => {
              const newIndex = parseInt(e.target.value, 10);
              handleParameterChange(paramName, options[newIndex].value);
            }}
            disabled={locked || isLoading || isGenerating}
            className="parameter-slider"
          />
          <div className="slider-labels">
            {options.map((opt, idx) => (
              <span 
                key={opt.value} 
                className={`slider-label ${currentIndex === idx ? 'active' : ''}`}
                onClick={() => !locked && !isLoading && !isGenerating && handleParameterChange(paramName, opt.value)}
              >
                {opt.label}
              </span>
            ))}
          </div>
        </div>
        
        {options[currentIndex]?.description && (
          <p className="parameter-description">{options[currentIndex].description}</p>
        )}
      </div>
    );
  };

  return (
    <div className="variation-editor-overlay" onClick={onClose}>
      <div className="variation-editor" onClick={e => e.stopPropagation()}>
        <div className="variation-editor-header">
          <h2>{draftItem ? 'Edit Variation' : 'Create Variation'}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="variation-editor-content">
          {/* Preview Panel */}
          <div className="preview-panel">
            <h3>Preview</h3>
            <div className="preview-image-container">
              {isGenerating ? (
                <div className="preview-generating">
                  <div className="generating-spinner"></div>
                  <span>Generating...</span>
                </div>
              ) : hasFailed ? (
                <div className="preview-error">
                  <span className="error-icon">❌</span>
                  <span>Generation failed</span>
                  <span className="error-message">{generationJob?.error_message}</span>
                </div>
              ) : draftImageUrl ? (
                <img src={draftImageUrl} alt="Preview" className="preview-image" />
              ) : (
                <div className="preview-placeholder">
                  <span className="placeholder-icon">🎨</span>
                  <span>Adjust parameters and click Generate to preview</span>
                </div>
              )}
            </div>
            
            {/* Draft status indicator */}
            {draftItem && (
              <div className="draft-status">
                <span className="draft-badge">Draft</span>
                <span className="draft-info">Only you can see this until published</span>
              </div>
            )}
          </div>

          {/* Controls Panel */}
          <div className="controls-panel">
            <h3>Parameters</h3>
            
            {/* Description input */}
            <div className="description-input-group">
              <label>Description</label>
              <textarea
                value={parameters.description}
                onChange={handleDescriptionChange}
                placeholder="Describe your character..."
                disabled={isLoading || isGenerating}
                rows={3}
              />
            </div>

            {/* Parameter sliders */}
            <div className="parameter-sliders">
              {renderParameterSlider('art_style')}
              {renderParameterSlider('view_angle')}
              {renderParameterSlider('pose')}
              {renderParameterSlider('expression')}
              {renderParameterSlider('color_palette')}
              {renderParameterSlider('background')}
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="variation-editor-actions">
          <button
            className="action-btn discard"
            onClick={handleDiscard}
            disabled={isLoading || isGenerating}
          >
            {draftItem ? 'Discard Draft' : 'Cancel'}
          </button>
          
          <button
            className="action-btn generate"
            onClick={handleCreateOrRegenerate}
            disabled={isLoading || isGenerating || (!draftItem && !parentItem)}
          >
            {isGenerating ? (
              <>
                <span className="btn-spinner"></span>
                Generating...
              </>
            ) : draftItem ? (
              hasChanges ? 'Regenerate' : 'Generate Again'
            ) : (
              'Generate Preview'
            )}
          </button>
          
          {draftItem && isComplete && (
            <button
              className="action-btn publish"
              onClick={handlePublish}
              disabled={isLoading || isGenerating}
            >
              ✓ Publish to Group
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default VariationEditor;
