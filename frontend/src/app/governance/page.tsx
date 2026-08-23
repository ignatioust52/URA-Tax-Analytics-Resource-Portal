"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { apiFetch } from '../../lib/api';

export default function GovernancePage() {
  const [data, setData] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchPending = () => {
    setLoading(true);
    apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/governance/pending`)
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleApproval = async (id: number, status: 'Approved' | 'Rejected') => {
    try {
      await apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/governance/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resource_id: id, status }),
      });
      fetchPending(); // Refresh list
    } catch (err) {
      alert('Error updating status');
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
            <h1 className="header-title" style={{ fontSize: '2rem' }}>Governance Queue</h1>
            <p className="header-subtitle" style={{ marginBottom: 0 }}>Review and approve resources pending publication</p>
          </div>
          <a href="/" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>← Back</a>
        </div>

        {loading ? (
          <div className="glass-panel" style={{ textAlign: 'center' }}>Loading Queue...</div>
        ) : data.length === 0 ? (
          <div className="glass-panel" style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ fontSize: '2rem', marginBottom: '16px' }}>🎉</div>
            <h3 style={{ margin: 0 }}>No resources pending approval.</h3>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <p><strong>{data.length} resource(s) awaiting your review.</strong></p>
            {data.map((item, idx) => (
              <div key={idx} className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>{item.business_name}</h3>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '4px' }}>
                    <strong>Category:</strong> {item.category} | <strong>Department:</strong> {item.department}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '4px' }}>
                    <strong>Description:</strong> {item.description}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    <strong>Requested by:</strong> {item.added_by}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexDirection: 'column' }}>
                  <button onClick={() => handleApproval(item.id, 'Approved')} className="btn-primary" style={{ padding: '8px 16px', background: '#22c55e' }}>Approve</button>
                  <button onClick={() => handleApproval(item.id, 'Rejected')} className="btn-primary" style={{ padding: '8px 16px', background: 'transparent', border: '1px solid #ef4444', color: '#ef4444' }}>Reject</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </AdminGuard>
  );
}
