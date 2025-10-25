"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from "@workos-inc/authkit-nextjs/components";

interface UserContextType {
  userId: string;
  setUserId: (id: string) => void;
  isAuthenticated: boolean;
  login: (id: string) => void;
  logout: () => void;
  isLoading: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

interface UserProviderProps {
  children: ReactNode;
}

export function UserProvider({ children }: UserProviderProps) {
  const { user, loading: authLoading } = useAuth();
  const [userId, setUserId] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Update user context when WorkOS auth state changes
  useEffect(() => {

    if (authLoading) {
      setIsLoading(true);
      return;
    }

    if (user) {
      // Try to get user ID from various possible properties
      let userIdentifier = '';
      if (user.id) {
        userIdentifier = user.id;
      } else if (user.email) {
        // Fallback to email if no ID
        userIdentifier = user.email;
      } else if (user.firstName && user.lastName) {
        // Fallback to name combination
        userIdentifier = `${user.firstName}_${user.lastName}`;
      } else {
        // Final fallback
        userIdentifier = 'unknown_user';
      }
      
      setUserId(userIdentifier);
      setIsAuthenticated(true);
      setIsLoading(false);
    } else {
      // No authenticated user
      setUserId('');
      setIsAuthenticated(false);
      setIsLoading(false);
    }
  }, [user, authLoading]);

  const login = (id: string) => {
    // This function is kept for compatibility but WorkOS handles authentication
    setUserId(id);
    setIsAuthenticated(true);
  };

  const logout = () => {
    // This function is kept for compatibility but WorkOS handles sign out
    setUserId('');
    setIsAuthenticated(false);
  };

  const value: UserContextType = {
    userId,
    setUserId,
    isAuthenticated,
    login,
    logout,
    isLoading,
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}