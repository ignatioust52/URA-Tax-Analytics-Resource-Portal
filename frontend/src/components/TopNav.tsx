"use client";

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '../app/contexts/AuthContext';

export function TopNav() {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const [departments, setDepartments] = useState<any[]>([]);
  const [announcements, setAnnouncements] = useState<any[]>([]);

  useEffect(() => {
    if (user && user.id) {
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/departments`, {
        credentials: 'include'
      })
      .then(res => res.ok ? res.json() : [])
      .then(data => setDepartments(Array.isArray(data) ? data : []))
      .catch(() => {});

      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/announcements/active`, {
        credentials: 'include'
      })
      .then(res => res.ok ? res.json() : [])
      .then(data => setAnnouncements(Array.isArray(data) ? data : []))
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
    <div style={{ width: '100%', position: 'sticky', top: 0, zIndex: 100 }}>
      {/* Global Announcements Banner */}
      {announcements.length > 0 && (
        <div style={{ width: '100%', background: '#FFF200', color: '#1C2430', padding: '0.5rem 1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          {announcements.map((ann, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', fontSize: '0.9rem', textAlign: 'center' }}>
              <span style={{ fontWeight: 700, textTransform: 'uppercase', background: '#1C2430', color: '#FFF200', padding: '2px 8px', borderRadius: '4px', fontSize: '0.75rem' }}>{ann.title}</span>
              <span style={{ fontWeight: 500 }}>{ann.body}</span>
            </div>
          ))}
        </div>
      )}

      {/* Desktop Header */}
      <div className="top-nav-header hidden-mobile" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', background: 'rgba(36, 63, 141, 0.85)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', color: 'white' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <img src="/logo.png" alt="URA Logo" style={{ height: '40px', width: 'auto' }} />
          <div className="top-nav-brand-text" style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: 'clamp(1rem, 4vw, 1.2rem)', fontWeight: 700 }}>Uganda Revenue Authority</span>
            <span style={{ fontSize: 'clamp(0.6rem, 2vw, 0.75rem)', letterSpacing: '0.05em', color: '#CBD5E1' }}>DEVELOPING UGANDA TOGETHER · REVENUE DASHBOARD</span>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span className="ura-live-badge" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.1)', padding: '0.25rem 0.75rem', borderRadius: '1rem', fontSize: '0.85rem' }}>
            <span className="ura-live-dot" style={{ width: '8px', height: '8px', background: '#10B981', borderRadius: '50%' }}></span>
            Live report
          </span>
        </div>
      </div>

      {/* Mobile Header (Refined Grid Layout) */}
      <div className="top-nav-header hidden-desktop" style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', padding: '0.75rem 1rem', background: 'rgba(36, 63, 141, 0.95)', color: 'white', position: 'relative' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifySelf: 'start' }}>
          <img src="/logo.png" alt="URA Logo" style={{ height: '32px', width: 'auto' }} />
        </div>
        
        <div style={{ fontWeight: 700, fontSize: '1.1rem', justifySelf: 'center', letterSpacing: '0.02em' }}>
          URA GO
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', justifySelf: 'end' }}>
          {user && (
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '1.4rem', padding: '0.25rem 0.5rem', cursor: 'pointer' }}
              aria-label="Menu"
            >
              ⋮
            </button>
          )}
        </div>

        {/* Mobile Dropdown Menu Overlay & Dropdown */}
        {mobileMenuOpen && user && (
          <>
            <div 
              onClick={() => setMobileMenuOpen(false)}
              style={{ position: 'fixed', inset: 0, zIndex: 999 }}
            />
            <div 
              style={{
                position: 'absolute',
                top: '100%',
                right: '1rem',
                marginTop: '0.5rem',
                width: '260px',
                background: '#1A2E66',
                color: 'white',
                display: 'flex',
                flexDirection: 'column',
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                zIndex: 1000
              }}
              onClick={e => e.stopPropagation()}
            >
              <div style={{ padding: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.1)' }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>{user.email}</div>
                <div style={{ color: '#CBD5E1', fontSize: '0.75rem', textTransform: 'uppercase' }}>{user.role}</div>
              </div>

              {departments.length > 1 && (
                <div style={{ padding: '0.75rem 1rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
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
                      padding: '0.5rem',
                      fontSize: '0.85rem',
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

              <div style={{ display: 'flex', flexDirection: 'column' }}>
                {navLinks.map((link) => {
                  const isActive = pathname === link.path || (pathname === '/' && link.path === '/resources');
                  return (
                    <Link 
                      key={link.path} 
                      href={link.path}
                      onClick={() => setMobileMenuOpen(false)}
                      style={{
                        padding: '1rem',
                        background: isActive ? 'rgba(255,242,0,0.1)' : 'transparent',
                        color: isActive ? '#FFF200' : 'white',
                        textDecoration: 'none',
                        fontWeight: isActive ? 600 : 400,
                        borderLeft: isActive ? '3px solid #FFF200' : '3px solid transparent',
                        fontSize: '0.95rem',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                    >
                      {link.name}
                    </Link>
                  );
                })}
              </div>

              <div style={{ padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.2)' }}>
                <button onClick={logout} style={{ width: '100%', padding: '0.75rem', background: 'transparent', border: '1px solid rgba(255,255,255,0.3)', color: 'white', borderRadius: '4px', fontSize: '0.9rem', cursor: 'pointer', transition: 'background 0.2s' }}>
                  Log out
                </button>
              </div>
            </div>
          </>
        )}
      </div>


      {user && (
        <>
          {/* Signature Triband Divider */}
          <div className="ura-stripe" style={{ height: '4px', background: 'linear-gradient(to right, #B54834 33%, #FFF200 33%, #FFF200 66%, #1C2430 66%)' }}></div>

          {/* Desktop Tabs / Auth Strip */}
          <div className="hidden-mobile" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 1rem', background: 'rgba(26, 46, 102, 0.85)', backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
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
              <button onClick={logout} className="hidden-mobile btn-secondary" style={{ padding: '0.5rem 1rem', background: 'transparent', border: '1px solid white', color: 'white', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem', marginLeft: '1rem' }}>
                Log out
              </button>
            </div>
          </div>

          {/* Drawer overlay removed from bottom since it is now part of the mobile header dropdown */}

        </>
      )}
    </div>
  );
}
