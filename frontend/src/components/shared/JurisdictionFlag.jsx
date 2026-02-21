import React from 'react';

const FLAGS = {
    'US': '🇺🇸',
    'UK': '🇬🇧',
    'DE': '🇩🇪',
    'AU': '🇦🇺'
};

const DOT_COLORS = {
    'US': 'var(--color-accent)', // Blue
    'UK': 'var(--color-error)',  // Red
    'DE': 'var(--color-warning)',// Amber
    'AU': 'var(--color-success)' // Green
};

export const JurisdictionFlag = ({ jurisdiction, showName = false, showDot = false }) => {
    const flag = FLAGS[jurisdiction] || '🌐';

    return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            {showDot && (
                <span style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: DOT_COLORS[jurisdiction] || 'var(--color-text-muted)',
                    display: 'inline-block'
                }} />
            )}
            <span style={{ fontSize: '16px', lineHeight: '1' }}>{flag}</span>
            {showName && <span style={{ fontWeight: '500' }}>{jurisdiction}</span>}
        </span>
    );
};
