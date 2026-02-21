import React from 'react';
import { Card } from '../ui/Card';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';
import { MOCK_FINANCIALS } from '../../data/mockData';

// Placeholder simplified paths for demo purposes
// In a real app, you would use accurate SVG definitions or topojson.
const SVGS = {
    'US': 'M20,60 Q40,50 80,40 Q150,30 220,50 Q260,80 230,120 Q180,150 120,130 Q60,110 20,60 Z', // blob vaguely US shaped
    'UK': 'M40,140 Q50,110 45,80 Q50,50 80,40 Q100,60 90,90 Q80,120 100,150 Q70,160 40,140 Z', // blob vaguely UK shaped
    'DE': 'M80,30 Q120,30 140,50 Q150,80 130,110 Q90,130 60,110 Q40,80 80,30 Z', // blob vaguely DE shaped
    'AU': 'M100,50 Q160,50 190,80 Q200,120 180,150 Q120,180 80,150 Q50,120 100,50 Z' // blob vaguely AU shaped
};

const STATS_MOCK = {
    'US': { txns: 42, vol: 142000, curr: 'USD', status: 'discrepancy' },
    'UK': { txns: 18, vol: 62000, curr: 'GBP', status: 'unmatched' },
    'DE': { txns: 12, vol: 89000, curr: 'EUR', status: 'matched' },
    'AU': { txns: 8, vol: 28000, curr: 'AUD', status: 'matched' }
};

const DOT_COLORS = {
    matched: 'var(--color-success)',
    unmatched: 'var(--color-warning)',
    discrepancy: 'var(--color-error)'
};

const FILL_COLORS = {
    'US': 'rgba(59, 130, 246, 0.15)',
    'UK': 'rgba(239, 68, 68, 0.15)',
    'DE': 'rgba(245, 158, 11, 0.15)',
    'AU': 'rgba(16, 185, 129, 0.15)'
};
const HOVER_COLORS = {
    'US': 'rgba(59, 130, 246, 0.3)',
    'UK': 'rgba(239, 68, 68, 0.3)',
    'DE': 'rgba(245, 158, 11, 0.3)',
    'AU': 'rgba(16, 185, 129, 0.3)'
};

export const RegionalMap = ({ jurisdictions, selectedJurisdiction, onSelectJurisdiction }) => {
    return (
        <Card noPadding style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-base)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>🌍</span> Regional Activity
                </h3>
            </div>

            <div style={{ flex: 1, padding: '20px', display: 'grid', gridTemplateColumns: jurisdictions.length > 2 ? '1fr 1fr' : '1fr', gap: '20px', overflowY: 'auto' }}>
                {jurisdictions.map(jur => {
                    const stats = STATS_MOCK[jur] || { txns: 0, vol: 0, curr: 'USD', status: 'matched' };
                    const isSelected = selectedJurisdiction === jur;

                    return (
                        <div
                            key={jur}
                            onClick={() => onSelectJurisdiction(isSelected ? null : jur)}
                            style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                padding: '16px',
                                borderRadius: '12px',
                                border: isSelected ? `2px solid ${DOT_COLORS[stats.status]}` : '1px solid var(--color-border)',
                                backgroundColor: isSelected ? 'var(--color-bg-surface)' : 'transparent',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                position: 'relative'
                            }}
                            onMouseEnter={(e) => {
                                if (!isSelected) {
                                    e.currentTarget.style.borderColor = 'var(--color-border-hover)';
                                    e.currentTarget.style.backgroundColor = 'var(--color-bg-surface)';
                                    const path = e.currentTarget.querySelector('path');
                                    if (path) path.style.fill = HOVER_COLORS[jur];
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!isSelected) {
                                    e.currentTarget.style.borderColor = 'var(--color-border)';
                                    e.currentTarget.style.backgroundColor = 'transparent';
                                    const path = e.currentTarget.querySelector('path');
                                    if (path) path.style.fill = FILL_COLORS[jur];
                                }
                            }}
                        >
                            <div style={{ position: 'absolute', top: '12px', right: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span style={{ fontSize: '18px' }}>
                                    {jur === 'US' ? '🇺🇸' : jur === 'UK' ? '🇬🇧' : jur === 'DE' ? '🇩🇪' : '🇦🇺'}
                                </span>
                                <span style={{ fontWeight: '600', fontSize: '14px' }}>{jur}</span>
                            </div>

                            <svg width="120" height="120" viewBox="0 0 250 200" style={{ marginBottom: '16px' }}>
                                <path
                                    d={SVGS[jur] || SVGS['US']}
                                    fill={isSelected ? HOVER_COLORS[jur] : FILL_COLORS[jur]}
                                    stroke={HOVER_COLORS[jur]}
                                    strokeWidth="2"
                                    style={{ transition: 'fill 0.2s' }}
                                />
                            </svg>

                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                <div style={{
                                    width: '8px', height: '8px', borderRadius: '50%',
                                    backgroundColor: DOT_COLORS[stats.status],
                                    animation: stats.status !== 'matched' ? 'pulse 2s infinite' : 'none'
                                }} />
                                <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{stats.txns} pending</span>
                            </div>

                            <div style={{ fontSize: '16px', fontWeight: '600', fontFamily: 'var(--font-mono)' }}>
                                {stats.vol >= 1000 ? <><CurrencyDisplay amount={stats.vol / 1000} currency={stats.curr} />K</> : <CurrencyDisplay amount={stats.vol} currency={stats.curr} />} vol
                            </div>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
};
