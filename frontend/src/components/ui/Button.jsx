import React from 'react';

export const Button = ({
    children,
    variant = 'primary',
    size = 'md',
    className = '',
    disabled = false,
    ...props
}) => {
    const baseStyles = {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '6px',
        fontWeight: '500',
        transition: 'all 0.15s ease',
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        fontFamily: 'var(--font-body)',
    };

    const variants = {
        primary: {
            backgroundColor: 'var(--color-accent)',
            color: '#fff',
            border: '1px solid var(--color-accent)',
        },
        secondary: {
            backgroundColor: 'transparent',
            color: 'var(--color-text-primary)',
            border: '1px solid var(--color-border)',
        },
        ghost: {
            backgroundColor: 'transparent',
            color: 'var(--color-text-muted)',
            border: '1px solid transparent',
        },
        danger: {
            backgroundColor: 'transparent',
            color: 'var(--color-error)',
            border: '1px solid var(--color-error)',
        }
    };

    const sizes = {
        sm: { padding: '6px 12px', fontSize: '13px' },
        md: { padding: '8px 16px', fontSize: '14px' },
        lg: { padding: '12px 24px', fontSize: '16px' },
    };

    const defaultHoverStyle = variant === 'primary'
        ? { filter: 'brightness(1.1)' }
        : variant === 'secondary'
            ? { backgroundColor: 'var(--color-border)' }
            : variant === 'ghost'
                ? { color: 'var(--color-text-primary)', backgroundColor: 'var(--color-bg-surface)' }
                : { backgroundColor: 'var(--color-error-glow)' };

    return (
        <button
            style={{ ...baseStyles, ...variants[variant], ...sizes[size] }}
            onMouseEnter={(e) => {
                if (!disabled) {
                    Object.assign(e.currentTarget.style, defaultHoverStyle);
                }
            }}
            onMouseLeave={(e) => {
                if (!disabled) {
                    e.currentTarget.style.filter = '';
                    e.currentTarget.style.backgroundColor = variants[variant].backgroundColor;
                    e.currentTarget.style.color = variants[variant].color;
                }
            }}
            disabled={disabled}
            className={className}
            {...props}
        >
            {children}
        </button>
    );
};
