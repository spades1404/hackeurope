import { Link, useLocation } from 'react-router';
import { LayoutDashboard, FileText, Plug, LogOut } from 'lucide-react';
import { Logo } from '../ui/Logo';
import { useAuth } from '../../contexts/AuthContext';

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  const workerNav = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/compliance', icon: FileText, label: 'Compliance' },
    { path: '/connectors', icon: Plug, label: 'Connectors' },
  ];

  const businessNav = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/connectors', icon: Plug, label: 'Connectors' },
  ];

  const navItems = user?.role === 'worker' ? workerNav : businessNav;

  return (
    <div className="w-60 h-screen bg-[var(--tt-bg-alt)] border-r border-[var(--tt-border)] flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-[var(--tt-border)]">
        <Logo size="default" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                active
                  ? 'bg-[var(--tt-primary-ghost)] text-[var(--tt-primary)] border-l-3 border-[var(--tt-primary)]'
                  : 'text-[var(--tt-text-body)] hover:bg-white hover:shadow-sm'
              }`}
              style={active ? { borderLeftWidth: '3px' } : {}}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User Section */}
      <div className="p-4 border-t border-[var(--tt-border)]">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-full bg-[var(--tt-primary)] flex items-center justify-center text-white font-semibold">
            {user?.name?.charAt(0) || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-medium text-sm truncate" style={{ color: 'var(--tt-text-body)' }}>
              {user?.name}
            </div>
            <div className="text-xs" style={{ color: 'var(--tt-text-muted)' }}>
              {user?.role === 'worker' ? 'Worker' : 'Business'}
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 w-full px-4 py-2 rounded-lg text-sm font-medium hover:bg-white transition-colors"
          style={{ color: 'var(--tt-text-muted)' }}
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </div>
  );
};
