import { useState } from 'react';
import { WIZARD_STEPS, buildFiboJson, buildApiParams, STEP_ORDER } from '../machines/characterWizardMachine';
import './CharacterWizard.css';

function CharacterWizard({ 
  onComplete, 
  onCancel, 
  onGenerate,
  isVariation = false,
  parentItem = null,
  lockedParams = {},
}) {
  // Initialize choices from parent item if creating a variation
  const getInitialChoices = () => {
    if (parentItem?.attributes?.generation_params) {
      const params = parentItem.attributes.generation_params;
      return {
        artStyle: params.art_style || null,
        viewAngle: params.view_angle || null,
        pose: params.pose || null,
        expression: params.expression || null,
        colorPalette: params.color_palette || null,
        background: params.background || null,
      };
    }
    return {
      artStyle: null,
      viewAngle: null,
      pose: null,
      expression: null,
      colorPalette: null,
      background: null,
    };
  };

  const [currentStep, setCurrentStep] = useState('description');
  const [description, setDescription] = useState(parentItem?.attributes?.description || '');
  const [choices, setChoices] = useState(getInitialChoices());
  const [fiboJson, setFiboJson] = useState(null);
  const [error, setError] = useState(null);

  const handleNext = () => {
    const stepIndex = STEP_ORDER.indexOf(currentStep);
    if (currentStep === 'background') {
      // Build FIBO JSON before going to review
      const context = { description, choices };
      setFiboJson(buildFiboJson(context));
    }
    if (stepIndex < STEP_ORDER.length - 1) {
      setCurrentStep(STEP_ORDER[stepIndex + 1]);
    }
  };

  const handleBack = () => {
    const stepIndex = STEP_ORDER.indexOf(currentStep);
    if (stepIndex > 0) {
      setCurrentStep(STEP_ORDER[stepIndex - 1]);
    }
  };

  const currentStepIndex = STEP_ORDER.indexOf(currentStep);
  const totalSteps = 7; // description through background

  const handleGenerate = async () => {
    setCurrentStep('generating');
    setError(null);
    try {
      // Build API params from wizard choices
      const apiParams = buildApiParams({ description, choices });
      const context = { 
        description, 
        choices, 
        fiboJson, 
        apiParams,
        isVariation, 
        parentItem, 
        lockedParams 
      };
      const result = await onGenerate(context);
      setCurrentStep('complete');
      onComplete?.(result);
    } catch (err) {
      setError(err.message);
      setCurrentStep('review');
    }
  };

  const isLocked = (stepKey, optionId) => {
    const apiField = WIZARD_STEPS[stepKey]?.apiField;
    return lockedParams[apiField] === optionId;
  };

  const renderProgressBar = () => {
    if (currentStep === 'generating' || currentStep === 'complete') return null;
    
    const progress = Math.min((currentStepIndex / totalSteps) * 100, 100);
    
    return (
      <div className="wizard-progress">
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="progress-steps">
          {STEP_ORDER.slice(0, totalSteps).map((step, idx) => (
            <div 
              key={step} 
              className={`progress-dot ${idx <= currentStepIndex ? 'active' : ''} ${idx === currentStepIndex ? 'current' : ''}`}
            />
          ))}
        </div>
        <span className="progress-text">Step {Math.min(currentStepIndex + 1, totalSteps)} of {totalSteps}</span>
      </div>
    );
  };

  const renderFiboPreview = () => {
    const currentFibo = buildFiboJson({ description, choices });
    
    return (
      <div className="fibo-preview">
        <div className="fibo-header">
          <span className="fibo-badge">FIBO JSON</span>
          <span className="fibo-subtitle">Real-time parameter preview</span>
        </div>
        <pre className="fibo-json">
          {JSON.stringify(currentFibo, null, 2)}
        </pre>
      </div>
    );
  };

  const renderDescriptionStep = () => (
    <div className="wizard-step description-step">
      <h2>Describe your character</h2>
      <p className="step-subtitle">Give a brief description of who this character is</p>
      
      <textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="e.g., A brave knight with a glowing sword, a mischievous goblin thief, a wise old wizard..."
        className="description-input"
        rows={4}
      />
      
      <div className="character-count">
        {description.length} characters {description.length < 3 && '(minimum 3)'}
      </div>
      
      <div className="wizard-actions">
        <button className="btn-secondary" onClick={onCancel}>Cancel</button>
        <button 
          className="btn-primary"
          onClick={handleNext}
          disabled={description.trim().length < 3}
        >
          Next →
        </button>
      </div>
    </div>
  );

  const renderOptionStep = (stepKey) => {
    const stepConfig = WIZARD_STEPS[stepKey];
    if (!stepConfig) return null;
    
    const selectedValue = choices[stepKey];
    
    return (
      <div className="wizard-step option-step">
        <h2>{stepConfig.title}</h2>
        <p className="step-subtitle">{stepConfig.subtitle}</p>
        
        <div className="options-grid">
          {stepConfig.options.map((option) => {
            const locked = isLocked(stepKey, option.id);
            const selected = selectedValue === option.id;
            
            return (
              <button
                key={option.id}
                className={`option-card ${selected ? 'selected' : ''} ${locked ? 'locked' : ''}`}
                onClick={() => !locked && setChoices(prev => ({ ...prev, [stepKey]: option.id }))}
                disabled={locked && !selected}
              >
                <span className="option-icon">{option.icon}</span>
                <span className="option-label">{option.label}</span>
                <span className="option-description">{option.description}</span>
                {locked && <span className="lock-badge">🔒 Locked</span>}
                {selected && <span className="check-badge">✓</span>}
              </button>
            );
          })}
        </div>
        
        <div className="wizard-actions">
          <button className="btn-secondary" onClick={handleBack}>
            ← Back
          </button>
          <button 
            className="btn-primary"
            onClick={handleNext}
            disabled={!selectedValue}
          >
            Next →
          </button>
        </div>
      </div>
    );
  };

  const renderReviewStep = () => (
    <div className="wizard-step review-step">
      <h2>Review & Generate</h2>
      <p className="step-subtitle">Here's what FIBO will create</p>
      
      <div className="review-content">
        <div className="review-summary">
          <h3>Your Choices</h3>
          <div className="choices-list">
            <div className="choice-item">
              <span className="choice-label">Description:</span>
              <span className="choice-value">"{description}"</span>
            </div>
            {Object.entries(choices).map(([key, value]) => {
              if (!value) return null;
              const stepConfig = WIZARD_STEPS[key];
              const option = stepConfig?.options.find(o => o.id === value);
              if (!option) return null;
              return (
                <div key={key} className="choice-item">
                  <span className="choice-label">{stepConfig?.title.replace('?', '')}:</span>
                  <span className="choice-value">
                    {option?.icon} {option?.label}
                    {isLocked(key, value) && <span className="locked-indicator">🔒</span>}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        
        <div className="review-fibo">
          <h3>FIBO Parameters</h3>
          <div className="fibo-json-box">
            <pre>{JSON.stringify(fiboJson, null, 2)}</pre>
          </div>
          <p className="fibo-note">
            These structured parameters give you deterministic control over the generation.
          </p>
        </div>
      </div>
      
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}
      
      <div className="wizard-actions">
        <button className="btn-secondary" onClick={handleBack}>
          ← Back
        </button>
        <button className="btn-primary generate-btn" onClick={handleGenerate}>
          ✨ Generate Character
        </button>
      </div>
    </div>
  );

  const renderGeneratingStep = () => (
    <div className="wizard-step generating-step">
      <div className="generating-animation">
        <div className="spinner-large" />
        <h2>Creating your character...</h2>
        <p>FIBO is processing your parameters</p>
      </div>
      
      <div className="generating-fibo">
        <span className="fibo-badge">Sending to FIBO</span>
        <pre className="fibo-json-small">
          {JSON.stringify(fiboJson, null, 2)}
        </pre>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (currentStep) {
      case 'description':
        return renderDescriptionStep();
      case 'artStyle':
      case 'viewAngle':
      case 'pose':
      case 'expression':
      case 'colorPalette':
      case 'background':
        return renderOptionStep(currentStep);
      case 'review':
        return renderReviewStep();
      case 'generating':
        return renderGeneratingStep();
      default:
        return null;
    }
  };

  return (
    <div className="character-wizard-overlay" onClick={onCancel}>
      <div className="character-wizard" onClick={(e) => e.stopPropagation()}>
        <div className="wizard-header">
          <h1>{isVariation ? '🎨 Create Variation' : '✨ New Character'}</h1>
          <button className="close-btn" onClick={onCancel}>×</button>
        </div>
        
        {renderProgressBar()}
        
        <div className="wizard-body">
          <div className="wizard-main">
            {renderContent()}
          </div>
          
          {currentStep !== 'generating' && currentStep !== 'complete' && (
            <div className="wizard-sidebar">
              {renderFiboPreview()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CharacterWizard;
