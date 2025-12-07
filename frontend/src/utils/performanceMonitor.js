/**
 * Performance monitoring utilities for mobile optimization
 * Tracks key performance metrics and provides insights
 */

export const measurePageLoad = () => {
  if (!window.performance || !window.performance.timing) {
    console.warn('Performance API not supported');
    return null;
  }

  const timing = window.performance.timing;
  const metrics = {
    // DNS lookup time
    dns: timing.domainLookupEnd - timing.domainLookupStart,
    
    // TCP connection time
    tcp: timing.connectEnd - timing.connectStart,
    
    // Time to first byte
    ttfb: timing.responseStart - timing.requestStart,
    
    // Content download time
    download: timing.responseEnd - timing.responseStart,
    
    // DOM processing time
    domProcessing: timing.domComplete - timing.domLoading,
    
    // Total page load time
    totalLoad: timing.loadEventEnd - timing.navigationStart,
    
    // DOM content loaded
    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart
  };

  console.log('Performance Metrics:', metrics);
  return metrics;
};

export const measureResourceTiming = () => {
  if (!window.performance || !window.performance.getEntriesByType) {
    console.warn('Resource Timing API not supported');
    return [];
  }

  const resources = window.performance.getEntriesByType('resource');
  const resourceMetrics = resources.map(resource => ({
    name: resource.name,
    type: resource.initiatorType,
    duration: resource.duration,
    size: resource.transferSize || 0,
    cached: resource.transferSize === 0
  }));

  // Group by type
  const byType = resourceMetrics.reduce((acc, resource) => {
    if (!acc[resource.type]) {
      acc[resource.type] = [];
    }
    acc[resource.type].push(resource);
    return acc;
  }, {});

  console.log('Resource Timing by Type:', byType);
  return resourceMetrics;
};

export const measureFirstContentfulPaint = () => {
  if (!window.performance || !window.performance.getEntriesByType) {
    console.warn('Paint Timing API not supported');
    return null;
  }

  const paintEntries = window.performance.getEntriesByType('paint');
  const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
  
  if (fcp) {
    console.log('First Contentful Paint:', fcp.startTime, 'ms');
    return fcp.startTime;
  }
  
  return null;
};

export const measureLargestContentfulPaint = () => {
  if (!window.PerformanceObserver) {
    console.warn('PerformanceObserver not supported');
    return;
  }

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      console.log('Largest Contentful Paint:', lastEntry.renderTime || lastEntry.loadTime, 'ms');
    });

    observer.observe({ entryTypes: ['largest-contentful-paint'] });
  } catch (error) {
    console.warn('LCP measurement failed:', error);
  }
};

export const measureCumulativeLayoutShift = () => {
  if (!window.PerformanceObserver) {
    console.warn('PerformanceObserver not supported');
    return;
  }

  let clsScore = 0;

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (!entry.hadRecentInput) {
          clsScore += entry.value;
        }
      }
      console.log('Cumulative Layout Shift:', clsScore);
    });

    observer.observe({ entryTypes: ['layout-shift'] });
  } catch (error) {
    console.warn('CLS measurement failed:', error);
  }
};

export const measureFirstInputDelay = () => {
  if (!window.PerformanceObserver) {
    console.warn('PerformanceObserver not supported');
    return;
  }

  try {
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const firstInput = entries[0];
      const fid = firstInput.processingStart - firstInput.startTime;
      console.log('First Input Delay:', fid, 'ms');
    });

    observer.observe({ entryTypes: ['first-input'] });
  } catch (error) {
    console.warn('FID measurement failed:', error);
  }
};

export const getConnectionInfo = () => {
  if (!navigator.connection && !navigator.mozConnection && !navigator.webkitConnection) {
    console.warn('Network Information API not supported');
    return null;
  }

  const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  
  const info = {
    effectiveType: connection.effectiveType, // '4g', '3g', '2g', 'slow-2g'
    downlink: connection.downlink, // Mbps
    rtt: connection.rtt, // Round trip time in ms
    saveData: connection.saveData // Data saver mode
  };

  console.log('Connection Info:', info);
  return info;
};

export const initPerformanceMonitoring = () => {
  // Wait for page load to complete
  window.addEventListener('load', () => {
    setTimeout(() => {
      measurePageLoad();
      measureResourceTiming();
      measureFirstContentfulPaint();
      getConnectionInfo();
    }, 0);
  });

  // Measure Web Vitals
  measureLargestContentfulPaint();
  measureCumulativeLayoutShift();
  measureFirstInputDelay();
};

// Export a function to log all metrics
export const logAllMetrics = () => {
  console.group('Performance Metrics');
  measurePageLoad();
  measureResourceTiming();
  measureFirstContentfulPaint();
  getConnectionInfo();
  console.groupEnd();
};
