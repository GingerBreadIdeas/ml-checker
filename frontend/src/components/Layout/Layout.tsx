import React, { useState, useContext } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../../App';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const { isAuthenticated, user, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const location = useLocation();
  
  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };
  
  const toggleUserDropdown = () => {
    setUserDropdownOpen(!userDropdownOpen);
  };
  
  const handleLogout = () => {
    logout();
    setUserDropdownOpen(false);
    navigate('/login');
  };
  
  // Helper to check if a path is active
  const isActive = (path: string) => {
    return location.pathname === path;
  };
  
  return (
    <div className="bg-gray-50 min-h-screen flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center">
            {/* Sidebar toggle button */}
            <button onClick={toggleSidebar} className="p-1 mr-3 text-gray-500 hover:text-gray-700 focus:outline-none">
              <i className="fas fa-bars text-xl"></i>
            </button>
            <h1 className="text-2xl font-roboto-medium font-roboto-medium text-gray-900">ML-Checker</h1>
          </div>
          <div className="flex items-center space-x-4">
            <Link to="/settings" className="p-1 rounded-full text-gray-500 hover:text-gray-700 focus:outline-none">
              <i className="fas fa-cog text-xl"></i>
            </Link>
            <div className="relative">
              <button onClick={toggleUserDropdown} className="p-1 rounded-full text-gray-500 hover:text-gray-700 focus:outline-none">
                <i className="fas fa-user-circle text-xl"></i>
              </button>
              {userDropdownOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                  {isAuthenticated ? (
                    <>
                      <div className="px-4 py-2 text-sm text-gray-700 border-b border-gray-200">
                        <div>{user?.username || 'User'}</div>
                        <div className="text-xs text-gray-500">{user?.email || 'user@example.com'}</div>
                      </div>
                      <Link to="/settings" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Settings</Link>
                      <button onClick={handleLogout} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Logout</button>
                    </>
                  ) : (
                    <>
                      <Link to="/login" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Login</Link>
                      <Link to="/register" className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Register</Link>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className={`bg-white shadow-md transition-all duration-300 ease-in-out ${sidebarCollapsed ? 'w-16' : 'w-64'}`}>
          {/* Logo at the top of the sidebar */}
          <div className="px-2 py-4 flex justify-center">
            <img 
              src="/assets/ml-checker_logo.png" 
              alt="ML-Checker Logo" 
              className={`max-w-full ${sidebarCollapsed ? 'hidden' : 'w-56'}`} 
            />
          </div>
          <nav className="px-2 py-3">
            <div className="py-2">
              <Link 
                to="/" 
                className={`flex items-center px-4 py-3 text-gray-700 hover:bg-blue-100 hover:text-blue-800 rounded-lg transition-colors duration-150 ${isActive('/') ? 'bg-blue-100 text-blue-800' : ''}`}
              >
                <i className="fas fa-home mr-3 text-lg"></i>
                <span className={sidebarCollapsed ? 'hidden' : ''}>Dashboard</span>
              </Link>
            </div>
            <div className="py-2 border-t border-gray-200">
              <Link 
                to="/tracking" 
                className={`flex items-center px-4 py-3 text-gray-700 hover:bg-blue-100 hover:text-blue-800 rounded-lg transition-colors duration-150 ${isActive('/tracking') ? 'bg-blue-100 text-blue-800' : ''}`}
              >
                <i className="fas fa-chart-line mr-3 text-lg"></i>
                <span className={sidebarCollapsed ? 'hidden' : ''}>Tracking</span>
              </Link>
            </div>
            <div className="py-2 border-t border-gray-200">
              <Link 
                to="/anomaly" 
                className={`flex items-center px-4 py-3 text-gray-700 hover:bg-blue-100 hover:text-blue-800 rounded-lg transition-colors duration-150 ${isActive('/anomaly') ? 'bg-blue-100 text-blue-800' : ''}`}
              >
                <i className="fas fa-exclamation-triangle mr-3 text-lg"></i>
                <span className={sidebarCollapsed ? 'hidden' : ''}>Anomaly Detection</span>
              </Link>
            </div>
            <div className="py-2 border-t border-gray-200">
              <Link 
                to="/prompt"
                className={`flex items-center px-4 py-3 text-gray-700 hover:bg-blue-100 hover:text-blue-800 rounded-lg transition-colors duration-150 ${isActive('/prompt') ? 'bg-blue-100 text-blue-800' : ''}`}
              >
                <i className="fas fa-tachometer mr-3 text-lg"></i>
                <span className={sidebarCollapsed ? 'hidden' : ''}>Prompt Testing</span>
              </Link>
            </div>
            <div className="py-2 border-t border-gray-200">
              <Link 
                to="/settings" 
                className={`flex items-center px-4 py-3 text-gray-700 hover:bg-blue-100 hover:text-blue-800 rounded-lg transition-colors duration-150 ${isActive('/settings') ? 'bg-blue-100 text-blue-800' : ''}`}
              >
                <i className="fas fa-cog mr-3 text-lg"></i>
                <span className={sidebarCollapsed ? 'hidden' : ''}>Settings</span>
              </Link>
            </div>
          </nav>
        </aside>

        {/* Mobile Menu Button (visible only on mobile) */}
        <div className="md:hidden fixed bottom-4 right-4 z-20">
          <button 
            onClick={toggleSidebar} 
            className="bg-blue-600 text-white p-3 rounded-full shadow-lg"
          >
            <i className="fas fa-bars"></i>
          </button>
        </div>

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4">
          {children}
        </main>
      </div>

      {/* Click outside handler for user dropdown */}
      {userDropdownOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setUserDropdownOpen(false)}
        ></div>
      )}
    </div>
  );
};

export default Layout;
