"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';

const STANDARD_DEPARTMENTS = [
  'Domestic Taxes Department',
  'Customs Department',
  'Tax Investigations Department',
  'Legal Services & Board Affairs',
  'Finance Department',
  'Human Resources & Development',
  'Information Technology (IT/Digital)',
  'Internal Audit',
  'Public and Corporate Affairs',
  'Research, Policy Analysis & Planning',
  'Commissioner General\'s Office / Executive Management',
  'Taxpayer Services / Client Service',
  'Enforcement / Compliance',
  'Corporate Services / Administration',
  'Internal Affairs / Risk Management'
];

export default function LoginPage() {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');
  
  // Login State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  
  // Department Selection State
  const [pendingUser, setPendingUser] = useState<any>(null);
  const [availableDepartments, setAvailableDepartments] = useState<any[]>([]);
  const [selectedDeptId, setSelectedDeptId] = useState<number | ''>('');
  
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
      
      if (data.requires_department_selection) {
        setPendingUser(data.user);
        setAvailableDepartments(data.departments);
        if (data.departments && data.departments.length > 0) {
           setSelectedDeptId(data.departments[0].id);
        }
      } else {
        login(data.user);
        router.push('/resources');
      }
    } catch (err) {
      setLoginError('Network error');
    }
  };

  const handleSelectDepartment = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/select-department`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ department_id: selectedDeptId }),
      });
      
      const data = await res.json();
      if (!res.ok) {
        setLoginError(data.detail || 'Department selection failed');
        return;
      }
      
      login({ ...pendingUser, active_department_id: data.active_department_id });
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
    if (!regDepartment) {
      setRegError('Please select a department');
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
          {!pendingUser && (
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
          )}
          
          {pendingUser ? (
            <div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: 'var(--space-2)' }}>Select Active Department</h2>
              <p style={{ color: 'var(--text-secondary)', marginBottom: 'var(--space-4)', fontSize: '0.9rem' }}>
                You have access to multiple departments. Please select the context you wish to sign in with.
              </p>
              
              {loginError && (
                <div style={{ background: 'var(--error-bg)', border: '1px solid var(--error)', color: 'var(--error)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)', textAlign: 'center', fontSize: '0.9rem', fontWeight: 500 }}>
                  {loginError}
                </div>
              )}
              
              <form onSubmit={handleSelectDepartment} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div className="input-group">
                  <label className="input-label">Department Context</label>
                  <select 
                    className="input-field" 
                    value={selectedDeptId}
                    onChange={(e) => setSelectedDeptId(Number(e.target.value))}
                    required
                  >
                    {availableDepartments.length === 0 && <option value="" disabled>No departments available</option>}
                    {availableDepartments.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
                
                <Button type="submit" fullWidth size="lg" style={{ marginTop: 'var(--space-2)' }} disabled={!selectedDeptId}>
                  Continue to Portal
                </Button>
                <Button type="button" variant="ghost" fullWidth onClick={() => {
                  setPendingUser(null);
                  setEmail('');
                  setPassword('');
                }}>
                  Cancel Login
                </Button>
              </form>
            </div>
          ) : activeTab === 'login' ? (
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
              
              <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                <Input 
                  label="Email Address"
                  type="email" 
                  value={regEmail} 
                  onChange={(e) => setRegEmail(e.target.value)} 
                  placeholder="user@ura.go.ug" 
                  required 
                  autoComplete="off"
                />
                
                <div className="input-group" style={{ marginBottom: 'var(--space-3)' }}>
                  <label className="input-label">Department</label>
                  <select 
                    className="input-field" 
                    value={regDepartment}
                    onChange={(e) => setRegDepartment(e.target.value)}
                    required
                  >
                    <option value="" disabled>Select a department</option>
                    {STANDARD_DEPARTMENTS.map(d => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
                
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
