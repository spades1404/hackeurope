import React from 'react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../shared/StatusBadge';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';

export const TransactionList = ({ transactions, candidateIds = [], selectedId, onSelect, filterJurisdiction }) => {
    let filtered = filterJurisdiction ? transactions.filter(t => t.jurisdiction === filterJurisdiction) : transactions;

    // Sort candidates to the top if any are provided
    if (candidateIds.length > 0) {
        filtered = [...filtered].sort((a, b) => {
            const aIsCand = candidateIds.includes(a.id);
            const bIsCand = candidateIds.includes(b.id);
            if (aIsCand && !bIsCand) return -1;
            if (!aIsCand && bIsCand) return 1;
            return 0;
        });
    }

    return (
        <Card noPadding style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', backgroundColor: 'var(--color-bg-base)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: '600', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span>🏦</span> Bank Transactions
                    <span style={{ fontSize: '12px', fontWeight: 'normal', color: 'var(--color-text-muted)', backgroundColor: 'var(--color-bg-surface)', padding: '2px 8px', borderRadius: '12px' }}>
                        {filtered.length}
                    </span>
                </h3>
            </div>
            <div style={{ flex: 1, overflowY: 'auto' }}>
                {filtered.map((txn, idx) => {
                    const isSelected = selectedId === txn.id;
                    const isCandidate = candidateIds.includes(txn.id);

                    return (
                        <div
                            key={txn.id}
                            onClick={() => onSelect(txn)}
                            style={{
                                padding: '16px',
                                borderBottom: idx === filtered.length - 1 ? 'none' : '1px solid var(--color-border)',
                                borderLeft: isCandidate ? '3px solid var(--color-accent)' : '3px solid transparent',
                                backgroundColor: isSelected ? 'var(--color-border)' : (isCandidate ? 'rgba(59, 130, 246, 0.05)' : 'transparent'),
                                cursor: 'pointer',
                                transition: 'background-color 0.2s'
                            }}
                            onMouseEnter={e => { if (!isSelected) e.currentTarget.style.backgroundColor = isCandidate ? 'rgba(59, 130, 246, 0.1)' : 'var(--color-bg-surface)'; }}
                            onMouseLeave={e => { if (!isSelected) e.currentTarget.style.backgroundColor = isCandidate ? 'rgba(59, 130, 246, 0.05)' : 'transparent'; }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <JurisdictionFlag jurisdiction={txn.jurisdiction} />
                                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--color-text-dim)' }}>{txn.id}</span>
                                </div>
                                <StatusBadge status={txn.status} />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                <div style={{ fontWeight: '500', color: 'var(--color-text-primary)' }}>{txn.description}</div>
                                <div style={{ fontWeight: '600' }}><CurrencyDisplay amount={txn.amount} currency={txn.currency} colorize /></div>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                                <div>{txn.account}</div>
                                <div>{txn.date}</div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
};
