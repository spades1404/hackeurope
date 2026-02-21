import React, { useState } from 'react';
import { InvoiceList } from './InvoiceList';
import { TransactionList } from './TransactionList';
import { ReconciliationPanel } from './ReconciliationPanel';
import { RegionalMap } from './RegionalMap';
import { MOCK_INVOICES, MOCK_TRANSACTIONS } from '../../data/mockData';
import { useAppContext } from '../../contexts/AppContext';

export const WorkerDashboard = () => {
    const { company } = useAppContext();
    const [invoices, setInvoices] = useState(MOCK_INVOICES);
    const [transactions, setTransactions] = useState(MOCK_TRANSACTIONS);

    const [selectedInvoiceId, setSelectedInvoiceId] = useState(null);
    const [selectedTxnId, setSelectedTxnId] = useState(null);
    const [selectedJurisdiction, setSelectedJurisdiction] = useState(null);

    // Dynamic candidate matching based on selected invoice
    const selectedInvoice = invoices.find(i => i.id === selectedInvoiceId);
    const selectedTxn = transactions.find(t => t.id === selectedTxnId);

    let candidateTxnIds = [];
    if (selectedInvoice) {
        const invAmtStr = selectedInvoice.amount.toString().replace(/[^0-9.-]+/g, "");
        const invAmt = parseFloat(invAmtStr);

        candidateTxnIds = transactions
            .filter(t => {
                if (t.status === 'matched') return false;
                if (t.jurisdiction !== selectedInvoice.jurisdiction) return false;

                const txAmt = Math.abs(parseFloat(t.amount.toString().replace(/[^0-9.-]+/g, "")));
                // Within 5% tolerance for highlight
                return Math.abs(invAmt - txAmt) / invAmt < 0.05;
            })
            .map(t => t.id);
    }

    const handleConfirmMatch = () => {
        if (!selectedInvoiceId || !selectedTxnId) return;

        setInvoices(prev => prev.map(inv =>
            inv.id === selectedInvoiceId ? { ...inv, status: 'matched', matchedTxn: selectedTxnId } : inv
        ));

        setTransactions(prev => prev.map(txn =>
            txn.id === selectedTxnId ? { ...txn, status: 'matched', matchedInv: selectedInvoiceId } : txn
        ));

        setTimeout(() => {
            setSelectedInvoiceId(null);
            setSelectedTxnId(null);
        }, 500);
    };

    const handleFlagDiscrepancy = () => {
        if (!selectedInvoiceId) return;
        setInvoices(prev => prev.map(inv =>
            inv.id === selectedInvoiceId ? { ...inv, status: 'discrepancy' } : inv
        ));
        if (selectedTxnId) {
            setTransactions(prev => prev.map(txn =>
                txn.id === selectedTxnId ? { ...txn, status: 'discrepancy' } : txn
            ));
        }
        setSelectedInvoiceId(null);
        setSelectedTxnId(null);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>

            {/* Top row: 3 columns */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: '24px',
                flex: 1, // take remaining height of viewport minus header/footer
                minHeight: '400px',
                maxHeight: '600px'
            }}>

                <div style={{ minWidth: 0 }}>
                    <InvoiceList
                        invoices={invoices}
                        selectedId={selectedInvoiceId}
                        onSelect={(inv) => setSelectedInvoiceId(prev => prev === inv.id ? null : inv.id)}
                        filterJurisdiction={selectedJurisdiction}
                    />
                </div>

                <div style={{ minWidth: 0 }}>
                    <TransactionList
                        transactions={transactions}
                        candidateIds={candidateTxnIds}
                        selectedId={selectedTxnId}
                        onSelect={(txn) => setSelectedTxnId(prev => prev === txn.id ? null : txn.id)}
                        filterJurisdiction={selectedJurisdiction}
                    />
                </div>

                <div style={{ minWidth: 0 }}>
                    <RegionalMap
                        jurisdictions={company.jurisdictions}
                        selectedJurisdiction={selectedJurisdiction}
                        onSelectJurisdiction={setSelectedJurisdiction}
                    />
                </div>

            </div>

            {/* Bottom panel: appears when items are selected */}
            {(selectedInvoice || selectedTxn) && (
                <div style={{ marginTop: 'auto' }}>
                    <ReconciliationPanel
                        invoice={selectedInvoice}
                        transaction={selectedTxn}
                        onConfirmMatch={handleConfirmMatch}
                        onFlagDiscrepancy={handleFlagDiscrepancy}
                    />
                </div>
            )}

        </div>
    );
};
