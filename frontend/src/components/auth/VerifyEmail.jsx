import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import axios from 'axios';
import Logo from '../common/Logo';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying'); // 'verifying', 'success', 'error'
  const [error, setError] = useState('');
  const [username, setUsername] = useState('');
  const [token, setToken] = useState('');
  const [directVerifyLink, setDirectVerifyLink] = useState('');
  const [directTokenLink, setDirectTokenLink] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');
      setToken(token);
      
      console.log('Verification token:', token);
      
      if (!token) {
        console.error('No token found in URL');
        setStatus('error');
        setError('No verification token found');
        return;
      }

      try {
        console.log('Making verification API request...');
        // Use axios with the configured baseURL from main.jsx
        
        // Set up direct verification links
        setDirectTokenLink(`https://web-production-af8b.up.railway.app/api/auth/email/dev-verify-token/${token}`);
        
        // Try a direct API call
        const apiURL = `/api/auth/email/verify-email/${token}`;
        console.log('API URL:', apiURL);
        
        const response = await axios.get(apiURL);
        console.log('Verification API response:', response);
        
        if (response.status === 200) {
          console.log('Verification successful!');
          setStatus('success');
          // Save username if available in response
          if (response.data && response.data.username) {
            setUsername(response.data.username);
            // Create direct verification link
            setDirectVerifyLink(`https://web-production-af8b.up.railway.app/api/auth/email/dev/verify/${response.data.username}`);
          }
          // Redirect to login after 3 seconds
          setTimeout(() => navigate('/login'), 3000);
        }
      } catch (err) {
        console.error('Verification error details:', err);
        if (err.response) {
          console.error('Error response data:', err.response.data);
          console.error('Error response status:', err.response.status);
          
          // If we got a username from the error response, set up direct verification
          if (err.response.data && err.response.data.username) {
            setUsername(err.response.data.username);
            // Create direct verification link
            setDirectVerifyLink(`https://web-production-af8b.up.railway.app/api/auth/email/dev/verify/${err.response.data.username}`);
          }
        }
        setStatus('error');
        setError(err.response?.data?.detail || 'Failed to verify email. Please try again.');
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  const renderContent = () => {
    switch (status) {
      case 'verifying':
        return (
          <>
            <div className="mx-auto mb-6">
              <Logo size="lg" />
            </div>
            <h2 className="text-3xl font-bold text-yellow-400 mb-4">Verifying Your Email</h2>
            <p className="text-gray-300 mb-6">Please wait while we verify your email address...</p>
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
            </div>
          </>
        );
      case 'success':
        return (
          <>
            <div className="mx-auto mb-6">
              <Logo size="lg" />
            </div>
            <h2 className="text-3xl font-bold text-green-400 mb-4">Email Verified!</h2>
            <p className="text-gray-300 mb-6">
              {username ? `Thank you, ${username}!` : 'Your email has been successfully verified.'} You will be redirected to the login page shortly.
            </p>
            <Link to="/login" className="bg-yellow-400 text-gray-900 px-6 py-2 rounded-lg hover:bg-yellow-500 transition-colors">
              Go to Login
            </Link>
          </>
        );
      case 'error':
        return (
          <>
            <div className="mx-auto mb-6">
              <Logo size="lg" />
            </div>
            <h2 className="text-3xl font-bold text-red-400 mb-4">Verification Failed</h2>
            <p className="text-gray-300 mb-6">{error}</p>
            <div className="flex flex-col gap-4">
              {directTokenLink && (
                <>
                  <p className="text-gray-300 mt-2">
                    Try direct token verification:
                  </p>
                  <a 
                    href={directTokenLink}
                    className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
                  >
                    Verify with Token
                  </a>
                </>
              )}
              
              {directVerifyLink && (
                <>
                  <p className="text-gray-300 mt-2">
                    Or verify by username:
                  </p>
                  <a 
                    href={directVerifyLink}
                    className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Verify by Username
                  </a>
                </>
              )}
              
              <p className="text-gray-300 mt-4">
                You can also try these options:
              </p>
              
              <Link to="/direct-verify" className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition-colors">
                Manual Verification
              </Link>
              
              <Link to="/verify-user" className="bg-indigo-500 text-white px-6 py-2 rounded-lg hover:bg-indigo-600 transition-colors">
                Verify by Username
              </Link>
              
              <Link to="/login" className="bg-yellow-400 text-gray-900 px-6 py-2 rounded-lg hover:bg-yellow-500 transition-colors">
                Go to Login
              </Link>
              
              <Link 
                to="/api/auth/email/resend-verification"
                className="text-yellow-400 underline hover:text-yellow-500"
              >
                Resend Verification Email
              </Link>
            </div>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center py-12">
      <div className="max-w-md mx-auto">
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 shadow-lg text-center">
          {renderContent()}
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail; 