import usePullToRefresh from '../hooks/usePullToRefresh';
import './PullToRefresh.css';

/**
 * PullToRefresh wrapper component for mobile lists
 * Provides visual feedback during pull-to-refresh gesture
 */
const PullToRefresh = ({ 
  onRefresh, 
  children, 
  enabled = true,
  threshold = 80 
}) => {
  const { 
    containerRef, 
    isPulling, 
    isRefreshing, 
    pullDistance,
    pullProgress 
  } = usePullToRefresh(onRefresh, { enabled, threshold });

  return (
    <div className="pull-to-refresh-wrapper">
      {(isPulling || isRefreshing) && (
        <div 
          className="pull-to-refresh-indicator"
          style={{ 
            transform: `translateY(${Math.min(pullDistance, threshold)}px)`,
            opacity: pullProgress / 100
          }}
        >
          <div className={`refresh-spinner ${isRefreshing ? 'spinning' : ''}`}>
            <svg 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="23 4 23 10 17 10"></polyline>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
            </svg>
          </div>
          <span className="refresh-text">
            {isRefreshing ? 'Refreshing...' : pullProgress >= 100 ? 'Release to refresh' : 'Pull to refresh'}
          </span>
        </div>
      )}
      <div ref={containerRef} className="pull-to-refresh-content">
        {children}
      </div>
    </div>
  );
};

export default PullToRefresh;
