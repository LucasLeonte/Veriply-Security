"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { getAccessToken, clearAccessToken } from '@/lib/auth';

interface User {
  id: string;
  email: string;
  name: string;
  tenant_id: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (token: string, rememberMe: boolean) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Fetch user profile from API
  const fetchUserProfile = async (authToken: string): Promise<User | null> => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const response = await fetch(`${apiUrl}/api/v1/users/me`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          clearAccessToken();
          return null;
        }
        throw new Error('Failed to fetch user profile');
      }

      const userData = await response.json();
      return userData;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      return null;
    }
  };

  // Initialize auth state on mount
  useEffect(() => {
    const initAuth = async () => {
      const existingToken = getAccessToken();
      
      if (existingToken) {
        setToken(existingToken);
        const userData = await fetchUserProfile(existingToken);
        
        if (userData) {
          setUser(userData);
        } else {
          // Token invalid, clear it
          setToken(null);
          clearAccessToken();
        }
      }
      
      setLoading(false);
    };

    initAuth();
  }, []);

  // Login function - store token and fetch user
  const login = async (newToken: string, rememberMe: boolean) => {
    // Store token in appropriate storage
    if (rememberMe) {
      localStorage.setItem('access_token', newToken);
    } else {
      sessionStorage.setItem('access_token', newToken);
    }

    setToken(newToken);
    
    // Fetch user profile
    const userData = await fetchUserProfile(newToken);
    if (userData) {
      setUser(userData);
    }
  };

  // Logout function
  const logout = () => {
    clearAccessToken();
    setToken(null);
    setUser(null);
    router.push('/login');
  };

  // Refresh user profile
  const refreshUser = async () => {
    const currentToken = token || getAccessToken();
    if (currentToken) {
      const userData = await fetchUserProfile(currentToken);
      if (userData) {
        setUser(userData);
      } else {
        logout();
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        refreshUser,
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
