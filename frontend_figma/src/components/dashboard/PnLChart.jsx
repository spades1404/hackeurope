import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const PnLChart = ({ financials }) => {
  const data = Object.entries(financials.by_jurisdiction).map(([code, data]) => ({
    jurisdiction: code,
    revenue: data.revenue / 1000000,
    expenses: data.expenses / 1000000,
    flag: code === 'US' ? '🇺🇸' : code === 'UK' ? '🇬🇧' : code === 'DE' ? '🇩🇪' : '🇦🇺',
  }));

  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
      <h3 className="font-semibold text-lg mb-4" style={{ color: 'var(--tt-text)' }}>
        P&L by Jurisdiction
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--tt-border-light)" />
          <XAxis 
            dataKey="jurisdiction" 
            tick={{ fill: 'var(--tt-text-muted)', fontSize: 12 }}
            tickFormatter={(value, index) => `${data[index].flag} ${value}`}
          />
          <YAxis 
            tick={{ fill: 'var(--tt-text-muted)', fontSize: 12 }}
            label={{ value: 'Amount (M)', angle: -90, position: 'insideLeft', style: { fill: 'var(--tt-text-muted)' } }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid var(--tt-border)',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            formatter={(value) => `$${value.toFixed(2)}M`}
          />
          <Legend />
          <Bar dataKey="revenue" fill="var(--tt-success)" radius={[4, 4, 0, 0]} name="Revenue" />
          <Bar dataKey="expenses" fill="var(--tt-danger)" radius={[4, 4, 0, 0]} name="Expenses" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
