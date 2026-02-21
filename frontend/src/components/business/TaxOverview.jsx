import React from 'react';
import { Card } from '../ui/Card';
import { ProgressBar } from '../ui/ProgressBar';
import { CurrencyDisplay } from '../shared/CurrencyDisplay';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';
import { MOCK_FINANCIALS } from '../../data/mockData';

export const TaxOverview = () => {
    const { estimatedTax, jurisdictions } = MOCK_FINANCIALS;

    return (
        <Card style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '24px', color: 'var(--color-text-primary)' }}>
                Tax Overview
            </h3>

            <div style={{ marginBottom: '32px' }}>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Estimated Total Tax Liability</div>
                <div style={{ fontSize: '32px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>
                    <CurrencyDisplay amount={estimatedTax} currency="USD" />
                </div>
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto', paddingRight: '8px' }}>
                {jurisdictions.map(jur => (
                    <div key={jur.id}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <JurisdictionFlag jurisdiction={jur.id} />
                                <span style={{ fontWeight: '500', fontSize: '14px' }}>{jur.id} Tax</span>
                                <span style={{ fontSize: '12px', color: 'var(--color-text-muted)', backgroundColor: 'var(--color-bg-base)', padding: '2px 6px', borderRadius: '4px' }}>
                                    {jur.taxRate}% rate
                                </span>
                            </div>
                            <div style={{ fontWeight: '600', fontFamily: 'var(--font-mono)', fontSize: '14px' }}>
                                <CurrencyDisplay amount={jur.taxLiability} currency="USD" />
                            </div>
                        </div>
                        <ProgressBar progress={(jur.taxLiability / estimatedTax) * 100} color={
                            jur.id === 'US' ? 'var(--color-accent)' :
                                jur.id === 'UK' ? 'var(--color-error)' :
                                    jur.id === 'DE' ? 'var(--color-warning)' : 'var(--color-success)'
                        } />
                    </div>
                ))}
            </div>
        </Card>
    );
};
