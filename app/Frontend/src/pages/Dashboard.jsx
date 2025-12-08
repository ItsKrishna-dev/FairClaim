import { useAuth } from '../context/AuthContext';
import VictimDashboard from './dashboard/VictimDashboard';
import OfficialDashboard from './dashboard/OfficialDashboard';
import { Navigate } from 'react-router-dom';

export default function Dashboard() {
  const { user, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  if (!user) return <Navigate to="/login" />;

  // Render based on 'role' field from User model in models.py
  if (user?.role === 'victim' || user?.role?.toUpperCase() === 'VICTIM') {
    return <VictimDashboard />;
  }
  
  return <OfficialDashboard />;
}