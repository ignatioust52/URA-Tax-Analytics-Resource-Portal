"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { apiFetch } from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
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

const STANDARD_ROLES = [
  'Super Administrator',
  'System Administrator',
  'Department Administrator',
  'Manager',
  'Senior Analyst',
  'Analyst',
  'Officer',
  'Viewer'
];

export default function UsersPage() {
  const [activeTab, setActiveTab] = useState('active');
  const [data, setData] = useState<any[]>([]);
  const [pendingUsers, setPendingUsers] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  // Modal State for Approval
  const [approveModalOpen, setApproveModalOpen] = useState(false);
  const [selectedPendingUser, setSelectedPendingUser] = useState<any>(null);
  const [approveRole, setApproveRole] = useState('Viewer');
  const [approveDeptIds, setApproveDeptIds] = useState<number[]>([]);

  const fetchUsers = () => {
    setLoading(true);
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    apiFetch(`${baseUrl}/api/users`)
      .then(d => setData(d))
      .catch(err => setError(err.message));
      
    apiFetch(`${baseUrl}/api/users/pending`)
      .then(d => setPendingUsers(d))
      .finally(() => setLoading(false));
  };

  const fetchDepartments = () => {
    // Actually we could just use a static list, but the API needs dept IDs for user creation.
    // Let's assume departments are fetched or we can lookup ID from backend if needed.
    // Wait, the API requires `department_ids` (list[int]). 
    // We should fetch the full list of departments from the backend.
    apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/departments`)
      // Actually we don't have a public GET /api/departments endpoint yet.
      // Wait, we can add one or just rely on the IDs matching.
  };

  // We need a way to get all departments with IDs. 
  useEffect(() => {
    fetchUsers();
    // Fetch all departments from backend
    apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/all-departments`)
      .then(d => setDepartments(d))
      .catch(e => console.error(e));
  }, []);

  const handleStatusUpdate = async (id: number, isActive: boolean, status: string) => {
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: id, is_active: isActive, status }),
      });
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleApprove = async () => {
    if (!selectedPendingUser) return;
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_id: selectedPendingUser.id, 
          role: approveRole, 
          department_ids: approveDeptIds 
        })
      });
      setApproveModalOpen(false);
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleReject = async (id: number) => {
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: id })
      });
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Create User State
  const [createForm, setCreateForm] = useState({ email: '', password: '', role: 'Viewer' });
  const [createDeptIds, setCreateDeptIds] = useState<number[]>([]);
  
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...createForm, department_ids: createDeptIds })
      });
      alert("User created successfully!");
      setCreateForm({ email: '', password: '', role: 'Viewer' });
      setCreateDeptIds([]);
      fetchUsers();
      setActiveTab('active');
    } catch(err: any) {
      alert(err.message);
    }
  };

  if (error) {
    return (
      <AdminGuard>
        <main className="main-container">
          <Card style={{ color: 'var(--error)', textAlign: 'center' }}>
            <h2>Access Denied</h2>
            <p>You must be an administrator to view this page.</p>
          </Card>
        </main>
      </AdminGuard>
    );
  }

  const toggleDept = (id: number, currentList: number[], setList: (l: number[]) => void) => {
    if (currentList.includes(id)) {
      setList(currentList.filter(x => x !== id));
    } else {
      setList([...currentList, id]);
    }
  };

  return (
    <AdminGuard>
      <main className="main-container">
      <div className="flex-between" style={{ marginBottom: 'var(--space-5)' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>User Management</h1>
          <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>Manage access and roles for all system users</p>
        </div>
        <Button as="a" href="/" variant="secondary">
          ← Back to Dashboard
        </Button>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-4)', borderBottom: '1px solid var(--border-light)', marginBottom: 'var(--space-4)', overflowX: 'auto', whiteSpace: 'nowrap', paddingBottom: '4px' }}>
        {['active', 'pending', 'create'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'none', 
              border: 'none', 
              padding: 'var(--space-3) var(--space-1)', 
              cursor: 'pointer',
              color: activeTab === tab ? 'var(--ura-blue)' : 'var(--text-secondary)',
              borderBottom: activeTab === tab ? '2px solid var(--ura-blue)' : '2px solid transparent',
              fontWeight: activeTab === tab ? 600 : 500,
              textTransform: 'capitalize',
              fontSize: '0.95rem'
            }}
          >
            {tab === 'active' ? 'Active Users' : 
             tab === 'pending' ? 'Pending Approvals' : 'Create Account'}
          </button>
        ))}
      </div>

      {loading ? (
        <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Loading Users...</Card>
      ) : activeTab === 'active' ? (
        <Card noPadding>
          <div className="table-responsive-wrapper">
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '700px' }}>
            <thead>
              <tr style={{ background: 'var(--surface-hover)', borderBottom: '1px solid var(--border-light)' }}>
                <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase' }}>Email</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase' }}>Role</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase' }}>Status</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase' }}>Joined</th>
                <th style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((user, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-light)' }}>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 500 }}>{user.email}</td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    <Badge variant={user.role === 'Super Administrator' ? 'info' : 'neutral'}>
                      {user.role || 'none'}
                    </Badge>
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                    <Badge variant={user.is_active ? 'success' : 'error'}>
                      {user.status}
                    </Badge>
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-tertiary)', fontSize: '0.9rem' }}>
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>
                    {user.is_active ? (
                      <Button size="sm" variant="danger" onClick={() => handleStatusUpdate(user.id, false, 'disabled')}>
                        Disable
                      </Button>
                    ) : (
                      <Button size="sm" onClick={() => handleStatusUpdate(user.id, true, 'active')}>
                        Enable
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </Card>
      ) : activeTab === 'pending' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {pendingUsers.length === 0 ? (
            <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No pending registrations found.</Card>
          ) : pendingUsers.map(pu => (
            <Card key={pu.id} className="flex-between">
              <div>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '1.1rem' }}>{pu.email}</h4>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Requested Department: <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{pu.requested_department || 'None'}</span></div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <Button variant="danger" onClick={() => handleReject(pu.id)}>Reject</Button>
                <Button onClick={() => {
                  setSelectedPendingUser(pu);
                  setApproveRole('Viewer');
                  setApproveDeptIds([]);
                  setApproveModalOpen(true);
                }}>Approve...</Button>
              </div>
            </Card>
          ))}
          
          {approveModalOpen && selectedPendingUser && (
            <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000, padding: '16px' }}>
              <Card style={{ width: '100%', maxWidth: '500px', maxHeight: '90vh', overflowY: 'auto' }}>
                <h3 style={{ marginBottom: 'var(--space-4)' }}>Approve User: {selectedPendingUser.email}</h3>
                <div style={{ marginBottom: 'var(--space-3)' }}>
                  <label>Role</label>
                  <select 
                    value={approveRole} 
                    onChange={e => setApproveRole(e.target.value)} 
                    style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--border-medium)', marginTop: '4px' }}
                  >
                    {STANDARD_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <label>Departments (Multi-Select)</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px', maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border-medium)', padding: '8px', borderRadius: '4px' }}>
                    {departments.map(d => (
                      <label key={d.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input type="checkbox" checked={approveDeptIds.includes(d.id)} onChange={() => toggleDept(d.id, approveDeptIds, setApproveDeptIds)} />
                        {d.name}
                      </label>
                    ))}
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                  <Button variant="ghost" onClick={() => setApproveModalOpen(false)}>Cancel</Button>
                  <Button onClick={handleApprove}>Approve & Save</Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      ) : (
        <Card style={{ maxWidth: '500px', margin: '0 auto' }}>
          <h3 style={{ marginBottom: 'var(--space-4)' }}>Create New Account</h3>
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
            <Input 
              label="Email Address"
              type="email" 
              required 
              value={createForm.email} 
              onChange={e => setCreateForm({...createForm, email: e.target.value})} 
              placeholder="user@ura.go.ug"
            />
            <Input 
              label="Temporary Password"
              type="password" 
              required 
              value={createForm.password} 
              onChange={e => setCreateForm({...createForm, password: e.target.value})} 
              placeholder="••••••••"
            />
            <div style={{ marginBottom: 'var(--space-3)' }}>
              <label>Role</label>
              <select 
                value={createForm.role} 
                onChange={e => setCreateForm({...createForm, role: e.target.value})} 
                style={{ 
                  width: '100%', 
                  padding: '10px 12px', 
                  borderRadius: 'var(--radius-md)', 
                  border: '1px solid var(--border-medium)', 
                  background: 'var(--surface)', 
                  color: 'var(--text-primary)',
                  fontSize: '0.95rem',
                  outline: 'none',
                  marginTop: '4px'
                }}
              >
                {STANDARD_ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            
            <div style={{ marginBottom: 'var(--space-4)' }}>
              <label>Departments (Multi-Select)</label>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px', maxHeight: '200px', overflowY: 'auto', border: '1px solid var(--border-medium)', padding: '8px', borderRadius: '4px' }}>
                {departments.map(d => (
                  <label key={d.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <input type="checkbox" checked={createDeptIds.includes(d.id)} onChange={() => toggleDept(d.id, createDeptIds, setCreateDeptIds)} />
                    {d.name}
                  </label>
                ))}
              </div>
            </div>
                
            <Button type="submit" fullWidth style={{ marginTop: 'var(--space-2)' }}>Create Account</Button>
          </form>
        </Card>
      )}
      </main>
    </AdminGuard>
  );
}
