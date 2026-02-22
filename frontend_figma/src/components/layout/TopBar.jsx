import { Bell } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { StatusBadge } from '../ui/StatusBadge';

export const TopBar = ({ title }) => {
  const { user } = useAuth();

  return (
    <div className="h-16 bg-white border-b border-[var(--tt-border)] flex items-center justify-between px-6">
      <h1 className="text-2xl font-semibold" style={{ fontFamily: 'var(--font-heading)', color: 'var(--tt-text)' }}>
        {title}
      </h1>

      <div className="flex items-center gap-4">
        <button className="p-2 rounded-lg hover:bg-[var(--tt-bg-alt)] transition-colors relative">
          <Bell className="w-5 h-5" style={{ color: 'var(--tt-text-muted)' }} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-[var(--tt-danger)] rounded-full"></span>
        </button>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="font-medium text-sm" style={{ color: 'var(--tt-text-body)' }}>
              {user?.name}
            </div>
            <div className="text-xs" style={{ color: 'var(--tt-text-muted)' }}>
              {user?.role === 'worker' ? 'Worker Account' : 'Business Account'}
            </div>
          </div>
          <div className="w-9 h-9 rounded-full bg-[var(--tt-primary)] flex items-center justify-center text-white font-semibold text-sm">
            {user?.name?.charAt(0) || 'U'}
          </div>
        </div>
      </div>
    </div>
  );
};
