import { useEffect } from 'react';
import { MetricsCards } from './MetricsCards';
import { TransactionsList } from './TransactionsList';
import { InvoicesList } from './InvoicesList';
import { PnLChart } from './PnLChart';
import { ExpenseBreakdownChart } from './ExpenseBreakdownChart';
import { TaxOverview } from './TaxOverview';
import { MOCK_FINANCIALS } from '../../data/mockData';
import { useApi } from '../../hooks/useApi';
import { transactionsApi } from '../../api';

export const BusinessDashboard = () => {
  // Replace with real company_id from AuthContext in a full app
  const companyId = 'tuna-tax-ltd';

  const { data: transactionsData, loading, error, execute: fetchTransactions } = useApi(transactionsApi.getTransactions);

  useEffect(() => {
    fetchTransactions(companyId, {});
  }, [fetchTransactions, companyId]);

  const transactions = transactionsData?.transactions || [];

  // For now, simulate invoices by mapping parsed extracted invoices from the transactions payload
  const invoices = transactions
    .filter(t => t.match_proposal)
    .map(t => ({
      ...t.match_proposal.extracted_invoice,
      transaction_id: t.transaction_id,
      flag: t.currency === 'EUR' ? '🇩🇪' : t.currency === 'GBP' ? '🇬🇧' : '🇺🇸',
      status: t.status,
      currency: t.currency || 'USD'
    }));

  return (
    <div className="space-y-6">
      {/* Metrics Row */}
      <MetricsCards financials={MOCK_FINANCIALS} />

      {/* Charts */}
      <div className="grid lg:grid-cols-2 gap-6">
        <PnLChart financials={MOCK_FINANCIALS} />
        <ExpenseBreakdownChart financials={MOCK_FINANCIALS} />
      </div>

      {/* Transactions and Tax Overview */}
      <div className="grid lg:grid-cols-2 gap-6">
        <TransactionsList transactions={transactions} />
        <TaxOverview financials={MOCK_FINANCIALS} />
      </div>

      {/* Invoices */}
      <InvoicesList invoices={invoices} />
    </div>
  );
};
