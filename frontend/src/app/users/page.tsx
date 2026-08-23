"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';

export default function UsersPage() {
  const [activeTab, setActiveTab] = useState('active');
  const [data, setData] = useState<any[]>([]);
  const [pendingUsers, setPendingUsers] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchUsers = () => {
    setLoading(true);
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users`, { credentials: 'include' })
      .then(res => res.ok ? res.json() : [])
      .then(d => setData(d))
      .catch(err => setError(err.message));
      
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/pending`, { credentials: 'include' })
      .then(res => res.ok ? res.json() : [])
      .then(d => setPendingUsers(d))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleStatusUpdate = async (id: number, isActive: boolean, status: string) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ user_id: id, is_active: isActive, status }),
      });
      if (!res.ok) throw new Error('Failed to update status');
      fetchUsers();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleApprove = async (id: number) => {
    // Basic approval with 'viewer' role and no specific departments for now
    // A fully functional dashboard would have a form here to select roles and departments
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ user_id: id, role: 'viewer', department_ids: [] })
      });
      if (res.ok) fetchUsers();
      else alert("Failed to approve");
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleReject = async (id: number) => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ user_id: id })
      });
      if (res.ok) fetchUsers();
      else alert("Failed to reject");
    } catch (err: any) {
      alert(err.message);
    }
  };

  // Create User State
  const [createForm, setCreateForm] = useState({ email: '', password: '', role: 'viewer' });
  
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/users/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ...createForm, department_ids: [] })
      });
      if (res.ok) {
        alert("User created successfully!");
        setCreateForm({ email: '', password: '', role: 'viewer' });
        fetchUsers();
        setActiveTab('active');
      } else {
        const d = await res.json();
        alert(d.detail || "Failed to create user");
      }
    } catch(err: any) {
      alert(err.message);
    }
  };

  if (error) {
    return (
      <AdminGuard>
        <main className="main-container">
          <div className="glass-panel" style={{ color: '#ef4444', textAlign: 'center' }}>
            <h2>Access Denied</h2>
            <p>You must be an administrator to view this page.</p>
          </div>
        </main>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <main className="main-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 className="header-title" style={{ fontSize: '2rem' }}>User Management</h1>
          <p className="header-subtitle" style={{ marginBottom: 0 }}>Manage access and roles for all system users</p>
        </div>
        <a href="/" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>← Back to Dashboard</a>
      </div>

      <div style={{ display: 'flex', gap: '24px', borderBottom: '1px solid var(--border)', marginBottom: '24px' }}>
        {['active', 'pending', 'create'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'none', border: 'none', padding: '12px 4px', cursor: 'pointer',
              color: activeTab === tab ? 'white' : 'var(--text-secondary)',
              borderBottom: activeTab === tab ? '2px solid var(--accent)' : '2px solid transparent',
              fontWeight: activeTab === tab ? 600 : 400,
              textTransform: 'capitalize'
            }}
          >
            {tab === 'active' ? 'Active Users' : 
             tab === 'pending' ? 'Pending Approvals' : 'Create Account'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="glass-panel" style={{ textAlign: 'center' }}>Loading Users...</div>
      ) : activeTab === 'active' ? (
        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(0,0,0,0.3)', borderBottom: '1px solid var(--border)' }}>
                <th style={{ padding: '16px' }}>Email</th>
                <th style={{ padding: '16px' }}>Role</th>
                <th style={{ padding: '16px' }}>Department</th>
                <th style={{ padding: '16px' }}>Status</th>
                <th style={{ padding: '16px' }}>Joined</th>
                <th style={{ padding: '16px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((user, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border)' }}>
                  <td style={{ padding: '16px' }}>{user.email}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{ padding: '4px 8px', background: user.role === 'admin' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '0.85rem' }}>
                      {user.role || 'none'}
                    </span>
                  </td>
                  <td style={{ padding: '16px' }}>{user.department || '-'}</td>
                  <td style={{ padding: '16px' }}>
                    <span style={{ color: user.is_active ? '#22c55e' : '#ef4444' }}>
                      {user.status}
                    </span>
                  </td>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '16px', display: 'flex', gap: '8px' }}>
                    {user.is_active ? (
                      <button onClick={() => handleStatusUpdate(user.id, false, 'disabled')} className="btn-primary" style={{ padding: '6px 12px', background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', fontSize: '0.85rem' }}>
                        Disable
                      </button>
                    ) : (
                      <button onClick={() => handleStatusUpdate(user.id, true, 'active')} className="btn-primary" style={{ padding: '6px 12px', background: '#22c55e', fontSize: '0.85rem' }}>
                        Enable
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : activeTab === 'pending' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {pendingUsers.length === 0 ? (
            <div className="glass-panel" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No pending registrations found.</div>
          ) : pendingUsers.map(pu => (
            <div key={pu.id} className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ marginBottom: '4px' }}>{pu.email}</h4>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Requested Department: {pu.requested_department || 'None'}</div>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button onClick={() => handleReject(pu.id)} className="btn-secondary" style={{ color: '#ef4444', borderColor: '#ef4444' }}>Reject</button>
                <button onClick={() => handleApprove(pu.id)} className="btn-primary" style={{ background: '#22c55e' }}>Approve</button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-panel" style={{ maxWidth: '500px', margin: '0 auto' }}>
          <h3 style={{ marginBottom: '24px' }}>Create New Account</h3>
          <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Email</label>
              <input type="email" required value={createForm.email} onChange={e => setCreateForm({...createForm, email: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: 'white' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Temporary Password</label>
              <input type="password" required value={createForm.password} onChange={e => setCreateForm({...createForm, password: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: 'white' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>Role</label>
              <select value={createForm.role} onChange={e => setCreateForm({...createForm, role: e.target.value})} style={{ width: '100%', padding: '10px', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: 'white' }}>
                <option value="viewer">Viewer</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button type="submit" className="btn-primary" style={{ marginTop: '16px', padding: '12px' }}>Create Account</button>
          </form>
        </div>
      )}
      </main>
    </AdminGuard>
  );
}
