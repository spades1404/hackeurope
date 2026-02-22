import React, { useState } from 'react';
import { TransactionList } from './TransactionList';
import { ReconciliationPanel } from './ReconciliationPanel';
import { MOCK_TRANSACTIONS } from '../../data/mockData';
import { useAppContext } from '../../contexts/AppContext';

export const WorkerDashboard = () => {
    const { company } = useAppContext();
    const [transactions, setTransactions] = useState(MOCK_TRANSACTIONS);

    const [selectedTxnId, setSelectedTxnId] = useState(null);
    const [previewTxnId, setPreviewTxnId] = useState(null);

    const selectedTxn = transactions.find(t => t.id === selectedTxnId);
    const previewTxn = transactions.find(t => t.id === previewTxnId);

    const handleConfirmMatch = () => {
        if (!selectedTxnId) return;

        setTransactions(prev => prev.map(txn =>
            txn.id === selectedTxnId ? { ...txn, status: 'matched' } : txn
        ));

        setTimeout(() => {
            setSelectedTxnId(null);
        }, 500);
    };

    const handleFlagDiscrepancy = () => {
        if (selectedTxnId) {
            setTransactions(prev => prev.map(txn =>
                txn.id === selectedTxnId ? { ...txn, status: 'discrepancy' } : txn
            ));
        }
        setSelectedTxnId(null);
    };

    const handleValidate = (txnId) => {
        setTransactions(prev => prev.map(txn =>
            txn.id === txnId ? { ...txn, status: 'validated' } : txn
        ));
    };

    const handleUpload = async (txn, files) => {
        if (!files?.length) return;
        const formData = new FormData();
        for (const file of files) formData.append('files', file);
        try {
            const res = await fetch('/api/upload-invoice', { method: 'POST', body: formData });
            if (!res.ok) throw new Error(await res.text());
            const data = await res.json();
            console.log('Uploaded:', data?.saved?.length ?? 0, 'file(s) for transaction', txn.id);
        } catch (err) {
            console.error('Upload failed:', err);
        }
    };

    return (
        <div style={{ display: 'flex', gap: '24px', height: '600px', width: '100%' }}>

            {/* Transaction List - Fixed width when preview is open */}
            <div style={{
                width: previewTxnId ? 'calc(100% - 404px)' : '100%',
                height: '600px',
                transition: 'width 0.3s ease'
            }}>
                <TransactionList
                    transactions={transactions}
                    candidateIds={[]}
                    selectedId={selectedTxnId}
                    onSelect={(txn) => setSelectedTxnId(prev => prev === txn.id ? null : txn.id)}
                    onPreview={(txn) => setPreviewTxnId(txn.id)}
                    onValidate={handleValidate}
                    onUpload={handleUpload}
                    filterJurisdiction={null}
                />
            </div>

            {/* Preview Panel - Fixed width */}
            {previewTxnId && previewTxn && (
                <div style={{
                    width: '380px',
                    height: '600px',
                    backgroundColor: '#1a1d24',
                    border: '2px solid #2d3748',
                    borderRadius: '16px',
                    padding: '24px',
                    overflowY: 'auto',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
                    animation: 'slideInRight 0.3s ease-out',
                    flexShrink: 0
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '1px solid #2d3748' }}>
                        <h3 style={{ fontSize: '18px', fontWeight: '600', margin: 0, color: '#f7fafc' }}>Invoice Preview</h3>
                        <button 
                            onClick={() => setPreviewTxnId(null)}
                            style={{ 
                                background: '#2d3748', 
                                border: 'none', 
                                fontSize: '20px', 
                                cursor: 'pointer',
                                color: '#a0aec0',
                                padding: '4px 10px',
                                lineHeight: '1',
                                borderRadius: '6px',
                                transition: 'all 0.2s'
                            }}
                            onMouseEnter={(e) => {
                                e.target.style.background = '#4a5568';
                                e.target.style.color = '#fff';
                            }}
                            onMouseLeave={(e) => {
                                e.target.style.background = '#2d3748';
                                e.target.style.color = '#a0aec0';
                            }}
                        >×</button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ 
                            padding: '12px 16px', 
                            backgroundColor: '#0f1419', 
                            borderRadius: '8px',
                            border: '1px solid #2d3748'
                        }}>
                            <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Transaction ID</div>
                            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', color: '#e2e8f0' }}>{previewTxn.id}</div>
                        </div>

                        <div style={{ 
                            padding: '12px 16px', 
                            backgroundColor: '#0f1419', 
                            borderRadius: '8px',
                            border: '1px solid #2d3748'
                        }}>
                            <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Description</div>
                            <div style={{ fontSize: '14px', fontWeight: '500', color: '#f7fafc' }}>{previewTxn.description}</div>
                        </div>

                        <div style={{ 
                            padding: '12px 16px', 
                            backgroundColor: '#0f1419', 
                            borderRadius: '8px',
                            border: '1px solid #2d3748'
                        }}>
                            <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Amount</div>
                            <div style={{ 
                                fontSize: '18px', 
                                fontWeight: '700', 
                                fontFamily: 'var(--font-mono)',
                                color: previewTxn.amount < 0 ? '#fc8181' : '#68d391'
                            }}>
                                {new Intl.NumberFormat('en-US', { style: 'currency', currency: previewTxn.currency }).format(previewTxn.amount)}
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                            <div style={{ 
                                padding: '12px 16px', 
                                backgroundColor: '#0f1419', 
                                borderRadius: '8px',
                                border: '1px solid #2d3748'
                            }}>
                                <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Date</div>
                                <div style={{ fontSize: '13px', color: '#e2e8f0' }}>{previewTxn.date}</div>
                            </div>

                            <div style={{ 
                                padding: '12px 16px', 
                                backgroundColor: '#0f1419', 
                                borderRadius: '8px',
                                border: '1px solid #2d3748'
                            }}>
                                <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Jurisdiction</div>
                                <div style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: '600' }}>{previewTxn.jurisdiction}</div>
                            </div>
                        </div>

                        <div style={{ 
                            padding: '12px 16px', 
                            backgroundColor: '#0f1419', 
                            borderRadius: '8px',
                            border: '1px solid #2d3748'
                        }}>
                            <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Account</div>
                            <div style={{ fontSize: '14px', color: '#e2e8f0' }}>{previewTxn.account}</div>
                        </div>

                        <div style={{ 
                            padding: '12px 16px', 
                            backgroundColor: '#0f1419', 
                            borderRadius: '8px',
                            border: '1px solid #2d3748'
                        }}>
                            <div style={{ fontSize: '11px', color: '#718096', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Status</div>
                            <div style={{ 
                                fontSize: '13px', 
                                display: 'inline-block',
                                padding: '6px 14px',
                                borderRadius: '20px',
                                fontWeight: '600',
                                backgroundColor: previewTxn.status === 'matched' ? 'rgba(72, 187, 120, 0.15)' : 'rgba(251, 191, 36, 0.15)',
                                color: previewTxn.status === 'matched' ? '#68d391' : '#fbbf24',
                                border: `1px solid ${previewTxn.status === 'matched' ? 'rgba(72, 187, 120, 0.3)' : 'rgba(251, 191, 36, 0.3)'}`
                            }}>
                                {previewTxn.status.toUpperCase()}
                            </div>
                        </div>

                        {previewTxn.matchedInv && (
                            <div style={{ 
                                padding: '12px 16px', 
                                backgroundColor: '#0f1419', 
                                borderRadius: '8px',
                                border: '1px solid #48bb78'
                            }}>
                                <div style={{ fontSize: '11px', color: '#68d391', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Matched Invoice</div>
                                <div style={{ fontSize: '14px', fontFamily: 'var(--font-mono)', color: '#68d391', fontWeight: '600' }}>{previewTxn.matchedInv}</div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <style>{`
                @keyframes slideInRight {
                    from { opacity: 0; transform: translateX(30px); }
                    to { opacity: 1; transform: translateX(0); }
                }
            `}</style>

        </div>
    );
};
