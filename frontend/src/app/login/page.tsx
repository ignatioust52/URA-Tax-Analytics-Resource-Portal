"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

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
    <main style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh', 
      background: 'var(--background)' 
    }}>
      <div style={{ width: '100%', maxWidth: '440px', padding: 'var(--space-4)' }}>
        
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-5)' }}>
          <h1 className="page-title" style={{ margin: 0 }}>URA GO PORTAL</h1>
          <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>Enterprise Analytics & Resources</p>
        </div>
        
        <Card>
          <div style={{ display: 'flex', borderBottom: '1px solid var(--border-light)', marginBottom: 'var(--space-4)' }}>
            <button 
              onClick={() => setActiveTab('login')}
              style={{ 
                flex: 1, 
                padding: 'var(--space-3)', 
                background: 'none', 
                border: 'none', 
                color: activeTab === 'login' ? 'var(--ura-blue)' : 'var(--text-secondary)', 
                borderBottom: activeTab === 'login' ? '2px solid var(--ura-blue)' : '2px solid transparent', 
                cursor: 'pointer', 
                fontWeight: 600,
                fontSize: '0.95rem'
              }}
            >
              Sign In
            </button>
            <button 
              onClick={() => setActiveTab('register')}
              style={{ 
                flex: 1, 
                padding: 'var(--space-3)', 
                background: 'none', 
                border: 'none', 
                color: activeTab === 'register' ? 'var(--ura-blue)' : 'var(--text-secondary)', 
                borderBottom: activeTab === 'register' ? '2px solid var(--ura-blue)' : '2px solid transparent', 
                cursor: 'pointer', 
                fontWeight: 600,
                fontSize: '0.95rem'
              }}
            >
              Request Access
            </button>
          </div>
          
          {activeTab === 'login' ? (
            <div>
              {loginError && (
                <div style={{ background: 'var(--error-bg)', border: '1px solid var(--error)', color: 'var(--error)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)', textAlign: 'center', fontSize: '0.9rem', fontWeight: 500 }}>
                  {loginError}
                </div>
              )}
              
              <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column' }}>
                <Input 
                  label="Email Address"
                  type="email" 
                  value={email} 
                  onChange={(e) => setEmail(e.target.value)} 
                  placeholder="admin@ura.go.ug" 
                  required 
                  autoComplete="off"
                />
                <Input 
                  label="Password"
                  type="password" 
                  value={password} 
                  onChange={(e) => setPassword(e.target.value)} 
                  placeholder="••••••••" 
                  required 
                  autoComplete="new-password"
                />
                <Button type="submit" fullWidth size="lg" style={{ marginTop: 'var(--space-2)' }}>
                  Secure Login
                </Button>
              </form>
            </div>
          ) : (
            <div>
              {regError && (
                <div style={{ background: 'var(--error-bg)', border: '1px solid var(--error)', color: 'var(--error)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)', textAlign: 'center', fontSize: '0.9rem', fontWeight: 500 }}>
                  {regError}
                </div>
              )}
              {regSuccess && (
                <div style={{ background: 'var(--success-bg)', border: '1px solid var(--success)', color: 'var(--success)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)', textAlign: 'center', fontSize: '0.9rem', fontWeight: 500 }}>
                  {regSuccess}
                </div>
              )}
              
              <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column' }}>
                <Input 
                  label="Email Address"
                  type="email" 
                  value={regEmail} 
                  onChange={(e) => setRegEmail(e.target.value)} 
                  placeholder="user@ura.go.ug" 
                  required 
                  autoComplete="off"
                />
                <Input 
                  label="Department"
                  type="text" 
                  value={regDepartment} 
                  onChange={(e) => setRegDepartment(e.target.value)} 
                  placeholder="e.g. Data Analytics" 
                  required 
                  autoComplete="off"
                />
                <Input 
                  label="Password"
                  type="password" 
                  value={regPassword} 
                  onChange={(e) => setRegPassword(e.target.value)} 
                  placeholder="••••••••" 
                  required 
                  autoComplete="new-password"
                />
                <Input 
                  label="Confirm Password"
                  type="password" 
                  value={regConfirm} 
                  onChange={(e) => setRegConfirm(e.target.value)} 
                  placeholder="••••••••" 
                  required 
                  autoComplete="new-password"
                />
                <Button type="submit" fullWidth size="lg" style={{ marginTop: 'var(--space-2)' }}>
                  Submit Request
                </Button>
              </form>
            </div>
          )}
        </Card>
        
        <div style={{ textAlign: 'center', marginTop: 'var(--space-5)', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
          &copy; {new Date().getFullYear()} Uganda Revenue Authority. All rights reserved.
        </div>
      </div>
    </main>
  );
}
