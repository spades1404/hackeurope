import { useState, useEffect } from 'react';
import { Download, CheckCircle, Edit, RefreshCw, FileText } from 'lucide-react';
import { SlidePanel } from '../ui/SlidePanel';
import { StatusBadge } from '../ui/StatusBadge';
import { CurrencyDisplay } from '../ui/CurrencyDisplay';
import { toast } from 'sonner';
import { useApi } from '../../hooks/useApi';
import { transactionsApi } from '../../api';

export const DocumentDetailPanel = ({ document, isOpen, onClose }) => {
  const [generated, setGenerated] = useState(document?.generated || false);
  const [generating, setGenerating] = useState(false);
  const [showPDF, setShowPDF] = useState(false);
  const [docId, setDocId] = useState(null);

  const { data: txns, execute: fetchTxns } = useApi(transactionsApi.getTransactions);

  useEffect(() => {
    if (isOpen && document) {
      fetchTxns('tuna-tax-ltd', { jurisdiction: document.jurisdiction });
    }
  }, [isOpen, document, fetchTxns]);

  if (!document) return null;

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const resp = await fetch(`http://localhost:8000/api/actions/${document.id}/generate-document`, { method: 'POST' });
      if (!resp.ok) throw new Error('Generation failed');
      const data = await resp.json();
      setDocId(data.document_id);
      setGenerated(true);
      setShowPDF(true);
      toast.success('Document generated successfully');
    } catch (e) {
      toast.error(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleApprove = async () => {
    if (!docId) return;
    try {
      await fetch(`http://localhost:8000/api/documents/${docId}/approve`, { method: 'POST' });
      toast.success('Document approved');
    } catch (e) {
      toast.error('Failed to approve');
    }
  };

  const handleAutoApproveAll = async () => {
    try {
      await transactionsApi.autoApproveAction(document.id);
      toast.success('All transactions auto-approved');
      // Refresh transactions
      fetchTxns('tuna-tax-ltd', { jurisdiction: document.jurisdiction });
    } catch (e) {
      toast.error('Failed to auto-approve');
    }
  };

  const periodTransactions = txns || [];
  const resolvedCount = periodTransactions.filter(t => t.reconciliation_status === 'approved' || t.reconciliation_status === 'matched').length;
  const unresolvedCount = periodTransactions.length - resolvedCount;

  // Compute stats client-side 
  const stats = { revenue: 0, expenses: 0, net_pnl: 0, output_vat: 0, input_vat: 0, net_vat_due: 0, tax_exposure: 0 };
  periodTransactions.forEach(t => {
    if (t.category === 'revenue') stats.revenue += t.amount;
    if (t.category === 'expense') stats.expenses += Math.abs(t.amount);
    if (t.category === 'vat_collected') stats.output_vat += t.amount;
    if (t.category === 'vat_paid') stats.input_vat += Math.abs(t.amount);
  });
  stats.net_pnl = stats.revenue - stats.expenses;
  stats.net_vat_due = stats.output_vat - stats.input_vat;
  // tax exposure is random estimate here:
  stats.tax_exposure = stats.net_pnl > 0 ? stats.net_pnl * 0.2 : 0;

  const getCurrency = () => {
    if (document.jurisdiction === 'US') return 'USD';
    if (document.jurisdiction === 'UK') return 'GBP';
    if (document.jurisdiction === 'DE') return 'EUR';
    if (document.jurisdiction === 'AU') return 'AUD';
    return 'USD';
  };

  const currency = getCurrency();

  return (
    <SlidePanel isOpen={isOpen} onClose={onClose} title={`${document.flag} ${document.jurisdiction} — ${document.form_number}`} width="600px">
      <div className="space-y-6">
        {/* Header Info */}
        <div className="space-y-2">
          <h3 className="text-xl font-semibold" style={{ color: 'var(--tt-text)' }}>
            {document.name}
          </h3>
          <div className="flex items-center gap-4 text-sm" style={{ color: 'var(--tt-text-muted)' }}>
            <div>Form: <span className="font-mono font-semibold">{document.form_number}</span></div>
            <div>Due: <span className="font-semibold">{new Date(document.due_date).toLocaleDateString()}</span></div>
            <StatusBadge status={document.status} />
          </div>
        </div>

        {/* Period Overview */}
        <div className="bg-[var(--tt-bg-alt)] rounded-lg p-4 space-y-3">
          <h4 className="font-semibold text-sm uppercase tracking-wide" style={{ color: 'var(--tt-text-muted)' }}>
            Period Overview
          </h4>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Revenue</div>
              <div className="text-lg font-bold">
                <CurrencyDisplay amount={stats.revenue} currency={currency} />
              </div>
            </div>
            <div>
              <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Expenses</div>
              <div className="text-lg font-bold">
                <CurrencyDisplay amount={stats.expenses} currency={currency} />
              </div>
            </div>
            <div>
              <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Net P&L</div>
              <div className="text-lg font-bold">
                <CurrencyDisplay amount={stats.net_pnl} currency={currency} />
              </div>
            </div>
            <div>
              <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Tax Exposure</div>
              <div className="text-lg font-bold">
                <CurrencyDisplay amount={stats.tax_exposure} currency={currency} />
              </div>
            </div>
          </div>

          {stats.output_vat && (
            <div className="pt-3 border-t border-[var(--tt-border)] grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Output VAT</div>
                <div className="font-mono"><CurrencyDisplay amount={stats.output_vat} currency={currency} /></div>
              </div>
              <div>
                <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Input VAT</div>
                <div className="font-mono"><CurrencyDisplay amount={stats.input_vat} currency={currency} /></div>
              </div>
              <div>
                <div className="text-xs mb-1" style={{ color: 'var(--tt-text-muted)' }}>Net VAT Due</div>
                <div className="font-mono font-semibold"><CurrencyDisplay amount={stats.net_vat_due} currency={currency} /></div>
              </div>
            </div>
          )}
        </div>

        {/* Transactions */}
        <div>
          <h4 className="font-semibold text-sm uppercase tracking-wide mb-3" style={{ color: 'var(--tt-text-muted)' }}>
            Transactions ({document.period})
          </h4>

          {/* Resolved */}
          <details open className="mb-4">
            <summary className="cursor-pointer flex items-center gap-2 text-sm font-medium mb-2" style={{ color: 'var(--tt-success)' }}>
              ✅ Resolved ({resolvedCount})
            </summary>
            <div className="bg-white rounded-lg border border-[var(--tt-border)] max-h-48 overflow-y-auto">
              <table className="w-full text-sm">
                <tbody>
                  {periodTransactions.filter(t => t.reconciliation_status === 'approved' || t.reconciliation_status === 'matched').map((txn, idx) => (
                    <tr key={txn.id} className={idx % 2 === 0 ? '' : 'bg-[var(--tt-bg-alt)]'}>
                      <td className="px-3 py-2 font-mono text-xs">{txn.id}</td>
                      <td className="px-3 py-2 text-xs">{txn.category || 'N/A'}</td>
                      <td className="px-3 py-2 text-xs text-right font-mono">
                        <CurrencyDisplay amount={txn.amount} currency={txn.currency} showSign />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>

          {/* Unresolved */}
          {unresolvedCount > 0 && (
            <details open className="mb-4">
              <summary className="cursor-pointer flex items-center gap-2 text-sm font-medium mb-2" style={{ color: 'var(--tt-warning)' }}>
                ⚠️ Unresolved ({unresolvedCount})
              </summary>
              <div className="bg-[var(--tt-warning-bg)] rounded-lg border border-[var(--tt-warning)] p-3 space-y-2">
                {periodTransactions.filter(t => t.reconciliation_status !== 'approved' && t.reconciliation_status !== 'matched').map(txn => (
                  <div key={txn.id} className="flex items-center justify-between text-sm">
                    <span className="font-mono text-xs">{txn.id}</span>
                    <span className="text-xs">{txn.category || 'Unknown'}</span>
                    <span className="font-mono text-xs"><CurrencyDisplay amount={txn.amount} currency={txn.currency} showSign /></span>
                  </div>
                ))}
              </div>
              <button
                onClick={handleAutoApproveAll}
                className="mt-2 w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[var(--tt-success)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
              >
                <CheckCircle className="w-4 h-4" />
                Auto-approve all transactions
              </button>
            </details>
          )}
        </div>

        {/* Generate Document */}
        <div className="border-t border-[var(--tt-border)] pt-6">
          <h4 className="font-semibold text-sm uppercase tracking-wide mb-3" style={{ color: 'var(--tt-text-muted)' }}>
            Generate Document
          </h4>

          {!generated && !generating && (
            <button
              onClick={handleGenerate}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg bg-[var(--tt-primary)] text-white font-medium hover:bg-[var(--tt-primary-dark)] transition-all"
            >
              <FileText className="w-5 h-5" />
              Generate Filing Document
            </button>
          )}

          {generating && (
            <div className="text-center py-8">
              <div className="w-12 h-12 border-4 border-[var(--tt-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p style={{ color: 'var(--tt-text-muted)' }}>Generating with AI...</p>
            </div>
          )}

          {generated && showPDF && (
            <div className="space-y-4">
              {/* PDF Preview */}
              <div className="bg-[var(--tt-bg-alt)] rounded-lg border border-[var(--tt-border)] p-6 text-center">
                <FileText className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--tt-primary)' }} />
                <h5 className="font-semibold mb-2" style={{ color: 'var(--tt-text)' }}>
                  {document.jurisdiction} {document.form_number} — {document.period}
                </h5>
                <p className="text-sm mb-4" style={{ color: 'var(--tt-text-muted)' }}>
                  Document generated and ready for review
                </p>
                <div className="text-xs space-y-1" style={{ color: 'var(--tt-text-muted)' }}>
                  <div>Pages: 8</div>
                  <div>Generated: {new Date().toLocaleString()}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <a
                  href={`http://localhost:8000/api/documents/${docId}/pdf`}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[var(--tt-border)] hover:bg-[var(--tt-bg-alt)] transition-colors"
                >
                  <Download className="w-4 h-4" />
                  View PDF
                </a>
                <button
                  onClick={handleApprove}
                  className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[var(--tt-success)] text-white hover:opacity-90 transition-opacity"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </button>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[var(--tt-border)] hover:bg-[var(--tt-bg-alt)] transition-colors">
                  <Edit className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={() => { setShowPDF(false); setGenerated(false); }}
                  className="flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-[var(--tt-border)] hover:bg-[var(--tt-bg-alt)] transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  Regenerate
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </SlidePanel>
  );
};
