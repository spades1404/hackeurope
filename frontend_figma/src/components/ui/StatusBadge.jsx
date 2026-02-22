export const StatusBadge = ({ status, children }) => {
  // Map reconciliation statuses from Addendum 5
  let label = status;
  let color = 'muted';
  let pulse = false;

  switch (status?.toLowerCase()) {
    case 'unreconciled':
      label = 'Unreconciled';
      color = 'warning';
      pulse = true;
      break;
    case 'matched':
      label = 'Matched';
      color = 'info';
      break;
    case 'approved':
      label = 'Approved';
      color = 'success';
      break;
    case 'flagged':
    case 'needs_review':
      label = 'Flagged';
      color = 'danger';
      break;
    default:
      label = status || 'Unknown';
      color = 'muted';
  }

  const colors = {
    success: 'bg-[var(--tt-success-bg)] text-[var(--tt-success)] border-[var(--tt-success)]/20',
    danger: 'bg-[var(--tt-danger-bg)] text-[var(--tt-danger)] border-[var(--tt-danger)]/20',
    warning: 'bg-[var(--tt-warning-bg)] text-[var(--tt-warning)] border-[var(--tt-warning)]/20',
    info: 'bg-[var(--tt-primary-glow)] text-[var(--tt-primary)] border-[var(--tt-primary)]/20',
    muted: 'bg-[var(--tt-bg-alt)] text-[var(--tt-text-muted)] border-[var(--tt-border)]',
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${colors[color]} ${pulse ? 'animate-pulse' : ''}`}>
      {children || label}
    </span>
  );
};
