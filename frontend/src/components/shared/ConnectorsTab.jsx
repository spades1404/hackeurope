import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { StatusBadge } from './StatusBadge';
import { MOCK_CONNECTORS } from '../../data/mockData';
import { RefreshCw, Settings, Unlink, Plus } from 'lucide-react';

export const ConnectorsTab = () => {
    const [connectors, setConnectors] = useState(MOCK_CONNECTORS);

    const handleConnect = (id) => {
        setConnectors(prev => prev.map(c => {
            if (c.id === id) {
                return { ...c, status: 'connected', accountInfo: 'Connecting...', stats: '0 records', lastSync: 'Just now' };
            }
            return c;
        }));

        // Simulate connection flow
        setTimeout(() => {
            setConnectors(prev => prev.map(c => {
                if (c.id === id) {
                    return { ...c, accountInfo: 'demo@user.com', stats: 'Ready to sync' };
                }
                return c;
            }));
        }, 1500);
    };

    const handleDisconnect = (id) => {
        setConnectors(prev => prev.map(c => {
            if (c.id === id) {
                const { accountInfo, lastSync, stats, ...rest } = c;
                return { ...rest, status: 'available' };
            }
            return c;
        }));
    };

    const renderConnector = (c) => {
        const isConnected = c.status === 'connected';
        const isAvailable = c.status === 'available';

        return (
            <Card
                key={c.id}
                style={{
                    borderColor: isConnected ? 'var(--color-success)' : 'var(--color-border)',
                    opacity: c.status === 'coming_soon' ? 0.5 : 1,
                    display: 'flex',
                    flexDirection: 'column',
                    height: '100%',
                }}
                noPadding
            >
                <div style={{ padding: '20px', flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ fontSize: '24px' }}>{c.icon}</span>
                            <h3 style={{ fontSize: '18px', margin: 0 }}>{c.name}</h3>
                        </div>
                        <StatusBadge status={c.status} />
                    </div>

                    <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', marginBottom: '16px' }}>
                        {c.description}
                    </p>

                    {isConnected && (
                        <div style={{ fontSize: '13px', color: 'var(--color-text-dim)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <div><span style={{ color: 'var(--color-text-muted)' }}>Account:</span> {c.accountInfo}</div>
                            {c.lastSync && <div><span style={{ color: 'var(--color-text-muted)' }}>Last sync:</span> {c.lastSync}</div>}
                            {c.stats && <div><span style={{ color: 'var(--color-text-muted)' }}>Stats:</span> {c.stats}</div>}
                        </div>
                    )}
                </div>

                <div style={{ padding: '16px 20px', borderTop: '1px solid var(--color-border)', marginTop: 'auto', display: 'flex', gap: '8px' }}>
                    {isConnected ? (
                        <>
                            <Button size="sm" variant="secondary" style={{ flex: 1 }}><RefreshCw size={14} style={{ marginRight: '6px' }} /> Sync</Button>
                            <Button size="sm" variant="secondary"><Settings size={14} /></Button>
                            <Button size="sm" variant="danger" onClick={() => handleDisconnect(c.id)}><Unlink size={14} /></Button>
                        </>
                    ) : isAvailable ? (
                        <Button size="sm" variant="primary" style={{ width: '100%' }} onClick={() => handleConnect(c.id)}>
                            <Plus size={16} style={{ marginRight: '6px' }} /> Connect
                        </Button>
                    ) : (
                        <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', textAlign: 'center', width: '100%', fontWeight: '500' }}>
                            Coming {c.availableDate}
                        </div>
                    )}
                </div>
            </Card>
        );
    };

    const connected = connectors.filter(c => c.status === 'connected');
    const available = connectors.filter(c => c.status === 'available');
    const comingSoon = connectors.filter(c => c.status === 'coming_soon');

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', animation: 'fadeIn 0.5s ease-out' }}>
            <div>
                <h2 style={{ fontSize: '20px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    Connected ({connected.length})
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {connected.map(renderConnector)}
                </div>
            </div>

            <div>
                <h2 style={{ fontSize: '20px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    Available ({available.length})
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {available.map(renderConnector)}
                </div>
            </div>

            {comingSoon.length > 0 && (
                <div>
                    <h2 style={{ fontSize: '20px', marginBottom: '16px', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        Coming Soon
                    </h2>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                        {comingSoon.map(renderConnector)}
                    </div>
                </div>
            )}
            <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </div>
    );
};
