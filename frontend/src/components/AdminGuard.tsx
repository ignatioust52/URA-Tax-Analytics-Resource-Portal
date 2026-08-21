"use client";
/**
 * AdminGuard.tsx
 * RBAC enforcement component for admin-only pages.
 * 
 * Usage: Wrap any admin page with <AdminGuard>...</AdminGuard>
 * - Shows a loading spinner while auth state is initializing
 * - Redirects non-admins to the home page
 * - Renders children only for verified admins
 */
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../app/contexts/AuthContext';

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || user.role !== 'admin')) {
      router.replace('/');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <main className="main-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '16px' }}>🔒</div>
          <p>Verifying access...</p>
        </div>
      </main>
    );
  }

  if (!user || user.role !== 'admin') {
    // Will redirect via useEffect — render nothing in the meantime
    return null;
  }

  return <>{children}</>;
}
