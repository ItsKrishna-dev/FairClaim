import { useState } from 'react';
import { X, Info, FileText } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function NewCaseModal({ isOpen, onClose, onSuccess, user }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    // Visual Fields
    victim_name: user?.full_name || '',
    victim_aadhaar: user?.aadhaar_number || '',
    fir_number: '', 
    act_type: '',  
    bank_name: '', 
    bank_account_number: '',
    ifsc_code: '',
    incident_location: '',
    incident_date: new Date().toISOString().split('T')[0], // Default today (YYYY-MM-DD)
    incident_description: '' // ✅ Added New Field
  });

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    // 1. Construct the Payload strictly matching 'VictimCaseCreate' schema
    const payload = {
      victim_name: formData.victim_name,
      victim_aadhaar: formData.victim_aadhaar,
      fir_number: formData.fir_number,
      act_type: formData.act_type, // Must be "PCR Act 1955" or "PoA Act 2015"
      bank_name: formData.bank_name,
      bank_account_number: formData.bank_account_number,
      ifsc_code: formData.ifsc_code,
      incident_location: formData.incident_location,
      incident_date: formData.incident_date,
      incident_description: formData.incident_description
    };

    try {
      // ✅ Updated Endpoint: /cases/victim/register
      await api.post('/cases/victim/register', payload);
      toast.success('Case Registered Successfully');
      onSuccess(); // Refresh the dashboard list
      onClose();   // Close modal
    } catch (error) {
      console.error(error);
      const msg = error.response?.data?.detail || "Failed to register case";
      toast.error(msg);
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
          
          {/* Row 1: Personal Info */}
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
                placeholder="12-digit Aadhaar"
                pattern="\d{12}"
                title="Aadhaar must be 12 digits"
                required
              />
            </div>
          </div>

          {/* Row 2: Case Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">FIR Number *</label>
              <input 
                name="fir_number"
                value={formData.fir_number}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="e.g. FIR/2025/001234"
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
                <option value="PCR Act 1955">PCR Act 1955</option>
                <option value="PoA Act 2015">PoA Act 2015</option>
              </select>
            </div>
          </div>

          {/* Row 3: Bank Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700">Bank Name *</label>
              <input 
                name="bank_name"
                value={formData.bank_name}
                onChange={handleChange}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                placeholder="e.g. State Bank of India"
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
                placeholder="Account Number"
                required
              />
            </div>
          </div>

          {/* Row 4: IFSC & Location */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700">IFSC Code *</label>
                <input 
                  name="ifsc_code"
                  value={formData.ifsc_code}
                  onChange={handleChange}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
                  placeholder="e.g. SBIN0001234"
                  maxLength={11}
                  required
                />
            </div>
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
          </div>

          {/* Row 5: Date & Description */}
          <div className="space-y-4">
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
             
             {/* ✅ NEW: Incident Description Field */}
             <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700 flex items-center gap-1">
                  <FileText size={16} /> Incident Description *
                </label>
                <textarea 
                    name="incident_description" 
                    value={formData.incident_description} 
                    onChange={handleChange} 
                    placeholder="Please describe the incident in detail..."
                    className="w-full p-3 border border-gray-300 rounded-lg outline-none min-h-[100px]" 
                    required 
                    minLength={10}
                />
             </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex gap-3">
            <Info className="text-blue-600 shrink-0 mt-1" size={20} />
            <div>
              <h4 className="text-blue-700 font-semibold text-sm mb-1">Important Information</h4>
              <p className="text-blue-600/80 text-xs leading-relaxed">
                Compensation amount will be automatically calculated based on the Act Type selected. 
                Your case will be reviewed by the concerned authorities within 15-30 days.
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