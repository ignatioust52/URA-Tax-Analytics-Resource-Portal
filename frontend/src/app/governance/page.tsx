"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { apiFetch } from '../../lib/api';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

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
          <Card style={{ color: 'var(--error)', textAlign: 'center' }}>
            <h2>Access Denied</h2>
            <p>You must be an administrator to view this page.</p>
          </Card>
        </main>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <main className="main-container">
        <div className="flex-between" style={{ marginBottom: 'var(--space-5)' }}>
          <div>
            <h1 className="page-title" style={{ margin: 0 }}>Governance Queue</h1>
            <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>Review and approve resources pending publication</p>
          </div>
          <Button as="a" href="/" variant="secondary">
            ← Back to Dashboard
          </Button>
        </div>

        {loading ? (
          <Card style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Loading Queue...</Card>
        ) : data.length === 0 ? (
          <Card style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
            <div style={{ fontSize: '2.5rem', marginBottom: 'var(--space-3)' }}>🎉</div>
            <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>No resources pending approval.</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: 'var(--space-2)' }}>The governance queue is clear.</p>
          </Card>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <p style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
              <strong>{data.length}</strong> resource(s) awaiting your review.
            </p>
            {data.map((item, idx) => (
              <Card key={idx} className="flex-between" style={{ alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                    <h3 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1.25rem' }}>{item.business_name}</h3>
                    <Badge variant="warning">Pending Review</Badge>
                  </div>
                  
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: 'var(--space-1)' }}>
                    <strong>Category:</strong> {item.category} <span style={{ margin: '0 8px', color: 'var(--border-medium)' }}>|</span> <strong>Department:</strong> {item.department}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: 'var(--space-1)' }}>
                    <strong>Description:</strong> {item.description}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
                    <strong>Requested by:</strong> {item.added_by}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexDirection: 'column', minWidth: '120px' }}>
                  <Button onClick={() => handleApproval(item.id, 'Approved')} style={{ background: 'var(--success)', borderColor: 'var(--success)' }}>
                    Approve
                  </Button>
                  <Button variant="danger" onClick={() => handleApproval(item.id, 'Rejected')}>
                    Reject
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </AdminGuard>
  );
}
