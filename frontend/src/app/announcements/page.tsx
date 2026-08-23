"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';

type Announcement = {
  announcement_id: number;
  title: string;
  body: string;
  visibility: string;
  departments?: any[];
  published_by: number;
  published_at: string;
  expires_at: string | null;
  is_active: boolean;
};

export default function AnnouncementsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [allDepartments, setAllDepartments] = useState<any[]>([]);
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingAnn, setEditingAnn] = useState<Announcement | null>(null);
  
  // Form state
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [visibility, setVisibility] = useState('EVERYONE');
  const [deptIdList, setDeptIdList] = useState<number[]>([]);
  const [expiresAt, setExpiresAt] = useState('');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    const isUserAdmin = user && user.role && (user.role.includes('admin') || user.role === 'manager');
    
    if (!authLoading && !isUserAdmin) {
      router.push('/');
    } else if (isUserAdmin) {
      fetchAnnouncements();
      apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/all-departments`)
        .then(d => setAllDepartments(d))
        .catch(e => console.error(e));
    }
  }, [user, authLoading, router]);

  const fetchAnnouncements = async () => {
    setLoading(true);
    try {
      const data = await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/announcements`);
      setAnnouncements(data || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const openModal = (ann?: Announcement) => {
    if (ann) {
      setEditingAnn(ann);
      setTitle(ann.title);
      setBody(ann.body);
      setVisibility(ann.visibility || 'EVERYONE');
      setDeptIdList(ann.departments ? ann.departments.map(d => typeof d === 'object' ? d.id : d) : []);
      setExpiresAt(ann.expires_at ? new Date(ann.expires_at).toISOString().slice(0,16) : '');
      setIsActive(ann.is_active);
    } else {
      setEditingAnn(null);
      setTitle('');
      setBody('');
      setVisibility('EVERYONE');
      setDeptIdList([]);
      setExpiresAt('');
      setIsActive(true);
    }
    setShowModal(true);
  };

  const toggleDept = (id: number) => {
    setDeptIdList(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload = {
      title,
      body,
      visibility,
      dept_id_list: deptIdList,
      expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      is_active: isActive
    };
    
    try {
      const url = editingAnn 
        ? `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/announcements/${editingAnn.announcement_id}`
        : `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/announcements`;
        
      await apiFetch(url, {
        method: editingAnn ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      setShowModal(false);
      fetchAnnouncements();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this announcement?")) return;
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/announcements/${id}`, {
        method: 'DELETE'
      });
      fetchAnnouncements();
    } catch (err) {
      console.error(err);
    }
  };

  if (authLoading || loading) return <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading...</div>;
  
  const isAdmin = user && user.role && (user.role.includes('admin') || user.role === 'manager');
  if (!isAdmin) return null;

  return (
    <AdminGuard>
      <main className="main-container">
      <div className="flex-between" style={{ marginBottom: 'var(--space-5)' }}>
        <div>
          <h1 className="page-title" style={{ margin: 0 }}>Announcements</h1>
          <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>Manage news feed broadcasts</p>
        </div>
        <Button onClick={() => openModal()}>
          + New Announcement
        </Button>
      </div>

      <Card noPadding style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '700px' }}>
          <thead>
            <tr style={{ background: 'var(--surface-hover)', borderBottom: '1px solid var(--border-light)' }}>
              <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Status</th>
              <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Title</th>
              <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Visibility</th>
              <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Published</th>
              <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase' }}>Expires</th>
              <th style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 600, color: 'var(--text-secondary)', fontSize: '0.85rem', textTransform: 'uppercase', textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {announcements.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: 'var(--space-4)', textAlign: 'center', color: 'var(--text-secondary)' }}>No announcements found.</td></tr>
            ) : announcements.map(ann => (
              <tr key={ann.announcement_id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                <td style={{ padding: 'var(--space-3) var(--space-4)' }}>
                  <Badge variant={ann.is_active ? 'success' : 'neutral'}>{ann.is_active ? 'Active' : 'Inactive'}</Badge>
                </td>
                <td style={{ padding: 'var(--space-3) var(--space-4)', fontWeight: 500 }}>{ann.title}</td>
                <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)' }}>{ann.visibility}</td>
                <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{new Date(ann.published_at).toLocaleDateString()}</td>
                <td style={{ padding: 'var(--space-3) var(--space-4)', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{ann.expires_at ? new Date(ann.expires_at).toLocaleDateString() : 'Never'}</td>
                <td style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'right' }}>
                  <Button variant="secondary" size="sm" onClick={() => openModal(ann)} style={{ marginRight: '8px' }}>Edit</Button>
                  <Button variant="danger" size="sm" onClick={() => handleDelete(ann.announcement_id)}>Delete</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <Card style={{ width: '100%', maxWidth: '600px', padding: 'var(--space-5)', boxShadow: 'var(--shadow-lg)' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-4)' }}>
              {editingAnn ? 'Edit Announcement' : 'New Announcement'}
            </h2>
            
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
              <Input 
                label="Title"
                value={title} 
                onChange={e => setTitle(e.target.value)} 
                required 
              />
              
              <div style={{ marginBottom: 'var(--space-3)' }}>
                <label>Body</label>
                <textarea 
                  value={body} 
                  onChange={e => setBody(e.target.value)} 
                  required 
                  rows={4}
                  style={{ 
                    width: '100%', 
                    padding: '10px 12px', 
                    borderRadius: 'var(--radius-md)', 
                    border: '1px solid var(--border-medium)', 
                    background: 'var(--surface)', 
                    color: 'var(--text-primary)',
                    fontSize: '0.95rem',
                    outline: 'none',
                    resize: 'vertical'
                  }}
                />
              </div>

              <div style={{ marginBottom: 'var(--space-3)' }}>
                <label style={{ display: 'block', marginBottom: '8px' }}>Visibility</label>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input type="radio" name="visibility" value="EVERYONE" checked={visibility === 'EVERYONE'} onChange={e => setVisibility(e.target.value)} />
                    Everyone
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input type="radio" name="visibility" value="ADMIN_ONLY" checked={visibility === 'ADMIN_ONLY'} onChange={e => setVisibility(e.target.value)} />
                    Admin Only
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <input type="radio" name="visibility" value="SELECTED_DEPARTMENTS" checked={visibility === 'SELECTED_DEPARTMENTS'} onChange={e => setVisibility(e.target.value)} />
                    Selected Departments
                  </label>
                </div>
              </div>

              {visibility === 'SELECTED_DEPARTMENTS' && (
                <div style={{ marginBottom: 'var(--space-3)' }}>
                  <label style={{ display: 'block', marginBottom: '8px' }}>Select Departments</label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '150px', overflowY: 'auto', border: '1px solid var(--border-medium)', padding: '8px' }}>
                    {allDepartments.map(d => (
                      <label key={d.id} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <input type="checkbox" checked={deptIdList.includes(d.id)} onChange={() => toggleDept(d.id)} />
                        {d.name}
                      </label>
                    ))}
                  </div>
                </div>
              )}
              
              <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                <Input 
                  label="Expires At (Optional)"
                  type="datetime-local" 
                  value={expiresAt} 
                  onChange={e => setExpiresAt(e.target.value)} 
                />
              </div>

              {editingAnn && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: 'var(--space-2)' }}>
                  <input 
                    type="checkbox" 
                    id="isActive" 
                    checked={isActive} 
                    onChange={e => setIsActive(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <label htmlFor="isActive" style={{ margin: 0, fontWeight: 500, color: 'var(--text-secondary)' }}>Active (Visible in News Feed)</label>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: 'var(--space-5)' }}>
                <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>Cancel</Button>
                <Button type="submit">Save Announcement</Button>
              </div>
            </form>
          </Card>
        </div>
      )}
      </main>
    </AdminGuard>
  );
}
