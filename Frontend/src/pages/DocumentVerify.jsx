import { useState } from 'react';
import api from '../services/api';
import toast from 'react-hot-toast';
import { UploadCloud, CheckCircle, AlertTriangle, ShieldAlert, FileText, Activity } from 'lucide-react';

export default function DocumentVerify() {
  const [file, setFile] = useState(null);
  const [docType, setDocType] = useState('aadhaar');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return toast.error("Please select a file");

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', docType);

    setLoading(true);
    try {
      const { data } = await api.post('/verify-document', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(data);
      
      if(data.verification_result?.verified) {
        toast.success('Document Verified Successfully');
      } else {
        toast.error('Verification Failed');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-gray-800">AI Document Verification</h2>
        <p className="text-gray-500">Upload documents for OCR & QR-based validation against the government registry.</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LEFT: Upload Form */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 h-fit">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Select Document Type</label>
              <select 
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gov-500 outline-none bg-white"
              >
                <option value="aadhaar">Aadhaar Card (QR Supported)</option>
                <option value="caste_certificate">Caste Certificate</option>
                <option value="income_certificate">Income Certificate</option>
                <option value="fir_copy">FIR Copy</option>
              </select>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center hover:bg-gray-50 transition cursor-pointer relative group">
              <input 
                type="file" 
                onChange={handleFileChange} 
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                accept=".jpg,.jpeg,.png,.pdf"
              />
              <div className="flex flex-col items-center">
                <div className="bg-gov-50 p-4 rounded-full mb-4 group-hover:scale-110 transition">
                  <UploadCloud className="h-8 w-8 text-gov-600" />
                </div>
                <p className="text-lg font-medium text-gray-700">
                  {file ? file.name : "Click to upload document"}
                </p>
                <p className="text-sm text-gray-400 mt-1">JPG, PNG or PDF (Max 10MB)</p>
              </div>
            </div>

            <button 
              disabled={loading}
              type="submit"
              className="w-full bg-gov-600 hover:bg-gov-900 text-white py-4 rounded-lg font-bold shadow-lg shadow-gov-200 transition disabled:opacity-70 flex items-center justify-center gap-2"
            >
              {loading ? (
                <><Activity className="animate-spin" /> Analyzing...</>
              ) : (
                'Verify Document'
              )}
            </button>
          </form>
        </div>

        {/* RIGHT: Results Panel */}
        {result && (
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden animate-in fade-in slide-in-from-bottom-4">
            {/* Header */}
            <div className={`p-6 border-b ${result.verification_result?.verified ? 'bg-green-50' : 'bg-red-50'}`}>
              <div className="flex items-center gap-4">
                {result.verification_result?.verified ? (
                  <div className="p-3 bg-green-100 rounded-full text-green-700">
                    <CheckCircle size={32} />
                  </div>
                ) : (
                  <div className="p-3 bg-red-100 rounded-full text-red-700">
                    <ShieldAlert size={32} />
                  </div>
                )}
                <div>
                  <h3 className={`text-xl font-bold ${result.verification_result?.verified ? 'text-green-800' : 'text-red-800'}`}>
                    {result.verification_result?.verified ? 'Verification Successful' : 'Verification Failed'}
                  </h3>
                  <p className="text-sm opacity-80">
                    Confidence Score: <span className="font-bold">{result.verification_result?.confidence || 0}%</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-6 space-y-6">
              
              {/* Security Alert Section */}
              {result.verification_result?.security_alert && (
                <div className="bg-red-50 border border-red-200 p-4 rounded-lg flex items-start gap-3">
                  <AlertTriangle className="text-red-600 shrink-0 mt-1" />
                  <div>
                    <h4 className="font-bold text-red-700">Security Alert</h4>
                    <p className="text-sm text-red-600">{result.verification_result?.reason || "Mismatch detected"}</p>
                    <p className="text-xs text-red-500 mt-1">{result.verification_result?.details}</p>
                  </div>
                </div>
              )}

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-gray-500 text-xs uppercase mb-1">Document Type</span>
                  <span className="font-semibold text-gray-800 capitalize">{result.document_type}</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                  <span className="block text-gray-500 text-xs uppercase mb-1">Method</span>
                  <span className="font-semibold text-gray-800">{result.verification_result?.verification_method || "Standard OCR"}</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                    <span className="block text-gray-500 text-xs uppercase mb-1">Uploaded By</span>
                    <span className="font-semibold text-gray-800">{result.user_name}</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg">
                    <span className="block text-gray-500 text-xs uppercase mb-1">File ID</span>
                    <span className="font-mono text-gray-800 text-xs truncate">{result.file_id}</span>
                </div>
              </div>

              {/* Extracted Data Preview */}
              {result.verification_result?.extracted_data && (
                 <div className="border rounded-lg p-4">
                    <h4 className="flex items-center gap-2 font-semibold text-gray-700 mb-2">
                        <FileText size={16} /> Extracted Data
                    </h4>
                    <div className="space-y-2">
                        {Object.entries(result.verification_result.extracted_data).map(([key, value]) => (
                            <div key={key} className="flex justify-between text-sm border-b border-gray-100 pb-1 last:border-0">
                                <span className="text-gray-500 capitalize">{key.replace('_', ' ')}</span>
                                <span className="font-medium">{value}</span>
                            </div>
                        ))}
                    </div>
                 </div>
              )}

              {/* Fallback Text Preview */}
              {result.verification_result?.extracted_text_preview && (
                <div className="border rounded-lg p-4 bg-gray-50">
                   <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Raw OCR Text</h4>
                   <p className="text-xs text-gray-600 font-mono break-all">
                      {result.verification_result.extracted_text_preview}
                   </p>
                </div>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  );
}