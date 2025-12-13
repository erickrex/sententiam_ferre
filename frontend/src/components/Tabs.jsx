import React, { useState } from 'react';
import PropTypes from 'prop-types';
import './Tabs.css';

function Tabs({ children, defaultTab }) {
  const tabs = React.Children.toArray(children);
  const [activeTab, setActiveTab] = useState(defaultTab || 0);

  return (
    <div className="tabs-container">
      <div className="tabs-header">
        {tabs.map((tab, index) => (
          <button
            key={index}
            className={`tab-button ${activeTab === index ? 'active' : ''} ${tab.props.badge ? 'has-badge' : ''}`}
            onClick={() => setActiveTab(index)}
            aria-selected={activeTab === index}
            role="tab"
          >
            {tab.props.label}
            {tab.props.badge > 0 && (
              <span className="tab-badge">{tab.props.badge > 9 ? '9+' : tab.props.badge}</span>
            )}
          </button>
        ))}
      </div>
      <div className="tabs-content" role="tabpanel">
        {tabs[activeTab]}
      </div>
    </div>
  );
}

Tabs.propTypes = {
  children: PropTypes.node.isRequired,
  defaultTab: PropTypes.number,
};

function Tab({ children }) {
  return <div className="tab-content">{children}</div>;
}

Tab.propTypes = {
  label: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  badge: PropTypes.number,
};

export { Tabs, Tab };
