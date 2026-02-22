import { ArrowRight, AlertCircle, Clock } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';

export const DocumentCard = ({ document, onClick }) => {
  const getDaysText = () => {
    if (document.days_overdue) {
      return `${document.days_overdue} days overdue`;
    }
    if (document.days_until) {
      return `${document.days_until} days left`;
    }
    if (document.filed_date) {
      return `Filed ${new Date(document.filed_date).toLocaleDateString()}`;
    }
    if (document.approved_date) {
      return `Approved ${new Date(document.approved_date).toLocaleDateString()}`;
    }
    return '';
  };

  const getIcon = () => {
    if (document.status === 'overdue') {
      return <AlertCircle className="w-5 h-5" style={{ color: 'var(--tt-danger)' }} />;
    }
    if (document.status === 'upcoming') {
      return <Clock className="w-5 h-5" style={{ color: 'var(--tt-warning)' }} />;
    }
    return null;
  };

  return (
    <div
      onClick={onClick}
      className="bg-[var(--tt-bg-alt)] rounded-lg border border-[var(--tt-border)] p-4 hover:border-[var(--tt-primary)] hover:shadow-md transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="font-mono font-semibold text-base mb-1" style={{ color: 'var(--tt-text)' }}>
            {document.form_number}
          </div>
          <div className="text-sm mb-2" style={{ color: 'var(--tt-text-body)' }}>
            {document.name}
          </div>
        </div>
        {getIcon()}
      </div>

      <div className="space-y-2">
        <div className="text-xs" style={{ color: 'var(--tt-text-muted)' }}>
          Due: {new Date(document.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>
        
        <div className="flex items-center justify-between">
          <StatusBadge status={document.status} />
          {getDaysText() && (
            <div className={`text-xs font-medium ${
              document.status === 'overdue' ? 'text-[var(--tt-danger)]' : 
              document.status === 'upcoming' ? 'text-[var(--tt-warning)]' : 
              'text-[var(--tt-text-muted)]'
            }`}>
              {getDaysText()}
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-[var(--tt-border-light)] flex items-center justify-between">
        <span className="text-xs font-medium group-hover:text-[var(--tt-primary)] transition-colors" style={{ color: 'var(--tt-text-muted)' }}>
          View Details
        </span>
        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" style={{ color: 'var(--tt-primary)' }} />
      </div>
    </div>
  );
};
