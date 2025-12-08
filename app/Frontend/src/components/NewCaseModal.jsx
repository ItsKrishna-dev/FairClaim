import { useState } from 'react';
import { X, Info } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function NewCaseModal({ isOpen, onClose, onSuccess, user }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    // Visual Fields (from Image)
    victim_name: user?.full_name || '',
    victim_aadhaar: user?.aadhaar_number || '',
    fir_input: '', // Used for description since backend auto-generates Case Number
    act_type: '',  // Used for description
    bank_name: '', // Not in DB, will append to notes
    bank_account_number: '',
    ifsc_code: '',

    // Backend Required Fields (Hidden/Auto-filled or Added)
    victim_phone: user?.phone || '',
    victim_email: user?.email || '',
    incident_date: new Date().toISOString().split('T')[0], // Default today
    incident_location: '',
    compensation_amount: 0, // Default
    stage: 'fir_stage'
  });

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // 1. Construct the Payload to match cases.py -> CaseCreate schema
    // We combine visual fields into the required backend fields
    const payload = {
      victim_name: formData.victim_name,
      victim_aadhaar: formData.victim_aadhaar,
      victim_phone: formData.victim_phone || "0000000000",
      victim_email: formData.victim_email || "noemail@provided.com",
      
      // Combine FIR/Act info into description because create_case doesn't accept fir_number directly
      incident_description: `FIR: ${formData.fir_input} | Act: ${formData.act_type} | Bank: ${formData.bank_name}`,
      
      incident_date: new Date(formData.incident_date).toISOString(),
      incident_location: formData.incident_location || "Not Specified",
      stage: formData.stage,
      compensation_amount: parseFloat(formData.compensation_amount),
      bank_account_number: formData.bank_account_number,
      ifsc_code: formData.ifsc_code
    };

    try {
      await api.post('/cases/', payload);
      toast.success('Case Registered Successfully');
      onSuccess(); // Refresh the dashboard list
      onClose();   // Close modal
    } catch (error) {
      console.error(error);
      const msg = error.response?.data?.detail || "Failed to register case";
      
      if(error.response?.status === 403) {
        toast.error("Permission Denied: Only Officials can register cases.");
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <span className="text-blue-600 text-3xl">+</span> Add New Case
            </h2>
            <p className="text-gray-500 text-sm mt-1">Register a new case for compensation under PCR/PoA Acts</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full text-gray-400 hover:text-gray-600 transition">
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          
          {/* Row 1 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">Full Name *</label>
              <input 
                name="victim_name"
                value={formData.victim_name}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="Sample Victim"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">Aadhaar Number *</label>
              <input 
                name="victim_aadhaar"
                value={formData.victim_aadhaar}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="1234-5678-9012"
                required
              />
            </div>
          </div>

          {/* Row 2 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">FIR Number *</label>
              <input 
                name="fir_input"
                value={formData.fir_input}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder=" For eg. FIR/2025/001234"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">Act Type *</label>
              <select 
                name="act_type"
                value={formData.act_type}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white transition"
                required
              >
                <option value="">Select applicable act</option>
                <option value="PCR Act">PCR Act 1955</option>
                <option value="PoA Act">PoA Act 1989</option>
              </select>
            </div>
          </div>

          {/* Row 3 - Bank Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">Bank Name *</label>
              <input 
                name="bank_name"
                value={formData.bank_name}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="Bank Name"
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">Account Number *</label>
              <input 
                name="bank_account_number"
                value={formData.bank_account_number}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="Enter Acc No."
                required
              />
            </div>
          </div>

          {/* Row 4 - IFSC */}
          <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">IFSC Code *</label>
              <input 
                name="ifsc_code"
                value={formData.ifsc_code}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="Enter IFSC Code"
                required
              />
          </div>

          {/* Extra Fields required by Backend but not in Image (Collapsible or just added) */}
          <div className="pt-4 border-t border-gray-100 grid grid-cols-1 md:grid-cols-2 gap-6">
             <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700">Incident Location *</label>
                <input 
                    name="incident_location" 
                    value={formData.incident_location} 
                    onChange={handleChange} 
                    placeholder="City, District"
                    className="w-full p-3 border border-gray-300 rounded-lg outline-none" 
                    required 
                />
             </div>
             <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700">Incident Date *</label>
                <input 
                    type="date"
                    name="incident_date" 
                    value={formData.incident_date} 
                    onChange={handleChange} 
                    className="w-full p-3 border border-gray-300 rounded-lg outline-none" 
                    required 
                />
             </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3">
            <Info className="text-blue-600 shrink-0 mt-1" size={20} />
            <div>
              <h4 className="text-blue-700 font-semibold text-sm mb-1">Important Information</h4>
              <p className="text-blue-600/80 text-xs leading-relaxed">
                After registering your case, you will need to submit supporting documents including FIR copy, 
                medical reports (if applicable), income certificate, and identity proof. Your case will be 
                reviewed by the concerned authorities within 15-30 days.
              </p>
            </div>
          </div>

          {/* Footer Buttons */}
          <div className="flex justify-end gap-3 pt-2">
            <button 
              type="button" 
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={loading}
              className="px-6 py-3 bg-blue-600 rounded-lg text-white font-bold hover:bg-blue-700 transition shadow-lg shadow-blue-200 disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? 'Registering...' : 'Register Case'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}