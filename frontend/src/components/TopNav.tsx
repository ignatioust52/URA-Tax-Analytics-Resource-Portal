"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../app/contexts/AuthContext';

export function TopNav() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();

  const navLinks = [
    { name: 'Public Resources', path: '/resources' }
  ];

  if (user?.role?.toLowerCase() === 'admin') {
    navLinks.push({ name: 'User Management', path: '/users' });
    navLinks.push({ name: 'Analytics', path: '/analytics' });
    navLinks.push({ name: 'Governance', path: '/governance' });
    navLinks.push({ name: 'Announcements', path: '/announcements' });
    navLinks.push({ name: 'AI Assistant', path: '/chat' });
  }

  // The login page shouldn't show the full nav
  if (pathname === '/login') return null;

  return (
    <div style={{ width: '100%' }}>
      {/* Top Header */}
      <div className="top-nav-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem 2rem', background: '#243F8D', color: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: '36px', height: '36px', background: 'gold', borderRadius: '50%' }}></div> {/* Placeholder logo */}
          <div className="top-nav-brand-text" style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '1.2rem', fontWeight: 700 }}>Uganda Revenue Authority</span>
            <span style={{ fontSize: '0.75rem', letterSpacing: '0.05em', color: '#CBD5E1' }}>DEVELOPING UGANDA TOGETHER · REVENUE DASHBOARD</span>
          </div>
        </div>
        <div>
          <span className="ura-live-badge" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.1)', padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.85rem' }}>
            <span className="ura-live-dot" style={{ width: '8px', height: '8px', background: '#10B981', borderRadius: '50%' }}></span>
            Live report
          </span>
        </div>
      </div>

      {/* Signature Triband Divider */}
      <div className="ura-stripe" style={{ height: '4px', background: 'linear-gradient(to right, #B54834 33%, #FFF200 33%, #FFF200 66%, #1C2430 66%)' }}></div>

      {/* Tabs / Auth Strip */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 2rem', background: '#1A2E66', borderBottom: '1px solid #1C2430' }}>
        <div style={{ display: 'flex', gap: '1rem' }}>
          {navLinks.map((link) => {
            const isActive = pathname === link.path || (pathname === '/' && link.path === '/resources');
            return (
              <Link 
                key={link.path} 
                href={link.path}
                style={{
                  padding: '1rem',
                  color: 'white',
                  textDecoration: 'none',
                  fontWeight: 600,
                  borderBottom: isActive ? '3px solid #FFF200' : '3px solid transparent',
                  opacity: isActive ? 1 : 0.8
                }}
              >
                {link.name}
              </Link>
            );
          })}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          {!loading && user ? (
            <>
              <div style={{ color: 'white', fontSize: '0.9rem', textAlign: 'right' }}>
                <div>{user.email}</div>
                <div style={{ color: '#CBD5E1', fontSize: '0.8rem' }}>{user.role} • {user.department || 'All'}</div>
              </div>
              <button onClick={logout} className="btn-secondary" style={{ padding: '0.5rem 1rem', background: 'transparent', border: '1px solid white', color: 'white', borderRadius: '4px', cursor: 'pointer' }}>
                Log out
              </button>
            </>
          ) : !loading && !user ? (
            <>
              <div style={{ color: 'white', fontSize: '0.9rem', textAlign: 'right' }}>
                <div>Public Visitor</div>
                <div style={{ color: '#CBD5E1', fontSize: '0.8rem' }}>Unauthenticated</div>
              </div>
              <Link href="/login" className="btn-primary" style={{ padding: '0.5rem 1rem', background: '#FFF200', color: '#1C2430', border: 'none', borderRadius: '4px', textDecoration: 'none', fontWeight: 600 }}>
                Log In
              </Link>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
