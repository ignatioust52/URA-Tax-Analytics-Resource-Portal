"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('http://localhost:8000/api/analytics', {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })
      .then(res => {
        if (!res.ok) throw new Error('Unauthorized');
        return res.json();
      })
      .then(setData)
      .catch(err => setError(err.message));
  }, []);

  if (error) {
    return (
      <AdminGuard>
        <main className="main-container">
          <div className="glass-panel" style={{ color: '#ef4444', textAlign: 'center' }}>
            <h2>Analytics Error</h2>
            <p>{error}</p>
          </div>
        </main>
      </AdminGuard>
    );
  }

  if (!data) {
    return (
      <AdminGuard>
        <main className="main-container"><div className="glass-panel" style={{ textAlign: 'center' }}>Loading Analytics...</div></main>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <main className="main-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
          <div>
            <h1 className="header-title" style={{ fontSize: '2rem' }}>Admin Analytics</h1>
            <p className="header-subtitle" style={{ marginBottom: 0 }}>Resource-view activity across the catalog</p>
          </div>
          <a href="/" style={{ color: 'var(--text-secondary)', textDecoration: 'none' }}>← Back</a>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginBottom: '32px' }}>
          <div className="glass-panel" style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Total Recorded Views</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{data.kpis.total_views || 0}</div>
          </div>
          <div className="glass-panel" style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Unique Viewers</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{data.kpis.unique_users || 0}</div>
          </div>
          <div className="glass-panel" style={{ textAlign: 'center' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Resources Viewed</div>
            <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{data.kpis.unique_resources || 0}</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div className="glass-panel">
            <h3 style={{ marginBottom: '24px' }}>Daily Views Trend</h3>
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.daily_views}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="date" stroke="var(--text-secondary)" />
                  <YAxis stroke="var(--text-secondary)" />
                  <Tooltip contentStyle={{ background: 'var(--surface)', border: 'none', borderRadius: '8px' }} />
                  <Line type="monotone" dataKey="views" stroke="#60a5fa" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="glass-panel">
            <h3 style={{ marginBottom: '24px' }}>Top 10 Most Popular</h3>
            <div style={{ height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.popular}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="resource_id" stroke="var(--text-secondary)" tick={{fontSize: 10}} angle={-45} textAnchor="end" height={60} />
                  <YAxis stroke="var(--text-secondary)" />
                  <Tooltip contentStyle={{ background: 'var(--surface)', border: 'none', borderRadius: '8px' }} />
                  <Bar dataKey="views" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </main>
    </AdminGuard>
  );
}
