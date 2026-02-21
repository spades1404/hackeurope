import React from 'react';
import { Card } from '../ui/Card';
import { ProfitLossCard } from './ProfitLossCard';
import { ExpenseBreakdown } from './ExpenseBreakdown';
import { TaxOverview } from './TaxOverview';
import { ComplianceStatus } from './ComplianceStatus';
import { MOCK_COMPANY, MOCK_FINANCIALS } from '../../data/mockData';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';

const StatCard = ({ title, amount, yoy, isPositiveGood = true }) => {
    const isPositive = yoy > 0;
    const isGood = isPositiveGood ? isPositive : !isPositive;

    return (
        <Card style={{ padding: '24px' }}>
            <div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '8px', fontWeight: '500' }}>{title}</div>
            <div style={{ fontSize: '36px', fontWeight: '700', fontFamily: 'var(--font-mono)', marginBottom: '16px' }}>
                <CurrencyDisplay amount={amount} currency="USD" />
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', fontWeight: '500', color: isGood ? 'var(--color-success)' : 'var(--color-error)' }}>
                {isPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                <span>{Math.abs(yoy)}% YoY</span>
            </div>
        </Card>
    );
};

export const BusinessDashboard = () => {
    const { totalRevenue, totalExpense, netProfit, revenueYoY, expenseYoY, profitYoY } = MOCK_FINANCIALS;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', animation: 'fadeIn 0.5s ease-out' }}>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h2 style={{ fontSize: '20px', fontWeight: '600', margin: 0 }}>Business Overview — {MOCK_COMPANY.name}</h2>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>As of {new Date().toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}</div>
            </div>

            {/* Top Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' }}>
                <StatCard title="Total Revenue" amount={totalRevenue} yoy={revenueYoY} />
                <StatCard title="Total Expenses" amount={totalExpense} yoy={expenseYoY} isPositiveGood={false} />
                <StatCard title="Net Profit" amount={netProfit} yoy={profitYoY} />
            </div>

            {/* Main Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '24px' }}>
                <ProfitLossCard />
                <TaxOverview />
                <ExpenseBreakdown />
                <ComplianceStatus />
            </div>

        </div>
    );
};
