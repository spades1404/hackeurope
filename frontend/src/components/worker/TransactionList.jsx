import React, { useRef } from 'react';
import { Card } from '../ui/Card';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';
import { CheckCircle2, XCircle, Upload, Eye, BadgeCheck } from 'lucide-react';

export const TransactionList = ({ transactions, candidateIds = [], selectedId, onSelect, onPreview, onValidate, onUpload, filterJurisdiction }) => {
    const fileInputRef = useRef(null);
    const pendingTxnRef = useRef(null);
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
            
            {/* Table Header */}
            <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr auto 100px 100px', 
                padding: '12px 16px', 
                borderBottom: '1px solid var(--color-border)', 
                backgroundColor: 'var(--color-bg-surface)',
                fontSize: '12px',
                fontWeight: '600',
                color: 'var(--color-text-muted)'
            }}>
                <div>Transaction</div>
                <div style={{ textAlign: 'right', paddingRight: '16px' }}>Amount</div>
                <div style={{ textAlign: 'center' }}>Status</div>
                <div style={{ textAlign: 'center' }}>Preview</div>
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
                                display: 'grid',
                                gridTemplateColumns: '1fr auto 100px 100px',
                                alignItems: 'center',
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
                            {/* Transaction Details Column */}
                            <div style={{ minWidth: 0 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                    <JurisdictionFlag jurisdiction={txn.jurisdiction} />
                                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--color-text-dim)' }}>{txn.id}</span>
                                </div>
                                <div style={{ fontWeight: '500', color: 'var(--color-text-primary)', marginBottom: '4px' }}>{txn.description}</div>
                                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                                    {txn.account} • {txn.date}
                                </div>
                            </div>

                            {/* Amount Column */}
                            <div style={{ fontWeight: '600', paddingRight: '16px', textAlign: 'right' }}>
                                <CurrencyDisplay amount={txn.amount} currency={txn.currency} colorize />
                            </div>

                            {/* Status Column */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                                {txn.status === 'matched' && (
                                    <>
                                        <CheckCircle2 
                                            size={24} 
                                            color="var(--color-success)"
                                            style={{ cursor: 'pointer' }}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onValidate && onValidate(txn.id);
                                            }}
                                        />
                                        <XCircle size={24} color="var(--color-error)" />
                                    </>
                                )}
                                {txn.status === 'validated' && (
                                    <BadgeCheck size={28} color="#60a5fa" />
                                )}
                                {txn.status === 'discrepancy' && <XCircle size={24} color="var(--color-error)" />}
                                {txn.status === 'unmatched' && (
                                    <>
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            multiple
                                            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,image/*,application/pdf"
                                            style={{ display: 'none' }}
                                            onChange={(e) => {
                                                const files = e.target.files;
                                                const txn = pendingTxnRef.current;
                                                if (files?.length && onUpload && txn) onUpload(txn, Array.from(files));
                                                pendingTxnRef.current = null;
                                                e.target.value = '';
                                            }}
                                        />
                                        <Upload
                                            size={24}
                                            color="var(--color-text-muted)"
                                            style={{ cursor: 'pointer' }}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (onUpload) {
                                                    pendingTxnRef.current = txn;
                                                    fileInputRef.current?.click();
                                                }
                                            }}
                                        />
                                    </>
                                )}
                            </div>

                            {/* Preview Column */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                {(txn.status === 'matched' || txn.status === 'unmatched') && (
                                    <Eye 
                                        size={24} 
                                        color="var(--color-text-muted)"
                                        style={{ cursor: 'pointer' }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onPreview && onPreview(txn);
                                        }}
                                    />
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </Card>
    );
};
