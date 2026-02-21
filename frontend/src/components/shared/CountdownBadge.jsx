import React from 'react';

export const CountdownBadge = ({ daysRemaining, priority }) => {
    let text = '';
    let color = '';
    let bg = '';

    if (daysRemaining < 0) {
        text = `${Math.abs(daysRemaining)} days overdue`;
        color = 'var(--color-error)';
        bg = 'var(--color-error-glow)';
    } else if (daysRemaining === 0) {
        text = 'Due today';
        color = 'var(--color-error)';
        bg = 'var(--color-error-glow)';
    } else {
        text = `${daysRemaining} days remaining`;
        if (priority === 'high' || daysRemaining <= 30) {
            color = 'var(--color-warning)';
            bg = 'var(--color-warning-glow)';
        } else if (priority === 'medium') {
            color = 'var(--color-info)';
            bg = 'var(--color-info-glow)';
        } else {
            color = 'var(--color-text-muted)';
            bg = 'var(--color-bg-surface)';
        }
    }

    return (
        <span style={{
            display: 'inline-flex',
            alignItems: 'center',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            fontWeight: '500',
            color: color,
            backgroundColor: bg,
        }}>
            {daysRemaining < 0 && '🔴 '}
            {daysRemaining >= 0 && daysRemaining <= 30 && '⚠️ '}
            {daysRemaining > 30 && priority === 'medium' && '🔵 '}
            {text}
        </span>
    );
};
