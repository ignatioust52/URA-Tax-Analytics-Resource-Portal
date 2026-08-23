import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement | HTMLAnchorElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  as?: 'button' | 'a';
  href?: string;
}

export function Button({ 
  children, 
  variant = 'primary', 
  size = 'md', 
  fullWidth = false,
  as = 'button',
  className = '',
  disabled,
  href,
  ...props 
}: ButtonProps) {
  
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '600',
    borderRadius: 'var(--radius-md)',
    cursor: disabled ? 'not-allowed' : 'pointer',
    border: '1px solid transparent',
    width: fullWidth ? '100%' : 'auto',
    opacity: disabled ? 0.6 : 1,
    outline: 'none',
  };

  const variants = {
    primary: {
      background: 'var(--ura-blue)',
      color: 'var(--text-inverse)',
      border: '1px solid var(--ura-blue)',
    },
    secondary: {
      background: 'var(--surface)',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-medium)',
    },
    danger: {
      background: 'var(--surface)',
      color: 'var(--error)',
      border: '1px solid var(--error)',
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-secondary)',
      border: '1px solid transparent',
    }
  };

  const sizes = {
    sm: { padding: '4px 12px', fontSize: '0.875rem' },
    md: { padding: '8px 16px', fontSize: '0.95rem' },
    lg: { padding: '12px 24px', fontSize: '1rem' },
  };

  // Hover states via style tag for simplicity without styled-components
  const [isHovered, setIsHovered] = React.useState(false);
  
  const getHoverStyle = () => {
    if (disabled || !isHovered) return {};
    switch (variant) {
      case 'primary': return { background: 'var(--ura-blue-hover)' };
      case 'secondary': return { background: 'var(--surface-hover)' };
      case 'danger': return { background: 'var(--error-bg)' };
      case 'ghost': return { background: 'var(--surface-hover)', color: 'var(--text-primary)' };
      default: return {};
    }
  };

  const commonProps = {
    style: {
      ...baseStyles,
      ...variants[variant],
      ...sizes[size],
      ...getHoverStyle(),
    },
    onMouseEnter: () => setIsHovered(true),
    onMouseLeave: () => setIsHovered(false),
    className,
    ...props
  };

  if (as === 'a') {
    return (
      <a href={href} {...commonProps as any}>
        {children}
      </a>
    );
  }

  return (
    <button
      disabled={disabled}
      {...commonProps as any}
    >
      {children}
    </button>
  );
}
