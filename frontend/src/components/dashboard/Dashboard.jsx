import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Helmet } from 'react-helmet-async';

const Dashboard = () => {
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(true);

  // Check subscription status only when authenticated
  useEffect(() => {
    const checkSubscriptionStatus = async () => {
      if (!isAuthenticated) {
        setSubscriptionStatus('no_subscription');
        setIsLoading(false);
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
        setIsLoading(false);
      }
    };

    checkSubscriptionStatus();
  }, [isAuthenticated]);

  // Clean up any old localStorage trial data
  useEffect(() => {
    const hadTrialData = localStorage.getItem('arbify_trial');
    if (hadTrialData) {
      localStorage.removeItem('arbify_trial');
    }
  }, []);

  const getAccountStatus = () => {
    if (!isAuthenticated) return { text: 'Guest', color: 'text-gray-400' };
    if (subscriptionStatus === 'active') return { text: 'Premium', color: 'text-yellow-400' };
    if (subscriptionStatus === 'trialing') return { text: 'Premium Trial', color: 'text-blue-400' };
    if (subscriptionStatus === 'no_subscription') return { text: 'No Subscription', color: 'text-red-400' };
    return { text: 'Basic', color: 'text-green-400' };
  };

  const accountStatus = getAccountStatus();

  // Static Data for "Live Markets Status" Widget
  // Static Data for "Live Markets Status" Widget
  const liveSports = [
    { id: 1, name: 'NBA (Basketball)', status: 'active', count: 'Active' },
    { id: 2, name: 'NFL (Football)', status: 'active', count: 'Active' },
    { id: 3, name: 'Premier League', status: 'active', count: 'Active' },
    { id: 4, name: 'UFC / MMA', status: 'active', count: 'Active' },
    { id: 5, name: 'Tennis (ATP/WTA)', status: 'active', count: 'Active' },
    { id: 6, name: 'NHL (Hockey)', status: 'active', count: 'Active' },
    { id: 7, name: 'MLB (Baseball)', status: 'off', count: 'Off Season' },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white py-10">
        <div className="container mx-auto px-4">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400"></div>
          </div>
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
              To access the arbitrage dashboard and all its features, you need an active subscription.
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

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <Helmet>
        <title>Dashboard - Arbify</title>
        <meta name="description" content="Arbify Dashboard - Your command center for sports arbitrage betting." />
      </Helmet>
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="mb-8 border-b border-gray-800 pb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back{isAuthenticated ? ', ' + (JSON.parse(localStorage.getItem('user') || '{}').full_name || 'User') : ''}
          </h1>
          <p className="text-gray-400">Your arbitrage command center.</p>
        </div>

        {/* Trial Banner */}
        {subscriptionStatus === 'trialing' && (
          <div className="bg-gradient-to-r from-blue-900/40 to-gray-900 border border-blue-500/30 rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-white text-lg">Premium Trial Active</h3>
                <p className="text-blue-200/70 text-sm">Full access enabled.</p>
              </div>
              <Link to="/subscriptions" className="text-blue-300 hover:text-white text-sm font-medium transition-colors">
                Upgrade Plan &rarr;
              </Link>
            </div>
          </div>
        )}

        {/* Quick Actions Grid */}
        <div className="mb-10">
          <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link
              to="/arbitrage"
              className="bg-gray-800 border border-gray-700 hover:border-yellow-500/50 rounded-lg p-6 transition-all duration-200 group hover:shadow-lg"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-gray-900 rounded-lg group-hover:bg-gray-800 transition-colors">
                  <svg className="w-6 h-6 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
              </div>
              <div className="font-bold text-white text-lg mb-1 group-hover:text-yellow-400 transition-colors">Find Opportunities</div>
              <p className="text-gray-400 text-sm">Scan markets for profitable arbitrage bets.</p>
            </Link>

            <Link
              to="/calculator"
              className="bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-lg p-6 transition-all duration-200 group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-gray-900 rounded-lg group-hover:bg-gray-800 transition-colors">
                  <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              <div className="font-bold text-white text-lg mb-1">Calculator</div>
              <p className="text-gray-400 text-sm">Calculate stakes and returns accurately.</p>
            </Link>

            <Link
              to="/profile?tab=myArbitrage"
              className="bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-lg p-6 transition-all duration-200 group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="p-3 bg-gray-900 rounded-lg group-hover:bg-gray-800 transition-colors">
                  <svg className="w-6 h-6 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
              <div className="font-bold text-white text-lg mb-1">My History</div>
              <p className="text-gray-400 text-sm">Review your tracked bets and performance.</p>
            </Link>
          </div>
        </div>

        {/* Main Content Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Left Column: Live Markets Status */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center bg-gray-800/50">
                <h2 className="text-lg font-bold text-white">Live Markets</h2>
                <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Data Feed: Live</span>
              </div>

              <div className="divide-y divide-gray-700/50">
                {liveSports.map((sport) => (
                  <div key={sport.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-750 transition-colors">
                    <span className={`font-medium ${sport.status === 'active' ? 'text-gray-200' : 'text-gray-500'}`}>
                      {sport.name}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded font-medium ${sport.status === 'active'
                      ? 'text-yellow-400 bg-yellow-400/10'
                      : 'text-gray-500 bg-gray-700/30'
                      }`}>
                      {sport.count}
                    </span>
                  </div>
                ))}
              </div>
              <div className="p-4 bg-gray-800/80 border-t border-gray-700 text-center">
                <Link to="/arbitrage" className="text-yellow-500 hover:text-yellow-400 text-sm font-medium transition-colors">
                  View All Markets &rarr;
                </Link>
              </div>
            </div>
          </div>

          {/* Right Column: Account & Support */}
          <div className="lg:col-span-1 space-y-6">

            {/* Account Summary */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4">Subscription</h3>
              <div className="flex justify-between items-center mb-6">
                <span className="text-gray-400 text-sm">Current Plan</span>
                <span className={`font-semibold text-sm px-2 py-1 rounded ${subscriptionStatus === 'active' ? 'bg-yellow-400/10 text-yellow-400' :
                  subscriptionStatus === 'trialing' ? 'bg-blue-400/10 text-blue-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                  {accountStatus.text}
                </span>
              </div>
              <Link to="/profile" className="block w-full bg-gray-700 hover:bg-gray-600 text-white rounded-md py-2 text-sm font-medium text-center transition-colors">
                Manage Account
              </Link>
            </div>

            {/* Help Card */}
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-bold text-white mb-2">Support</h3>
              <p className="text-gray-400 text-sm mb-4 leading-relaxed">
                Having issues or need assistance with your account? Our team is here to help.
              </p>
              <Link to="/support" className="text-yellow-500 hover:text-yellow-400 text-sm font-medium transition-colors">
                Contact Support &rarr;
              </Link>
            </div>

          </div>
        </div>
      </div>
    </div >
  );
};

export default Dashboard;