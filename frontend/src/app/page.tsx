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
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {user ? (
        <div className="main-container">
          <div style={{ maxWidth: '800px', margin: '0 auto', marginTop: '10vh' }}>
            <div style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
              <h1 className="page-title">URA GO PORTAL</h1>
              <p className="page-subtitle">DEVELOPING UGANDA TOGETHER</p>
            </div>
            
            <Card>
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
            </Card>
          </div>
        </div>
      ) : (
        <div style={{ 
          flex: 1, 
          display: 'flex', 
          flexDirection: 'column', 
          justifyContent: 'center', 
          alignItems: 'center',
          background: 'linear-gradient(rgba(28, 36, 48, 0.8), rgba(26, 46, 102, 0.9)), url("/ura-bg.jpg") no-repeat center center / cover',
          color: 'white',
          textAlign: 'center',
          padding: '0 20px'
        }}>
          <img src="/logo.png" alt="URA Logo" style={{ height: '100px', marginBottom: 'var(--space-4)' }} />
          <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', fontWeight: 800, marginBottom: 'var(--space-2)', textShadow: '0 4px 12px rgba(0,0,0,0.5)' }}>
            Uganda Revenue Authority
          </h1>
          <p style={{ fontSize: 'clamp(1.2rem, 3vw, 1.5rem)', fontWeight: 300, marginBottom: 'var(--space-6)', opacity: 0.9, letterSpacing: '2px', textTransform: 'uppercase' }}>
            Developing Uganda Together
          </p>
          
          <div style={{ background: 'rgba(255,255,255,0.1)', backdropFilter: 'blur(10px)', padding: 'var(--space-5)', borderRadius: 'var(--radius-lg)', border: '1px solid rgba(255,255,255,0.2)', maxWidth: '500px', width: '100%' }}>
            <p style={{ fontSize: '1.1rem', marginBottom: 'var(--space-5)', lineHeight: 1.6 }}>
              Welcome to the URA GO Portal. Access enterprise analytics, secure documentation, and public resources in one centralized platform.
            </p>
            <Button as="a" href="/login" size="lg" style={{ 
              background: '#FFF200', 
              color: '#1C2430', 
              border: 'none', 
              fontSize: '1.1rem', 
              fontWeight: 700, 
              padding: '16px 32px', 
              borderRadius: 'var(--radius-md)',
              boxShadow: '0 4px 14px rgba(255, 242, 0, 0.3)',
              textDecoration: 'none',
              display: 'inline-block'
            }}>
              Proceed to Login
            </Button>
          </div>
        </div>
      )}

      {user && (
        <div style={{ 
          padding: 'var(--space-4)', 
          textAlign: 'center', 
          fontSize: '0.875rem', 
          color: 'var(--text-tertiary)' 
        }}>
          System Status: <span style={{ 
            color: backendStatus === 'Running' ? 'var(--success)' : 'var(--error)', 
            fontWeight: 600 
          }}>{backendStatus}</span>
        </div>
      )}
    </main>
  );
}
