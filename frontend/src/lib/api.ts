import axios from 'axios';
import Cookies from 'js-cookie';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable cookies for refresh token
});

// Store tokens temporarily when cookies don't work (HTTPS frontend + HTTP backend)
let tempTokens: { access_token?: string; refresh_token?: string } = {};

// Flag to prevent multiple refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
}> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  
  failedQueue = [];
};

// Helper function to get access token from various sources
const getAccessToken = () => {
  // Try temporary storage first (for HTTPS frontend + HTTP backend)
  if (tempTokens.access_token) {
    return tempTokens.access_token;
  }
  
  // Try to get from non-httpOnly cookie (fallback)
  return Cookies.get('access_token');
};

// Request interceptor - add Authorization header if available
api.interceptors.request.use(
  (config) => {
    const accessToken = getAccessToken();
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token expiration and refresh
api.interceptors.response.use(
  (response) => {
    // Check if the response contains tokens in headers (for HTTPS frontend + HTTP backend)
    const accessToken = response.headers['x-access-token'];
    const refreshToken = response.headers['x-refresh-token'];
    
    if (accessToken) {
      tempTokens.access_token = accessToken;
      // Also try to set as non-httpOnly cookie for fallback
      Cookies.set('access_token', accessToken, { 
        expires: 1/24, // 1 hour
        secure: window.location.protocol === 'https:',
        sameSite: 'strict'
      });
    }
    
    if (refreshToken) {
      tempTokens.refresh_token = refreshToken;
      // Also try to set as non-httpOnly cookie for fallback
      Cookies.set('refresh_token', refreshToken, { 
        expires: 7, // 7 days
        secure: window.location.protocol === 'https:',
        sameSite: 'strict'
      });
    }
    
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Don't try to refresh tokens for auth endpoints to prevent infinite loops
    if (originalRequest.url?.includes('/auth/')) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If we're already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => {
          return api(originalRequest);
        }).catch((err) => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Try to refresh the token
        const refreshToken = tempTokens.refresh_token || Cookies.get('refresh_token');
        
        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken
        }, {
          withCredentials: true
        });

        // Update tokens from response
        if (response.data.access_token) {
          tempTokens.access_token = response.data.access_token;
          tempTokens.refresh_token = response.data.refresh_token;
        }
        
        // Check for tokens in headers
        const newAccessToken = response.headers['x-access-token'];
        const newRefreshToken = response.headers['x-refresh-token'];
        
        if (newAccessToken) {
          tempTokens.access_token = newAccessToken;
          Cookies.set('access_token', newAccessToken, { 
            expires: 1/24,
            secure: window.location.protocol === 'https:',
            sameSite: 'strict'
          });
        }
        
        if (newRefreshToken) {
          tempTokens.refresh_token = newRefreshToken;
          Cookies.set('refresh_token', newRefreshToken, { 
            expires: 7,
            secure: window.location.protocol === 'https:',
            sameSite: 'strict'
          });
        }

        processQueue(null, 'refreshed');
        
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        
        // Clear tokens on refresh failure
        tempTokens = {};
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');
        
        // Redirect to login page on refresh failure
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
