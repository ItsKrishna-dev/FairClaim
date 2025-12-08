import { useState, useEffect } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { FileText, CheckCircle, Clock, IndianRupee, Plus, Eye, MapPin, AlertCircle, MessageSquare } from 'lucide-react';
import NewCaseModal from '../../components/NewCaseModal';
import CaseDetailsModal from '../../components/CaseDetailsModal';
import NewGrievanceModal from '../../components/NewGrievanceModal'; // IMPORT THE NEW MODAL

export default function VictimDashboard() {
  const { user } = useAuth();
  const [cases, setCases] = useState([]);
  const [grievances, setGrievances] = useState([]); // State for grievances
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('Case Tracking');
  
  // Modal States
  const [isAddCaseOpen, setIsAddCaseOpen] = useState(false);
  const [isGrievanceOpen, setIsGrievanceOpen] = useState(false); // State for Grievance Modal
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);

  // Fetch Cases
  const fetchCases = async () => {
    try {
      const { data } = await api.get('/cases/'); 
      setCases(data.cases || []);
    } catch (error) {
      console.error("Failed to fetch cases", error);
    }
  };

  // Fetch Grievances (New Function)
  const fetchGrievances = async () => {
    try {
      const { data } = await api.get('/grievances/');
      setGrievances(data.grievances || []);
    } catch (error) {
      console.error("Failed to fetch grievances", error);
    }
  };

  // Initial Load
  useEffect(() => {
    const init = async () => {
        setLoading(true);
        await Promise.all([fetchCases(), fetchGrievances()]);
        setLoading(false);
    };
    init();
  }, []);

  // Handlers
  const handleViewDetails = (caseItem) => {
    setSelectedCase(caseItem);
    setIsDetailsModalOpen(true);
  };

  // Calculations
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

  if (loading) return <div className="p-8">Loading dashboard...</div>;

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Hello {user?.full_name || 'User'}, we're here to help
        </h1>
        <p className="text-gray-500 mt-1">Stay updated on your case and get the support you deserve.</p>
      </div>

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={<FileText className="text-blue-600" size={28} />}
          value={activeCase.case_number || "No Active Case"}
          label="Case Number"
          subLabel="Active Case Reference"
        />
        <StatCard 
          icon={<CheckCircle className="text-green-600" size={28} />}
          value={activeCase.stage?.replace('_', ' ').replace('stage', '') || "N/A"}
          label="Current Progress"
          subLabel="On Track"
        />
        <StatCard 
          icon={<IndianRupee className="text-yellow-600" size={28} />}
          value={`₹${totalReceived.toLocaleString()}`}
          label="Amount Received"
          subLabel="Direct Benefit Transfer"
        />
        <StatCard 
          icon={<Clock className="text-blue-500" size={28} />}
          value={getDaysSince(activeCase.created_at)}
          label="Days Since Registration"
          subLabel="Timeline"
        />
      </div>

      {/* Tabs Navigation */}
      <div className="bg-white rounded-lg p-1 shadow-sm border border-gray-100 flex overflow-x-auto">
        {['Case Tracking', 'Alerts', 'Support'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 px-6 text-sm font-medium rounded-md transition-colors whitespace-nowrap ${
              activeTab === tab 
                ? 'bg-white shadow-sm text-blue-700 border border-gray-100' 
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* CONDITIONAL CONTENT: Case Tracking VS Support */}
      
      {/* ----------------- SUPPORT TAB ----------------- */}
      {activeTab === 'Support' && (
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
           <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Grievance Support</h2>
              <button 
                onClick={() => setIsGrievanceOpen(true)}
                className="bg-orange-600 hover:bg-orange-700 text-white px-5 py-2.5 rounded-lg font-medium flex items-center gap-2 transition shadow-sm"
              >
                <AlertCircle size={18} /> Raise Grievance
              </button>
            </div>

            <div className="grid grid-cols-1 gap-4">
               {grievances.length > 0 ? grievances.map((item) => (
                  <div key={item.id} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row justify-between gap-4">
                     <div>
                        <div className="flex items-center gap-3 mb-2">
                           <span className="font-bold text-gray-800 text-lg">{item.title}</span>
                           <span className={`text-xs px-2 py-1 rounded font-bold uppercase ${
                              item.priority === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-blue-50 text-blue-600'
                           }`}>
                              {item.priority} Priority
                           </span>
                        </div>
                        <p className="text-gray-600 text-sm mb-2">{item.description}</p>
                        <div className="flex items-center gap-4 text-xs text-gray-400">
                           <span>Category: {item.category}</span>
                           <span>•</span>
                           <span>Ref: {item.grievance_number}</span>
                        </div>
                     </div>
                     <div className="flex items-center gap-3 md:border-l md:pl-6">
                         <div className={`px-4 py-2 rounded-lg text-sm font-bold capitalize ${
                             item.status === 'resolved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                         }`}>
                             {item.status?.replace('_', ' ')}
                         </div>
                     </div>
                  </div>
               )) : (
                  <div className="text-center py-12 bg-white rounded-xl border border-dashed border-gray-300">
                     <MessageSquare className="mx-auto h-12 w-12 text-gray-300 mb-3" />
                     <p className="text-gray-500 font-medium">No grievances raised yet.</p>
                     <p className="text-sm text-gray-400">Need help? Click the button above.</p>
                  </div>
               )}
            </div>
        </div>
      )}

      {/* ----------------- CASE TRACKING TAB (Default) ----------------- */}
      {activeTab === 'Case Tracking' && (
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">My Cases</h2>
                <button 
                onClick={() => setIsAddCaseOpen(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium flex items-center gap-2 transition shadow-sm"
                >
                <Plus size={18} /> Add New Case
                </button>
            </div>

            <div className="grid grid-cols-1 gap-6">
                {cases.length > 0 ? cases.map((item) => (
                <div 
                    key={item.id} 
                    className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition cursor-pointer"
                    onClick={() => handleViewDetails(item)}
                >
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-3">
                            <FileText className="text-gray-400" size={20} />
                            <div>
                                <h3 className="text-xl font-bold text-gray-800 hover:text-blue-600 transition">
                                {item.case_number}
                                </h3>
                                <p className="text-sm text-gray-400">Registered: {new Date(item.created_at).toLocaleDateString()}</p>
                            </div>
                        </div>
                        <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-blue-100 text-blue-700">
                            {item.status || "Active"}
                        </span>
                    </div>

                    <p className="text-gray-600 font-medium mb-6 line-clamp-2">
                        {item.incident_description || "Description Pending"}
                    </p>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-6 mb-6">
                        <div>
                            <p className="text-xs text-gray-400 uppercase font-semibold flex items-center gap-1">
                                <MapPin size={12}/> Location
                            </p>
                            <p className="font-medium text-gray-800">{item.incident_location || "Not specified"}</p>
                        </div>
                        <div>
                            <p className="text-xs text-gray-400 uppercase font-semibold">Stage</p>
                            <p className="font-medium text-gray-800 capitalize">
                                {item.stage?.replace('_', ' ')}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-gray-400 uppercase font-semibold">Officer</p>
                            <p className="font-medium text-gray-800">
                                {item.assigned_officer_user_id ? `ID: ${item.assigned_officer_user_id}` : "Pending"}
                            </p>
                        </div>
                    </div>

                    <div className="mb-6">
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-500">Progress</span>
                            <span className="font-semibold text-blue-600">{getProgress(item.stage)}% Complete</span>
                        </div>
                        <div className="h-3 w-full bg-gray-100 rounded-full overflow-hidden">
                            <div 
                            className="h-full bg-blue-600 rounded-full transition-all duration-1000 ease-out"
                            style={{ width: `${getProgress(item.stage)}%` }}
                            />
                        </div>
                    </div>

                    <div className="flex justify-end pt-4 border-t border-gray-50">
                        <button 
                            onClick={(e) => {
                            e.stopPropagation(); 
                            handleViewDetails(item);
                            }}
                            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 font-medium border border-gray-200 px-4 py-2 rounded-lg hover:border-blue-200 transition"
                        >
                            <Eye size={16} /> View Details
                        </button>
                    </div>
                </div>
                )) : (
                    <div className="text-center py-10 bg-white rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500">No cases found.</p>
                    </div>
                )}
            </div>
        </div>
      )}

      {/* Modals */}
      <NewCaseModal 
        isOpen={isAddCaseOpen} 
        onClose={() => setIsAddCaseOpen(false)} 
        onSuccess={fetchCases} 
        user={user}
      />
      
      <NewGrievanceModal
        isOpen={isGrievanceOpen}
        onClose={() => setIsGrievanceOpen(false)}
        onSuccess={fetchGrievances} // Updates the grievance list after submission
        userCases={cases} // Passes user's cases to populate dropdown
        user={user}
      />
      
      <CaseDetailsModal 
        isOpen={isDetailsModalOpen}
        onClose={() => setIsDetailsModalOpen(false)}
        caseData={selectedCase}
      />

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