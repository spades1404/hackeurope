import { createBrowserRouter } from 'react-router';
import { HomePage } from '../pages/HomePage';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { CompliancePage } from '../pages/CompliancePage';
import { ConnectorsPage } from '../pages/ConnectorsPage';
import AdminPage from '../pages/AdminPage';
import { ProtectedRoute } from '../components/layout/ProtectedRoute';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/compliance',
    element: (
      <ProtectedRoute workerOnly>
        <CompliancePage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/connectors',
    element: (
      <ProtectedRoute>
        <ConnectorsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: '/admin',
    element: <AdminPage />,
  },
]);
