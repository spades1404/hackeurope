import React from 'react';

export const Table = ({ headers, data, renderRow, className = '' }) => {
    return (
        <div style={{ width: '100%', overflowX: 'auto' }} className={className}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)', color: 'var(--color-text-muted)', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        {headers.map((h, i) => (
                            <th key={i} style={{ padding: '12px 16px', fontWeight: '500' }}>{h}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, i) => React.cloneElement(renderRow(row, i), {
                        style: {
                            ...renderRow(row, i).props.style,
                            borderBottom: i === data.length - 1 ? 'none' : '1px solid var(--color-border)',
                            transition: 'background-color 0.15s ease',
                        }
                    }))}
                </tbody>
            </table>
        </div>
    );
};

export const TableRow = ({ children, isSelected, onClick, style = {}, ...props }) => {
    return (
        <tr
            onClick={onClick}
            style={{
                cursor: onClick ? 'pointer' : 'default',
                backgroundColor: isSelected ? 'var(--color-border)' : 'transparent',
                ...style
            }}
            onMouseEnter={(e) => {
                if (!isSelected && onClick) e.currentTarget.style.backgroundColor = 'var(--color-bg-surface)';
            }}
            onMouseLeave={(e) => {
                if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent';
            }}
            {...props}
        >
            {children}
        </tr>
    );
};

export const TableCell = ({ children, style = {}, right = false }) => {
    return (
        <td style={{ padding: '12px 16px', textAlign: right ? 'right' : 'left', ...style }}>
            {children}
        </td>
    );
};
