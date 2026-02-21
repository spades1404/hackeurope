import React from 'react';
import { Bell, Search } from 'lucide-react';
import { useAppContext } from '../../contexts/AppContext';
import { useLocation } from 'react-router-dom';

export const TopBar = () => {
    const { role } = useAppContext();
    const location = useLocation();

    let title = 'Dashboard';
    if (role === 'business' && location.pathname === '/') title = 'Overview';
    if (location.pathname === '/compliance') title = 'Compliance';
    if (location.pathname === '/connectors') title = 'Connectors';

    return (
        <div style={{
            height: '72px',
            padding: '0 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid var(--color-border)',
            backgroundColor: 'rgba(11, 15, 26, 0.8)',
            backdropFilter: 'blur(12px)',
            position: 'sticky',
            top: 0,
            zIndex: 10
        }}>
            <h1 style={{ fontSize: '24px', fontWeight: '700', margin: 0 }}>{title}</h1>

            <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                <div style={{ position: 'relative' }}>
                    <Search size={16} color="var(--color-text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                        type="text"
                        placeholder="Search..."
                        style={{
                            backgroundColor: 'var(--color-bg-surface)',
                            border: '1px solid var(--color-border)',
                            borderRadius: '8px',
                            padding: '8px 16px 8px 36px',
                            color: 'var(--color-text-primary)',
                            fontSize: '14px',
                            width: '240px',
                            outline: 'none',
                            transition: 'border-color 0.2s',
                            fontFamily: 'var(--font-body)'
                        }}
                        onFocus={e => e.target.style.borderColor = 'var(--color-accent)'}
                        onBlur={e => e.target.style.borderColor = 'var(--color-border)'}
                    />
                </div>

                <button style={{ position: 'relative', color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}
                    onMouseEnter={e => e.currentTarget.style.color = 'var(--color-text-primary)'}
                    onMouseLeave={e => e.currentTarget.style.color = 'var(--color-text-muted)'}
                >
                    <Bell size={20} />
                    <span style={{
                        position: 'absolute', top: '-2px', right: '-4px',
                        width: '8px', height: '8px', borderRadius: '50%',
                        backgroundColor: 'var(--color-error)'
                    }} />
                </button>

                <div style={{
                    padding: '6px 12px',
                    borderRadius: '20px',
                    backgroundColor: role === 'worker' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                    border: `1px solid ${role === 'worker' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`,
                    color: role === 'worker' ? 'var(--color-accent)' : 'var(--color-success)',
                    fontSize: '13px',
                    fontWeight: '600'
                }}>
                    {role === 'worker' ? 'Accountant Mode' : 'Client Mode'}
                </div>
            </div>
        </div>
    );
};
