/**
 * Extract error message from API error response
 * @param {Error} error - The error object from axios
 * @returns {string} - User-friendly error message
 */
export const getErrorMessage = (error) => {
  if (error.response) {
    // Server responded with error
    const data = error.response.data;
    
    if (typeof data === 'string') {
      return data;
    }
    
    if (data.message) {
      return data.message;
    }
    
    if (data.errors) {
      // Handle validation errors
      const errors = Object.entries(data.errors)
        .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
        .join('; ');
      return errors;
    }
    
    return 'An error occurred';
  }
  
  if (error.request) {
    // Request made but no response
    return 'No response from server. Please check your connection.';
  }
  
  // Something else happened
  return error.message || 'An unexpected error occurred';
};

/**
 * Handle API response and extract data
 * @param {Promise} apiCall - The API call promise
 * @returns {Promise} - Promise resolving to response data
 */
export const handleApiCall = async (apiCall) => {
  try {
    const response = await apiCall;
    return response.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

/**
 * Store authentication token
 * @param {string} token - The auth token
 */
export const setAuthToken = (token) => {
  localStorage.setItem('authToken', token);
};

/**
 * Remove authentication token
 */
export const clearAuthToken = () => {
  localStorage.removeItem('authToken');
};

/**
 * Get authentication token
 * @returns {string|null} - The auth token or null
 */
export const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

/**
 * Check if user is authenticated
 * @returns {boolean} - True if authenticated
 */
export const isAuthenticated = () => {
  return !!getAuthToken();
};
