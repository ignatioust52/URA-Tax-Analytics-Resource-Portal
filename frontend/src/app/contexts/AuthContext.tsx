"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';

type User = {
  email: string;
  role: string;
  department: string;
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (user: User) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if session exists on load
    fetch('http://localhost:8000/api/auth/me', {credentials: 'include'})
      .then(res => {
        if (!res.ok) throw new Error('Not authenticated');
        return res.json();
      })
      .then(data => {
        setUser({
          email: data.email,
          role: data.role,
          department: data.department
        });
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const login = (userData: User) => setUser(userData);
  
  const logout = () => {
    fetch('http://localhost:8000/api/auth/logout', { method: 'POST', credentials: 'include' })
      .finally(() => {
        setUser(null);
        window.location.href = '/login';
      });
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
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
