import { X, FileText, MapPin, Calendar, CreditCard, User, Shield, Activity } from 'lucide-react';

export default function CaseDetailsModal({ isOpen, onClose, caseData }) {
  if (!isOpen || !caseData) return null;

  // Helper to format dates
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl animate-in fade-in zoom-in-95 duration-200 my-8">
        
        {/* Header */}
        <div className="flex justify-between items-start p-6 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-blue-100 text-blue-700 border border-blue-200">
                {caseData.status || "Active"}
              </span>
              <span className="text-sm text-gray-500 font-mono">
                {caseData.case_number}
              </span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Case Details</h2>
            <p className="text-sm text-gray-500 mt-1">
              Registered on {formatDate(caseData.created_at)}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-full text-gray-500 hover:text-gray-700 transition"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content Scrollable Area */}
        <div className="p-6 space-y-8 max-h-[70vh] overflow-y-auto">
          
          {/* Section 1: Incident Overview */}
          <section>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <FileText className="text-blue-600" size={20} /> Incident Report
            </h3>
            <div className="bg-blue-50/50 p-4 rounded-lg border border-blue-100 space-y-4">
              <div>
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Description</label>
                <p className="text-gray-800 mt-1 leading-relaxed">
                  {caseData.incident_description || "No description provided."}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                    <MapPin size={12} className="inline mr-1"/> Location
                  </label>
                  <p className="font-medium text-gray-800">{caseData.incident_location || "N/A"}</p>
                </div>
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                    <Calendar size={12} className="inline mr-1"/> Incident Date
                  </label>
                  <p className="font-medium text-gray-800">{formatDate(caseData.incident_date)}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Section 2: Victim & Bank Info */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <User className="text-purple-600" size={20} /> Victim Info
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 space-y-3">
                <div className="flex justify-between border-b border-gray-200 pb-2">
                  <span className="text-gray-500 text-sm">Name</span>
                  <span className="font-medium text-gray-900">{caseData.victim_name}</span>
                </div>
                <div className="flex justify-between border-b border-gray-200 pb-2">
                  <span className="text-gray-500 text-sm">Phone</span>
                  <span className="font-medium text-gray-900">{caseData.victim_phone}</span>
                </div>
                <div className="flex justify-between border-b border-gray-200 pb-2">
                  <span className="text-gray-500 text-sm">Email</span>
                  <span className="font-medium text-gray-900 truncate max-w-[150px]" title={caseData.victim_email}>
                    {caseData.victim_email}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 text-sm">Aadhaar</span>
                  <span className="font-medium text-gray-900">{caseData.victim_aadhaar}</span>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                <CreditCard className="text-green-600" size={20} /> Financial Details
              </h3>
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-100 space-y-3">
                <div className="flex justify-between border-b border-gray-200 pb-2">
                  <span className="text-gray-500 text-sm">Allocated Amount</span>
                  <span className="font-bold text-green-700">₹{caseData.compensation_amount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between border-b border-gray-200 pb-2">
                  <span className="text-gray-500 text-sm">Account No.</span>
                  <span className="font-medium text-gray-900 font-mono">
                    {caseData.bank_account_number || "Pending"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 text-sm">IFSC Code</span>
                  <span className="font-medium text-gray-900 font-mono">
                    {caseData.ifsc_code || "Pending"}
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: Official Status */}
          <section>
            <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
              <Shield className="text-orange-600" size={20} /> Official Status
            </h3>
            <div className="bg-orange-50/50 p-4 rounded-lg border border-orange-100 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                  Current Stage
                </label>
                <div className="flex items-center gap-2">
                  <Activity size={16} className="text-orange-600" />
                  <span className="font-bold text-gray-800 capitalize">
                    {caseData.stage?.replace(/_/g, ' ') || "Processing"}
                  </span>
                </div>
              </div>
              <div>
                <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                   Assigned Officer ID
                </label>
                <span className="font-medium text-gray-800">
                  {caseData.assigned_officer_user_id 
                    ? `Officer #${caseData.assigned_officer_user_id}` 
                    : "Pending Assignment"}
                </span>
              </div>
            </div>
          </section>

        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-100 bg-gray-50/50 rounded-b-xl flex justify-end">
          <button 
            onClick={onClose}
            className="px-6 py-2 bg-gray-900 text-white rounded-lg font-medium hover:bg-black transition shadow-lg"
          >
            Close
          </button>
        </div>

      </div>
    </div>
  );
}