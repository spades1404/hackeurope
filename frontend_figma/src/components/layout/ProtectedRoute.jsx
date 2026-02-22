import { Navigate } from 'react-router';
import { useAuth } from '../../contexts/AuthContext';

export const ProtectedRoute = ({ children, workerOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[var(--tt-primary)] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p style={{ color: 'var(--tt-text-muted)' }}>Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (workerOnly && user.role !== 'worker') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};
