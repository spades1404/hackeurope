import { CurrencyDisplay } from '../ui/CurrencyDisplay';

export const TaxOverview = ({ financials }) => {
  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
      <h3 className="font-semibold text-lg mb-4" style={{ color: 'var(--tt-text)' }}>
        Tax Overview
      </h3>

      <div className="space-y-4">
        {Object.entries(financials.by_jurisdiction).map(([code, data]) => {
          const flag = code === 'US' ? '🇺🇸' : code === 'UK' ? '🇬🇧' : code === 'DE' ? '🇩🇪' : '🇦🇺';
          const paid = data.tax_exposure * 0.6; // Mock: 60% paid
          const percentage = (paid / data.tax_exposure) * 100;

          return (
            <div key={code} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{flag}</span>
                  <span className="font-medium" style={{ color: 'var(--tt-text-body)' }}>
                    {code}
                  </span>
                </div>
                <div className="text-right">
                  <div className="font-mono text-sm" style={{ color: 'var(--tt-text-body)' }}>
                    <CurrencyDisplay amount={paid} currency={data.currency} /> / <CurrencyDisplay amount={data.tax_exposure} currency={data.currency} />
                  </div>
                  <div className="text-xs" style={{ color: 'var(--tt-text-muted)' }}>
                    {percentage.toFixed(0)}% paid
                  </div>
                </div>
              </div>

              {/* Progress bar */}
              <div className="h-2 bg-[var(--tt-bg-alt)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--tt-success)] transition-all"
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
