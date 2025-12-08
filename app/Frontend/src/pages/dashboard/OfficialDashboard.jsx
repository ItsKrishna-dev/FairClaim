import { useEffect, useState } from 'react';
import api from '../../services/api';
import toast from 'react-hot-toast';
import { 
  Loader2, Eye, CheckCircle, XCircle, IndianRupee, Search, 
  FileCheck, History, ShieldAlert 
} from 'lucide-react';
import CaseDetailsModal from '../../components/CaseDetailsModal';

export default function OfficialDashboard() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Tab State: 'verification', 'funds', 'audit'
  const [activeTab, setActiveTab] = useState('verification');
  
  // Modal State
  const [selectedCase, setSelectedCase] = useState(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);

  // Fetch all cases
  const fetchCases = async () => {
    try {
      const { data } = await api.get('/cases/');
      setCases(data.cases || []);
    } catch (error) {
      console.error("Failed to load cases", error);
      toast.error("Failed to load case list");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  // --- ACTIONS ---

  const updateCaseStatus = async (caseId, newStatus, successMessage) => {
    try {
      await api.patch(`/cases/${caseId}`, { status: newStatus });
      toast.success(successMessage);
      fetchCases(); // Refresh data to move case to correct tab automatically
    } catch (error) {
      toast.error("Action failed. Please try again.");
    }
  };

  const handleApprove = (id) => {
    if(window.confirm("Approve this case for funding? It will move to the Funds Approval tab.")) {
      updateCaseStatus(id, "APPROVED", "Case Approved. Moved to Funds Tab.");
    }
  };

  const handleReject = (id) => {
    if(window.confirm("Reject this case? This action cannot be undone.")) {
      updateCaseStatus(id, "REJECTED", "Case Rejected. Moved to Audit Logs.");
    }
  };

  const handleDisburse = (id) => {
    if(window.confirm("Confirm fund disbursement? This will mark the transaction as complete.")) {
      updateCaseStatus(id, "COMPLETED", "Funds Disbursed Successfully.");
    }
  };

  const handleReview = (caseItem) => {
    setSelectedCase(caseItem);
    setIsDetailsOpen(true);
  };

  // --- FILTERING LOGIC ---

  const getFilteredCases = () => {
    // 1. Filter by Tab logic
    let tabCases = [];
    if (activeTab === 'verification') {
      tabCases = cases.filter(c => ['PENDING', 'UNDER_REVIEW', 'FIR', 'fir_stage'].includes(c.status) || c.status === 'PENDING');
    } else if (activeTab === 'funds') {
      tabCases = cases.filter(c => ['APPROVED', 'PAYMENT_PROCESSING'].includes(c.status));
    } else if (activeTab === 'audit') {
      tabCases = cases.filter(c => ['COMPLETED', 'REJECTED'].includes(c.status));
    }

    // 2. Filter by Search Term
    if (!searchTerm) return tabCases;
    
    return tabCases.filter(c => 
      c.case_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.victim_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.incident_location?.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const displayCases = getFilteredCases();

  if (loading) return <div className="flex justify-center p-10"><Loader2 className="animate-spin text-orange-600" size={40} /></div>;

  return (
    <div className="space-y-6 pb-10">
      
      {/* 1. Header & Search */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-4">
        <div>
           <h2 className="text-2xl font-bold text-gray-900">Official Dashboard</h2>
           <p className="text-gray-500 mt-1">Manage verifications, approvals, and audit records.</p>
        </div>
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input 
            type="text" 
            placeholder="Search by Case ID, Name or Location..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 outline-none shadow-sm"
          />
        </div>
      </div>

      {/* 2. Tabs Navigation */}
      <div className="flex flex-col sm:flex-row gap-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('verification')}
          className={`pb-3 px-4 flex items-center gap-2 font-medium text-sm transition-colors relative ${
            activeTab === 'verification' 
              ? 'text-orange-600 border-b-2 border-orange-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <FileCheck size={18} />
          Case Verification
          <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
             {cases.filter(c => ['PENDING', 'UNDER_REVIEW'].includes(c.status)).length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('funds')}
          className={`pb-3 px-4 flex items-center gap-2 font-medium text-sm transition-colors relative ${
            activeTab === 'funds' 
              ? 'text-green-600 border-b-2 border-green-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <IndianRupee size={18} />
          Funds Approvals
          <span className="ml-2 bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
            {cases.filter(c => ['APPROVED', 'PAYMENT_PROCESSING'].includes(c.status)).length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`pb-3 px-4 flex items-center gap-2 font-medium text-sm transition-colors relative ${
            activeTab === 'audit' 
              ? 'text-blue-600 border-b-2 border-blue-600' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <History size={18} />
          Audit Logs
        </button>
      </div>

      {/* 3. Main Table */}
      <div className="bg-white border rounded-xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b text-gray-500 text-xs uppercase font-semibold">
                <th className="p-4 w-1/4">Case Details</th>
                <th className="p-4 w-1/4">Beneficiary</th>
                <th className="p-4 w-1/6">Amount</th>
                <th className="p-4 w-1/6">Status</th>
                <th className="p-4 w-1/6 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {displayCases.length > 0 ? displayCases.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition">
                  
                  {/* Case Info */}
                  <td className="p-4">
                    <p className="font-bold text-gray-800 text-sm">{item.case_number}</p>
                    <p className="text-xs text-gray-500 mt-1">{new Date(item.created_at).toLocaleDateString()}</p>
                    <p className="text-xs text-gray-400 font-mono mt-0.5 truncate max-w-[150px]">{item.fir_number || "No FIR Num"}</p>
                  </td>

                  {/* Beneficiary Info */}
                  <td className="p-4">
                    <p className="text-sm font-medium text-gray-900">{item.victim_name}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{item.incident_location}</p>
                    <p className="text-[10px] text-gray-400 uppercase mt-1">{item.act_type || "N/A"}</p>
                  </td>

                  {/* Amount */}
                  <td className="p-4">
                    <div className="font-mono font-medium text-gray-800">
                        ₹{item.compensation_amount?.toLocaleString()}
                    </div>
                  </td>

                  {/* Status Badge */}
                  <td className="p-4">
                    <StatusBadge status={item.status} />
                  </td>

                  {/* Actions Column - Dynamic based on Tab */}
                  <td className="p-4">
                    <div className="flex justify-center gap-2">
                        {/* Always show View Details */}
                        <button 
                            onClick={() => handleReview(item)}
                            title="View Full Details"
                            className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                        >
                            <Eye size={18} />
                        </button>

                        {/* Actions for 'Case Verification' Tab */}
                        {activeTab === 'verification' && (
                            <>
                                <button 
                                    onClick={() => handleApprove(item.id)}
                                    title="Approve for Funding"
                                    className="p-2 text-gray-500 hover:text-green-600 hover:bg-green-50 rounded-lg transition"
                                >
                                    <CheckCircle size={18} />
                                </button>
                                <button 
                                    onClick={() => handleReject(item.id)}
                                    title="Reject Case"
                                    className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                                >
                                    <XCircle size={18} />
                                </button>
                            </>
                        )}

                        {/* Actions for 'Funds Approvals' Tab */}
                        {activeTab === 'funds' && (
                            <button 
                                onClick={() => handleDisburse(item.id)}
                                title="Disburse Funds"
                                className="flex items-center gap-2 px-3 py-1.5 text-xs font-bold text-white bg-green-600 hover:bg-green-700 rounded-md shadow-sm transition"
                            >
                                <IndianRupee size={14} /> Disburse
                            </button>
                        )}

                        {/* Actions for 'Audit Logs' Tab */}
                        {activeTab === 'audit' && (
                            <span className="text-xs text-gray-400 font-medium px-2 py-1 bg-gray-50 rounded border">
                                Archived
                            </span>
                        )}
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                    <td colSpan="5" className="p-12 text-center text-gray-500">
                        <div className="flex flex-col items-center gap-2">
                            <ShieldAlert className="text-gray-300" size={48} />
                            <p className="font-medium">No cases found in this section.</p>
                            <p className="text-sm">Current filter: {activeTab.replace('_', ' ').toUpperCase()}</p>
                        </div>
                    </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Modal */}
      <CaseDetailsModal 
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        caseData={selectedCase}
      />

    </div>
  );
}

// Helper: Status Badge
function StatusBadge({ status }) {
    const styles = {
        PENDING: "bg-orange-50 text-orange-700 border-orange-200",
        UNDER_REVIEW: "bg-blue-50 text-blue-700 border-blue-200",
        APPROVED: "bg-purple-50 text-purple-700 border-purple-200",
        REJECTED: "bg-red-50 text-red-700 border-red-200",
        COMPLETED: "bg-green-50 text-green-700 border-green-200",
        PAYMENT_PROCESSING: "bg-yellow-50 text-yellow-700 border-yellow-200"
    };

    return (
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${styles[status] || "bg-gray-100 text-gray-600"}`}>
            {status?.replace(/_/g, ' ')}
        </span>
    );
}