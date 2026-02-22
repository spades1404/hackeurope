import { useState, useEffect } from 'react';
import { MetricsCards } from './MetricsCards';
import { TransactionsList } from './TransactionsList';
import { InvoicesList } from './InvoicesList';
import { CurrentTasks } from './CurrentTasks';
import { TaxExposureChart } from './TaxExposureChart';
import { RegionalMap } from './RegionalMap';
import { MOCK_FINANCIALS, MOCK_COMPLIANCE_DOCS, MOCK_TASKS } from '../../data/mockData';
import { useApi } from '../../hooks/useApi';
import { transactionsApi, proposalsApi } from '../../api';

export const WorkerDashboard = () => {
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  // Replace with real company_id from AuthContext in a full app
  const companyId = 'tuna-tax-ltd';

  const { data: txns, loading: loadingTxns, error: errorTxns, execute: fetchTransactions } = useApi(transactionsApi.getTransactions);
  const { data: invs, loading: loadingInvs, error: errorInvs, execute: fetchInvoices } = useApi(transactionsApi.getInvoices);
  const { data: props, loading: loadingProps, error: errorProps, execute: fetchProposals } = useApi(proposalsApi.getProposals);

  useEffect(() => {
    fetchTransactions(companyId, { limit: 20 });
    fetchInvoices(companyId, { limit: 20 });
    fetchProposals(companyId, { status: 'pending,needs_review,matched' });
  }, [fetchTransactions, fetchInvoices, fetchProposals, companyId]);

  const transactions = txns || [];
  const invoices = invs || [];

  // Create UI flags dynamically since real backend data has jurisdictions
  const flagMap = { 'EUR': '🇩🇪', 'GBP': '🇬🇧', 'USD': '🇺🇸', 'AUD': '🇦🇺' };

  const mappedTransactions = transactions.map(t => ({
    ...t,
    flag: flagMap[t.currency] || '🌍'
  }));

  const mappedInvoices = invoices.map(i => ({
    ...i,
    id: i.id, // Ensure id
    vendor: i.vendor_name, // Map vendor_name to vendor for InvoicesList
    amount: i.gross_amount, // Map gross_amount to amount
    date: i.invoice_date,
    flag: flagMap[i.currency] || '🌍'
  }));

  const proposals = props || [];

  const mappedProposals = proposals.map(p => {
    let reasons = p.match_reasons;
    try {
      if (typeof reasons === 'string') reasons = JSON.parse(reasons);
    } catch (e) { reasons = []; }

    const matchedInv = invoices.find(inv => inv.id === p.invoice_id) || {};

    return {
      id: `task-${p.id}`,
      type: 'reconciliation',
      status: 'pending',
      title: `Review match for TXN ${p.transaction_id}`,
      transaction_id: p.transaction_id,
      confidence_score: p.confidence_score,
      currency: p.currency || matchedInv.currency || 'USD',
      match_proposal: {
        ...p,
        match_reasons: reasons,
        extracted_invoice: {
          invoice_number: matchedInv.invoice_number || p.invoice_id,
          vendor_name: matchedInv.vendor_name || 'Unknown Vendor',
          gross_amount: matchedInv.gross_amount || 0
        }
      }
    };
  });

  const tasksToDisplay = mappedProposals.length > 0 ? mappedProposals : MOCK_TASKS;

  const loading = loadingTxns || loadingInvs || loadingProps;
  const error = errorTxns || errorInvs || errorProps;

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <MetricsCards financials={MOCK_FINANCIALS} />

      {/* Transactions and Invoices */}
      <div className="grid lg:grid-cols-2 gap-6">
        {loading ? (
          <div>Loading transactions...</div>
        ) : error ? (
          <div className="text-red-500">Error loading data: {error}</div>
        ) : (
          <>
            <TransactionsList
              transactions={mappedTransactions}
              onTransactionClick={setSelectedTransaction}
              selectedId={selectedTransaction?.id}
            />
            <InvoicesList invoices={mappedInvoices} />
          </>
        )}
      </div>

      {/* Current Tasks */}
      <CurrentTasks tasks={tasksToDisplay} />

      {/* Charts and Map */}
      <div className="grid lg:grid-cols-2 gap-6">
        <TaxExposureChart financials={MOCK_FINANCIALS} />
        <RegionalMap financials={MOCK_FINANCIALS} complianceDocs={MOCK_COMPLIANCE_DOCS} />
      </div>
    </div >
  );
};
