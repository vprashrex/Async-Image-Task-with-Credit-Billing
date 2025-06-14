'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import Cookies from 'js-cookie';
import { User, SessionInfo, SecuritySummary } from '@/types/api';
import { authApi } from '@/lib/api/auth';
import { creditsApi } from '@/lib/api/credits';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  signup: (email: string, username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshUser: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  getSessions: () => Promise<SessionInfo[]>;
  terminateSession: (sessionId: string) => Promise<void>;
  getSecuritySummary: () => Promise<SecuritySummary>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);  const refreshUser = useCallback(async () => {
    try {
      // Since access_token is httpOnly, we need to validate by making an API call
      const response = await authApi.validateToken();
      setUser(response.user);
    } catch (error: any) {
      // Only log error if it's not a simple 401 (no token case)
      if (error?.response?.status !== 401) {
        console.error('Failed to refresh user:', error);
      }
      // User is not authenticated or token is invalid
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      // Try to refresh using httpOnly cookies
      await authApi.refreshToken({ refresh_token: undefined }); // Server will use httpOnly cookie
      
      // If successful, refresh user data
      await refreshUser();

      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // User needs to login again
      setUser(null);
      return false;
    }
  }, [refreshUser]);
  const login = useCallback(async (email: string, password: string, rememberMe: boolean = false) => {
    try {
      const response = await authApi.login({ username: email, password, remember_me: rememberMe });
      
      // The backend now sets HTTP-only cookies automatically
      // No need to manually set cookies here
      // Access token, refresh token, and session info are all handled by the server

      await refreshUser();
    } catch (error) {
      throw error;
    }
  }, [refreshUser]);

  const signup = useCallback(async (email: string, username: string, password: string) => {
    try {
      const user = await authApi.signup({ email, username, password });
      // Auto login after signup
      await login(email, password);
    } catch (error) {
      throw error;
    }
  }, [login]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout API call failed:', error);
    } finally {      // Clear all cookies regardless of API success
      Cookies.remove('access_token'); // Updated cookie name
      Cookies.remove('refresh_token');
      Cookies.remove('session_info'); // Updated cookie name
      setUser(null);
    }
  }, []);

  const logoutAll = useCallback(async () => {
    try {
      await authApi.logoutAll();
    } catch (error) {
      console.error('Logout all API call failed:', error);
    } finally {
      // Clear all cookies regardless of API success
      Cookies.remove('access_token'); // Updated cookie name
      Cookies.remove('refresh_token');
      Cookies.remove('session_info'); // Updated cookie name
      setUser(null);
    }
  }, []);

  const getSessions = useCallback(async (): Promise<SessionInfo[]> => {
    try {
      const response = await authApi.getSessions();
      return response.sessions;
    } catch (error) {
      console.error('Get sessions failed:', error);
      throw error;
    }
  }, []);

  const terminateSession = useCallback(async (sessionId: string) => {
    try {
      await authApi.terminateSession(sessionId);
    } catch (error) {
      console.error('Terminate session failed:', error);
      throw error;
    }
  }, []);

  const getSecuritySummary = useCallback(async (): Promise<SecuritySummary> => {
    try {
      return await authApi.getSecuritySummary();
    } catch (error) {
      console.error('Get security summary failed:', error);
      throw error;
    }
  }, []);  // Auto-refresh token when user is logged in
  useEffect(() => {
    if (user) {
      const interval = setInterval(async () => {
        // Try to refresh token periodically while user is active
        await refreshToken();
      }, 10 * 60 * 1000); // Check every 10 minutes

      return () => clearInterval(interval);
    }
  }, [user, refreshToken]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        signup,
        logout,
        logoutAll,
        refreshUser,
        refreshToken,
        getSessions,
        terminateSession,
        getSecuritySummary,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
