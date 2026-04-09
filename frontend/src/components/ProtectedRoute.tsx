import { Navigate } from 'react-router-dom';
import { useAuthStore, hasRole } from '@/stores/auth';
import { ConfigSphereRole } from '@/types';

interface Props {
  children: React.ReactNode;
  minRole?: ConfigSphereRole;
}

const ProtectedRoute = ({ children, minRole = 'viewer' }: Props) => {
  const { token, user } = useAuthStore();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (user && !hasRole(user, minRole)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
