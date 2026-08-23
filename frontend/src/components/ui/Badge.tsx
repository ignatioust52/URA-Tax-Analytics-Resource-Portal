import React from 'react';

export function Badge({ children, variant = 'neutral' }: { children: React.ReactNode, variant?: 'success' | 'error' | 'warning' | 'info' | 'neutral' }) {
  const variants = {
    success: { background: 'var(--success-bg)', color: 'var(--success)' },
    error: { background: 'var(--error-bg)', color: 'var(--error)' },
    warning: { background: 'var(--warning-bg)', color: 'var(--warning)' },
    info: { background: 'var(--ura-blue-light)', color: 'var(--ura-blue)' },
    neutral: { background: 'var(--surface-hover)', color: 'var(--text-secondary)' },
  };

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '2px 8px',
      borderRadius: 'var(--radius-full)',
      fontSize: '0.75rem',
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      ...variants[variant]
    }}>
      {children}
    </span>
  );
}
