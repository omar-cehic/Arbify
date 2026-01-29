import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import axios from 'axios';

const SubscriptionGate = ({ children, pageName = "this feature" }) => {
  const { isAuthenticated } = useAuth();
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkSubscriptionStatus = async () => {
      if (!isAuthenticated) {
        setSubscriptionStatus('no_subscription');
        setLoading(false);
        return;
      }
      
      try {
        const response = await axios.get('/api/subscription/my-subscription');
        if (response && response.data && typeof response.data === 'object') {
          setSubscriptionStatus(response.data.status || 'no_subscription');
        } else {
          setSubscriptionStatus('no_subscription');
        }
      } catch (err) {
        console.error('Error fetching subscription:', err);
        setSubscriptionStatus('no_subscription');
      } finally {
        setLoading(false);
      }
    };

    checkSubscriptionStatus();
  }, [isAuthenticated]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show subscription required screen for users without subscription
  if (subscriptionStatus === 'no_subscription') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
        <div className="max-w-2xl mx-auto p-6 text-center">
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-8">
            <div className="w-16 h-16 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-yellow-400 text-2xl">🔒</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-4">Subscription Required</h1>
            <p className="text-gray-300 mb-6">
              To access {pageName}, you need an active subscription.
            </p>
            <div className="space-y-4">
              <Link 
                to="/subscriptions" 
                className="block w-full bg-yellow-400 text-gray-900 rounded-lg py-3 font-semibold text-center hover:bg-yellow-500 transition-colors"
              >
                View Subscription Plans
              </Link>
              {!isAuthenticated && (
                <Link 
                  to="/login" 
                  className="block w-full bg-gray-700/50 border border-gray-600/50 text-white rounded-lg py-3 font-medium text-center hover:bg-gray-600/50 transition-colors"
                >
                  Login to Existing Account
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // If user has active subscription or trial, show the content
  return children;
};

export default SubscriptionGate; 