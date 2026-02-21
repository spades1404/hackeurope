import React from 'react';

export const Card = ({ children, className = '', noPadding = false, ...props }) => {
    return (
        <div
            className={`bg-[var(--color-bg-surface)] border border-[var(--color-border)] rounded-xl transition-colors duration-200 hover:border-[var(--color-border-hover)] hover:-translate-y-[1px] ${noPadding ? '' : 'p-5'} ${className}`}
            style={{
                backgroundColor: 'var(--color-bg-surface)',
                borderColor: 'var(--color-border)',
                borderRadius: '12px',
                borderWidth: '1px',
                borderStyle: 'solid',
                transition: 'all 0.2s ease-in-out',
                ...(noPadding ? {} : { padding: '20px' }),
            }}
            {...props}
        >
            {children}
        </div>
    );
};
