"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

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
  const [userId, setUserId] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Simple local auth - auto-login with demo user for hackathon
  useEffect(() => {
    // Check localStorage for existing user
    const storedUserId = localStorage.getItem('otium_user_id');
    
    if (storedUserId) {
      setUserId(storedUserId);
      setIsAuthenticated(true);
    } else {
      // Auto-login with demo user for hackathon
      const demoUserId = 'demo_user';
      setUserId(demoUserId);
      setIsAuthenticated(true);
      localStorage.setItem('otium_user_id', demoUserId);
    }
    
      setIsLoading(false);
  }, []);

  const login = (id: string) => {
    setUserId(id);
    setIsAuthenticated(true);
    localStorage.setItem('otium_user_id', id);
  };

  const logout = () => {
    setUserId('');
    setIsAuthenticated(false);
    localStorage.removeItem('otium_user_id');
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