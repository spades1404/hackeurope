import React from 'react';

export const ProgressBar = ({ progress, color = 'var(--color-accent)' }) => {
    return (
        <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--color-bg-base)', borderRadius: '3px', overflow: 'hidden' }}>
            <div
                style={{
                    height: '100%',
                    backgroundColor: color,
                    width: `${Math.min(100, Math.max(0, progress))}%`,
                    transition: 'width 0.5s ease-out'
                }}
            />
        </div>
    );
};
