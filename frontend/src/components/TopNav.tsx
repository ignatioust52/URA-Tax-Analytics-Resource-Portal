"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../app/contexts/AuthContext';

export function TopNav() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const [departments, setDepartments] = useState<any[]>([]);

  useEffect(() => {
    if (user && user.id) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/departments`, {
        credentials: 'include'
      })
      .then(res => res.ok ? res.json() : [])
      .then(data => setDepartments(Array.isArray(data) ? data : []))
      .catch(() => {});
    }
  }, [user]);

  const handleSwitchDepartment = async (deptId: number) => {
    if (deptId === user?.active_department_id) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/select-department`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ department_id: deptId }),
      });
      if (res.ok) {
        window.location.reload();
      }
    } catch (e) {
      console.error('Failed to switch department');
    }
  };

  const navLinks = [
    { name: 'Public Resources', path: '/resources' }
  ];

  if (user?.role?.toLowerCase() === 'admin' || user?.role?.toLowerCase() === 'super administrator' || user?.role?.toLowerCase() === 'system administrator') {
    navLinks.push({ name: 'User Management', path: '/users' });
    navLinks.push({ name: 'Analytics', path: '/analytics' });
    navLinks.push({ name: 'Governance', path: '/governance' });
    navLinks.push({ name: 'Announcements', path: '/announcements' });
    navLinks.push({ name: 'AI Assistant', path: '/chat' });
  }

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // The login page shouldn't show the full nav
  if (pathname === '/login') return null;

  return (
    <div style={{ width: '100%' }}>
      {/* Top Header */}
      <div className="top-nav-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: '#243F8D', color: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <img src="/logo.png" alt="URA Logo" style={{ height: '40px', width: 'auto' }} />
          <div className="top-nav-brand-text hidden-mobile" style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 'clamp(1rem, 4vw, 1.2rem)', fontWeight: 700 }}>Uganda Revenue Authority</span>
            <span style={{ fontSize: 'clamp(0.6rem, 2vw, 0.75rem)', letterSpacing: '0.05em', color: '#CBD5E1' }}>DEVELOPING UGANDA TOGETHER · REVENUE DASHBOARD</span>
          </div>
          <div className="hidden-desktop" style={{ fontWeight: 700, fontSize: '1.2rem' }}>
            URA GO
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span className="ura-live-badge hidden-mobile" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.1)', padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.85rem' }}>
            <span className="ura-live-dot" style={{ width: '8px', height: '8px', background: '#10B981', borderRadius: '50%' }}></span>
            Live report
          </span>
          
          {user && (
            <button 
              className="hidden-desktop" 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '1.5rem', padding: '0.5rem' }}
            >
              ☰
            </button>
          )}
        </div>
      </div>

      {user && (
        <>
          {/* Signature Triband Divider */}
          <div className="ura-stripe" style={{ height: '4px', background: 'linear-gradient(to right, #B54834 33%, #FFF200 33%, #FFF200 66%, #1C2430 66%)' }}></div>

          {/* Desktop Tabs / Auth Strip */}
          <div className="hidden-mobile" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 1rem', background: '#1A2E66', borderBottom: '1px solid #1C2430' }}>
            <div style={{ display: 'flex', gap: '0.5rem', padding: '0.5rem 0' }}>
              {navLinks.map((link) => {
                const isActive = pathname === link.path || (pathname === '/' && link.path === '/resources');
                return (
                  <Link 
                    key={link.path} 
                    href={link.path}
                    style={{
                      padding: '0.5rem 1rem',
                      color: 'white',
                      textDecoration: 'none',
                      fontWeight: 600,
                      borderBottom: isActive ? '3px solid #FFF200' : '3px solid transparent',
                      opacity: isActive ? 1 : 0.8,
                      fontSize: '1rem'
                    }}
                  >
                    {link.name}
                  </Link>
                );
              })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingBottom: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {departments.length > 1 && (
                  <select 
                    value={user.active_department_id || ''}
                    onChange={(e) => handleSwitchDepartment(Number(e.target.value))}
                    style={{
                      background: 'rgba(255,255,255,0.1)',
                      color: 'white',
                      border: '1px solid rgba(255,255,255,0.2)',
                      borderRadius: '4px',
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.8rem',
                      outline: 'none'
                    }}
                  >
                    <option value="" disabled>Switch Department</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.id} style={{ color: 'black' }}>{d.name}</option>
                    ))}
                  </select>
                )}
                
                <div style={{ color: 'white', fontSize: '0.9rem', textAlign: 'right' }}>
                  <div>{user.email}</div>
                  <div style={{ color: '#CBD5E1', fontSize: '0.75rem' }}>
                    {user.role} 
                    {departments.length <= 1 && user.department ? ` • ${user.department}` : ''}
                  </div>
                </div>
              </div>
              <button onClick={logout} className="btn-secondary" style={{ padding: '0.5rem 1rem', background: 'transparent', border: '1px solid white', color: 'white', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}>
                Log out
              </button>
            </div>
          </div>

          {/* Mobile Drawer Overlay */}
          {mobileMenuOpen && (
            <div 
              className="hidden-desktop"
              style={{
                position: 'fixed',
                top: '72px', /* Height of the header */
                left: 0,
                right: 0,
                bottom: 0,
                background: 'rgba(0,0,0,0.5)',
                zIndex: 1000
              }}
              onClick={() => setMobileMenuOpen(false)}
            >
              {/* Drawer */}
              <div 
                style={{
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  bottom: 0,
                  width: '80%',
                  maxWidth: '300px',
                  background: '#1A2E66',
                  color: 'white',
                  display: 'flex',
                  flexDirection: 'column',
                  boxShadow: '-4px 0 15px rgba(0,0,0,0.3)',
                  padding: '1rem',
                  overflowY: 'auto'
                }}
                onClick={e => e.stopPropagation()}
              >
                <div style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', marginBottom: '1rem' }}>
                  <div style={{ fontWeight: 600 }}>{user.email}</div>
                  <div style={{ color: '#CBD5E1', fontSize: '0.8rem' }}>{user.role}</div>
                </div>

                {departments.length > 1 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{ fontSize: '0.8rem', color: '#CBD5E1', marginBottom: '0.5rem' }}>Department</div>
                    <select 
                      value={user.active_department_id || ''}
                      onChange={(e) => {
                        handleSwitchDepartment(Number(e.target.value));
                        setMobileMenuOpen(false);
                      }}
                      style={{
                        width: '100%',
                        background: 'rgba(255,255,255,0.1)',
                        color: 'white',
                        border: '1px solid rgba(255,255,255,0.2)',
                        borderRadius: '4px',
                        padding: '0.75rem',
                        fontSize: '0.9rem',
                        outline: 'none'
                      }}
                    >
                      <option value="" disabled>Switch Department</option>
                      {departments.map(d => (
                        <option key={d.id} value={d.id} style={{ color: 'black' }}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flexGrow: 1 }}>
                  <div style={{ fontSize: '0.8rem', color: '#CBD5E1', textTransform: 'uppercase', marginBottom: '0.5rem' }}>Navigation</div>
                  {navLinks.map((link) => {
                    const isActive = pathname === link.path || (pathname === '/' && link.path === '/resources');
                    return (
                      <Link 
                        key={link.path} 
                        href={link.path}
                        onClick={() => setMobileMenuOpen(false)}
                        style={{
                          padding: '0.75rem 1rem',
                          background: isActive ? 'rgba(255,242,0,0.1)' : 'transparent',
                          color: isActive ? '#FFF200' : 'white',
                          borderRadius: '4px',
                          textDecoration: 'none',
                          fontWeight: isActive ? 600 : 400,
                          borderLeft: isActive ? '3px solid #FFF200' : '3px solid transparent'
                        }}
                      >
                        {link.name}
                      </Link>
                    );
                  })}
                </div>

                <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                  <button onClick={logout} style={{ width: '100%', padding: '0.75rem', background: 'transparent', border: '1px solid white', color: 'white', borderRadius: '4px', fontSize: '0.9rem', cursor: 'pointer' }}>
                    Log out
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
