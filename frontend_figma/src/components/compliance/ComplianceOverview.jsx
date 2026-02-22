import { DocumentCard } from './DocumentCard';
import { AlertCircle, Clock, CheckCircle2, Calendar } from 'lucide-react';

export const ComplianceOverview = ({ documents, onDocumentClick }) => {
  const summary = {
    overdue: documents.filter(d => d.status === 'overdue').length,
    upcoming: documents.filter(d => d.status === 'upcoming' && d.days_until && d.days_until < 30).length,
    future: documents.filter(d => d.status === 'scheduled' || (d.days_until && d.days_until >= 30)).length,
    filed: documents.filter(d => d.status === 'sent' || d.status === 'approved').length,
  };

  const groupedByJurisdiction = documents.reduce((acc, doc) => {
    if (!acc[doc.jurisdiction]) {
      acc[doc.jurisdiction] = [];
    }
    acc[doc.jurisdiction].push(doc);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-[var(--tt-danger)] p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle className="w-5 h-5" style={{ color: 'var(--tt-danger)' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--tt-text-muted)' }}>Overdue</span>
          </div>
          <div className="text-3xl font-bold" style={{ color: 'var(--tt-danger)' }}>{summary.overdue}</div>
        </div>

        <div className="bg-white rounded-lg border border-[var(--tt-warning)] p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-5 h-5" style={{ color: 'var(--tt-warning)' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--tt-text-muted)' }}>Due {'<'}30 days</span>
          </div>
          <div className="text-3xl font-bold" style={{ color: 'var(--tt-warning)' }}>{summary.upcoming}</div>
        </div>

        <div className="bg-white rounded-lg border border-[var(--tt-border)] p-4">
          <div className="flex items-center gap-2 mb-2">
            <Calendar className="w-5 h-5" style={{ color: 'var(--tt-text-muted)' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--tt-text-muted)' }}>Upcoming</span>
          </div>
          <div className="text-3xl font-bold" style={{ color: 'var(--tt-text)' }}>{summary.future}</div>
        </div>

        <div className="bg-white rounded-lg border border-[var(--tt-success)] p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-5 h-5" style={{ color: 'var(--tt-success)' }} />
            <span className="text-sm font-medium" style={{ color: 'var(--tt-text-muted)' }}>Filed</span>
          </div>
          <div className="text-3xl font-bold" style={{ color: 'var(--tt-success)' }}>{summary.filed}</div>
        </div>
      </div>

      {/* Documents by Jurisdiction */}
      {Object.entries(groupedByJurisdiction).map(([jurisdiction, docs]) => {
        const firstDoc = docs[0];
        return (
          <div key={jurisdiction} className="bg-white rounded-lg border border-[var(--tt-border)] p-6">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">{firstDoc.flag}</span>
              <h2 className="text-xl font-semibold" style={{ color: 'var(--tt-text)' }}>
                {firstDoc.jurisdiction_name}
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {docs.map(doc => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onClick={() => onDocumentClick(doc)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};
