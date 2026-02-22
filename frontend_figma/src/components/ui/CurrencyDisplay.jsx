export const CurrencyDisplay = ({ amount, currency = 'USD', showSign = false, className = '' }) => {
  const symbols = {
    USD: '$',
    GBP: '£',
    EUR: '€',
    AUD: 'A$',
  };

  const symbol = symbols[currency] || '$';
  const isNegative = amount < 0;
  const absAmount = Math.abs(amount);
  
  const formatted = absAmount.toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });

  const sign = showSign ? (isNegative ? '-' : '+') : (isNegative ? '-' : '');
  const color = isNegative ? 'text-[var(--tt-danger)]' : 'text-[var(--tt-success)]';

  return (
    <span 
      className={`font-mono ${showSign ? color : ''} ${className}`}
      style={{ fontFamily: 'var(--font-mono)' }}
    >
      {sign}{symbol}{formatted}
    </span>
  );
};
