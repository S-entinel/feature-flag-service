import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API_KEY = process.env.REACT_APP_API_KEY;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    ...(API_KEY && { 'X-API-Key': API_KEY })
  },
});

// Flag operations
export const flagsApi = {
  // Get all flags
  getAll: async () => {
    const response = await api.get('/flags/');
    return response.data;
  },

  // Get single flag
  get: async (key) => {
    const response = await api.get(`/flags/${key}`);
    return response.data;
  },

  // Create flag
  create: async (flagData) => {
    const response = await api.post('/flags/', flagData);
    return response.data;
  },

  // Update flag
  update: async (key, flagData) => {
    const response = await api.put(`/flags/${key}`, flagData);
    return response.data;
  },

  // Delete flag
  delete: async (key) => {
    await api.delete(`/flags/${key}`);
  },

  // Evaluate flag
  evaluate: async (key, userId = null) => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get(`/flags/${key}/evaluate`, { params });
    return response.data;
  },

  // Get audit logs
  getAuditLogs: async (key, limit = 100) => {
    const response = await api.get(`/flags/${key}/audit`, {
      params: { limit },
    });
    return response.data;
  },
};

// Cache operations
export const cacheApi = {
  // Get cache stats
  getStats: async () => {
    const response = await api.get('/flags/_cache/stats');
    return response.data;
  },

  // Clear cache
  clear: async () => {
    await api.post('/flags/_cache/clear');
  },
};

export default api;