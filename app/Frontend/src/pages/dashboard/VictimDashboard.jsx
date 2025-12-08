import { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useTranslation } from 'react-i18next';
import { FileText, CheckCircle, Clock, IndianRupee, Plus, Eye, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import NewCaseModal from '../../components/NewCaseModal';
import LanguageSwitcher from '../../components/LanguageSwitcher';

export default function VictimDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('caseTracking');
  
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchCases = async () => {
    try {
      const { data } = await api.get('/cases/'); 
      setCases(data.cases || []);
    } catch (error) {
      console.error("Failed to fetch cases", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const getDaysSince = (dateString) => {
    if (!dateString) return 0;
    const diff = Math.floor((new Date() - new Date(dateString)) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  };

  const getProgress = (stage) => {
    switch(stage) {
      case 'fir_stage': return 25;
      case 'chargesheet_stage': return 60;
      case 'conviction_stage': return 100;
      default: return 10;
    }
  };

  const activeCase = cases[0] || {}; 
  const totalReceived = cases.reduce((acc, curr) => acc + (curr.compensation_amount || 0), 0);

  if (loading) return <div className="p-8 text-center">{t('common.loading')}</div>;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="absolute top-4 right-4">
        <LanguageSwitcher />
      </div>

      <div className="max-w-7xl mx-auto space-y-8 pb-10 pt-6 px-4">
        
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {t('victimDashboard.greeting', { name: user?.full_name || t('common.user') })}
          </h1>
          <p className="text-gray-500 mt-1">
            {t('victimDashboard.welcome')}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard 
            icon={<FileText className="text-blue-600" size={28} />}
            value={activeCase.case_number || t('victimDashboard.noActiveCase')}
            label={t('victimDashboard.caseNumber')}
            subLabel={t('victimDashboard.activeCaseRef')}
          />
          <StatCard 
            icon={<CheckCircle className="text-green-600" size={28} />}
            value={activeCase.stage ? t(`stages.${activeCase.stage}`, { defaultValue: activeCase.stage.replace('_', ' ').replace('stage', '') }) : t('common.notAvailable')}
            label={t('victimDashboard.currentProgress')}
            subLabel={t('victimDashboard.onTrack')}
          />
          <StatCard 
            icon={<IndianRupee className="text-yellow-600" size={28} />}
            value={`₹${totalReceived.toLocaleString()}`}
            label={t('victimDashboard.amountReceived')}
            subLabel={t('victimDashboard.dbt')}
          />
          <StatCard 
            icon={<Clock className="text-blue-500" size={28} />}
            value={getDaysSince(activeCase.created_at)}
            label={t('victimDashboard.daysSince')}
            subLabel={t('victimDashboard.timeline')}
          />
        </div>

        {/* Navigation */}
        <div className="bg-white rounded-lg p-1 shadow-sm border border-gray-100 flex overflow-x-auto">
          {['caseTracking', 'compensation', 'alerts', 'transparency', 'support'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-6 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${
                activeTab === tab 
                  ? 'bg-white shadow-sm text-blue-700 border border-gray-100' 
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              {t(`victimDashboard.tabs.${tab}`)}
            </button>
          ))}
        </div>

        {/* My Cases Header */}
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold text-gray-800">{t('victimDashboard.myCases')}</h2>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium flex items-center gap-2 transition shadow-sm"
          >
            <Plus size={18} /> {t('victimDashboard.addNewCase')}
          </button>
        </div>

        {/* Cases List */}
        <div className="grid grid-cols-1 gap-6">
          {cases.length > 0 ? cases.map((item) => (
            <div key={item.id} className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <FileText className="text-gray-400" size={20} />
                  <div>
                      <h3 className="text-xl font-bold text-gray-800">{item.case_number}</h3>
                      <p className="text-sm text-gray-400">
                        {t('victimDashboard.registered')}: {new Date(item.created_at).toLocaleDateString()}
                      </p>
                  </div>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-blue-100 text-blue-700">
                  {item.status ? t(`victimDashboard.status.${item.status.toLowerCase()}`, { defaultValue: item.status }) : t('victimDashboard.status.active')}
                </span>
              </div>

              <p className="text-gray-600 font-medium mb-6">
                  {item.incident_description || t('victimDashboard.descriptionPending')}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                <div>
                  <p className="text-xs text-gray-400 uppercase font-semibold flex items-center gap-1">
                      <MapPin size={12}/> {t('victimDashboard.location')}
                  </p>
                  <p className="font-medium text-gray-800">{item.incident_location || t('victimDashboard.notSpecified')}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase font-semibold">{t('victimDashboard.stage')}</p>
                  <p className="font-medium text-gray-800 capitalize">
                      {item.stage ? t(`stages.${item.stage}`, { defaultValue: item.stage.replace('_', ' ') }) : t('common.notAvailable')}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase font-semibold">{t('victimDashboard.compensation')}</p>
                  <p className="font-bold text-gray-800">₹{item.compensation_amount?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase font-semibold">{t('victimDashboard.officer')}</p>
                  <p className="font-medium text-gray-800">
                      {item.assigned_officer_user_id ? `ID: ${item.assigned_officer_user_id}` : t('victimDashboard.pending')}
                  </p>
                </div>
              </div>

              <div className="mb-6">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-500">{t('victimDashboard.progress')}</span>
                  <span className="font-semibold text-blue-600">
                    {getProgress(item.stage)}% {t('victimDashboard.complete')}
                  </span>
                </div>
                <div className="h-3 w-full bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-blue-600 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${getProgress(item.stage)}%` }}
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-gray-50">
                <button className="flex items-center gap-2 text-gray-600 hover:text-blue-600 font-medium border border-gray-200 px-4 py-2 rounded-lg hover:border-blue-200 transition">
                  <Eye size={16} /> {t('victimDashboard.viewDetails')}
                </button>
              </div>
            </div>
          )) : (
              <div className="text-center py-10 bg-white rounded-xl border border-dashed border-gray-300">
                  <p className="text-gray-500">{t('victimDashboard.noCases')}</p>
              </div>
          )}
        </div>

        <NewCaseModal 
          isOpen={isModalOpen} 
          onClose={() => setIsModalOpen(false)} 
          onSuccess={fetchCases}
          user={user}
        />

      </div>
    </div>
  );
}

function StatCard({ icon, value, label, subLabel }) {
  return (
    <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-start gap-4">
      <div className="p-3 bg-gray-50 rounded-lg shrink-0 border border-gray-100 shadow-sm">
        {icon}
      </div>
      <div>
        <h3 className="text-2xl font-bold text-gray-900 leading-none mb-1 break-words">{value}</h3>
        <p className="font-semibold text-gray-700 text-sm">{label}</p>
        <p className="text-xs text-gray-400 mt-1">{subLabel}</p>
      </div>
    </div>
  );
}
