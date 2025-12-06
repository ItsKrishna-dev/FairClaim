import { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  Loader2, TrendingUp, AlertCircle, CheckCircle, IndianRupee, 
  FileText, Clock, ShieldCheck, Activity 
} from 'lucide-react';

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

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="animate-spin text-gov-600" size={48} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Common Welcome Header */}
      <div>
        <h2 className="text-3xl font-bold text-gray-800">
          {stats?.role === 'victim' ? 'My Case Dashboard' : 'Overview'}
        </h2>
        <p className="text-gray-500">
          Welcome back, <span className="font-semibold text-gov-600">{user?.full_name}</span>.
          {stats?.role === 'victim' 
            ? ' Track your compensation and case status in real-time.' 
            : ' Here is the real-time status of the DBT system.'}
        </p>
      </div>

      {/* Conditional Rendering based on Role */}
      {stats?.role === 'victim' ? (
        <VictimDashboard stats={stats} />
      ) : (
        <OfficialDashboard stats={stats} />
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*                             VICTIM DASHBOARD                               */
/* -------------------------------------------------------------------------- */
function VictimDashboard({ stats }) {
  if (!stats.has_case) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 flex items-center gap-4">
        <AlertCircle className="text-yellow-600" size={32} />
        <div>
          <h3 className="text-lg font-bold text-yellow-800">No Active Case Found</h3>
          <p className="text-yellow-700">We could not find a case linked to your profile. Please contact the SC/ST Cell if this is an error.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Money Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Total Compensation" 
          value={`₹${stats.overview.total_sanctioned.toLocaleString('en-IN')}`} 
          icon={<ShieldCheck size={24} />} 
          color="bg-blue-600" 
          subtext="Sanctioned Amount"
        />
        <StatCard 
          title="Amount Received" 
          value={`₹${stats.overview.amount_received.toLocaleString('en-IN')}`} 
          icon={<CheckCircle size={24} />} 
          color="bg-green-600" 
          subtext="Directly in Bank"
        />
        <StatCard 
          title="Pending Release" 
          value={`₹${stats.overview.amount_pending.toLocaleString('en-IN')}`} 
          icon={<Clock size={24} />} 
          color="bg-orange-500" 
          subtext={`Next: ${stats.status.next_milestone}`}
        />
      </div>

      {/* 2. Progress Bar */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
        <div className="flex justify-between items-end mb-2">
            <h3 className="font-bold text-gray-800">Disbursement Progress</h3>
            <span className="text-sm font-medium text-gov-600">{stats.overview.completion_percentage}% Complete</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4">
          <div 
            className="bg-gov-600 h-4 rounded-full transition-all duration-500 ease-out" 
            style={{ width: `${stats.overview.completion_percentage}%` }}
          ></div>
        </div>
        <p className="text-xs text-gray-400 mt-2">Funds are released automatically at FIR, Chargesheet, and Conviction stages.</p>
      </div>

      {/* 3. Detailed Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Current Stage */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Activity className="text-gov-500" size={20} /> Case Status
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between border-b pb-3">
              <span className="text-gray-600">Current Stage</span>
              <span className="font-bold text-gov-700 px-2 py-1 bg-gov-50 rounded text-sm">
                {stats.status.current_stage}
              </span>
            </div>
            <div className="flex justify-between border-b pb-3">
              <span className="text-gray-600">Disbursement Status</span>
              <span className={`font-bold px-2 py-1 rounded text-sm ${stats.status.is_verified ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'}`}>
                {stats.status.is_verified ? 'Verified' : 'Pending'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Case Number</span>
              <span className="font-mono text-gray-800">{stats.case_number}</span>
            </div>
          </div>
        </div>

        {/* Grievance Snapshot */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <AlertCircle className="text-orange-500" size={20} /> My Grievances
          </h3>
          <div className="flex flex-col items-center justify-center h-32">
             <span className="text-4xl font-extrabold text-gray-800">{stats.grievances.active_count}</span>
             <span className="text-gray-500 text-sm mt-1">Active Issues</span>
             <button className="mt-4 text-sm text-gov-600 font-medium hover:underline">
               File New Grievance &rarr;
             </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*                            OFFICIAL DASHBOARD                              */
/* -------------------------------------------------------------------------- */
function OfficialDashboard({ stats }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Total Cases" 
          value={stats.overview.total_cases} 
          icon={<TrendingUp size={24} />} 
          color="bg-blue-500" 
        />
        <StatCard 
          title="Funds Disbursed" 
          value={`₹${stats.fund_statistics.total_disbursed.toLocaleString('en-IN')}`} 
          icon={<IndianRupee size={24} />} 
          color="bg-green-500" 
        />
        <StatCard 
          title="Action Items" 
          value={stats.overview.pending_actions} 
          icon={<AlertCircle size={24} />} 
          color="bg-red-500" 
          subtext="Pending Verification / Escalations"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Case Status Breakdown */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <FileText className="text-gov-500" size={20} /> Case Breakdown
          </h3>
          <div className="space-y-3">
            {stats.status_breakdown && Object.entries(stats.status_breakdown).map(([key, val]) => (
              <div key={key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
                <span className="capitalize font-medium text-gray-700">{key.replace(/_/g, ' ')}</span>
                <span className="font-bold text-gov-600 bg-white px-3 py-1 rounded shadow-sm">{val}</span>
              </div>
            ))}
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
                    <span className="font-bold text-xl">₹{stats.fund_statistics.total_allocated.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between items-end border-b pb-2">
                    <span className="text-gray-500 text-sm">Disbursed</span>
                    <span className="font-bold text-xl text-green-600">₹{stats.fund_statistics.total_disbursed.toLocaleString('en-IN')}</span>
                </div>
                <div className="flex justify-between items-end">
                    <span className="text-gray-500 text-sm">Pending Disbursement</span>
                    <span className="font-bold text-xl text-orange-500">₹{stats.fund_statistics.pending.toLocaleString('en-IN')}</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*                             SHARED COMPONENTS                              */
/* -------------------------------------------------------------------------- */
function StatCard({ title, value, icon, color, subtext }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 flex items-center justify-between transition hover:shadow-md">
      <div>
        <p className="text-gray-500 text-sm font-medium uppercase tracking-wider">{title}</p>
        <h3 className="text-2xl font-bold text-gray-800 mt-1">{value}</h3>
        {subtext && <p className="text-xs text-gray-400 mt-1">{subtext}</p>}
      </div>
      <div className={`p-4 rounded-full text-white shadow-lg ${color} bg-opacity-90`}>
        {icon}
      </div>
    </div>
  );
}
