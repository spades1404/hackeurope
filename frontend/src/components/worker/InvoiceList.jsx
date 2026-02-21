import React from 'react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../shared/StatusBadge';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';

export const InvoiceList = ({ invoices, selectedId, onSelect, filterJurisdiction }) => {
    const filtered = filterJurisdiction ? invoices.filter(i => i.jurisdiction === filterJurisdiction) : invoices;

    return (
        <Card noPadding style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-base)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>📧</span> Extracted Invoices
                    <span style={{ fontSize: '12px', fontWeight: 'normal', color: 'var(--color-text-muted)', backgroundColor: 'var(--color-bg-surface)', padding: '2px 8px', borderRadius: '12px' }}>
                        {filtered.length}
                    </span>
                </h3>
            </div>
            <div style={{ flex: 1, overflowY: 'auto' }}>
                {filtered.map((inv, idx) => {
                    const isSelected = selectedId === inv.id;
                    return (
                        <div
                            key={inv.id}
                            onClick={() => onSelect(inv)}
                            style={{
                                padding: '16px',
                                borderBottom: idx === filtered.length - 1 ? 'none' : '1px solid var(--color-border)',
                                backgroundColor: isSelected ? 'var(--color-border)' : 'transparent',
                                cursor: 'pointer',
                                transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={e => { if (!isSelected) e.currentTarget.style.backgroundColor = 'var(--color-bg-surface)'; }}
                            onMouseLeave={e => { if (!isSelected) e.currentTarget.style.backgroundColor = 'transparent'; }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <JurisdictionFlag jurisdiction={inv.jurisdiction} />
                                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--color-text-dim)' }}>{inv.id}</span>
                                </div>
                                <StatusBadge status={inv.status} dot />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <div style={{ fontWeight: '500', color: 'var(--color-text-primary)' }}>{inv.vendor}</div>
                                <div style={{ fontWeight: '600' }}><CurrencyDisplay amount={inv.amount} currency={inv.currency} /></div>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                                <div style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '60%' }}>
                                    Subject: {inv.emailSubject}
                                </div>
                                <div>{inv.date}</div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
};
