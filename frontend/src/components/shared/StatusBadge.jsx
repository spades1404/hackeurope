import React from 'react';

export const StatusBadge = ({ status, dot = false }) => {
    const config = {
        matched: { color: 'var(--color-success)', bg: 'var(--color-success-glow)', text: 'Matched' },
        approved: { color: 'var(--color-success)', bg: 'var(--color-success-glow)', text: 'Approved' },
        unmatched: { color: 'var(--color-warning)', bg: 'var(--color-warning-glow)', text: 'Unmatched' },
        generating: { color: 'var(--color-warning)', bg: 'var(--color-warning-glow)', text: 'Generating...' },
        discrepancy: { color: 'var(--color-error)', bg: 'var(--color-error-glow)', text: 'Discrepancy' },
        overdue: { color: 'var(--color-error)', bg: 'var(--color-error-glow)', text: 'Overdue' },
        draft_generated: { color: 'var(--color-info)', bg: 'var(--color-info-glow)', text: 'Draft ready' },
        submitted: { color: 'var(--color-info)', bg: 'var(--color-info-glow)', text: 'Submitted' },
        not_started: { color: 'var(--color-text-muted)', bg: 'transparent', text: 'Not started', border: '1px solid var(--color-border)' },
        connected: { color: 'var(--color-success)', bg: 'var(--color-success-glow)', text: 'Connected' },
        available: { color: 'var(--color-text-primary)', bg: 'var(--color-bg-surface)', text: 'Available', border: '1px solid var(--color-border)' },
        coming_soon: { color: 'var(--color-text-muted)', bg: 'transparent', text: 'Coming Soon' },
    };

    const styleConfig = config[status] || { color: 'var(--color-text-muted)', bg: 'var(--color-bg-surface)', text: status };

    return (
        <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 8px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            color: styleConfig.color,
            backgroundColor: styleConfig.bg,
            border: styleConfig.border || '1px solid transparent',
            whiteSpace: 'nowrap'
        }}>
            {dot && (
                <span style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    backgroundColor: styleConfig.color,
                    animation: status === 'unmatched' || status === 'generating' || status === 'overdue' ? 'pulse 2s infinite' : 'none'
                }} />
            )}
            {styleConfig.text}
            <style>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.4; }
          100% { opacity: 1; }
        }
      `}</style>
        </span>
    );
};
