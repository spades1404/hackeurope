import React from 'react';
import { Card } from '../ui/Card';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { MOCK_FINANCIALS } from '../../data/mockData';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{ backgroundColor: 'var(--color-bg-surface)', padding: '12px', border: '1px solid var(--color-border)', borderRadius: '8px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}>
                <p style={{ fontWeight: '600', marginBottom: '8px', borderBottom: '1px solid var(--color-border)', paddingBottom: '4px' }}>{label}</p>
                {payload.map((entry, index) => (
                    <div key={index} style={{ color: entry.color, fontSize: '14px', margin: '4px 0', display: 'flex', justifyContent: 'space-between', gap: '20px' }}>
                        <span>{entry.name}:</span>
                        <span style={{ fontFamily: 'var(--font-mono)' }}><CurrencyDisplay amount={entry.value} currency="USD" /></span>
                    </div>
                ))}
            </div>
        );
    }
    return null;
};

export const ProfitLossCard = () => {
    const data = MOCK_FINANCIALS.jurisdictions;
    return (
        <Card style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: 'var(--color-text-primary)' }}>
                Profit & Loss by Jurisdiction
            </h3>
            <div style={{ flex: 1, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <XAxis dataKey="id" stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }} />
                        <YAxis stroke="var(--color-text-muted)" tick={{ fill: 'var(--color-text-muted)', fontSize: 12, fontFamily: 'var(--font-mono)' }}
                            tickFormatter={(value) => `$${value / 1000}k`} />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} />
                        <Bar dataKey="revenue" name="Revenue" fill="var(--color-success)" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="expenses" name="Expenses" fill="var(--color-error)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </Card>
    );
};
