"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  
  // Login State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  
  // Register State
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirm, setRegConfirm] = useState('');
  const [regDepartment, setRegDepartment] = useState('');
  const [regError, setRegError] = useState('');
  const [regSuccess, setRegSuccess] = useState('');

  const router = useRouter();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });
      
      const data = await res.json();
      if (!res.ok) {
        setLoginError(data.detail || 'Login failed');
        return;
      }
      
      login(data.user);
      router.push('/resources');
    } catch (err) {
      setLoginError('Network error');
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError('');
    setRegSuccess('');
    
    if (regPassword !== regConfirm) {
      setRegError('Passwords do not match');
      return;
    }
    
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: regEmail, 
          password: regPassword,
          confirm_password: regConfirm,
          department: regDepartment
        }),
      });
      
      const data = await res.json();
      if (!res.ok) {
        setRegError(data.detail || 'Registration failed');
        return;
      }
      
      setRegSuccess(data.message || 'Account created! Awaiting admin approval.');
      setRegEmail('');
      setRegPassword('');
      setRegConfirm('');
      setRegDepartment('');
    } catch (err) {
      setRegError('Network error');
    }
  };

  return (
    <main className="main-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: 'radial-gradient(circle at top, #1e293b 0%, #0f172a 100%)' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '40px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h1 className="header-title" style={{ fontSize: '2rem', marginBottom: '8px' }}>URA Portal</h1>
          <p className="header-subtitle" style={{ fontSize: '1rem', margin: 0 }}>Revenue Dashboard</p>
        </div>
        
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '1px solid var(--border)' }}>
          <button 
            onClick={() => setActiveTab('login')}
            style={{ flex: 1, padding: '12px', background: 'none', border: 'none', color: activeTab === 'login' ? 'white' : 'var(--text-secondary)', borderBottom: activeTab === 'login' ? '2px solid var(--accent)' : '2px solid transparent', cursor: 'pointer', fontWeight: 600 }}
          >
            Sign In
          </button>
          <button 
            onClick={() => setActiveTab('register')}
            style={{ flex: 1, padding: '12px', background: 'none', border: 'none', color: activeTab === 'register' ? 'white' : 'var(--text-secondary)', borderBottom: activeTab === 'register' ? '2px solid var(--accent)' : '2px solid transparent', cursor: 'pointer', fontWeight: 600 }}
          >
            Create Account
          </button>
        </div>
        
        {activeTab === 'login' ? (
          <div>
            {loginError && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#fca5a5', padding: '12px', borderRadius: '8px', marginBottom: '24px', textAlign: 'center', fontSize: '0.9rem' }}>
                {loginError}
              </div>
            )}
            
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Email Address</label>
                <input 
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@ura.go.ug" required autoComplete="off"
                  style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Password</label>
                <input 
                  type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" required autoComplete="new-password"
                  style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              <button type="submit" className="btn-primary" style={{ marginTop: '12px', padding: '14px', width: '100%', fontWeight: 600 }}>
                Secure Login
              </button>
            </form>
          </div>
        ) : (
          <div>
            {regError && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', color: '#fca5a5', padding: '12px', borderRadius: '8px', marginBottom: '24px', textAlign: 'center', fontSize: '0.9rem' }}>
                {regError}
              </div>
            )}
            {regSuccess && (
              <div style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid #22c55e', color: '#86efac', padding: '12px', borderRadius: '8px', marginBottom: '24px', textAlign: 'center', fontSize: '0.9rem' }}>
                {regSuccess}
              </div>
            )}
            
            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Email Address</label>
                <input 
                  type="email" value={regEmail} onChange={(e) => setRegEmail(e.target.value)} placeholder="user@ura.go.ug" required autoComplete="off"
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Department</label>
                <input 
                  type="text" value={regDepartment} onChange={(e) => setRegDepartment(e.target.value)} placeholder="e.g. Analytics" required autoComplete="off"
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Password</label>
                <input 
                  type="password" value={regPassword} onChange={(e) => setRegPassword(e.target.value)} placeholder="••••••••" required autoComplete="new-password"
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Confirm Password</label>
                <input 
                  type="password" value={regConfirm} onChange={(e) => setRegConfirm(e.target.value)} placeholder="••••••••" required autoComplete="new-password"
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              <button type="submit" className="btn-primary" style={{ marginTop: '12px', padding: '14px', width: '100%', fontWeight: 600 }}>
                Request Access
              </button>
            </form>
          </div>
        )}
      </div>
    </main>
  );
}
