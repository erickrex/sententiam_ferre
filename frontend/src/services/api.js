import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Handle 401 Unauthorized - token expired or invalid
      if (error.response.status === 401) {
        localStorage.removeItem('authToken');
        window.location.href = '/login';
      }
      
      // Extract error message from various DRF error formats
      let errorMessage = 'An error occurred';
      const data = error.response.data;
      
      if (data) {
        // Check for common DRF error formats
        if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (data.detail) {
          errorMessage = data.detail;
        } else if (data.non_field_errors) {
          errorMessage = Array.isArray(data.non_field_errors) 
            ? data.non_field_errors[0] 
            : data.non_field_errors;
        } else if (data.group_name) {
          // Field-specific errors
          errorMessage = Array.isArray(data.group_name) 
            ? data.group_name[0] 
            : data.group_name;
        } else if (data.username) {
          errorMessage = Array.isArray(data.username) 
            ? data.username[0] 
            : data.username;
        } else {
          // Try to extract first field error
          const firstKey = Object.keys(data)[0];
          if (firstKey && data[firstKey]) {
            const fieldError = data[firstKey];
            errorMessage = Array.isArray(fieldError) ? fieldError[0] : fieldError;
          }
        }
      }
      
      return Promise.reject(new Error(errorMessage));
    }
    
    // Network error
    return Promise.reject(new Error('Network error. Please check your connection.'));
  }
);

// Authentication API
export const authAPI = {
  signup: (userData) => api.post('/auth/signup/', userData),
  login: (credentials) => api.post('/auth/login/', credentials),
  logout: () => api.post('/auth/logout/'),
  getCurrentUser: () => api.get('/auth/me/'),
};

// Groups API
export const groupsAPI = {
  list: () => api.get('/groups/'),
  create: (groupData) => api.post('/groups/', groupData),
  get: (groupId) => api.get(`/groups/${groupId}/`),
  listMembers: (groupId) => api.get(`/groups/${groupId}/members/`),
  inviteMember: (groupId, userData) => api.post(`/groups/${groupId}/members/`, userData),
  updateMembership: (groupId, userId, data) => api.patch(`/groups/${groupId}/members/${userId}/`, data),
  removeMember: (groupId, userId) => api.delete(`/groups/${groupId}/members/${userId}/`),
  
  // Join request methods
  createJoinRequest: (groupName) => api.post('/groups/join-request/', { group_name: groupName }),
  listMyRequests: () => api.get('/groups/my-requests/'),
  manageMyRequest: (requestId, action) => api.patch(`/groups/my-requests/${requestId}/`, { action }),
  
  // Invitation methods
  listMyInvitations: () => api.get('/groups/my-invitations/'),
  manageMyInvitation: (invitationId, action) => api.patch(`/groups/my-invitations/${invitationId}/`, { action }),
  
  // Admin management methods
  listGroupJoinRequests: (groupId) => api.get(`/groups/${groupId}/join-requests/`),
  manageJoinRequest: (groupId, requestId, action) => api.patch(`/groups/${groupId}/join-requests/${requestId}/`, { action }),
  listRejectedInvitations: (groupId) => api.get(`/groups/${groupId}/rejected-invitations/`),
  manageRejectedInvitation: (groupId, invitationId, action) => api.patch(`/groups/${groupId}/rejected-invitations/${invitationId}/`, { action }),
  listRejectedRequests: (groupId) => api.get(`/groups/${groupId}/rejected-requests/`),
  manageRejectedRequest: (groupId, requestId, action) => api.patch(`/groups/${groupId}/rejected-requests/${requestId}/`, { action }),
};

// Decisions API
export const decisionsAPI = {
  create: (decisionData) => api.post('/decisions/', decisionData),
  get: (decisionId) => api.get(`/decisions/${decisionId}/`),
  update: (decisionId, data) => api.patch(`/decisions/${decisionId}/`, data),
  listByGroup: (groupId) => api.get(`/groups/${groupId}/decisions/`),
  shareWithGroup: (decisionId, groupId) => api.post(`/decisions/${decisionId}/share-group/`, { group_id: groupId }),
  listFavourites: (decisionId) => api.get(`/decisions/${decisionId}/favourites/`),
};

// Items API
export const itemsAPI = {
  list: (decisionId, params = {}) => api.get('/items/', { params: { decision_id: decisionId, ...params } }),
  create: (decisionId, itemData) => api.post('/items/', { ...itemData, decision: decisionId }),
  update: (itemId, data) => api.patch(`/items/${itemId}/`, data),
  delete: (itemId) => api.delete(`/items/${itemId}/`),
  tagItem: (itemId, termId) => api.post(`/items/${itemId}/terms/${termId}/`),
  untagItem: (itemId, termId) => api.delete(`/items/${itemId}/terms/${termId}/`),
};

// Voting API
export const votingAPI = {
  castVote: (itemId, voteData) => api.post(`/votes/items/${itemId}/votes/`, voteData),
  getMyVote: (itemId) => api.get(`/votes/items/${itemId}/votes/me/`),
  getVoteSummary: (itemId) => api.get(`/votes/items/${itemId}/votes/summary/`),
  deleteVote: (itemId) => api.delete(`/votes/items/${itemId}/votes/`),
};

// Chat API
export const chatAPI = {
  getConversation: (decisionId) => api.get(`/decisions/${decisionId}/conversation/`),
  listMessages: (decisionId, params) => api.get(`/decisions/${decisionId}/messages/`, { params }),
  sendMessage: (decisionId, messageData) => api.post(`/decisions/${decisionId}/messages/`, messageData),
  markAsRead: (messageId) => api.patch(`/messages/${messageId}/`, { is_read: true }),
};

// Taxonomies API
export const taxonomiesAPI = {
  list: () => api.get('/taxonomies/'),
  create: (taxonomyData) => api.post('/taxonomies/', taxonomyData),
  listTerms: (taxonomyId) => api.get(`/taxonomies/${taxonomyId}/terms/`),
  createTerm: (taxonomyId, termData) => api.post(`/taxonomies/${taxonomyId}/terms/`, termData),
};

// Questionnaires API
export const questionnairesAPI = {
  listQuestions: (params) => api.get('/questions/', { params }),
  submitAnswer: (answerData) => api.post('/answers/', answerData),
};

export default api;
