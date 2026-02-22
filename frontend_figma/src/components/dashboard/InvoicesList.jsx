import { CurrencyDisplay } from '../ui/CurrencyDisplay';
import { StatusBadge } from '../ui/StatusBadge';

export const InvoicesList = ({ invoices }) => {
  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] overflow-hidden">
      <div className="p-4 border-b border-[var(--tt-border)]">
        <h3 className="font-semibold text-lg" style={{ color: 'var(--tt-text)' }}>
          Incoming Invoices
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-[var(--tt-bg-alt)] text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}></th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>ID</th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>Vendor</th>
              <th className="px-4 py-3 text-right font-medium" style={{ color: 'var(--tt-text-muted)' }}>Amount</th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>Date</th>
              <th className="px-4 py-3 text-left font-medium" style={{ color: 'var(--tt-text-muted)' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {invoices.slice(0, 8).map((inv, idx) => (
              <tr
                key={inv.id || idx}
                className={`border-t border-[var(--tt-border-light)] hover:bg-[var(--tt-bg-alt)] cursor-pointer transition-colors ${idx % 2 === 0 ? '' : 'bg-[var(--tt-bg-alt)]/30'
                  }`}
              >
                <td className="px-4 py-3 text-lg">{inv.flag || '📄'}</td>
                <td className="px-4 py-3">
                  <span className="font-mono text-sm" style={{ color: 'var(--tt-text-body)' }}>
                    {inv.id}
                  </span>
                  {inv.matched_transaction_id && (
                    <div className="text-xs text-[var(--tt-info)] font-medium mt-0.5">
                      → {inv.matched_transaction_id}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm font-medium" style={{ color: 'var(--tt-text-body)' }}>
                    {inv.vendor || 'Unknown Vendor'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <CurrencyDisplay amount={inv.amount || 0} currency={inv.currency || 'USD'} />
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm" style={{ color: 'var(--tt-text-muted)' }}>
                    {new Date(inv.date || Date.now()).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={inv.reconciliation_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
