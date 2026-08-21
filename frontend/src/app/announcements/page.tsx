"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { useRouter } from 'next/navigation';
import { useAuth } from '../contexts/AuthContext';

type Announcement = {
  announcement_id: number;
  title: string;
  body: string;
  audience_department_id: number | null;
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
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [editingAnn, setEditingAnn] = useState<Announcement | null>(null);
  
  // Form state
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [deptId, setDeptId] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [isActive, setIsActive] = useState(true);

  useEffect(() => {
    if (!authLoading && (!user || user.role !== 'admin')) {
      router.push('/');
    } else if (user && user.role === 'admin') {
      fetchAnnouncements();
    }
  }, [user, authLoading, router]);

  const fetchAnnouncements = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/announcements', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setAnnouncements(data || []);
      }
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
      setDeptId(ann.audience_department_id ? String(ann.audience_department_id) : '');
      setExpiresAt(ann.expires_at ? new Date(ann.expires_at).toISOString().slice(0,16) : '');
      setIsActive(ann.is_active);
    } else {
      setEditingAnn(null);
      setTitle('');
      setBody('');
      setDeptId('');
      setExpiresAt('');
      setIsActive(true);
    }
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const payload = {
      title,
      body,
      audience_department_id: deptId ? parseInt(deptId) : null,
      expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      is_active: isActive
    };
    
    try {
      const url = editingAnn 
        ? `http://localhost:8000/api/announcements/${editingAnn.announcement_id}`
        : `http://localhost:8000/api/announcements`;
        
      const res = await fetch(url, {
        method: editingAnn ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setShowModal(false);
        fetchAnnouncements();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this announcement?")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/announcements/${id}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) fetchAnnouncements();
    } catch (err) {
      console.error(err);
    }
  };

  if (authLoading || loading) return <div style={{ padding: '40px', textAlign: 'center', color: 'white' }}>Loading...</div>;
  if (!user || user.role !== 'admin') return null;

  return (
    <AdminGuard>
      <main className="main-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 className="header-title" style={{ fontSize: '2rem' }}>Announcements</h1>
          <p className="header-subtitle" style={{ marginBottom: 0 }}>Manage news feed broadcasts</p>
        </div>
        <button onClick={() => openModal()} className="btn-primary">
          + New Announcement
        </button>
      </div>

      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--border)' }}>
              <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Status</th>
              <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Title</th>
              <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Audience</th>
              <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Published</th>
              <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Expires</th>
              <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {announcements.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>No announcements found.</td></tr>
            ) : announcements.map(ann => (
              <tr key={ann.announcement_id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '16px' }}>
                  {ann.is_active ? <span className="ura-chip ura-chip-green">Active</span> : <span className="ura-chip ura-chip-gray">Inactive</span>}
                </td>
                <td style={{ padding: '16px', fontWeight: 500 }}>{ann.title}</td>
                <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{ann.audience_department_id ? `Dept ID: ${ann.audience_department_id}` : 'Global'}</td>
                <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{new Date(ann.published_at).toLocaleDateString()}</td>
                <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{ann.expires_at ? new Date(ann.expires_at).toLocaleDateString() : 'Never'}</td>
                <td style={{ padding: '16px' }}>
                  <button onClick={() => openModal(ann)} className="btn-secondary" style={{ marginRight: '8px', padding: '6px 12px', fontSize: '0.85rem' }}>Edit</button>
                  <button onClick={() => handleDelete(ann.announcement_id)} className="btn-primary" style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', padding: '6px 12px', fontSize: '0.85rem' }}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '600px', padding: '32px' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '24px' }}>
              {editingAnn ? 'Edit Announcement' : 'New Announcement'}
            </h2>
            
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Title</label>
                <input 
                  type="text" value={title} onChange={e => setTitle(e.target.value)} required 
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                />
              </div>
              
              <div>
                <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Body</label>
                <textarea 
                  value={body} onChange={e => setBody(e.target.value)} required rows={4}
                  style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white', resize: 'vertical' }}
                />
              </div>
              
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Target Department ID (Optional)</label>
                  <input 
                    type="number" value={deptId} onChange={e => setDeptId(e.target.value)} placeholder="Leave empty for Global"
                    style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Expires At (Optional)</label>
                  <input 
                    type="datetime-local" value={expiresAt} onChange={e => setExpiresAt(e.target.value)} 
                    style={{ width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
                  />
                </div>
              </div>

              {editingAnn && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
                  <input 
                    type="checkbox" id="isActive" checked={isActive} onChange={e => setIsActive(e.target.checked)}
                    style={{ width: '16px', height: '16px' }}
                  />
                  <label htmlFor="isActive" style={{ color: 'var(--text-secondary)' }}>Active (Visible in News Feed)</label>
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Cancel</button>
                <button type="submit" className="btn-primary">Save Announcement</button>
              </div>
            </form>
          </div>
        </div>
      )}
      </main>
    </AdminGuard>
  );
}
