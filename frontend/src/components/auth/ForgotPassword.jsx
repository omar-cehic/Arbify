import { useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Helmet } from 'react-helmet-async';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      if (!email) {
        throw new Error('Please enter your email address');
      }

      // Make API call to forgot password endpoint
      const response = await axios.post('/api/auth/password/request-reset',
        { email },
        {
          headers: {
            'Content-Type': 'application/json'
          },
          timeout: 10000 // 10 second timeout
        }
      );

      setSuccess('Password reset instructions have been sent to your email');
      setEmail('');
    } catch (err) {
      console.error('Forgot password error:', err);

      // Handle network errors
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out. The server might be down or unreachable.');
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Network error. Please check if the backend server is running.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError(err.message || 'Failed to process request. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <Helmet>
        <title>Forgot Password - Arbify</title>
        <meta name="description" content="Reset your Arbify account password." />
      </Helmet>
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
        <div className="text-center mb-8">
          <img
            src="/images/arbify-logo.png"
            alt="Arbify Logo"
            className="h-16 mx-auto mb-4"
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://placehold.co/200x100/yellow/black?text=ARBIFY';
            }}
          />
          <h3 className="text-2xl font-bold text-yellow-400">Forgot Password</h3>
          <p className="text-gray-400 mt-2">Enter your email to reset your password</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter your email"
              required
            />
          </div>

          {error && (
            <div className="p-4 bg-red-900/50 border border-red-700 rounded-lg">
              <div className="flex items-center">
                <i className="fas fa-exclamation-circle text-red-400 mr-3"></i>
                <p className="text-white text-sm">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="p-4 bg-green-900/50 border border-green-700 rounded-lg">
              <div className="flex items-center">
                <i className="fas fa-check-circle text-green-400 mr-3"></i>
                <p className="text-white text-sm">{success}</p>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900 mr-2"></div>
                Sending instructions...
              </>
            ) : (
              'Send Reset Instructions'
            )}
          </button>
        </form>

        <div className="mt-8 text-center">
          <Link
            to="/login"
            className="text-gray-400 hover:text-yellow-400 transition-colors text-sm"
          >
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
