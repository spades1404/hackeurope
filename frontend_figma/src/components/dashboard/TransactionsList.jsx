import { CurrencyDisplay } from '../ui/CurrencyDisplay';
import { StatusBadge } from '../ui/StatusBadge';

export const TransactionsList = ({ transactions, onTransactionClick, selectedId }) => {
  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] overflow-hidden">
      <div className="p-4 border-b border-[var(--tt-border)]">
        <h3 className="font-semibold text-lg" style={{ color: 'var(--tt-text)' }}>
          Recent Transactions
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[var(--tt-bg-alt)] text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}></th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>ID</th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>Description</th>
              <th className="px-4 py-3 text-right font-medium" style={{ color: 'var(--tt-text-muted)' }}>Amount</th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>Date</th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {transactions.slice(0, 8).map((txn, idx) => (
              <tr
                key={txn.id}
                onClick={() => onTransactionClick?.(txn)}
                className={`border-t border-[var(--tt-border-light)] hover:bg-[var(--tt-bg-alt)] cursor-pointer transition-colors ${selectedId === txn.id ? 'bg-[var(--tt-primary-ghost)]' : idx % 2 === 0 ? '' : 'bg-[var(--tt-bg-alt)]/30'
                  }`}
              >
                <td className="px-4 py-3 text-lg">{txn.flag || '📄'}</td>
                <td className="px-4 py-3">
                  <span className="font-mono text-sm" style={{ color: 'var(--tt-text-body)' }}>
                    {txn.id}
                  </span>
                  {txn.matched_invoice_id && (
                    <div className="text-xs text-[var(--tt-success)] font-medium mt-0.5">
                      → {txn.matched_invoice_id}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm" style={{ color: 'var(--tt-text-body)' }}>
                    {txn.description || 'N/A'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <CurrencyDisplay
                    amount={txn.amount || 0}
                    currency={txn.currency || 'USD'}
                    showSign
                  />
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm" style={{ color: 'var(--tt-text-muted)' }}>
                    {new Date(txn.transaction_date || Date.now()).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={txn.reconciliation_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
