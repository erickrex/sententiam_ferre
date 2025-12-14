import React from 'react';
import { PARAMETER_OPTIONS, PARAMETER_LABELS } from './parameterConstants';
import './ParameterControls.css';

function ParameterControls({ 
  parameters, 
  lockedParams = {}, 
  onChange, 
  disabled = false,
  showDescriptions = true 
}) {
  const handleParameterChange = (paramName, value) => {
    if (lockedParams[paramName] !== undefined) {
      // Parameter is locked, don't allow changes
      return;
    }
    onChange({
      ...parameters,
      [paramName]: value,
    });
  };

  const isLocked = (paramName) => {
    return lockedParams[paramName] !== undefined;
  };

  const getEffectiveValue = (paramName) => {
    // If locked, use locked value; otherwise use current parameter value
    if (isLocked(paramName)) {
      return lockedParams[paramName];
    }
    return parameters[paramName] || '';
  };

  const renderParameterGroup = (paramName) => {
    const options = PARAMETER_OPTIONS[paramName];
    const label = PARAMETER_LABELS[paramName];
    const locked = isLocked(paramName);
    const currentValue = getEffectiveValue(paramName);

    return (
      <div key={paramName} className={`parameter-group ${locked ? 'locked' : ''}`}>
        <div className="parameter-header">
          <label className="parameter-label">
            {label}
            {locked && <span className="lock-indicator" title="This parameter is locked for this decision">🔒</span>}
          </label>
        </div>
        <div className="parameter-options">
          {options.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`parameter-option ${currentValue === option.value ? 'selected' : ''} ${locked ? 'locked' : ''}`}
              onClick={() => handleParameterChange(paramName, option.value)}
              disabled={disabled || locked}
              title={locked ? `Locked to "${option.label}"` : option.description}
            >
              <span className="option-label">{option.label}</span>
              {showDescriptions && (
                <span className="option-description">{option.description}</span>
              )}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="parameter-controls">
      {renderParameterGroup('art_style')}
      {renderParameterGroup('view_angle')}
      {renderParameterGroup('pose')}
      {renderParameterGroup('expression')}
      {renderParameterGroup('background')}
      {renderParameterGroup('color_palette')}
    </div>
  );
}

export default ParameterControls;
