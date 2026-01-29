import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="bg-gray-800 border-b border-gray-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex-shrink-0">
              <img
                className="h-10 w-auto transition-transform duration-300 hover:scale-105"
                src="/images/arbify-logo.png"
                alt="Arbify"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = 'https://placehold.co/200x100/yellow/black?text=ARBIFY';
                }}
              />
            </Link>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link
                  to="/"
                  className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Home
                </Link>
                <Link
                  to="/dashboard"
                  className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </Link>

                <Link
                  to="/dashboard#arbitrage"
                  className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  onClick={e => {
                    if (window.location.pathname === '/dashboard') {
                      e.preventDefault();
                      window.dispatchEvent(new CustomEvent('dashboardTabChange', { detail: 'arbitrage' }));
                    }
                  }}
                >
                  Arbitrage
                </Link>
                <Link
                  to="/dashboard#calculator"
                  className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  onClick={e => {
                    if (window.location.pathname === '/dashboard') {
                      e.preventDefault();
                      window.dispatchEvent(new CustomEvent('dashboardTabChange', { detail: 'calculator' }));
                    }
                  }}
                >
                  Calculator
                </Link>
                <Link
                  to="/subscriptions"
                  className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Subscriptions
                </Link>
                {isAuthenticated && (
                  <Link
                    to="/profile"
                    className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Profile
                  </Link>
                )}
                {!isAuthenticated && (
                  <Link
                    to="/register"
                    className="text-gray-300 hover:text-yellow-400 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                  >
                    Register
                  </Link>
                )}
              </div>
            </div>
          </div>
          <div className="hidden md:block">
            <div className="ml-4 flex items-center md:ml-6">
              {isAuthenticated ? (
                <div className="flex items-center space-x-4">
                  <span className="text-gray-300 text-sm">
                    Welcome, {user?.username}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <Link
                  to="/login"
                  className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Login
                </Link>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-300 hover:text-yellow-400 p-2 rounded-md transition-colors"
            >
              {isMobileMenuOpen ? (
                <i className="fas fa-times text-xl"></i>
              ) : (
                <i className="fas fa-bars text-xl"></i>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-gray-800 border-t border-gray-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            <Link
              to="/"
              className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Home
            </Link>
            <Link
              to="/dashboard"
              className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Dashboard
            </Link>
            <Link
              to="/dashboard#odds"
              className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Odds
            </Link>
            <Link
              to="/dashboard#arbitrage"
              className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Arbitrage
            </Link>
            <Link
              to="/dashboard#calculator"
              className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Calculator
            </Link>
            <Link
              to="/subscriptions"
              className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Subscriptions
            </Link>
            {isAuthenticated && (
              <Link
                to="/profile"
                className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Profile
              </Link>
            )}
            {!isAuthenticated && (
              <Link
                to="/register"
                className="text-gray-300 hover:text-yellow-400 block px-3 py-2 rounded-md text-base font-medium transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Register
              </Link>
            )}
            {isAuthenticated ? (
              <div className="px-3 py-2">
                <span className="text-gray-300 text-sm block mb-2">
                  Welcome, {user?.username}
                </span>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="bg-yellow-400 hover:bg-yellow-500 text-gray-900 block px-3 py-2 rounded-lg text-base font-medium transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Login
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar; 