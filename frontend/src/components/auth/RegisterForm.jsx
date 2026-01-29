import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Helmet } from 'react-helmet-async';

const RegisterForm = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    full_name: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [passwordErrors, setPasswordErrors] = useState([]);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear password errors when user starts typing in the password field
    if (name === 'password') {
      setPasswordErrors([]);
    }
  };

  // Validate password and return array of errors or empty array if valid
  const validatePassword = (password) => {
    const errors = [];

    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }

    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }

    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain at least one lowercase letter');
    }

    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }

    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setPasswordErrors([]);

    try {
      // Validate input
      if (!formData.username || !formData.email || !formData.full_name || !formData.password) {
        throw new Error('Please fill in all fields');
      }

      // Validate password
      const passwordValidationErrors = validatePassword(formData.password);
      if (passwordValidationErrors.length > 0) {
        setPasswordErrors(passwordValidationErrors);
        setLoading(false);
        return; // Stop here, don't try to submit to server
      }

      // Use axios with the configured baseURL from main.jsx
      const response = await axios.post('/api/auth/register', formData, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        timeout: 10000 // 10 second timeout
      });

      console.log('Registration successful:', response.data);

      setSuccess('Registration successful! You can now log in to your account.');

      // Redirect after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      console.error('Registration error:', err);

      // Handle network errors
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The server might be down or unreachable.');
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError(`Network error. Please check if the backend server is running at ${window.location.hostname === 'localhost' ? 'http://localhost:8001' : window.location.origin}`);
      }
      // Handle validation errors returned by FastAPI
      else if (err.response?.data?.detail) {
        // Check if detail is an array (validation errors)
        if (Array.isArray(err.response.data.detail)) {
          // Get the first validation error message
          const firstError = err.response.data.detail[0];
          setError(firstError.msg || 'Validation error');
        } else if (typeof err.response.data.detail === 'object') {
          // If detail is an object with keys like type, loc, msg
          setError(err.response.data.detail.msg || 'Validation error');
        } else {
          // If detail is a simple string
          setError(err.response.data.detail);
        }
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-900 px-4 py-8">
      <Helmet>
        <title>Register - Arbify Sports Arbitrage</title>
        <meta name="description" content="Create your Arbify account to start finding profitable sports arbitrage betting opportunities today." />
      </Helmet>
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 max-w-md w-full">
        <div className="text-center mb-8">
          <img
            src="/images/arbify-logo.png"
            alt="Arbify Logo"
            className="h-32 mx-auto mb-4"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://placehold.co/200x100/d4af37/000000?text=ARBIFY';
            }}
          />
          <h2 className="text-2xl font-bold text-yellow-400">Create Account</h2>
          <p className="text-gray-400 mt-2">Join Arbify today</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-red-900/50 border border-red-700 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-red-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-white text-sm">{error}</p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Choose a username"
              required
            />
            <p className="text-xs text-gray-400 mt-1">Alphanumeric characters only.</p>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Full Name
            </label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter your full name"
              required
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className={`w-full px-4 py-3 bg-gray-700 text-white rounded-lg border ${passwordErrors.length > 0 ? 'border-red-500' : 'border-gray-600'} focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors`}
              placeholder="Create a password"
              required
            />

            {passwordErrors.length > 0 ? (
              <div className="mt-2 p-3 bg-red-900/30 border border-red-700/50 rounded text-sm">
                <p className="font-medium text-red-400 mb-1">Password requirements:</p>
                <ul className="list-disc list-inside text-xs text-gray-300 space-y-1">
                  {passwordErrors.map((error, index) => (
                    <li key={index} className="text-red-300">{error}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-xs text-gray-400 mt-1">
                Password must have:
                <ul className="list-disc list-inside mt-1 ml-1 space-y-0.5">
                  <li>At least 8 characters</li>
                  <li>At least one uppercase letter (A-Z)</li>
                  <li>At least one lowercase letter (a-z)</li>
                  <li>At least one number (0-9)</li>
                </ul>
              </p>
            )}
          </div>

          {/* Legal Agreement Checkboxes */}
          <div className="space-y-3">
            <div className="flex items-start">
              <input
                type="checkbox"
                id="terms"
                name="terms"
                required
                className="mt-1 mr-3 w-4 h-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
              />
              <label htmlFor="terms" className="text-sm text-gray-300">
                I agree to the{' '}
                <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-yellow-400 hover:text-yellow-300 underline">
                  Terms of Service
                </a>
              </label>
            </div>

            <div className="flex items-start">
              <input
                type="checkbox"
                id="privacy"
                name="privacy"
                required
                className="mt-1 mr-3 w-4 h-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
              />
              <label htmlFor="privacy" className="text-sm text-gray-300">
                I agree to the{' '}
                <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-yellow-400 hover:text-yellow-300 underline">
                  Privacy Policy
                </a>
              </label>
            </div>

            <div className="flex items-start">
              <input
                type="checkbox"
                id="email_consent"
                name="email_consent"
                className="mt-1 mr-3 w-4 h-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
              />
              <label htmlFor="email_consent" className="text-sm text-gray-300">
                I consent to receive email notifications about arbitrage opportunities
              </label>
            </div>
          </div>

          {success && (
            <div className="p-4 bg-green-900/50 border border-green-700 rounded-lg">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-green-400 mr-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <p className="text-white text-sm">{success}</p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading || passwordErrors.length > 0}
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900 mr-2"></div>
                Creating account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-gray-400">
            Already have an account?{' '}
            <Link to="/login" className="text-yellow-400 hover:text-yellow-500 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterForm; 