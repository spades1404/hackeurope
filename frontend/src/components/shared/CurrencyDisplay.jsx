import React from 'react';

export const CurrencyDisplay = ({ amount, currency = 'USD', colorize = false }) => {
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });

    const isNegative = amount < 0;
    const formatted = formatter.format(Math.abs(amount));

    let color = 'inherit';
    if (colorize) {
        color = isNegative ? 'var(--color-error)' : 'var(--color-success)';
    }

    return (
        <span style={{
            fontFamily: 'var(--font-mono)',
            color: color,
            whiteSpace: 'nowrap'
        }}>
            {isNegative ? '-' : ''}{formatted}
        </span>
    );
};
