import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export const TaxExposureChart = ({ financials }) => {
  const data = Object.entries(financials.by_jurisdiction).map(([code, data]) => ({
    jurisdiction: code,
    exposure: data.tax_exposure / 1000, // Convert to K
    flag: code === 'US' ? '🇺🇸' : code === 'UK' ? '🇬🇧' : code === 'DE' ? '🇩🇪' : '🇦🇺',
    currency: data.currency,
  }));

  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
      <h3 className="font-semibold text-lg mb-4" style={{ color: 'var(--tt-text)' }}>
        Tax Exposure by Region
      </h3>

      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--tt-border-light)" />
          <XAxis 
            dataKey="jurisdiction" 
            tick={{ fill: 'var(--tt-text-muted)', fontSize: 12 }}
            tickFormatter={(value, index) => `${data[index].flag} ${value}`}
          />
          <YAxis 
            tick={{ fill: 'var(--tt-text-muted)', fontSize: 12 }}
            label={{ value: 'Tax Exposure (K)', angle: -90, position: 'insideLeft', style: { fill: 'var(--tt-text-muted)' } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid var(--tt-border)',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            formatter={(value, name, props) => {
              const item = props.payload;
              return [`${item.currency === 'USD' ? '$' : item.currency === 'GBP' ? '£' : item.currency === 'EUR' ? '€' : 'A$'}${value.toFixed(0)}K`, 'Tax Exposure'];
            }}
          />
          <Bar dataKey="exposure" fill="var(--tt-primary)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
