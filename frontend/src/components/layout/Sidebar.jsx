import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileCheck2, Plug, MessageSquare, Briefcase, Building2 } from 'lucide-react';
import { useAppContext } from '../../contexts/AppContext';

export const Sidebar = ({ onOpenChat }) => {
    const { role, toggleRole, company } = useAppContext();

    const workerLinks = [
        { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
        { to: '/compliance', icon: <FileCheck2 size={20} />, label: 'Compliance' },
        { to: '/connectors', icon: <Plug size={20} />, label: 'Connectors' }
    ];

    const businessLinks = [
        { to: '/', icon: <LayoutDashboard size={20} />, label: 'Overview' },
        { to: '/compliance', icon: <FileCheck2 size={20} />, label: 'Compliance' },
        { to: '/connectors', icon: <Plug size={20} />, label: 'Connectors' }
    ];

    const links = role === 'worker' ? workerLinks : businessLinks;

    return (
        <div style={{
            width: '240px',
            height: '100vh',
            backgroundColor: 'var(--color-bg-sidebar)',
            borderRight: '1px solid var(--color-border)',
            display: 'flex',
            flexDirection: 'column',
            padding: '24px 16px',
            position: 'fixed',
            left: 0,
            top: 0,
            zIndex: 20
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 8px', marginBottom: '40px' }}>
                <div style={{ width: '32px', height: '32px', backgroundColor: 'var(--color-accent)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Briefcase size={18} color="#fff" />
                </div>
                <span style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: '700', letterSpacing: '-0.5px' }}>TunaTax</span>
            </div>

            <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {links.map(link => (
                    <NavLink
                        key={link.to}
                        to={link.to}
                        style={({ isActive }) => ({
                            display: 'flex', alignItems: 'center', gap: '12px',
                            padding: '10px 12px', borderRadius: '8px',
                            color: isActive ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
                            backgroundColor: isActive ? 'var(--color-bg-surface)' : 'transparent',
                            fontWeight: isActive ? '600' : '500',
                            transition: 'all 0.2s'
                        })}
                    >
                        {link.icon}
                        {link.label}
                    </NavLink>
                ))}

                <button
                    onClick={onOpenChat}
                    style={{
                        display: 'flex', alignItems: 'center', gap: '12px',
                        padding: '10px 12px', borderRadius: '8px',
                        color: 'var(--color-text-muted)',
                        backgroundColor: 'transparent',
                        fontWeight: '500',
                        transition: 'all 0.2s',
                        textAlign: 'left',
                        marginTop: '8px'
                    }}
                    onMouseEnter={e => { e.currentTarget.style.color = 'var(--color-text-primary)'; e.currentTarget.style.backgroundColor = 'var(--color-bg-surface)'; }}
                    onMouseLeave={e => { e.currentTarget.style.color = 'var(--color-text-muted)'; e.currentTarget.style.backgroundColor = 'transparent'; }}
                >
                    <MessageSquare size={20} />
                    Chat
                </button>
            </nav>

            <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <button
                    onClick={toggleRole}
                    style={{
                        display: 'flex', alignItems: 'center', padding: '4px',
                        backgroundColor: 'var(--color-bg-surface)', borderRadius: '24px',
                        border: '1px solid var(--color-border)', cursor: 'pointer',
                        position: 'relative'
                    }}
                >
                    <div style={{
                        position: 'absolute',
                        width: '50%', height: 'calc(100% - 8px)',
                        backgroundColor: 'var(--color-accent)',
                        borderRadius: '20px',
                        left: role === 'worker' ? '4px' : 'calc(50% - 4px)',
                        transition: 'left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        zIndex: 1
                    }} />
                    <div style={{ flex: 1, textAlign: 'center', fontSize: '12px', fontWeight: '600', padding: '6px 0', zIndex: 2, color: role === 'worker' ? '#fff' : 'var(--color-text-muted)', transition: 'color 0.3s' }}>
                        Worker
                    </div>
                    <div style={{ flex: 1, textAlign: 'center', fontSize: '12px', fontWeight: '600', padding: '6px 0', zIndex: 2, color: role === 'business' ? '#fff' : 'var(--color-text-muted)', transition: 'color 0.3s' }}>
                        Business
                    </div>
                </button>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 8px', borderTop: '1px solid var(--color-border)' }}>
                    <div style={{ width: '36px', height: '36px', backgroundColor: 'var(--color-bg-surface)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--color-border)' }}>
                        <Building2 size={18} color="var(--color-accent)" />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-primary)' }}>{company.name}</span>
                        <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{role === 'worker' ? 'Accountant View' : 'Client View'}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
