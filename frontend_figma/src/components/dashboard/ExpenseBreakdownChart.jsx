import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS = ['#4059AD', '#5A73C4', '#0EA770', '#E8920B', '#E5383B'];

export const ExpenseBreakdownChart = ({ financials }) => {
  const data = financials.expense_breakdown.map((item, index) => ({
    ...item,
    color: COLORS[index % COLORS.length],
  }));

  return (
    <div className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
      <h3 className="font-semibold text-lg mb-4" style={{ color: 'var(--tt-text)' }}>
        Expense Breakdown
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ category, percentage }) => `${category} ${percentage}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="amount"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid var(--tt-border)',
              borderRadius: '8px',
              fontSize: '12px',
            }}
            formatter={(value, name, props) => {
              return [`$${(value / 1000000).toFixed(2)}M (${props.payload.percentage}%)`, props.payload.category];
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
