"use client";
import { useState, useEffect } from 'react';
import { useAuth } from './contexts/AuthContext';

export default function Home() {
  const { user, loading } = useAuth();
  const [backendStatus, setBackendStatus] = useState('Checking...');

  useEffect(() => {
    fetch('http://localhost:8000/api/health')
      .then((res) => res.json())
      .then((data) => {
        setBackendStatus(data.status === 'ok' ? 'Running' : 'Error');
      })
      .catch(() => setBackendStatus('Offline'));
  }, []);

  const handleLogout = async () => {
    await fetch('http://localhost:8000/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    });
    window.location.href = '/login';
  };

  if (loading) {
    return (
      <main className="main-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: '100vh', paddingTop: '10vh' }}>
        <div className="glass-panel" style={{ maxWidth: '800px', width: '100%', padding: '40px', textAlign: 'center' }}>
          <p style={{ color: 'var(--text-secondary)' }}>Loading session...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="main-container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minHeight: '100vh', paddingTop: '10vh' }}>
      <div className="glass-panel" style={{ maxWidth: '800px', width: '100%', padding: '40px' }}>
        <h1 className="header-title" style={{ fontSize: '2.5rem', textAlign: 'center', marginBottom: '8px' }}>URA Revenue Dashboard</h1>
        <p className="header-subtitle" style={{ textAlign: 'center', marginBottom: '32px' }}>
          DEVELOPING UGANDA TOGETHER
        </p>
        
        {user ? (
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <p style={{ fontSize: '1.1rem', marginBottom: '8px' }}>Welcome back, <strong>{user.email}</strong></p>
            <div style={{ display: 'inline-block', padding: '4px 12px', background: 'rgba(255,255,255,0.1)', borderRadius: '16px', fontSize: '0.9rem', color: 'var(--brand-yellow)' }}>
              Role: {user.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : 'User'}
            </div>
            
            <div style={{ marginTop: '32px', padding: '24px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '0' }}>
                Please use the navigation bar above to access your tools and dashboards.
              </p>
            </div>
            
            <button onClick={handleLogout} className="btn-primary" style={{ marginTop: '32px', background: 'transparent', border: '1px solid rgba(255,255,255,0.2)', color: 'var(--text-secondary)' }}>
              Sign Out
            </button>
          </div>
        ) : (
          <div style={{ textAlign: 'center' }}>
            <p style={{ marginBottom: '24px', color: 'var(--text-secondary)' }}>
              Sign in to access URA tax analytics, reports, and resources.
            </p>
            
            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
              <a href="/login" className="btn-primary" style={{ display: 'inline-block', textDecoration: 'none', padding: '12px 24px' }}>
                Sign In
              </a>
            </div>
          </div>
        )}

        <div style={{ marginTop: '40px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)', textAlign: 'center', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
          Backend Status: <strong>{backendStatus}</strong>
        </div>
      </div>
    </main>
  );
}
