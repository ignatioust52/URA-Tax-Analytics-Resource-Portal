import React from 'react';

export function Card({ children, className = '', style = {}, noPadding = false }: { children: React.ReactNode, className?: string, style?: React.CSSProperties, noPadding?: boolean }) {
  return (
    <div 
      className={`card ${className}`} 
      style={{
        background: 'var(--surface)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: '1px solid var(--border-light)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)',
        padding: noPadding ? '0' : 'var(--space-4)',
        overflow: 'hidden',
        ...style
      }}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }: { title: string, subtitle?: string, action?: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
      <div>
        <h3 style={{ margin: 0, fontSize: '1.125rem', color: 'var(--text-primary)' }}>{title}</h3>
        {subtitle && <p style={{ margin: '4px 0 0 0', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
