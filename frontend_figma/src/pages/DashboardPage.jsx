import { useAuth } from '../contexts/AuthContext';
import { AppShell } from '../components/layout/AppShell';
import { WorkerDashboard } from '../components/dashboard/WorkerDashboard';
import { BusinessDashboard } from '../components/dashboard/BusinessDashboard';

export const DashboardPage = () => {
  const { user } = useAuth();

  return (
    <AppShell title="Dashboard">
      {user?.role === 'worker' ? <WorkerDashboard /> : <BusinessDashboard />}
    </AppShell>
  );
};
