import React, { useState } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Modal } from '../ui/Modal';
import { StatusBadge } from '../shared/StatusBadge';
import { CountdownBadge } from '../shared/CountdownBadge';
import { JurisdictionFlag } from '../shared/JurisdictionFlag';
import { MOCK_COMPLIANCE_ACTIONS } from '../../data/mockData';
import { FileText, CheckCircle, Edit2, Play, Download } from 'lucide-react';

export const ComplianceTab = () => {
    const [actions, setActions] = useState(MOCK_COMPLIANCE_ACTIONS);
    const [selectedDoc, setSelectedDoc] = useState(null);

    const handleApprove = (id) => {
        setActions(prev => prev.map(a => a.id === id ? { ...a, status: 'approved' } : a));
        setSelectedDoc(null);
    };

    const handleGenerate = (id) => {
        setActions(prev => prev.map(a => a.id === id ? { ...a, status: 'generating' } : a));
        setTimeout(() => {
            setActions(prev => prev.map(a => a.id === id ? { ...a, status: 'draft_generated' } : a));
        }, 2000);
    };

    const stats = {
        overdue: actions.filter(a => a.status === 'overdue').length,
        dueSoon: actions.filter(a => a.daysRemaining >= 0 && a.daysRemaining <= 30).length,
        upcoming: actions.filter(a => a.daysRemaining > 30 && a.status !== 'submitted').length,
        filed: actions.filter(a => a.status === 'submitted').length
    };

    // Sort by days remaining
    const sortedActions = [...actions].sort((a, b) => a.daysRemaining - b.daysRemaining);

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', animation: 'fadeIn 0.4s' }}>

            {/* Overview Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                <Card style={{ borderLeft: '3px solid var(--color-error)' }}>
                    <div style={{ fontSize: '32px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{stats.overdue}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)' }}>OVERDUE</div>
                </Card>
                <Card style={{ borderLeft: '3px solid var(--color-warning)' }}>
                    <div style={{ fontSize: '32px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{stats.dueSoon}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)' }}>DUE &lt;30 DAYS</div>
                </Card>
                <Card style={{ borderLeft: '3px solid var(--color-info)' }}>
                    <div style={{ fontSize: '32px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{stats.upcoming}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)' }}>UPCOMING THIS QTR</div>
                </Card>
                <Card style={{ borderLeft: '3px solid var(--color-success)' }}>
                    <div style={{ fontSize: '32px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{stats.filed}</div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)' }}>FILED THIS QTR</div>
                </Card>
            </div>

            {/* Timeline View (Simplified for Demo) */}
            <Card style={{ overflowX: 'auto', whiteSpace: 'nowrap', padding: '32px 24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', position: 'relative', width: 'max-content', minWidth: '100%' }}>
                    {/* Base line */}
                    <div style={{ position: 'absolute', top: '5px', left: '0', right: '0', height: '2px', backgroundColor: 'var(--color-border)', zIndex: 1 }} />

                    {/* Today marker */}
                    <div style={{ position: 'absolute', top: '-10px', left: '10%', height: '32px', width: '2px', backgroundColor: 'var(--color-accent)', zIndex: 1 }} />
                    <div style={{ position: 'absolute', top: '24px', left: 'calc(10% - 14px)', fontSize: '11px', fontWeight: '700', color: 'var(--color-accent)' }}>TODAY</div>

                    {sortedActions.slice(0, 7).map((action, idx) => {
                        // Position based on days remaining (simplified math for horizontal layout)
                        const offset = 10 + Math.max(0, action.daysRemaining) * 0.5;
                        const isOverdue = action.daysRemaining < 0;

                        const color = isOverdue ? 'var(--color-error)' :
                            action.daysRemaining <= 30 ? 'var(--color-warning)' :
                                action.priority === 'medium' ? 'var(--color-info)' : 'var(--color-text-muted)';

                        return (
                            <div key={action.id} style={{ position: 'absolute', left: `${Math.min(95, offset)}%`, top: '0', display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2 }}>
                                <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: color, border: '2px solid var(--color-bg-surface)' }} />
                                <div style={{ marginTop: '12px', fontSize: '12px', fontWeight: '500' }}>{new Date(action.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>{action.jurisdiction} {action.form}</div>
                            </div>
                        );
                    })}
                </div>
                <div style={{ height: '40px' }} />
            </Card>

            {/* Action Cards */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {sortedActions.map(action => (
                    <Card key={action.id} style={{ display: 'flex', flexDirection: 'column', gap: '16px', opacity: action.status === 'submitted' ? 0.7 : 1 }}>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                    <JurisdictionFlag jurisdiction={action.jurisdiction} />
                                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>{action.name} ({action.form})</h3>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '13px', color: 'var(--color-text-muted)' }}>
                                    <span>Due: {new Date(action.dueDate).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                                    <CountdownBadge daysRemaining={action.daysRemaining} priority={action.priority} />
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>AI Status:</span>
                                <StatusBadge status={action.status} dot={['generating', 'overdue'].includes(action.status)} />
                            </div>
                        </div>

                        <div style={{ display: 'flex', gap: '12px', borderTop: '1px solid var(--color-border)', paddingTop: '16px', marginTop: '4px' }}>
                            {action.status === 'not_started' && (
                                <Button variant="primary" onClick={() => handleGenerate(action.id)}>
                                    <Play size={16} style={{ marginRight: '6px' }} /> Generate Draft
                                </Button>
                            )}
                            {action.status === 'generating' && (
                                <Button variant="secondary" disabled>
                                    Generating...
                                </Button>
                            )}
                            {action.status === 'draft_generated' && (
                                <>
                                    <Button variant="primary" onClick={() => setSelectedDoc(action)}>
                                        <FileText size={16} style={{ marginRight: '6px' }} /> Review AI Draft
                                    </Button>
                                    <Button variant="secondary"><Edit2 size={16} style={{ marginRight: '6px' }} /> Edit</Button>
                                    <Button variant="secondary" onClick={() => handleApprove(action.id)} style={{ color: 'var(--color-success)', borderColor: 'var(--color-border)' }}>
                                        <CheckCircle size={16} style={{ marginRight: '6px' }} /> Quick Approve
                                    </Button>
                                </>
                            )}
                            {action.status === 'approved' && (
                                <>
                                    <Button variant="primary" onClick={() => setActions(prev => prev.map(a => a.id === action.id ? { ...a, status: 'submitted' } : a))}>
                                        Submit Filing
                                    </Button>
                                    <Button variant="ghost">Revoke Approval</Button>
                                </>
                            )}
                            {(action.status === 'submitted' || action.status === 'overdue') && (
                                <>
                                    <Button variant="secondary"><FileText size={16} style={{ marginRight: '6px' }} /> View Filing</Button>
                                    <Button variant="ghost"><Download size={16} style={{ marginRight: '6px' }} /> PDF</Button>
                                </>
                            )}
                        </div>

                    </Card>
                ))}
            </div>

            {/* Document Viewer Modal */}
            <Modal isOpen={!!selectedDoc} onClose={() => setSelectedDoc(null)} title={`Review: ${selectedDoc?.name}`}>
                {selectedDoc && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ backgroundColor: '#fff', color: '#000', padding: '40px', borderRadius: '4px', minHeight: '400px', fontSize: '13px', fontFamily: 'serif' }}>
                            <h1 style={{ textAlign: 'center', marginBottom: '8px' }}>{selectedDoc.jurisdiction} Department of Treasury</h1>
                            <h2 style={{ textAlign: 'center', marginBottom: '32px' }}>{selectedDoc.form} - {selectedDoc.name}</h2>
                            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #000', paddingBottom: '8px', marginBottom: '24px' }}>
                                <div><strong>Company:</strong> Acme Global Corp</div>
                                <div><strong>Tax ID:</strong> 98-7654321</div>
                            </div>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <tbody>
                                    <tr><td style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>1. Gross receipts or sales</td><td style={{ padding: '8px', borderBottom: '1px solid #ccc', textAlign: 'right' }}>$4,500,000.00</td></tr>
                                    <tr><td style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>2. Cost of goods sold</td><td style={{ padding: '8px', borderBottom: '1px solid #ccc', textAlign: 'right' }}>$1,350,000.00</td></tr>
                                    <tr><td style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>3. Gross profit</td><td style={{ padding: '8px', borderBottom: '1px solid #ccc', textAlign: 'right', fontWeight: 'bold' }}>$3,150,000.00</td></tr>
                                    <tr><td style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>4. Total deductions</td><td style={{ padding: '8px', borderBottom: '1px solid #ccc', textAlign: 'right' }}>$1,750,000.00</td></tr>
                                    <tr><td style={{ padding: '8px', borderBottom: '1px solid #ccc' }}>5. Ordinary business income</td><td style={{ padding: '8px', borderBottom: '1px solid #ccc', textAlign: 'right', fontWeight: 'bold' }}>$1,400,000.00</td></tr>
                                </tbody>
                            </table>
                        </div>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', borderTop: '1px solid var(--color-border)', paddingTop: '16px' }}>
                            <Button variant="secondary" onClick={() => setSelectedDoc(null)}>Cancel</Button>
                            <Button variant="secondary"><Edit2 size={16} style={{ marginRight: '6px' }} /> Request Changes</Button>
                            <Button variant="primary" onClick={() => handleApprove(selectedDoc.id)}>
                                <CheckCircle size={16} style={{ marginRight: '6px' }} /> Approve & Sign
                            </Button>
                        </div>
                    </div>
                )}
            </Modal>

        </div>
    );
};
