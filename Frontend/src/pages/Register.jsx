import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'victim',
    phone: '',
    aadhaar_number: '',
    address: ''
  });
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setFormData({...formData, [e.target.name]: e.target.value});

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await register(formData);
    if (success) navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gov-50 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-2xl shadow-lg w-full max-w-md my-8">
        <h2 className="text-2xl font-bold text-center text-gov-900 mb-6">Create Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          
          <input name="full_name" placeholder="Full Name" onChange={handleChange} required className="w-full p-3 border rounded-lg" />
          <input name="email" type="email" placeholder="Email" onChange={handleChange} required className="w-full p-3 border rounded-lg" />
          <input name="password" type="password" placeholder="Password (Min 6 chars)" onChange={handleChange} required className="w-full p-3 border rounded-lg" />
          
          <div className="grid grid-cols-2 gap-4">
            <input name="phone" placeholder="Phone (+91...)" onChange={handleChange} className="w-full p-3 border rounded-lg" />
            <select name="role" onChange={handleChange} className="w-full p-3 border rounded-lg bg-white">
              <option value="victim">Victim</option>
              <option value="official">Official</option>
            </select>
          </div>
          
          <input name="aadhaar_number" placeholder="Aadhaar Number" onChange={handleChange} className="w-full p-3 border rounded-lg" />
          <textarea name="address" placeholder="Address" onChange={handleChange} className="w-full p-3 border rounded-lg h-24" />

          <button type="submit" className="w-full bg-gov-600 text-white py-3 rounded-lg font-bold hover:bg-gov-900 transition">Register</button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-600">
          Already have an account? <Link to="/login" className="text-gov-600 font-semibold">Login</Link>
        </p>
      </div>
    </div>
  );
}