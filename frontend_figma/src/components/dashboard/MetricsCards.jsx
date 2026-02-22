import { TrendingUp, TrendingDown } from 'lucide-react';
import { CurrencyDisplay } from '../ui/CurrencyDisplay';
import { motion } from 'motion/react';

export const MetricsCards = ({ financials }) => {
  const metrics = [
    {
      label: 'Revenue',
      value: financials.summary.revenue,
      change: financials.summary.revenue_change,
      currency: 'USD',
    },
    {
      label: 'Expenses',
      value: financials.summary.expenses,
      change: financials.summary.expenses_change,
      currency: 'USD',
    },
    {
      label: 'Net P&L',
      value: financials.summary.net_pnl,
      change: financials.summary.net_pnl_change,
      currency: 'USD',
    },
    {
      label: 'Tax Exposure',
      value: financials.summary.tax_exposure,
      change: null,
      currency: 'USD',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((metric, index) => (
        <motion.div
          key={metric.label}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          className="bg-white rounded-lg border border-[var(--tt-border)] p-5 hover:shadow-md transition-shadow"
        >
          <div className="text-sm font-medium mb-2" style={{ color: 'var(--tt-text-muted)' }}>
            {metric.label}
          </div>
          <div className="text-3xl font-bold mb-2">
            <CurrencyDisplay amount={metric.value} currency={metric.currency} />
          </div>
          {metric.change !== null && (
            <div className={`flex items-center gap-1 text-sm ${metric.change >= 0 ? 'text-[var(--tt-success)]' : 'text-[var(--tt-danger)]'}`}>
              {metric.change >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              <span>{Math.abs(metric.change)}%</span>
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
};
