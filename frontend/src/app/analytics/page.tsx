"use client";
import { useEffect, useState } from 'react';
import { AdminGuard } from '../../components/AdminGuard';
import { apiFetch } from '../../lib/api';
import { Card, CardHeader } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
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
    apiFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/analytics`)
      .then(setData)
      .catch(err => setError(err.message));
  }, []);

  if (error) {
    return (
      <AdminGuard>
        <main className="main-container">
          <Card style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
            <h2 style={{ color: 'var(--error)' }}>Analytics Error</h2>
            <p style={{ color: 'var(--text-secondary)' }}>{error}</p>
          </Card>
        </main>
      </AdminGuard>
    );
  }

  if (!data) {
    return (
      <AdminGuard>
        <main className="main-container">
          <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--text-secondary)' }}>
            Loading Analytics...
          </div>
        </main>
      </AdminGuard>
    );
  }

  return (
    <AdminGuard>
      <main className="main-container">
        <div className="flex-between" style={{ marginBottom: 'var(--space-5)' }}>
          <div>
            <h1 className="page-title" style={{ margin: 0 }}>Analytics Dashboard</h1>
            <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0' }}>Resource views and usage activity</p>
          </div>
          <Button as="a" href="/" variant="secondary">
            ← Back to Dashboard
          </Button>
        </div>

        <div className="grid-kpi">
          <Card style={{ textAlign: 'center', padding: 'var(--space-5)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total Recorded Views</div>
            <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 'var(--space-2)' }}>{data.kpis.total_views || 0}</div>
          </Card>
          
          <Card style={{ textAlign: 'center', padding: 'var(--space-5)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Unique Viewers</div>
            <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 'var(--space-2)' }}>{data.kpis.unique_users || 0}</div>
          </Card>
          
          <Card style={{ textAlign: 'center', padding: 'var(--space-5)' }}>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Resources Viewed</div>
            <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--text-primary)', marginTop: 'var(--space-2)' }}>{data.kpis.unique_resources || 0}</div>
          </Card>
        </div>

        <div className="grid-dashboard">
          <Card>
            <CardHeader title="Daily Views Trend" />
            <div style={{ height: '320px', width: '100%', marginTop: 'var(--space-4)' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.daily_views}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" vertical={false} />
                  <XAxis 
                    dataKey="date" 
                    stroke="var(--text-tertiary)" 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} 
                    axisLine={false} 
                    tickLine={false} 
                    dy={10} 
                  />
                  <YAxis 
                    stroke="var(--text-tertiary)" 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} 
                    axisLine={false} 
                    tickLine={false} 
                    dx={-10} 
                  />
                  <Tooltip 
                    contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }} 
                    itemStyle={{ color: 'var(--ura-blue)' }} 
                  />
                  <Line type="monotone" dataKey="views" stroke="var(--ura-blue)" strokeWidth={3} dot={{ r: 4, fill: 'var(--ura-blue)', strokeWidth: 2, stroke: 'var(--surface)' }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
          
          <Card>
            <CardHeader title="Top 10 Most Popular Resources" />
            <div style={{ height: '320px', width: '100%', marginTop: 'var(--space-4)' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.popular} margin={{ bottom: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" vertical={false} />
                  <XAxis 
                    dataKey="resource_id" 
                    stroke="var(--text-tertiary)" 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 11 }} 
                    angle={-45} 
                    textAnchor="end" 
                    axisLine={false} 
                    tickLine={false} 
                    dy={10} 
                  />
                  <YAxis 
                    stroke="var(--text-tertiary)" 
                    tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} 
                    axisLine={false} 
                    tickLine={false} 
                    dx={-10} 
                  />
                  <Tooltip 
                    contentStyle={{ background: 'var(--surface)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }} 
                    itemStyle={{ color: 'var(--ura-yellow)', fontWeight: 600 }} 
                  />
                  <Bar dataKey="views" fill="var(--ura-blue)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </main>
    </AdminGuard>
  );
}
