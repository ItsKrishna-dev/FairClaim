import { useState } from 'react';
import { X, AlertCircle } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function NewGrievanceModal({ isOpen, onClose, onSuccess, userCases, user }) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    case_id: '',
    title: '',
    category: 'Delayed Payment',
    description: '',
    contact_name: user?.full_name || '',
    contact_phone: user?.phone || '',
    contact_email: user?.email || ''
  });

  if (!isOpen) return null;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.case_id) {
      toast.error("Please select a relevant case");
      return;
    }

    setLoading(true);

    try {
      // Matches app/schemas.py GrievanceCreate structure
      const payload = {
        case_id: parseInt(formData.case_id),
        title: formData.title,
        description: formData.description,
        category: formData.category,
        contact_name: formData.contact_name,
        contact_phone: formData.contact_phone,
        contact_email: formData.contact_email
      };

      await api.post('/grievances/', payload);
      toast.success('Grievance Submitted. Priority will be auto-assigned.');
      onSuccess();
      onClose();
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to submit grievance");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-100">
          <div>
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <AlertCircle className="text-orange-500" size={24} /> Raise Grievance
            </h2>
            <p className="text-gray-500 text-sm mt-1">Report an issue regarding your case</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full text-gray-400 hover:text-gray-600 transition">
            <X size={24} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          
          {/* Case Selection */}
          <div className="space-y-1">
            <label className="text-sm font-semibold text-gray-700">Select Case *</label>
            <select 
              name="case_id"
              value={formData.case_id}
              onChange={handleChange}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white transition"
              required
            >
              <option value="">-- Select Relevant Case --</option>
              {userCases.map(c => (
                <option key={c.id} value={c.id}>
                  {c.case_number} - {c.incident_location || "Unknown Location"}
                </option>
              ))}
            </select>
          </div>

          {/* Issue Details */}
          <div className="grid grid-cols-2 gap-4">
             <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700">Category *</label>
                <select 
                    name="category"
                    value={formData.category}
                    onChange={handleChange}
                    className="w-full p-3 border border-gray-300 rounded-lg outline-none bg-white"
                >
                    <option>Delayed Payment</option>
                    <option>Harassment</option>
                    <option>Document Issue</option>
                    <option>Official Misconduct</option>
                    <option>Other</option>
                </select>
             </div>
             <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700">Subject *</label>
                <input 
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    placeholder="e.g., Fund not received"
                    className="w-full p-3 border border-gray-300 rounded-lg outline-none"
                    required
                />
             </div>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-semibold text-gray-700">Description *</label>
            <textarea 
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
              placeholder="Please describe your issue in detail..."
              required
            />
          </div>

          {/* Contact Details (Auto-filled) */}
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
             <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Contact Information</h4>
             <div className="grid grid-cols-2 gap-4">
                <input 
                    name="contact_name" 
                    value={formData.contact_name} 
                    onChange={handleChange} 
                    className="p-2 text-sm border rounded bg-white" 
                    placeholder="Name" 
                />
                <input 
                    name="contact_phone" 
                    value={formData.contact_phone} 
                    onChange={handleChange} 
                    className="p-2 text-sm border rounded bg-white" 
                    placeholder="Phone" 
                />
             </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-2">
            <button 
              type="button" 
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={loading}
              className="px-6 py-2 bg-orange-600 rounded-lg text-white font-bold hover:bg-orange-700 transition shadow-lg shadow-orange-200 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Grievance'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}