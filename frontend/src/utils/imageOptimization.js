/**
 * Image optimization utilities for mobile performance
 * Provides helpers for responsive images and lazy loading
 */

/**
 * Generate srcset for responsive images
 * @param {string} baseUrl - Base URL of the image
 * @param {Array<number>} widths - Array of widths to generate
 * @returns {string} - srcset string
 */
export const generateSrcSet = (baseUrl, widths = [320, 640, 960, 1280, 1920]) => {
  return widths
    .map(width => `${baseUrl}?w=${width} ${width}w`)
    .join(', ');
};

/**
 * Generate sizes attribute for responsive images
 * @param {Object} breakpoints - Object with breakpoint: size pairs
 * @returns {string} - sizes string
 */
export const generateSizes = (breakpoints = {
  '(max-width: 640px)': '100vw',
  '(max-width: 1024px)': '50vw',
  default: '33vw'
}) => {
  const entries = Object.entries(breakpoints);
  const mediaQueries = entries
    .filter(([key]) => key !== 'default')
    .map(([query, size]) => `${query} ${size}`);
  
  const defaultSize = breakpoints.default || '100vw';
  return [...mediaQueries, defaultSize].join(', ');
};

/**
 * Compress image quality based on connection speed
 * @param {string} url - Image URL
 * @returns {string} - Optimized URL with quality parameter
 */
export const optimizeImageQuality = (url) => {
  if (!navigator.connection) {
    return url;
  }

  const connection = navigator.connection;
  const effectiveType = connection.effectiveType;

  // Adjust quality based on connection
  const qualityMap = {
    'slow-2g': 30,
    '2g': 40,
    '3g': 60,
    '4g': 80
  };

  const quality = qualityMap[effectiveType] || 80;
  const separator = url.includes('?') ? '&' : '?';
  
  return `${url}${separator}q=${quality}`;
};

/**
 * Check if image should be loaded based on data saver mode
 * @returns {boolean}
 */
export const shouldLoadImage = () => {
  if (!navigator.connection) {
    return true;
  }

  return !navigator.connection.saveData;
};

/**
 * Get optimal image format based on browser support
 * @returns {string} - Preferred image format
 */
export const getOptimalImageFormat = () => {
  // Check for WebP support
  const canvas = document.createElement('canvas');
  if (canvas.getContext && canvas.getContext('2d')) {
    const webpSupport = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    if (webpSupport) {
      return 'webp';
    }
  }

  // Check for AVIF support
  const avifSupport = document.createElement('img');
  avifSupport.src = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgANogQEAwgMg8f8D///8WfhwB8+ErK42A=';
  
  return new Promise((resolve) => {
    avifSupport.onload = () => resolve('avif');
    avifSupport.onerror = () => resolve('jpg');
  });
};

/**
 * Preload critical images
 * @param {Array<string>} urls - Array of image URLs to preload
 */
export const preloadImages = (urls) => {
  urls.forEach(url => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = url;
    document.head.appendChild(link);
  });
};

/**
 * Create a placeholder for lazy-loaded images
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @param {string} color - Placeholder color
 * @returns {string} - Data URL for placeholder
 */
export const createPlaceholder = (width = 16, height = 9, color = '#e0e0e0') => {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, width, height);
  
  return canvas.toDataURL();
};

/**
 * Calculate aspect ratio padding for responsive images
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @returns {string} - Padding percentage
 */
export const getAspectRatioPadding = (width, height) => {
  return `${(height / width) * 100}%`;
};

/**
 * Decode image before displaying to prevent jank
 * @param {HTMLImageElement} img - Image element
 * @returns {Promise}
 */
export const decodeImage = async (img) => {
  if ('decode' in img) {
    try {
      await img.decode();
    } catch (error) {
      console.warn('Image decode failed:', error);
    }
  }
};
