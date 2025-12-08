import { useEffect, useState } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { Loader2, FileText, AlertCircle, IndianRupee, Users } from 'lucide-react';
import LanguageSwitcher from '../../components/LanguageSwitcher';

export default function OfficialDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/dashboard/stats')
      .then(({ data }) => setStats(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex justify-center items-center h-screen">
      <Loader2 className="w-8 h-8 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>

      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">{t('officialDashboard.title')}</h1>
          <p className="text-gray-600">{t('officialDashboard.subtitle')}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={<FileText className="w-8 h-8" />}
            title={t('officialDashboard.totalCases')}
            value={stats?.total_cases || 0}
          />
          <StatCard
            icon={<AlertCircle className="w-8 h-8" />}
            title={t('officialDashboard.pendingVerification')}
            value={stats?.pending_verification || 0}
          />
          <StatCard
            icon={<IndianRupee className="w-8 h-8" />}
            title={t('officialDashboard.compensationPaid')}
            value={`₹${(stats?.compensation_paid || 0).toLocaleString()}`}
          />
          <StatCard
            icon={<Users className="w-8 h-8" />}
            title={t('officialDashboard.activeUsers')}
            value={stats?.active_users || 0}
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <div className="text-blue-600 mb-3">{icon}</div>
      <h3 className="text-sm text-gray-600 mb-1">{title}</h3>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
