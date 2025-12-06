import { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Loader2, TrendingUp, AlertCircle, CheckCircle, IndianRupee } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const { data } = await api.get('/dashboard/stats');
        setStats(data);
      } catch (error) {
        console.error("Failed to load stats", error);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="flex h-96 items-center justify-center"><Loader2 className="animate-spin text-gov-600" size={48} /></div>;

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-800">Overview</h2>
        <p className="text-gray-500">
          Welcome back, <span className="font-semibold text-gov-600">{user?.full_name}</span>. 
          Here is the real-time status of the DBT system.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Total Cases" 
          value={stats?.total_cases || 0} 
          icon={<TrendingUp size={24} />} 
          color="bg-blue-500" 
        />
        <StatCard 
          title="Funds Disbursed" 
          value={`₹${stats?.fund_statistics?.total_disbursed?.toLocaleString('en-IN') || 0}`} 
          icon={<IndianRupee size={24} />} 
          color="bg-green-500" 
        />
        <StatCard 
          title="Pending Grievances" 
          value={stats?.grievances?.pending ?? 0} 
          icon={<AlertCircle size={24} />} 
          color="bg-orange-500" 
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Case Status Breakdown */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <CheckCircle className="text-gov-500" size={20} /> Case Status
          </h3>
          <div className="space-y-3">
            {stats?.status_breakdown && Object.keys(stats.status_breakdown).length > 0 ? (
              Object.entries(stats.status_breakdown).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
                  <span className="capitalize font-medium text-gray-700">{key.replace(/_/g, ' ')}</span>
                  <span className="font-bold text-gov-600 bg-white px-3 py-1 rounded shadow-sm">{val}</span>
                </div>
              ))
            ) : (
                <div className="text-center py-8 text-gray-400">No cases recorded yet.</div>
            )}
          </div>
        </div>

        {/* Fund Allocation Details */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <IndianRupee className="text-green-600" size={20} /> Fund Utilization
            </h3>
            <div className="space-y-4">
                <div className="flex justify-between items-end border-b pb-2">
                    <span className="text-gray-500 text-sm">Total Allocated</span>
                    <span className="font-bold text-xl">₹{stats?.fund_statistics?.total_allocated?.toLocaleString('en-IN') || 0}</span>
                </div>
                <div className="flex justify-between items-end border-b pb-2">
                    <span className="text-gray-500 text-sm">Disbursed</span>
                    <span className="font-bold text-xl text-green-600">₹{stats?.fund_statistics?.total_disbursed?.toLocaleString('en-IN') || 0}</span>
                </div>
                <div className="flex justify-between items-end">
                    <span className="text-gray-500 text-sm">Pending Disbursement</span>
                    <span className="font-bold text-xl text-orange-500">₹{stats?.fund_statistics?.pending?.toLocaleString('en-IN') || 0}</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between transition hover:shadow-md">
      <div>
        <p className="text-gray-500 text-sm font-medium uppercase tracking-wider">{title}</p>
        <h3 className="text-3xl font-bold text-gray-800 mt-2">{value}</h3>
      </div>
      <div className={`p-4 rounded-full text-white shadow-lg ${color} bg-opacity-90`}>
        {icon}
      </div>
    </div>
  );
}