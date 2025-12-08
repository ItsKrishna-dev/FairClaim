import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileCheck, LogOut, Upload } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { 
      label: user?.role === 'victim' ? 'Upload Docs' : 'Verify Docs', 
      path: '/verify', 
      icon: user?.role === 'victim' ? <Upload size={20} /> : <FileCheck size={20} />
    },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md z-10 hidden md:flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-gov-600">FairClaim</h1>
          <p className="text-xs text-gray-500 mt-1">DBT System (PCR/PoA)</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === item.path 
                  ? 'bg-gov-50 text-gov-600 border-r-4 border-gov-600' 
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {item.icon}
              <span className="font-medium">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gov-100 rounded-full flex items-center justify-center text-gov-600 font-bold">
              {user?.full_name?.charAt(0)}
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">{user?.full_name}</p>
              <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
            </div>
          </div>
          <button 
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 text-red-500 hover:bg-red-50 py-2 rounded-md transition"
          >
            <LogOut size={18} /> Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}