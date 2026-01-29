import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { AuthContext } from '../../context/AuthContext';
import axios from 'axios';

// Mock data to use when API fails
const mockPlans = [
  {
    id: 'basic-plan',
    name: 'Basic',
    price_monthly: 19.99,
    description: 'Get started with arbitrage betting',
    features: [
      'Arbitrage finder & calculator',
      'Pre-match opportunities only (no live betting)',
      '2 strategy templates (Quick Arbs, Mid-Margin)',
      '2 custom strategies max',
      '1 email alert per day',
      'Odds refresh every 60 seconds',
      'Save & track your bets (record wins/losses)',
    ],
    trial: false
  },
  {
    id: 'premium-plan',
    name: 'Premium',
    price_monthly: 59.99,
    description: 'Full access to all features',
    features: [
      'Live arbitrage opportunities (higher profit percentages)',
      '5 strategy templates (including Live Arbitrage)',
      'Unlimited custom strategies',
      '3 alerts per day (email + browser notifications)',
      'Odds refresh every 30 seconds (2x faster)',
      'Advanced filtering options',
    ],
    trial: true,
    trial_days: 7
  }
];

const premiumExclusiveFeatures = [
  'Live arbitrage opportunities (higher profit percentages)',
  '5 strategy templates (including Live Arbitrage)',
  'Unlimited custom strategies',
  '3 alerts per day (email + browser notifications)',
  'Odds refresh every 30 seconds (2x faster)',
  'Advanced filtering options',
];

const Subscription = () => {
  const { user, isAuthenticated } = useContext(AuthContext);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [subscribing, setSubscribing] = useState(null);
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [subscriptionDetails, setSubscriptionDetails] = useState(null);
  const [trialEligibility, setTrialEligibility] = useState({ eligible: false, has_used_trial: false });
  const [apiError, setApiError] = useState('');
  const navigate = useNavigate();

  // Clean up old localStorage trial data on component mount
  useEffect(() => {
    // Remove any old trial data from localStorage since we now use backend-only trials
    const hadTrialData = localStorage.getItem('arbify_trial');
    if (hadTrialData) {
      console.log('Cleaning up old localStorage trial data:', hadTrialData);
      localStorage.removeItem('arbify_trial');
    }

    // Also clean up any other trial-related localStorage keys that might exist
    const keysToClean = ['trial_start', 'trial_status', 'trial_days_left'];
    keysToClean.forEach(key => {
      if (localStorage.getItem(key)) {
        console.log(`Cleaning up old localStorage key: ${key}`);
        localStorage.removeItem(key);
      }
    });
  }, []);

  // Fetch subscription plans
  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await axios.get('/api/subscription/plans');
        setPlans(res.data);
      } catch (err) {
        console.error('Error fetching plans:', err);
        setPlans([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  // Fetch trial eligibility
  useEffect(() => {
    const fetchTrialEligibility = async () => {
      if (!isAuthenticated || !user) return;

      try {
        const res = await axios.get('/api/subscription/trial-eligibility');
        setTrialEligibility(res.data);
      } catch (err) {
        console.error('Error fetching trial eligibility:', err);
        setTrialEligibility({ eligible: false, has_used_trial: true });
      }
    };

    fetchTrialEligibility();
  }, [isAuthenticated, user]);

  // Define fetchSubscriptionDetails function
  const fetchSubscriptionDetails = async () => {
    if (!isAuthenticated || !user) return;

    try {
      // Clean up any abandoned pending subscriptions first
      await axios.post('/api/subscription/cleanup-pending');

      const res = await axios.get('/api/subscription/my-subscription');
      console.log('📊 Subscription details response:', res.data);

      if (res.data) {
        setSubscriptionDetails(res.data);
        setSubscriptionStatus(res.data.status);
      } else {
        cleanupSubscriptionData();
      }
    } catch (err) {
      console.error('Error fetching subscription details:', err);
      cleanupSubscriptionData();
    }
  };

  useEffect(() => {
    fetchSubscriptionDetails();

    // Handle URL parameters for success/cancel scenarios
    const urlParams = new URLSearchParams(window.location.search);
    const success = urlParams.get('success');
    const trial = urlParams.get('trial');
    const upgrade = urlParams.get('upgrade');
    const prorate = urlParams.get('prorate');
    const canceled = urlParams.get('canceled');

    console.log('🔍 URL Parameters Debug:', {
      currentURL: window.location.href,
      success,
      trial,
      upgrade,
      prorate,
      canceled,
      allParams: Object.fromEntries(urlParams.entries())
    });

    if (success === 'true') {
      if (trial === 'true') {
        // Activate pending trial
        console.log('🎯 Detected trial signup success');
        activateTrial();
      } else if (upgrade === 'true') {
        // Handle upgrade success
        console.log('🎯 Detected upgrade success');
        if (prorate === 'true') {
          console.log('🎉 Prorated upgrade successful! You were only charged the difference.');
          alert('🎉 Upgrade successful! You were only charged the prorated difference for your new plan.');
        } else {
          console.log('🎉 Upgrade successful! Refreshing subscription data...');
        }
        // Refresh subscription data after upgrade
        setTimeout(() => {
          fetchSubscriptionDetails();
        }, 1000);
      } else {
        // Handle regular subscription success
        console.log('🎯 Detected regular subscription success. Syncing...');

        // Call sync endpoint
        const sessionId = urlParams.get('session_id');
        if (sessionId) {
          axios.post(`/api/subscriptions/sync-subscription?session_id=${sessionId}`)
            .then(() => {
              console.log('✅ Sync successful');
              fetchSubscriptionDetails();
            })
            .catch(err => {
              console.error('Sync failed, relying on webhook', err);
              setTimeout(() => fetchSubscriptionDetails(), 2000);
            });
        } else {
          setTimeout(() => {
            fetchSubscriptionDetails();
          }, 1000);
        }
      }
    } else if (canceled === 'true') {
      console.log('❌ Checkout canceled');
    }

    // Clean up URL parameters after processing
    if (success || canceled) {
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
    }
  }, [isAuthenticated, user]);

  const handleStripeCheckout = async (planId, isTrialRequest = false) => {
    if (!isAuthenticated || !user) {
      alert('You must be logged in to subscribe.');
      navigate('/login');
      return;
    }

    setSubscribing(planId);

    try {
      console.log('🔍 Checkout Request Details:', {
        planId,
        isTrialRequest,
        subscriptionStatus,
        user: user.username,
        currentPlan: subscriptionDetails?.plan?.name,
        hasExistingSubscription: !!subscriptionDetails
      });

      // Use different endpoint for trials
      const endpoint = isTrialRequest ? '/api/subscription/checkout-trial' : '/api/subscription/checkout';

      console.log(`📡 Making request to: ${endpoint}`);
      console.log(`📊 Current subscription details:`, subscriptionDetails);

      const res = await axios.post(endpoint, { plan_id: planId });
      console.log('✅ Checkout response:', res.data);

      if (res.data && res.data.checkout_url) {
        console.log('🔗 Redirecting to Stripe checkout:', res.data.checkout_url);
        window.location.href = res.data.checkout_url;
      } else {
        console.error('❌ No checkout URL in response:', res.data);
        alert('Failed to create checkout session. Please try again.');
      }
    } catch (e) {
      console.error('❌ Checkout error:', {
        status: e.response?.status,
        data: e.response?.data,
        message: e.message
      });

      if (e.response?.status === 401) {
        alert('Your session has expired. Please log in again.');
        navigate('/login');
        return;
      } else if (e.response?.status === 422) {
        console.error('Validation error - check plan_id and user authentication');
        alert('There was an issue with your request. Please try logging out and back in.');
        return;
      } else if (e.response?.status === 400) {
        // Handle trial-specific errors
        const errorMessage = e.response?.data?.detail || 'You may have already used a free trial or have an active subscription.';
        alert(errorMessage);
        return;
      }

      alert('Failed to create checkout session. Please try again later.');
    } finally {
      setSubscribing(null);
    }
  };

  const handleManageSubscription = async () => {
    if (!isAuthenticated || !user) {
      alert('You must be logged in to manage your subscription.');
      return;
    }

    try {
      const res = await axios.post('/api/subscription/create-portal-session');
      if (res.data && res.data.url) {
        window.location.href = res.data.url;
      } else {
        alert('Failed to redirect to subscription portal.');
      }
    } catch (e) {
      console.error('Portal error:', e);
      alert('Failed to access subscription portal. Please try again later.');
    }
  };

  const isButtonDisabled = (planId, isTrialButton = false) => {
    if (!isAuthenticated || !user) return true;
    if (subscribing === planId) return true;

    // For trial buttons, check eligibility
    if (isTrialButton) {
      // Disable if user is not eligible for trial
      if (!trialEligibility.eligible) return true;

      // Disable if user is already on Premium trial or Premium subscription
      if (subscriptionStatus === 'trialing' && subscriptionDetails?.plan?.name.toLowerCase().includes('premium')) {
        return true;
      }

      return false;
    }

    // If user has an active subscription, only disable the button for the current plan
    if (subscriptionStatus === 'active' && subscriptionDetails) {
      // SINGLE PLAN MODE: If user has ANY active subscription, disable subscribing again.
      // This prevents the "Subscribe" button from showing up if they are already on a plan.
      return true;
    }

    return false;
  };

  // Helper function to get button text based on current subscription status
  const getButtonText = (planId, isTrialButton = false) => {
    if (subscribing === planId) return 'Redirecting...';
    if (isTrialButton) {
      if (!trialEligibility.eligible) return 'Trial Used';
      return 'Start 7-Day Free Trial';
    }

    // Check if this is the user's current plan
    if (subscriptionStatus === 'active') {
      return 'Active Plan';
    }

    if (subscriptionStatus === 'trialing') return 'Upgrade Now';
    return 'Subscribe';
  };

  // Helper function to check if a plan is the user's current plan
  const isCurrentPlan = (planId) => {
    if (!subscriptionDetails || !subscriptionStatus || subscriptionStatus === 'no_subscription') return false;

    // Handle both string and integer comparisons
    return subscriptionDetails.plan.id === planId ||
      subscriptionDetails.plan.id === parseInt(planId) ||
      String(subscriptionDetails.plan.id) === String(planId);
  };

  // Helper function to check if manage button should show
  const shouldShowManageButton = () => {
    if (!subscriptionDetails) return false;
    // Show for any active or trialing subscription, even if set to cancel at period end
    return subscriptionStatus === 'active' || subscriptionStatus === 'trialing';
  };

  // Helper function to check if subscription is cancelled but still active
  const isSubscriptionCancelled = () => {
    return subscriptionStatus === 'active' && subscriptionDetails?.cancel_at_period_end === true;
  };

  // Helper function to format trial status message
  const getTrialStatusMessage = () => {
    if (!subscriptionDetails || subscriptionStatus !== 'trialing') return null;

    const daysRemaining = subscriptionDetails.trial_days_remaining;

    if (daysRemaining === 0) {
      return "Your trial ends today! Subscribe now to continue access.";
    } else if (daysRemaining === 1) {
      return "Your trial ends in 1 day! Subscribe now to continue access.";
    } else if (daysRemaining && daysRemaining > 1) {
      return `Your trial has ${daysRemaining} days remaining.`;
    } else {
      return "You are currently on a 7-day free trial!";
    }
  };

  // Clean up subscription data
  const cleanupSubscriptionData = () => {
    setSubscriptionDetails(null);
    setSubscriptionStatus('no_subscription');
    setLoading(false);
  };

  const activateTrial = async () => {
    try {
      const res = await axios.post('/api/subscription/activate-trial');
      if (res.data && res.data.status === 'trialing') {
        console.log('✅ Trial activated successfully');
        // Refresh subscription data
        fetchSubscriptionDetails();
      }
    } catch (err) {
      console.error('Error activating trial:', err);
      // Still try to refresh subscription data in case it was already activated
      fetchSubscriptionDetails();
    }
  };

  // Debug function for troubleshooting
  const debugSubscriptionState = async () => {
    console.log('🔍 DEBUGGING CURRENT STATE:');
    console.log('🧑 User:', user);
    console.log('🔐 Authenticated:', isAuthenticated);
    console.log('📊 Subscription Details:', subscriptionDetails);
    console.log('📊 Subscription Status:', subscriptionStatus);
    console.log('🔗 Current URL:', window.location.href);

    try {
      const res = await axios.get('/api/subscription/my-subscription');
      console.log('🌐 Live subscription data from API:', res.data);
    } catch (err) {
      console.error('❌ Error fetching live subscription data:', err);
    }

    try {
      const res = await axios.post('/api/subscription/cleanup-pending');
      console.log('🧹 Cleanup pending response:', res.data);
    } catch (err) {
      console.error('❌ Error cleaning up pending subscriptions:', err);
    }
  };

  // Make debug function available globally for console testing
  useEffect(() => {
    window.debugSubscriptionState = debugSubscriptionState;
    return () => {
      delete window.debugSubscriptionState;
    };
  }, [user, subscriptionDetails, subscriptionStatus]);

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-br from-gray-900 via-black to-gray-900">
      <div className="max-w-4xl w-full py-12 px-4">
        <div className="bg-gray-900 rounded-xl border border-yellow-500/30 p-8 shadow-2xl text-center">
          <h2 className="text-4xl font-extrabold text-yellow-400 mb-2 tracking-tight">Subscriptions</h2>
          <p className="text-gray-300 mb-8 text-lg">Choose the plan that fits your needs and unlock premium features.</p>

          {(!isAuthenticated || !user) && (
            <div className="bg-red-900/30 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6 text-sm inline-block">
              You must be logged in to view your subscription.
            </div>
          )}

          {loading ? (
            <div className="text-gray-400">Loading plans...</div>
          ) : !plans || plans.length === 0 ? (
            <div className="text-gray-400">No plans available. Please try again later.</div>
          ) : (

            (() => {
              // Prioritize 'Pro' plan, fallback to 'Premium' if legacy DB
              const proPlan = plans.find(p => p.name.toLowerCase().includes('pro')) || plans.find(p => p.name.toLowerCase().includes('premium'));

              if (!proPlan) return (
                <div className="text-center text-gray-400 py-12">
                  <p>No subscription plans currently available.</p>
                </div>
              );

              const isUserCurrentPlan = isCurrentPlan(proPlan.id);

              return (
                <div className="flex justify-center">
                  <div className={`relative w-full max-w-lg bg-black rounded-xl border-2 ${isUserCurrentPlan
                    ? 'border-yellow-400 ring-2 ring-yellow-400/30'
                    : 'border-yellow-500/50 hover:border-yellow-500'
                    } p-8 flex flex-col items-center shadow-xl transition-all duration-200 hover:scale-[1.02]`}>
                    {/* Trial Badge for eligible users who aren't current subscribers */}
                    {!isUserCurrentPlan && trialEligibility.eligible && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-yellow-400 text-black px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                        7-Day Free Trial Available
                      </div>
                    )}
                    {/* Current Plan Badge */}
                    {isUserCurrentPlan && (
                      <div className="absolute -top-3 right-4 bg-yellow-400 text-black px-3 py-1 rounded-full text-xs font-bold shadow-lg">
                        Current Plan
                      </div>
                    )}

                    <h3 className="text-3xl font-bold text-yellow-400 mb-2 tracking-wide mt-2">Arbitrage Pro</h3>
                    <p className="text-gray-400 mb-6 text-sm">The ultimate tool for sports arbitrage</p>

                    <div className="text-6xl font-extrabold text-white mb-8">
                      $39.99<span className="text-xl font-medium text-gray-400">/mo</span>
                    </div>

                    <div className="w-full bg-gray-900/50 rounded-lg p-6 mb-8 border border-gray-800">
                      <ul className="text-left text-gray-200 space-y-4">
                        <li className="flex items-center gap-3">
                          <span className="text-yellow-400 text-xl font-bold">✓</span>
                          <span className="text-base"><span className="text-white font-semibold">Real-Time</span> Arbitrage Opportunities</span>
                        </li>
                        <li className="flex items-center gap-3">
                          <span className="text-yellow-400 text-xl font-bold">✓</span>
                          <span className="text-base"><span className="text-white font-semibold">50+ Global Sports Leagues</span> (NFL, NBA, Soccer & more)</span>
                        </li>
                        <li className="flex items-center gap-3">
                          <span className="text-yellow-400 text-xl font-bold">✓</span>
                          <span className="text-base"><span className="text-white font-semibold">80+ Bookmakers</span> (FanDuel, DraftKings, Pinnacle, etc)</span>
                        </li>
                        <li className="flex items-center gap-3">
                          <span className="text-yellow-400 text-xl font-bold">✓</span>
                          <span className="text-base">Live In-Game Opportunities</span>
                        </li>
                        <li className="flex items-center gap-3">
                          <span className="text-yellow-400 text-xl font-bold">✓</span>
                          <span className="text-base">Advanced ROI Calculator & Bet Tracking</span>
                        </li>
                        <li className="flex items-center gap-3">
                          <span className="text-yellow-400 text-xl font-bold">✓</span>
                          <span className="text-base">Instant Browser Notifications</span>
                        </li>
                      </ul>
                    </div>

                    <button
                      className={`w-full px-8 py-4 rounded-xl font-bold text-lg transition-all duration-200 mb-4 ${isUserCurrentPlan
                        ? 'bg-green-900/30 text-green-400 border border-green-500/30 cursor-default'
                        : 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-black hover:from-yellow-300 hover:to-yellow-400 hover:scale-[1.02] shadow-xl hover:shadow-yellow-500/20'
                        }`}
                      onClick={() => handleStripeCheckout(proPlan.id, false)}
                      disabled={isButtonDisabled(proPlan.id)}
                    >
                      {getButtonText(proPlan.id, false)}
                    </button>

                    {/* Free Trial Button - only show if eligible */}
                    {!isUserCurrentPlan && trialEligibility.eligible && (
                      <button
                        className="w-full px-8 py-4 rounded-xl bg-gray-800/80 text-yellow-400 border border-yellow-400/50 font-bold text-lg hover:bg-yellow-400 hover:text-black transition-all duration-200 mb-2"
                        onClick={() => handleStripeCheckout(proPlan.id, true)}
                        disabled={isButtonDisabled(proPlan.id, true)}
                      >
                        Start 7-Day Free Trial
                      </button>
                    )}

                    {/* Manage Subscription button for current plan */}
                    {shouldShowManageButton() && (
                      <button
                        className="w-full px-8 py-3 rounded-xl bg-gray-800 text-gray-300 border border-gray-600 font-semibold text-base hover:bg-gray-700 hover:text-white transition-all duration-200 mt-2"
                        onClick={handleManageSubscription}
                      >
                        Manage Subscription
                      </button>
                    )}
                  </div>
                </div>
              );
            })()
          )}
        </div>
      </div>
    </div>
  );
};

export default Subscription;
