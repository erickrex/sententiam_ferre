import React, { useState, useEffect } from 'react';
import './RuleSelector.css';

function RuleSelector({ rules, onChange, disabled }) {
  const [ruleType, setRuleType] = useState(rules?.type || 'unanimous');
  const [thresholdValue, setThresholdValue] = useState(
    rules?.type === 'threshold' ? rules.value : 0.5
  );

  useEffect(() => {
    if (rules) {
      setRuleType(rules.type);
      if (rules.type === 'threshold') {
        setThresholdValue(rules.value);
      }
    }
  }, [rules]);

  const handleRuleTypeChange = (e) => {
    const newType = e.target.value;
    setRuleType(newType);
    
    if (newType === 'unanimous') {
      onChange({ type: 'unanimous' });
    } else if (newType === 'threshold') {
      onChange({ type: 'threshold', value: thresholdValue });
    }
  };

  const handleThresholdChange = (e) => {
    const value = parseFloat(e.target.value);
    setThresholdValue(value);
    onChange({ type: 'threshold', value });
  };

  const handlePercentageChange = (e) => {
    const percentage = parseInt(e.target.value, 10);
    const value = percentage / 100;
    setThresholdValue(value);
    onChange({ type: 'threshold', value });
  };

  const getThresholdPercentage = () => {
    return Math.round(thresholdValue * 100);
  };

  return (
    <div className="rule-selector">
      <div className="rule-type-options">
        <label className="rule-option">
          <input
            type="radio"
            name="ruleType"
            value="unanimous"
            checked={ruleType === 'unanimous'}
            onChange={handleRuleTypeChange}
            disabled={disabled}
          />
          <div className="rule-option-content">
            <span className="rule-option-title">Unanimous</span>
            <span className="rule-option-description">
              All members must approve for items to become favourites
            </span>
          </div>
        </label>

        <label className="rule-option">
          <input
            type="radio"
            name="ruleType"
            value="threshold"
            checked={ruleType === 'threshold'}
            onChange={handleRuleTypeChange}
            disabled={disabled}
          />
          <div className="rule-option-content">
            <span className="rule-option-title">Threshold</span>
            <span className="rule-option-description">
              A percentage of members must approve
            </span>
          </div>
        </label>
      </div>

      {ruleType === 'threshold' && (
        <div className="threshold-config">
          <div className="threshold-input-group">
            <label htmlFor="threshold-percentage" className="threshold-label">
              Approval Threshold: <strong>{getThresholdPercentage()}%</strong>
            </label>
            <input
              type="range"
              id="threshold-percentage"
              min="1"
              max="100"
              value={getThresholdPercentage()}
              onChange={handlePercentageChange}
              className="threshold-slider"
              disabled={disabled}
            />
            <div className="threshold-markers">
              <span>1%</span>
              <span>25%</span>
              <span>50%</span>
              <span>75%</span>
              <span>100%</span>
            </div>
          </div>
          
          <div className="threshold-example">
            <p className="example-text">
              Example: With {getThresholdPercentage()}% threshold and 10 members, 
              at least {Math.ceil(10 * thresholdValue)} members must approve.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default RuleSelector;
