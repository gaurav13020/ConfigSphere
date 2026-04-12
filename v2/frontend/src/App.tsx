import { Navigate, Route, Routes } from 'react-router-dom';

import ProtectedRoute from '@/components/ProtectedRoute';
import AdminPage from '@/pages/AdminPage';
import DashboardPage from '@/pages/DashboardPage';
import LoginPage from '@/pages/LoginPage';
import RequestsPage from '@/pages/RequestsPage';
import ReviewsPage from '@/pages/ReviewsPage';
import RollbacksPage from '@/pages/RollbacksPage';
import ServicesPage from '@/pages/ServicesPage';

const App = () => (
  <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route
      path="/"
      element={
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/admin"
      element={
        <ProtectedRoute>
          <AdminPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/services"
      element={
        <ProtectedRoute>
          <ServicesPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/requests"
      element={
        <ProtectedRoute>
          <RequestsPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/reviews"
      element={
        <ProtectedRoute>
          <ReviewsPage />
        </ProtectedRoute>
      }
    />
    <Route
      path="/rollbacks"
      element={
        <ProtectedRoute>
          <RollbacksPage />
        </ProtectedRoute>
      }
    />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
);

export default App;
