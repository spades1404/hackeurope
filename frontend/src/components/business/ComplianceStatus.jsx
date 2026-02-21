import React from 'react';
import { Card } from '../ui/Card';
import { StatusBadge } from '../shared/StatusBadge';
import { CountdownBadge } from '../shared/CountdownBadge';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';
import { MOCK_COMPLIANCE_ACTIONS } from '../../data/mockData';

export const ComplianceStatus = () => {
    const actions = [...MOCK_COMPLIANCE_ACTIONS];
    const sortedActions = actions.sort((a, b) => a.daysRemaining - b.daysRemaining);
    const nextUp = sortedActions.filter(a => a.status !== 'submitted')[0];

    const stats = {
        dueSoon: actions.filter(a => a.daysRemaining >= 0 && a.daysRemaining <= 30 && a.status !== 'submitted').length,
        upcoming: actions.filter(a => a.daysRemaining > 30 && a.daysRemaining <= 90 && a.status !== 'submitted').length,
        filed: actions.filter(a => a.status === 'submitted').length
    };

    return (
        <Card style={{ height: '400px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '24px', color: 'var(--color-text-primary)' }}>
                Compliance Status
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '24px' }}>
                <div style={{ backgroundColor: 'var(--color-bg-base)', padding: '12px', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '24px', fontWeight: '700', fontFamily: 'var(--font-mono)', color: 'var(--color-warning)' }}>{stats.dueSoon}</div>
                    <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--color-text-muted)' }}>DUE &lt;30 DAYS</div>
                </div>
                <div style={{ backgroundColor: 'var(--color-bg-base)', padding: '12px', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '24px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{stats.upcoming}</div>
                    <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--color-text-muted)' }}>UPCOMING (QTR)</div>
                </div>
                <div style={{ backgroundColor: 'var(--color-bg-base)', padding: '12px', borderRadius: '8px', border: '1px solid var(--color-border)' }}>
                    <div style={{ fontSize: '24px', fontWeight: '700', fontFamily: 'var(--font-mono)', color: 'var(--color-success)' }}>{stats.filed}</div>
                    <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--color-text-muted)' }}>FILED YTD</div>
                </div>
            </div>

            <div style={{ flex: 1, backgroundColor: 'var(--color-bg-base)', borderRadius: '8px', border: '1px solid var(--color-border)', padding: '16px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '12px', fontWeight: '500' }}>Next upcoming deadline:</div>

                {nextUp ? (
                    <>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <JurisdictionFlag jurisdiction={nextUp.jurisdiction} />
                            <div style={{ fontWeight: '600', fontSize: '15px' }}>{nextUp.name}</div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{nextUp.form}</span>
                            <CountdownBadge daysRemaining={nextUp.daysRemaining} priority={nextUp.priority} />
                        </div>

                        <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: '12px' }}>
                            <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>AI Status:</span>
                            <StatusBadge status={nextUp.status} />
                        </div>
                    </>
                ) : (
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
                        All caught up!
                    </div>
                )}
            </div>
        </Card>
    );
};
