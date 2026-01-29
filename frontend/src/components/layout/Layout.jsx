import { Link, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import Logo from '../common/Logo';

const Layout = ({ children }) => {
  const [isNavOpen, setIsNavOpen] = useState(false);
  const navigate = useNavigate();

  // Get auth context unconditionally (proper hook usage)
  const authContext = useAuth();

  // Then safely extract values, falling back to localStorage if needed
  const user = authContext?.user || JSON.parse(localStorage.getItem('user') || 'null');
  const isAuthenticated = authContext?.isAuthenticated || !!localStorage.getItem('access_token');

  const handleLogout = () => {
    if (authContext?.logout) {
      authContext.logout();
    } else {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      navigate('/');
    }
  };

  const toggleNav = () => setIsNavOpen(!isNavOpen);

  // Define styles for nav links and buttons
  const navLinkStyles = "px-3 py-2 rounded text-white hover:text-yellow-400 transition-colors font-medium";
  const profileButton = "px-3 py-2 bg-yellow-400 text-gray-900 rounded hover:bg-yellow-500 transition-colors font-medium";
  const buttonDanger = "px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors";

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      {/* Navbar */}
      <nav className="bg-gray-800 shadow-lg" role="navigation" aria-label="Main navigation">
        <div className="container mx-auto px-4">
          <div className="flex justify-between h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/" className="flex items-center text-gray-100 hover:text-yellow-400 transition-colors">
                <Logo size="md" />
                <span className="hidden md:inline text-xl font-semibold ml-3">Arbify</span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex space-x-1">
              <Link to="/" className={navLinkStyles}>Home</Link>
              <Link to="/dashboard" className={navLinkStyles}>Dashboard</Link>

              <Link to="/arbitrage" className={navLinkStyles}>Arbitrage</Link>
              <Link to="/calculator" className={navLinkStyles}>Calculator</Link>
              <Link to="/subscriptions" className={navLinkStyles}>Subscriptions</Link>
            </div>

            {/* Right side */}
            <div className="hidden md:flex items-center space-x-4">
              {isAuthenticated ? (
                <>
                  <Link to="/profile" className={profileButton}>
                    <span className="flex items-center">
                      <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                      </svg>
                      {user?.username || 'Profile'}
                    </span>
                  </Link>
                  <button onClick={handleLogout} className={buttonDanger}>
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className={navLinkStyles}>
                    Sign In
                  </Link>
                  <Link to="/register" className={navLinkStyles + " bg-yellow-400 text-gray-900 hover:bg-yellow-500"}>
                    Register
                  </Link>
                </>
              )}
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center">
              <button
                onClick={toggleNav}
                className="text-gray-400 hover:text-gray-100 focus:outline-none focus:text-gray-100"
                aria-label={isNavOpen ? "Close navigation menu" : "Open navigation menu"}
                aria-expanded={isNavOpen}
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>

          {/* Mobile menu */}
          {isNavOpen && (
            <div className="md:hidden py-2" role="menu" aria-label="Mobile navigation menu">
              <Link to="/" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                Home
              </Link>
              <Link to="/dashboard" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                Dashboard
              </Link>

              <Link to="/arbitrage" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                Arbitrage
              </Link>
              <Link to="/calculator" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                Calculator
              </Link>
              <Link to="/subscriptions" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                Subscriptions
              </Link>
              {isAuthenticated ? (
                <>
                  <Link to="/profile" className="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-900 bg-yellow-400 hover:bg-yellow-500">
                    <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                    </svg>
                    Profile
                  </Link>
                  <button onClick={handleLogout} className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-400 hover:bg-gray-700">
                    Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                    Sign In
                  </Link>
                  <Link to="/register" className="block px-3 py-2 rounded-md text-base font-medium text-gray-100 hover:text-yellow-400 hover:bg-gray-700">
                    Register
                  </Link>
                </>
              )}
            </div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Cookie Notice */}
      <div className="bg-gray-800 border-t border-gray-600 py-3">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <p className="text-sm text-gray-400">
              This site uses essential cookies for security and functionality. No tracking or advertising cookies are used.
            </p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8" role="contentinfo">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <Logo size="sm" className="mb-2" />
            </div>
            <div className="flex flex-wrap justify-center md:justify-end gap-4">
              <Link to="/" className="text-gray-400 hover:text-yellow-400 text-sm">Home</Link>
              <Link to="/dashboard" className="text-gray-400 hover:text-yellow-400 text-sm">Dashboard</Link>

              <Link to="/arbitrage" className="text-gray-400 hover:text-yellow-400 text-sm">Arbitrage</Link>
              <Link to="/calculator" className="text-gray-400 hover:text-yellow-400 text-sm">Calculator</Link>
              <Link to="/subscriptions" className="text-gray-400 hover:text-yellow-400 text-sm">Subscriptions</Link>
              {isAuthenticated && (
                <Link to="/profile" className="text-yellow-400 hover:text-yellow-300 text-sm font-medium">Profile</Link>
              )}
            </div>
          </div>

          {/* Legal Footer */}
          <div className="mt-6 pt-6 border-t border-gray-600">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="flex flex-wrap justify-center md:justify-start gap-4 mb-4 md:mb-0">
                <Link to="/terms" className="text-gray-400 hover:text-yellow-400 text-xs">Terms of Service</Link>
                <span className="text-gray-600">|</span>
                <Link to="/privacy" className="text-gray-400 hover:text-yellow-400 text-xs">Privacy Policy</Link>
                <span className="text-gray-600">|</span>
                <Link to="/refund-policy" className="text-gray-400 hover:text-yellow-400 text-xs">Refund Policy</Link>
                <span className="text-gray-600">|</span>
                <Link to="/support" className="text-gray-400 hover:text-yellow-400 text-xs">Support</Link>
              </div>
              <div className="text-gray-400 text-xs">
                © {new Date().getFullYear()} Arbify. All rights reserved.
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;