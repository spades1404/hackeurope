import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { CheckCircle2, AlertTriangle, Edit3, Save } from 'lucide-react';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';

const ComparisonRow = ({ label, leftVal, rightVal, onMatchCheck }) => {
    const status = onMatchCheck(leftVal, rightVal); // 'match', 'warning', 'mismatch'

    return (
        <div style={{ display: 'flex', padding: '12px 0', borderBottom: '1px solid var(--color-border)', alignItems: 'center' }}>
            <div style={{ width: '120px', fontSize: '13px', color: 'var(--color-text-muted)' }}>{label}</div>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingRight: '20px', borderRight: '1px solid var(--color-border)', fontFamily: label === 'Amount' ? 'var(--font-mono)' : 'var(--font-body)' }}>
                <span style={{ fontWeight: '500' }}>{leftVal}</span>
            </div>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingLeft: '20px', fontFamily: label === 'Amount' ? 'var(--font-mono)' : 'var(--font-body)' }}>
                <span style={{ fontWeight: '500' }}>{rightVal || <span style={{ color: 'var(--color-text-dim)' }}>—</span>}</span>
                {status === 'match' && <CheckCircle2 size={16} color="var(--color-success)" />}
                {status === 'warning' && <AlertTriangle size={16} color="var(--color-warning)" />}
                {status === 'mismatch' && <span style={{ color: 'var(--color-error)', fontWeight: 'bold' }}>✕</span>}
            </div>
        </div>
    );
};

export const ReconciliationPanel = ({ invoice, transaction, onConfirmMatch, onFlagDiscrepancy }) => {
    const [isManualMode, setIsManualMode] = useState(false);

    if (!invoice && !transaction) {
        return (
            <Card style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
                Select an invoice or transaction to reconcile
            </Card>
        );
    }

    // Matching logic for UI
    const checkAmount = (inv, txn) => {
        if (!inv || !txn) return 'mismatch';
        const invAmt = parseFloat(inv.toString().replace(/[^0-9.-]+/g, ""));
        const txnAmt = Math.abs(parseFloat(txn.toString().replace(/[^0-9.-]+/g, "")));
        if (Math.abs(invAmt - txnAmt) < 0.02) return 'match';
        if (Math.abs(invAmt - txnAmt) / invAmt < 0.05) return 'warning';
        return 'mismatch';
    };

    const checkDate = (inv, txn) => {
        if (!inv || !txn) return 'mismatch';
        const t1 = new Date(inv).getTime();
        const t2 = new Date(txn).getTime();
        if (isNaN(t1) || isNaN(t2)) return 'mismatch';
        const diffDays = Math.abs((t1 - t2) / (1000 * 60 * 60 * 24));
        if (diffDays <= 3) return 'match';
        if (diffDays <= 7) return 'warning';
        return 'mismatch';
    };

    const checkStringMatch = (a, b) => {
        if (!a || !b) return 'mismatch';
        return a.toLowerCase() === b.toLowerCase() ? 'match' : 'mismatch';
    };

    const formatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: invoice?.currency || transaction?.currency || 'USD' });

    return (
        <Card style={{ animation: 'fadeInUp 0.3s ease-out' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', margin: 0 }}>Reconciliation Workspace</h3>
                {!isManualMode && (
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <Button variant="danger" onClick={onFlagDiscrepancy}><AlertTriangle size={16} style={{ marginRight: '6px' }} /> Flag Discrepancy</Button>
                        <Button variant="secondary" onClick={() => setIsManualMode(true)}><Edit3 size={16} style={{ marginRight: '6px' }} /> Manual Entry</Button>
                        <Button variant="primary" onClick={onConfirmMatch} disabled={!transaction || !invoice}><CheckCircle2 size={16} style={{ marginRight: '6px' }} /> Confirm Match</Button>
                    </div>
                )}
            </div>

            <div style={{ display: 'flex', border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden' }}>
                {/* Left Column - Invoice */}
                <div style={{ flex: 1, backgroundColor: 'var(--color-bg-base)', borderRight: '1px solid var(--color-border)' }}>
                    <div style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>📧</span> Invoice details
                    </div>
                    {invoice ? (
                        <div style={{ padding: '0 16px', paddingBottom: '16px' }}>
                            <ComparisonRow label="ID" leftVal={invoice.id} rightVal={transaction?.id} onMatchCheck={() => 'match'} />
                            <ComparisonRow label="Vendor/Desc" leftVal={invoice.vendor} rightVal={transaction?.description} onMatchCheck={() => 'warning'} />
                            <ComparisonRow label="Amount" leftVal={formatter.format(invoice.amount)} rightVal={transaction ? formatter.format(transaction.amount) : null} onMatchCheck={checkAmount} />
                            <ComparisonRow label="Date" leftVal={invoice.date} rightVal={transaction?.date} onMatchCheck={checkDate} />
                            <ComparisonRow label="Jurisdiction"
                                leftVal={<><JurisdictionFlag jurisdiction={invoice.jurisdiction} /> {invoice.jurisdiction}</>}
                                rightVal={transaction ? <><JurisdictionFlag jurisdiction={transaction.jurisdiction} /> {transaction.jurisdiction}</> : null}
                                onMatchCheck={() => invoice.jurisdiction === transaction?.jurisdiction ? 'match' : 'mismatch'}
                            />
                        </div>
                    ) : (
                        <div style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--color-text-muted)' }}>No invoice selected</div>
                    )}
                </div>

                {/* Right Column - Transaction */}
                <div style={{ flex: 1, backgroundColor: 'var(--color-bg-base)' }}>
                    <div style={{ padding: '16px', borderBottom: '1px solid var(--color-border)', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>🏦</span> Transaction details
                    </div>
                    {isManualMode ? (
                        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Enter missing transaction details manually:</div>
                            <input type="date" style={{ padding: '8px 12px', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '6px', color: '#fff' }} defaultValue={invoice?.date} />
                            <input type="text" placeholder="Amount" style={{ padding: '8px 12px', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '6px', color: '#fff' }} defaultValue={invoice?.amount ? `-${invoice.amount}` : ''} />
                            <input type="text" placeholder="Reference" style={{ padding: '8px 12px', background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', borderRadius: '6px', color: '#fff' }} />
                            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                                <Button variant="primary" style={{ flex: 1 }} onClick={() => setIsManualMode(false)}><Save size={16} style={{ marginRight: '6px' }} /> Save Entry</Button>
                                <Button variant="secondary" onClick={() => setIsManualMode(false)}>Cancel</Button>
                            </div>
                        </div>
                    ) : transaction ? (
                        <div style={{ padding: '0 16px' }}>
                            {/* Right side cells are rendered in ComparisonRow visually matching left side row height */}
                        </div>
                    ) : (
                        <div style={{ padding: '40px 16px', textAlign: 'center', color: 'var(--color-text-muted)' }}>No transaction selected. Select one from the list or add manually.</div>
                    )}
                </div>
            </div>
            <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
        </Card>
    );
};
