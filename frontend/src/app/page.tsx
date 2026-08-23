"use client";
import { useState, useEffect } from 'react';
import { useAuth } from './contexts/AuthContext';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';

export default function Home() {
  const { user, loading } = useAuth();
  const [backendStatus, setBackendStatus] = useState('Checking...');

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/health`)
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus(data.status === 'ok' ? 'Running' : 'Error');
      })
      .catch(() => setBackendStatus('Offline'));
  }, []);

  const handleLogout = async () => {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    window.location.href = '/login';
  };

  if (loading) {
    return (
      <main className="main-container" style={{ minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Authenticating...</p>
      </main>
    );
  }

  return (
    <main className="main-container">
      <div style={{ maxWidth: '800px', margin: '0 auto', marginTop: '10vh' }}>
        
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
          <h1 className="page-title">URA GO PORTAL</h1>
          <p className="page-subtitle">DEVELOPING UGANDA TOGETHER</p>
        </div>
        
        <Card>
          {user ? (
            <div style={{ textAlign: 'center', padding: 'var(--space-4) 0' }}>
              <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-2)' }}>Welcome, {user.email}</h2>
              <Badge variant="info">
                Role: {user.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'User'}
              </Badge>
              
              <div style={{ 
                marginTop: 'var(--space-5)', 
                padding: 'var(--space-4)', 
                background: 'var(--surface-hover)', 
                borderRadius: 'var(--radius-lg)', 
                border: '1px dashed var(--border-medium)' 
              }}>
                <p style={{ color: 'var(--text-secondary)', margin: 0, fontWeight: 500 }}>
                  Please use the navigation bar above to access your tools and dashboards.
                </p>
              </div>
              
              <Button onClick={handleLogout} variant="ghost" style={{ marginTop: 'var(--space-5)' }}>
                Sign Out
              </Button>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: 'var(--space-4) 0' }}>
              <p style={{ marginBottom: 'var(--space-5)', color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
                Sign in to access URA tax analytics, reports, and enterprise resources.
              </p>
              
              <Button as="a" href="/login" size="lg">
                Proceed to Login
              </Button>
            </div>
          )}
        </Card>

        <div style={{ 
          marginTop: 'var(--space-6)', 
          paddingTop: 'var(--space-4)', 
          borderTop: '1px solid var(--border-light)', 
          textAlign: 'center', 
          fontSize: '0.875rem', 
          color: 'var(--text-tertiary)' 
        }}>
          System Status: <span style={{ 
            color: backendStatus === 'Running' ? 'var(--success)' : 'var(--error)', 
            fontWeight: 600 
          }}>{backendStatus}</span>
        </div>
      </div>
    </main>
  );
}
