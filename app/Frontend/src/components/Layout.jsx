import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileCheck, LogOut, Shield } from 'lucide-react';

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  // Check if user is an Official/Officer
  const isOfficial = user?.role === 'official' || user?.role === 'officer' || user?.role === 'admin';

  // --- 1. OFFICIAL LAYOUT (Top Nav, No Sidebar) ---
  if (isOfficial) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col">
        {/* Top Header */}
        <header className="bg-white shadow-sm border-b px-8 py-4 flex justify-between items-center sticky top-0 z-50">
          <div className="flex items-center gap-3">
            <Shield className="text-orange-600" size={28} />
            <div>
              <h1 className="text-xl font-bold text-gray-900">FairClaim <span className="text-orange-600">Official</span></h1>
              <p className="text-xs text-gray-500">Government Portal</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right hidden md:block">
              <p className="text-sm font-semibold text-gray-800">{user?.full_name}</p>
              <p className="text-xs text-gray-500 uppercase tracking-wide">{user?.role}</p>
            </div>
            <button 
              onClick={logout}
              className="flex items-center gap-2 text-red-600 hover:bg-red-50 px-4 py-2 rounded-lg transition font-medium border border-transparent hover:border-red-100"
            >
              <LogOut size={18} /> Logout
            </button>
          </div>
        </header>

        {/* Main Content Area - Full Width */}
        <main className="flex-1 p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    );
  }

  // --- 2. VICTIM LAYOUT (Original Sidebar) ---
  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: <LayoutDashboard size={20} /> },
    { label: 'Verify Docs', path: '/verify', icon: <FileCheck size={20} /> },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white shadow-md z-10 hidden md:flex flex-col">
        <div className="p-6 border-b">
          <h1 className="text-2xl font-bold text-blue-600">FairClaim</h1>
          <p className="text-xs text-gray-500 mt-1">DBT System (PCR/PoA)</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === item.path 
                  ? 'bg-blue-50 text-blue-600 border-r-4 border-blue-600' 
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
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
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

      <main className="flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  );
}