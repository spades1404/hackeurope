import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Sector } from 'recharts';
import { MOCK_FINANCIALS } from '../../data/mockData';

const COLORS = ['#3B82F6', '#8B5CF6', '#F59E0B', '#10B981', '#EC4899', '#64748B'];

const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
        return (
            <div style={{ backgroundColor: 'var(--color-bg-surface)', padding: '12px', border: '1px solid var(--color-border)', borderRadius: '8px' }}>
                <p style={{ margin: 0, fontWeight: '500', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: payload[0].payload.fill }} />
                    {payload[0].name}: {payload[0].value}%
                </p>
            </div>
        );
    }
    return null;
};

export const ExpenseBreakdown = () => {
    const data = MOCK_FINANCIALS.expenseBreakdown;
    const [activeIndex, setActiveIndex] = useState(null);

    return (
        <Card style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: 'var(--color-text-primary)' }}>
                Expense Breakdown
            </h3>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
                {/* Center label */}
                <div style={{ position: 'absolute', top: '40%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none' }}>
                    <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--color-text-primary)' }}>100%</div>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Total Exp</div>
                </div>

                <div style={{ flex: 1 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="45%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                                onMouseEnter={(_, index) => setActiveIndex(index)}
                                onMouseLeave={() => setActiveIndex(null)}
                            >
                                {data.map((entry, index) => (
                                    <Cell
                                        key={`cell-${index}`}
                                        fill={COLORS[index % COLORS.length]}
                                        style={{ transition: 'all 0.3s ease', opacity: activeIndex === null || activeIndex === index ? 1 : 0.5, cursor: 'pointer' }}
                                    />
                                ))}
                            </Pie>
                            <Tooltip content={<CustomTooltip />} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
                    {data.map((item, index) => (
                        <div key={item.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <div style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: COLORS[index % COLORS.length] }} />
                                <span style={{ color: 'var(--color-text-muted)' }}>{item.name}</span>
                            </div>
                            <span style={{ fontWeight: '600', fontFamily: 'var(--font-mono)' }}>{item.value}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </Card>
    );
};
