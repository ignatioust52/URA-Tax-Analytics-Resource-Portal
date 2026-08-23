import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export function Input({ label, error, fullWidth = true, className = '', style = {}, ...props }: InputProps) {
  return (
    <div style={{ width: fullWidth ? '100%' : 'auto', marginBottom: 'var(--space-3)' }}>
      {label && <label>{label}</label>}
      <input
        className={className}
        style={{
          width: '100%',
          padding: '10px 12px',
          borderRadius: 'var(--radius-md)',
          border: `1px solid ${error ? 'var(--error)' : 'var(--border-medium)'}`,
          background: 'var(--surface)',
          color: 'var(--text-primary)',
          fontSize: '0.95rem',
          outline: 'none',
          transition: 'border-color 0.2s',
          ...style
        }}
        onFocus={(e) => {
          if (!error) e.currentTarget.style.borderColor = 'var(--ura-blue)';
        }}
        onBlur={(e) => {
          if (!error) e.currentTarget.style.borderColor = 'var(--border-medium)';
        }}
        {...props}
      />
      {error && <span style={{ color: 'var(--error)', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>{error}</span>}
    </div>
  );
}
