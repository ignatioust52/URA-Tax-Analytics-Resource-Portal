import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

export function Input({ label, error, fullWidth = true, className = '', style = {}, type = 'text', ...props }: InputProps) {
  const [showPassword, setShowPassword] = React.useState(false);
  const isPasswordInput = type === 'password';
  const currentType = isPasswordInput ? (showPassword ? 'text' : 'password') : type;

  return (
    <div style={{ width: fullWidth ? '100%' : 'auto', marginBottom: 'var(--space-3)' }}>
      {label && <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', color: 'var(--text-primary)' }}>{label}</label>}
      <div style={{ position: 'relative' }}>
        <input
          type={currentType}
          className={className}
          style={{
            width: '100%',
            padding: '10px 12px',
            paddingRight: isPasswordInput ? '40px' : '12px',
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
        {isPasswordInput && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            style={{
              position: 'absolute',
              right: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '4px'
            }}
            title={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            )}
          </button>
        )}
      </div>
      {error && <span style={{ color: 'var(--error)', fontSize: '0.8rem', marginTop: '4px', display: 'block' }}>{error}</span>}
    </div>
  );
}
