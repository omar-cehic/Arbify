import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Helmet } from 'react-helmet-async';
import * as Sentry from "@sentry/react";
import { useLocation } from 'react-router-dom';
import ProfileSidebar from './ProfileSidebar';
import axios from 'axios';
import MyArbitrageTab from './MyArbitrageTab';
import PreferencesTab from './PreferencesTab';
import { updateUserProfile } from '../../utils/api';

const TABS = [
  { key: 'profile', label: 'Profile' },
  { key: 'security', label: 'Security' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'myArbitrage', label: 'My Arbitrage' },
];

const Profile = () => {
  const { user, logout, updateUser } = useAuth();
  const location = useLocation();

  // Get initial tab from URL parameter or default to 'profile'
  const getInitialTab = () => {
    const urlParams = new URLSearchParams(location.search);
    const tabFromUrl = urlParams.get('tab');
    const validTabs = ['profile', 'security', 'preferences', 'myArbitrage'];
    return validTabs.includes(tabFromUrl) ? tabFromUrl : 'profile';
  };

  const [activeTab, setActiveTab] = useState(getInitialTab());
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  // Update form data when user changes
  useEffect(() => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        full_name: user.full_name || user.username || '',
        email: user.email || ''
      }));
    }
  }, [user]);

  // Update active tab when URL changes
  useEffect(() => {
    setActiveTab(getInitialTab());
  }, [location.search]);
  const [feedback, setFeedback] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // Strategies state
  const [strategies, setStrategies] = useState([]);
  const [currentStrategy, setCurrentStrategy] = useState({
    id: null,
    name: '',
    description: '',
    min_odds: 1.1,
    max_stake: 100,
    profit_range: 'medium',
    strategy_type: 'percentage',
    time_sensitivity: 'medium',
    capital_required: 'medium',
    preferred_sports: [],
    is_live: false
  });
  const [isEditing, setIsEditing] = useState(false);
  const [showStrategyForm, setShowStrategyForm] = useState(false);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [showRecommendedStrategies, setShowRecommendedStrategies] = useState(false);
  const [activeStrategyForOdds, setActiveStrategyForOdds] = useState(null);
  const [matchingArbitrageOpportunities, setMatchingArbitrageOpportunities] = useState([]);
  const [isLoadingOpportunities, setIsLoadingOpportunities] = useState(false);

  // Subscription tier limits
  const SUBSCRIPTION_LIMITS = {
    basic: {
      max_strategies: 2,
      features: ['Basic arbitrage filters', 'Limited sports', 'All profit ranges']
    },
    premium: {
      max_strategies: Number.POSITIVE_INFINITY,
      features: ['Unlimited strategies', 'All sports', 'Advanced arbitrage tools', 'Performance tracking']
    }
  };

  // User's current subscription tier (default to basic if not specified)
  const [userTier, setUserTier] = useState('basic');

  // Odds API defaults and live toggle for strategies (premium gets live)
  const DEFAULT_REGIONS = ['us', 'uk', 'eu'];
  const DEFAULT_MARKETS = ['h2h', 'spreads', 'totals'];
  const ODDS_FORMATS = ['decimal', 'american'];
  const [apiSettings, setApiSettings] = useState({
    regions: DEFAULT_REGIONS,
    markets: DEFAULT_MARKETS,
    oddsFormat: 'decimal',
    include_live: false,
    refresh_pre_seconds: 60,
    refresh_live_seconds: 60,
  });

  // Keep API defaults aligned with user tier and provider update intervals
  useEffect(() => {
    const includeLive = userTier === 'premium';
    const pre = 60;  // Provider pre-match cadence
    const live = includeLive ? 40 : 60; // Provider live cadence; basic treated as 60
    setApiSettings(prev => ({
      ...prev,
      include_live: includeLive,
      refresh_pre_seconds: pre,
      refresh_live_seconds: live,
    }));
  }, [userTier]);

  // Fetch actual subscription tier from backend so gating reflects real plan
  useEffect(() => {
    let isMounted = true;
    const fetchSubscriptionTier = async () => {
      try {
        const res = await axios.get('/api/subscription/my-subscription');
        const status = res?.data?.status;
        const planName = (res?.data?.plan?.name || '').toLowerCase();
        // Treat trial as premium; premium plan name indicates premium as well
        const isPremium = status === 'trialing' || planName.includes('premium');
        if (isMounted) {
          setUserTier(isPremium ? 'premium' : 'basic');
        }
      } catch (err) {
        // On error, default to basic tier (safe fallback)
        if (isMounted) setUserTier('basic');
      }
    };
    fetchSubscriptionTier();
    return () => { isMounted = false; };
  }, []);

  // Recommended strategies that users can easily adopt
  const recommendedStrategies = [
    {
      id: 'rec1',
      name: 'Quick Arbs',
      description: 'Low-friction 1–2% profit arbs with high availability and faster execution. Great starting point.',
      min_odds: 1.6,
      max_stake: 300,
      profit_range: 'low',
      recommended_for: ['basic', 'premium'],
      avg_margin: 1.6,
      strategy_type: 'percentage',
      time_sensitivity: 'low',
      capital_required: 'low',
      is_live: false
    },
    {
      id: 'rec2',
      name: 'Balanced Arbs',
      description: 'Balanced 2–4% opportunities. Slightly fewer matches than Quick Arbs but higher yields.',
      min_odds: 1.7,
      max_stake: 200,
      profit_range: 'medium',
      recommended_for: ['basic', 'premium'],
      avg_margin: 3.0,
      strategy_type: 'percentage',
      time_sensitivity: 'medium',
      capital_required: 'medium',
      is_live: false
    },
    {
      id: 'rec3',
      name: 'High-Margin Arbs',
      description: 'Target 4%+ profit. Fewer spots, more volatility around events. Best with experience and strict limits.',
      min_odds: 1.8,
      max_stake: 150,
      profit_range: 'high',
      recommended_for: ['premium'],
      avg_margin: 4.5,
      strategy_type: 'timing',
      time_sensitivity: 'medium',
      capital_required: 'medium',
      is_live: false
    },
    {
      id: 'rec4',
      name: 'Live Arbitrage',
      description: 'In-play edges with fast-moving lines. Requires quick action and active monitoring. Premium only.',
      min_odds: 1.2,
      max_stake: 100,
      profit_range: 'medium',
      recommended_for: ['premium'],
      avg_margin: 2.5,
      strategy_type: 'timing',
      time_sensitivity: 'high',
      capital_required: 'medium',
      is_live: true
    }
  ];

  // Sports options for strategies
  const sportsOptions = [
    { value: 'football', label: 'Football' },
    { value: 'basketball', label: 'Basketball' },
    { value: 'tennis', label: 'Tennis' },
    { value: 'baseball', label: 'Baseball' },
    { value: 'hockey', label: 'Hockey' },
    { value: 'soccer', label: 'Soccer' },
  ];

  // Profit range options (replacing risk levels)
  const profitRanges = [
    { value: 'low', label: '1-2% Profit' },
    { value: 'medium', label: '2-5% Profit' },
    { value: 'high', label: '5%+ Profit' },
  ];

  // Strategy type options
  const strategyTypes = [
    { value: 'percentage', label: 'Percentage-based' },
    { value: 'timing', label: 'Time-based' },
    { value: 'bookmaker', label: 'Bookmaker-focused' },
  ];

  useEffect(() => {
    // New function: ensure localStorage user has all required fields 
    const ensureUserDataComplete = () => {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          const userData = JSON.parse(userStr);
          if (userData && userData.id) {
            // Check if fields are missing and add them if needed
            let isChanged = false;
            if (!userData.full_name && userData.username) {
              userData.full_name = userData.username;
              isChanged = true;
            }
            // Save back to localStorage if changes were made
            if (isChanged) {
              localStorage.setItem('user', JSON.stringify(userData));
              // This will trigger the useAuth hook to update
              window.dispatchEvent(new Event('storage'));
            }
          }
        } catch (e) {
          console.error('Error ensuring user data is complete', e);
        }
      }
    };

    // Run once on component mount
    ensureUserDataComplete();

    if (user) {
      setFormData(prev => ({
        ...prev,
        full_name: user.full_name || user.username || '',
        email: user.email || ''
      }));

      // Mock data for strategies - in a real app, you would fetch from the API
      // This would be replaced with an actual API call like:
      // fetch('/api/user/strategies')
      //   .then(res => res.json())
      //   .then(data => setStrategies(data))
      //   .catch(err => console.error('Error fetching strategies:', err));

      setStrategies([
        {
          id: 1,
          name: 'Conservative Approach',
          description: 'Focusing on low-risk bets with consistent small profits',
          min_odds: 1.2,
          max_stake: 50,
          preferred_sports: ['football', 'basketball'],
          profit_range: 'low',
          created_at: '2023-10-15T14:30:00Z',
          is_active: true
        },
        {
          id: 2,
          name: 'High Leverage Strategy',
          description: 'Higher risk but potentially higher return strategy focusing on undervalued odds',
          min_odds: 2.0,
          max_stake: 200,
          preferred_sports: ['tennis', 'soccer'],
          profit_range: 'high',
          created_at: '2023-11-20T09:15:00Z',
          is_active: true
        }
      ]);
    }
  }, [user]);

  useEffect(() => {
    if (activeStrategyForOdds) {
      findMatchingArbitrageOpportunities(activeStrategyForOdds);
    }
  }, [activeStrategyForOdds]);

  // Function to find arbitrage opportunities that match a strategy
  const findMatchingArbitrageOpportunities = (strategy) => {
    setIsLoadingOpportunities(true);

    // In a real implementation, this would be an API call to your backend
    // For now, we'll simulate with mock data and a timeout
    setTimeout(() => {
      // Mock data for arbitrage opportunities that match the strategy criteria
      const mockOpportunities = [
        {
          id: 'opp1',
          match: 'Chelsea vs Arsenal',
          sport: strategy.preferred_sports.includes('soccer') ? 'soccer' : strategy.preferred_sports[0],
          sport_key: 'football_epl',
          sport_title: 'English Premier League',
          bookmakers: ['Bet365', 'Unibet'],
          odds: [1.95, 2.15],
          profit_margin: 2.8,
          stake_recommendation: Math.min(strategy.max_stake, 150),
          time_remaining: '2h 15m',
          match_time: '2023-05-18T14:45:00Z'
        },
        {
          id: 'opp2',
          match: 'Lakers vs Warriors',
          sport: strategy.preferred_sports.includes('basketball') ? 'basketball' : strategy.preferred_sports[0],
          sport_key: 'basketball_nba',
          sport_title: 'Basketball NBA',
          bookmakers: ['DraftKings', 'FanDuel'],
          odds: [2.10, 1.85],
          profit_margin: 3.4,
          stake_recommendation: Math.min(strategy.max_stake, 120),
          time_remaining: '5h 30m',
          match_time: '2023-05-18T18:00:00Z'
        },
        {
          id: 'opp3',
          match: 'Djokovic vs Nadal',
          sport: strategy.preferred_sports.includes('tennis') ? 'tennis' : strategy.preferred_sports[0],
          sport_key: 'tennis_atp',
          sport_title: 'Tennis ATP',
          bookmakers: ['Betway', 'William Hill'],
          odds: [2.25, 1.75],
          profit_margin: 4.1,
          stake_recommendation: Math.min(strategy.max_stake, 200),
          time_remaining: '1h 45m',
          match_time: '2023-05-18T13:00:00Z'
        },
        {
          id: 'opp4',
          match: 'Manchester United vs Liverpool',
          sport: strategy.preferred_sports.includes('soccer') ? 'soccer' : strategy.preferred_sports[0],
          sport_key: 'football_epl',
          sport_title: 'English Premier League',
          bookmakers: ['Bet365', 'Betway', 'William Hill'],
          odds: [3.50, 2.10, 3.80],
          profit_margin: 6.2,
          stake_recommendation: Math.min(strategy.max_stake, 100),
          time_remaining: '1d 6h',
          match_time: '2023-05-19T19:45:00Z'
        },
        {
          id: 'opp5',
          match: 'LA Lakers vs Boston Celtics',
          sport: strategy.preferred_sports.includes('basketball') ? 'basketball' : strategy.preferred_sports[0],
          sport_key: 'basketball_nba',
          sport_title: 'Basketball NBA',
          bookmakers: ['William Hill', 'Bet365'],
          odds: [1.92, 2.15],
          profit_margin: 5.8,
          stake_recommendation: Math.min(strategy.max_stake, 150),
          time_remaining: '1d 10h',
          match_time: '2023-05-19T23:00:00Z'
        }
      ];

      // Filter to keep only opportunities that meet the strategy's criteria
      const filteredOpportunities = mockOpportunities.filter(opp => {
        // Check if sport is in preferred sports
        const sportMatch = strategy.preferred_sports.includes(opp.sport);

        // Check if odds meet minimum requirement
        const oddsMatch = Math.max(...opp.odds) >= strategy.min_odds;

        // Match profit range to strategy's profit range
        let profitRangeMatch = false;
        if (strategy.profit_range === 'low') {
          // 1-2% profit range
          profitRangeMatch = opp.profit_margin >= 1.0 && opp.profit_margin < 2.0;
        } else if (strategy.profit_range === 'medium') {
          // 2-5% profit range
          profitRangeMatch = opp.profit_margin >= 2.0 && opp.profit_margin < 5.0;
        } else if (strategy.profit_range === 'high') {
          // 5%+ profit range
          profitRangeMatch = opp.profit_margin >= 5.0;
        }

        return sportMatch && oddsMatch && profitRangeMatch;
      });

      setMatchingArbitrageOpportunities(filteredOpportunities);
      setIsLoadingOpportunities(false);
    }, 1500); // Simulate API delay
  };

  // Save strategy filters to be used on the arbitrage page
  const applyStrategyToArbitragePage = (strategy, opportunity = null) => {
    // Create filter settings based on strategy
    const filterSettings = {
      sportFilter: opportunity ? opportunity.sport_title :
        (strategy.preferred_sports.length > 0 ?
          mapSportToTitle(strategy.preferred_sports[0]) : 'all'),
      minProfit: strategy.profit_range === 'high' ? 3.0 : strategy.profit_range === 'medium' ? 2.0 : 0.5,
      minOdds: strategy.min_odds,
      maxStake: strategy.max_stake,
      bookmakers: opportunity ? opportunity.bookmakers : [],
      fromStrategy: strategy.name,
      timestamp: new Date().getTime() // To ensure it's a fresh request
    };

    console.log("Saving strategy filters to localStorage:", filterSettings);

    // Save to localStorage so the arbitrage page can access it
    localStorage.setItem('arbifyStrategyFilters', JSON.stringify(filterSettings));

    // Force the arbitrage page to show data by adding dummy data for the mock backend response
    localStorage.setItem('arbify_force_show_opportunities', 'true');

    // Navigate to the arbitrage page happens via normal link
    // Delay just a tiny bit to ensure localStorage is set before navigation
    setTimeout(() => {
      console.log("Strategy filters saved, now navigating to arbitrage page");
    }, 50);
  };

  // Helper function to map sport name to title format used in arbitrage
  const mapSportToTitle = (sport) => {
    const sportMap = {
      'soccer': 'English Premier League',
      'football': 'English Premier League',
      'basketball': 'Basketball NBA',
      'tennis': 'Tennis ATP',
      'baseball': 'Baseball MLB',
      'hockey': 'Hockey NHL'
    };

    return sportMap[sport.toLowerCase()] || sport;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleStrategyInputChange = (e) => {
    const { name, value } = e.target;
    setCurrentStrategy(prev => ({ ...prev, [name]: value }));
  };

  const handleSportsSelection = (e) => {
    const { value } = e.target;
    const isSelected = currentStrategy.preferred_sports.includes(value);

    if (isSelected) {
      // Remove if already selected
      setCurrentStrategy(prev => ({
        ...prev,
        preferred_sports: prev.preferred_sports.filter(sport => sport !== value)
      }));
    } else {
      // Add if not selected
      setCurrentStrategy(prev => ({
        ...prev,
        preferred_sports: [...prev.preferred_sports, value]
      }));
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      setFeedback('Updating profile...');

      const updatedUser = await updateUserProfile({
        full_name: formData.full_name
      });

      // Update form data
      setFormData(prev => ({
        ...prev,
        full_name: updatedUser.full_name,
        email: updatedUser.email
      }));

      // Update user in local state and localStorage
      const currentUser = JSON.parse(localStorage.getItem('user'));
      const userObj = {
        ...currentUser,
        full_name: updatedUser.full_name
      };

      localStorage.setItem('user', JSON.stringify(userObj));

      // Update user in context if needed
      if (updateUser) {
        updateUser(userObj);
      }

      setFeedback('Profile updated successfully!');
    } catch (err) {
      console.error('Profile update error:', err);
      setFeedback(`Error: ${err.message}`);
    }

    // Clear feedback after a delay
    setTimeout(() => setFeedback(''), 5000);
  };

  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    if (formData.new_password !== formData.confirm_password) {
      setFeedback('New passwords do not match');
      return;
    }

    try {
      // Clear any previous errors
      setFeedback('Processing request...');

      // Use the direct-change-password endpoint for compatibility
      const response = await axios.post('/api/auth/direct-change-password', {
        username: user.username,
        current_password: formData.current_password,
        new_password: formData.new_password
      });

      console.log("Password change response:", response.data);
      setFeedback('Password updated successfully!');

      // Clear password fields after successful update
      setFormData(prev => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_password: ''
      }));
    } catch (err) {
      console.error('Password update error:', err);
      // Detailed error message handling
      let errorMessage = 'Failed to update password';
      if (err.response && err.response.data && err.response.data.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setFeedback(`Error: ${errorMessage}`);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      setFeedback('Deleting account...');

      const token = localStorage.getItem('access_token');

      const res = await fetch('/api/auth/me', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        // Clear all local storage
        localStorage.clear();

        // Redirect to home page
        window.location.href = '/';
        setFeedback('Account deleted successfully. Redirecting...');
      } else {
        let errorMessage = 'Failed to delete account';
        try {
          const errorData = await res.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (jsonError) {
          console.error('Error parsing error response:', jsonError);
          errorMessage = `Server error: ${res.status} ${res.statusText}`;
        }
        throw new Error(errorMessage);
      }
    } catch (err) {
      console.error('Delete account error:', err);
      setFeedback(`Error: ${err.message}`);
      setShowDeleteModal(false);
    }
  };

  const handleAddStrategy = () => {
    // Check if user has reached their strategy limit
    if (strategies.length >= SUBSCRIPTION_LIMITS[userTier].max_strategies) {
      setFeedback(`You've reached your ${userTier} tier limit of ${SUBSCRIPTION_LIMITS[userTier].max_strategies} arbitrage strategies. Upgrade to Premium for unlimited strategies.`);
      setTimeout(() => setFeedback(''), 5000);
      return;
    }

    setCurrentStrategy({
      id: null,
      name: '',
      description: '',
      min_odds: 1.1,
      max_stake: 100,
      profit_range: 'medium',
      strategy_type: 'percentage',
      time_sensitivity: 'medium',
      capital_required: 'medium',
      preferred_sports: [],
      is_live: false,
      is_active: false
    });
    setIsEditing(false);
    setShowStrategyForm(true);
  };

  const handleEditStrategy = (strategyId) => {
    const strategyToEdit = strategies.find(s => s.id === strategyId);
    if (strategyToEdit) {
      setCurrentStrategy(strategyToEdit);
      setIsEditing(true);
      setShowStrategyForm(true);
    }
  };

  const handleDeleteStrategy = (strategyId) => {
    // In a real app, you would make an API call to delete the strategy
    // For now, just update the local state
    setStrategies(strategies.filter(s => s.id !== strategyId));
    setFeedback('Strategy deleted successfully!');
    setTimeout(() => setFeedback(''), 3000);
  };

  const handleStrategySubmit = (e) => {
    e.preventDefault();

    if (isEditing) {
      // Update existing strategy
      const updatedStrategies = strategies.map(s =>
        s.id === currentStrategy.id ? currentStrategy : s
      );
      setStrategies(updatedStrategies);
      setFeedback('Strategy updated successfully!');
    } else {
      // Add new strategy with a generated ID
      const newStrategy = {
        ...currentStrategy,
        id: Date.now(), // Simple way to generate unique IDs
        created_at: new Date().toISOString(),
        is_active: false
      };
      setStrategies([...strategies, newStrategy]);
      setFeedback('Strategy added successfully!');
    }

    // Reset and close form
    setShowStrategyForm(false);
    setIsEditing(false);
    setTimeout(() => setFeedback(''), 3000);
  };

  const toggleStrategyActive = (strategyId) => {
    // Enforce single-active strategy
    const updated = strategies.map(s => {
      if (s.id === strategyId) {
        return { ...s, is_active: !s.is_active };
      }
      return { ...s, is_active: false };
    });
    setStrategies(updated);

    // Persist active strategy preferences for ArbitrageFinder
    const active = updated.find(s => s.is_active);
    if (active) {
      const minProfitByRange = { low: 1, medium: 2, high: 4 };
      const activePrefs = {
        name: active.name,
        profit_range: active.profit_range,
        minimum_profit_threshold: minProfitByRange[active.profit_range] || 1,
        preferred_sports: active.preferred_sports || [],
        is_live: !!active.is_live,
      };
      localStorage.setItem('activeStrategy', JSON.stringify(activePrefs));
    } else {
      localStorage.removeItem('activeStrategy');
    }
  };

  const applyStrategyFilter = (strategy) => {
    // Set the active strategy for finding odds
    setActiveStrategyForOdds(strategy);

    // Show feedback
    setFeedback(`Finding arbitrage opportunities for "${strategy.name}" strategy...`);

    // Set the selectedStrategyId for UI highlighting
    setSelectedStrategyId(strategy.id);
  };

  const addRecommendedStrategy = (recommended) => {
    // Check if user has reached their strategy limit
    if (strategies.length >= SUBSCRIPTION_LIMITS[userTier].max_strategies) {
      setFeedback(`You've reached your ${userTier} tier limit of ${SUBSCRIPTION_LIMITS[userTier].max_strategies} arbitrage strategies. Upgrade to Premium for unlimited strategies.`);
      setTimeout(() => setFeedback(''), 5000);
      return;
    }
    // Restrict live arbitrage to premium users
    if (recommended.is_live && userTier !== 'premium') {
      setFeedback('Live Arbitrage is a Premium feature. Upgrade to access live opportunities.');
      setTimeout(() => setFeedback(''), 5000);
      return;
    }
    // Check if this strategy is available for user's tier
    if (!recommended.recommended_for.includes(userTier)) {
      setFeedback(`This strategy requires a Premium subscription.`);
      setTimeout(() => setFeedback(''), 3000);
      return;
    }
    // Add the recommended strategy to user's strategies
    const newStrategy = {
      ...recommended,
      id: Date.now(), // New unique ID
      created_at: new Date().toISOString(),
      is_active: true,
      avg_margin: recommended.avg_margin
    };
    setStrategies([...strategies, newStrategy]);
    setFeedback('Recommended strategy added to your collection!');
    setTimeout(() => setFeedback(''), 3000);
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="bg-gray-800 p-8 rounded-lg shadow-lg text-center">
          <div className="text-yellow-400 text-3xl mb-4">⚠️</div>
          <div className="text-gray-200 text-lg">Please log in to view your profile.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col md:flex-row">
      <Helmet>
        <title>Your Profile - Arbify</title>
        <meta name="description" content="Manage your Arbify account settings, subscription, and betting preferences." />
      </Helmet>
      {/* Sidebar */}
      <div className="md:w-1/4 w-full p-4">
        <ProfileSidebar user={user} activeTab={activeTab} setActiveTab={setActiveTab} onLogout={logout} />
      </div>
      {/* Main Content */}
      <div className="md:w-3/4 w-full p-4 flex flex-col gap-6">
        <div className="flex gap-2 mb-2 flex-wrap">
          {TABS.map(tab => (
            <button
              key={tab.key}
              className={`px-4 py-2 rounded-lg font-semibold transition-colors text-sm ${activeTab === tab.key ? 'bg-yellow-400 text-gray-900' : 'bg-gray-700 text-gray-200 hover:bg-gray-600'}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
        {feedback && (
          <div className={`px-4 py-2 rounded-lg font-medium border ${feedback.startsWith('Error')
            ? 'bg-red-900/50 text-red-200 border-red-700'
            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
            }`}>
            <div className="flex items-center gap-2">
              {feedback.startsWith('Error') ? <i className="fas fa-exclamation-circle"></i> : <i className="fas fa-check-circle"></i>}
              {feedback}
            </div>
          </div>
        )}


        {activeTab === 'profile' && (
          <div className="bg-gray-800 rounded-lg shadow-lg p-8 flex flex-col items-center">
            <div className="w-24 h-24 rounded-full bg-yellow-400 flex items-center justify-center text-4xl font-bold text-gray-900 mb-4">
              {user.full_name ? user.full_name[0] : user.username[0]}
            </div>
            <h2 className="text-2xl font-bold text-yellow-300 mb-1">{user.full_name || user.username}</h2>
            <div className="text-gray-400 mb-2">{user.email || 'No email available'}</div>
            {user.last_login && <div className="text-xs text-gray-500 mb-2">Last login: {new Date(user.last_login).toLocaleString()}</div>}
            <form className="w-full max-w-md mt-4" onSubmit={handleProfileUpdate}>
              <div className="mb-4">
                <label htmlFor="full_name" className="block text-gray-300 mb-1">Full Name</label>
                <input
                  type="text"
                  id="full_name"
                  name="full_name"
                  className="w-full px-3 py-2 rounded bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                  value={formData.full_name}
                  onChange={handleInputChange}
                />
              </div>
              <div className="mb-4">
                <label htmlFor="email" className="block text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  className="w-full px-3 py-2 rounded bg-gray-700 text-gray-400 focus:outline-none cursor-not-allowed"
                  value={formData.email}
                  readOnly
                />
              </div>
              <button type="submit" className="w-full bg-yellow-400 text-gray-900 font-semibold py-2 rounded-lg hover:bg-yellow-500 transition-colors">Update Profile</button>
            </form>
            <button
              className="mt-6 text-red-400 hover:text-red-600 underline text-sm"
              onClick={() => setShowDeleteModal(true)}
            >
              Delete Account
            </button>
            {showDeleteModal && (
              <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-60 z-50">
                <div className="bg-gray-800 p-8 rounded-lg shadow-lg text-center">
                  <div className="text-yellow-400 text-2xl mb-4">Are you sure?</div>
                  <div className="text-gray-200 mb-4">This action cannot be undone. Your account will be permanently deleted.</div>
                  <button className="bg-red-500 text-white px-4 py-2 rounded-lg mr-2" onClick={handleDeleteAccount}>Delete</button>
                  <button className="bg-gray-600 text-gray-200 px-4 py-2 rounded-lg" onClick={() => setShowDeleteModal(false)}>Cancel</button>
                </div>
              </div>
            )}
          </div>
        )}
        {activeTab === 'security' && (
          <div className="bg-gray-800 rounded-lg shadow-lg p-8 max-w-md w-full mx-auto">
            <h2 className="text-xl font-bold text-yellow-300 mb-4">Change Password</h2>

            <form onSubmit={handlePasswordUpdate}>
              <div className="mb-4">
                <label htmlFor="current_password" className="block text-gray-300 mb-1">Current Password</label>
                <input
                  type="password"
                  id="current_password"
                  name="current_password"
                  className="w-full px-3 py-2 rounded bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                  value={formData.current_password}
                  onChange={handleInputChange}
                />
              </div>
              <div className="mb-4">
                <label htmlFor="new_password" className="block text-gray-300 mb-1">New Password</label>
                <input
                  type="password"
                  id="new_password"
                  name="new_password"
                  className="w-full px-3 py-2 rounded bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                  value={formData.new_password}
                  onChange={handleInputChange}
                />
              </div>
              <div className="mb-4">
                <label htmlFor="confirm_password" className="block text-gray-300 mb-1">Confirm New Password</label>
                <input
                  type="password"
                  id="confirm_password"
                  name="confirm_password"
                  className="w-full px-3 py-2 rounded bg-gray-700 text-gray-200 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                  value={formData.confirm_password}
                  onChange={handleInputChange}
                />
              </div>
              <button type="submit" className="w-full bg-yellow-400 text-gray-900 font-semibold py-2 rounded-lg hover:bg-yellow-500 transition-colors">Update Password</button>
            </form>
          </div>
        )}
        {activeTab === 'preferences' && (
          <PreferencesTab />
        )}
        {activeTab === 'strategies' && (
          <div className="bg-gray-800 rounded-lg shadow-lg p-8 w-full">
            {/* Condensed info block at the top */}
            {!showStrategyForm && !showRecommendedStrategies && (
              <div className="bg-gray-750 p-4 rounded-lg border border-yellow-500/30 mb-6">
                <h3 className="text-yellow-400 font-semibold mb-2">What is Arbitrage Betting?</h3>
                <p className="text-gray-300 text-sm mb-2">
                  Arbitrage betting lets you lock in a profit by betting on all outcomes at the right odds. Use Arbify to find and calculate these opportunities automatically.
                </p>
                <p className="text-yellow-300 text-xs font-semibold mt-2">
                  Always double-check odds before placing bets, especially for live events, as odds can change very quickly.
                </p>
              </div>
            )}

            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-bold text-yellow-300">Your Arbitrage Strategies</h2>
                <p className="text-gray-400 text-sm mt-1">
                  {userTier === 'premium'
                    ? 'Premium tier: Unlimited arbitrage strategies'
                    : `Basic tier: ${strategies.length}/${SUBSCRIPTION_LIMITS.basic.max_strategies} arbitrage strategies`}
                </p>
              </div>
              <div className="flex gap-2">
                {!showStrategyForm && !showRecommendedStrategies && (
                  <>
                    <button
                      onClick={() => setShowRecommendedStrategies(true)}
                      className="border border-yellow-500/40 text-yellow-300 font-semibold px-4 py-2 rounded-lg hover:bg-yellow-500/10 transition-colors text-sm"
                    >
                      Recommended Strategies
                    </button>
                    <button
                      onClick={handleAddStrategy}
                      className="bg-yellow-400 text-gray-900 font-semibold px-4 py-2 rounded-lg hover:bg-yellow-500 transition-colors text-sm"
                    >
                      + New Strategy
                    </button>
                  </>
                )}
                {showRecommendedStrategies && (
                  <button
                    onClick={() => setShowRecommendedStrategies(false)}
                    className="bg-gray-600 text-gray-200 px-4 py-2 rounded-lg hover:bg-gray-500 transition-colors text-sm"
                  >
                    Back to My Strategies
                  </button>
                )}
              </div>
            </div>

            {userTier === 'basic' && strategies.length >= SUBSCRIPTION_LIMITS.basic.max_strategies && (
              <div className="bg-gray-900/50 border border-yellow-500/20 text-gray-200 p-4 rounded-lg mb-6 flex justify-between items-center">
                <div>
                  <p className="font-semibold">You've reached your Basic tier strategy limit.</p>
                  <p className="text-sm text-gray-400">Upgrade to Premium for unlimited arbitrage strategies and advanced features.</p>
                </div>
                <a
                  href="/subscriptions"
                  className="bg-yellow-400 text-gray-900 px-4 py-2 rounded-lg font-semibold hover:bg-yellow-500 transition-colors"
                >
                  Upgrade Now
                </a>
              </div>
            )}

            {showStrategyForm ? (
              <div className="bg-gray-900/50 p-6 rounded-lg mb-6 border border-yellow-500/20">
                <h3 className="text-lg font-semibold text-yellow-300 mb-4">{isEditing ? 'Edit Strategy' : 'Create New Strategy'}</h3>
                <form onSubmit={handleStrategySubmit}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="mb-4">
                      <label htmlFor="name" className="block text-gray-300 mb-1">Strategy Name</label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        className="w-full px-3 py-2 rounded bg-gray-800 text-gray-100 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                        value={currentStrategy.name}
                        onChange={handleStrategyInputChange}
                        required
                      />
                    </div>

                    <div className="mb-4">
                      <label htmlFor="profit_range" className="block text-gray-300 mb-1">Target Profit Range</label>
                      <select
                        id="profit_range"
                        name="profit_range"
                        className="w-full px-3 py-2 rounded bg-gray-800 text-gray-100 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                        value={currentStrategy.profit_range}
                        onChange={handleStrategyInputChange}
                      >
                        {profitRanges.map(range => (
                          <option key={range.value} value={range.value}>{range.label}</option>
                        ))}
                      </select>
                    </div>

                    <div className="mb-4">
                      <label htmlFor="min_odds" className="block text-gray-300 mb-1">Minimum Odds</label>
                      <input
                        type="number"
                        id="min_odds"
                        name="min_odds"
                        step="0.1"
                        min="1.0"
                        className="w-full px-3 py-2 rounded bg-gray-800 text-gray-100 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                        value={currentStrategy.min_odds}
                        onChange={handleStrategyInputChange}
                      />
                    </div>

                    <div className="mb-4">
                      <label htmlFor="max_stake" className="block text-gray-300 mb-1">Maximum Stake ($)</label>
                      <input
                        type="number"
                        id="max_stake"
                        name="max_stake"
                        step="5"
                        min="5"
                        className="w-full px-3 py-2 rounded bg-gray-800 text-gray-100 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                        value={currentStrategy.max_stake}
                        onChange={handleStrategyInputChange}
                      />
                    </div>
                  </div>

                  <div className="mb-4">
                    <label htmlFor="strategy_type" className="block text-gray-300 mb-1">Strategy Type</label>
                    <select
                      id="strategy_type"
                      name="strategy_type"
                      className="w-full px-3 py-2 rounded bg-gray-800 text-gray-100 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                      value={currentStrategy.strategy_type}
                      onChange={handleStrategyInputChange}
                    >
                      {strategyTypes.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-4">
                    <label htmlFor="description" className="block text-gray-300 mb-1">Description</label>
                    <textarea
                      id="description"
                      name="description"
                      rows="3"
                      className="w-full px-3 py-2 rounded bg-gray-800 text-gray-100 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-yellow-400"
                      value={currentStrategy.description}
                      onChange={handleStrategyInputChange}
                    ></textarea>
                  </div>

                  <div className="mb-4">
                    <label className="block text-gray-300 mb-2">Preferred Sports</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {sportsOptions.map(sport => (
                        <div key={sport.value} className="flex items-center">
                          <input
                            type="checkbox"
                            id={`sport-${sport.value}`}
                            value={sport.value}
                            checked={currentStrategy.preferred_sports.includes(sport.value)}
                            onChange={handleSportsSelection}
                            className="mr-2"
                          />
                          <label htmlFor={`sport-${sport.value}`} className="text-gray-300 text-sm">{sport.label}</label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2 mt-6">
                    <button
                      type="submit"
                      className="bg-yellow-400 text-gray-900 font-semibold px-4 py-2 rounded-lg hover:bg-yellow-500 transition-colors"
                    >
                      {isEditing ? 'Update Strategy' : 'Save Strategy'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowStrategyForm(false)}
                      className="bg-gray-600 text-gray-200 px-4 py-2 rounded-lg hover:bg-gray-500 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            ) : showRecommendedStrategies ? (
              <div>
                <h3 className="text-lg font-semibold text-yellow-300 mb-4">Recommended Strategies</h3>
                <p className="text-gray-400 mb-4">Add these expert-curated strategies to your collection with one click.</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendedStrategies.map(strategy => {
                    const isAvailable = strategy.recommended_for.includes(userTier);

                    return (
                      <div
                        key={strategy.id}
                        className={`bg-gray-700 rounded-lg p-5 border ${isAvailable ? 'border-transparent' : 'border-yellow-600 border-dashed'
                          }`}
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-lg font-semibold text-white mb-1">{strategy.name}</h3>
                            {!isAvailable && (
                              <span className="text-xs px-2 py-1 rounded border border-yellow-500/40 text-yellow-300">
                                Premium Only
                              </span>
                            )}
                          </div>
                          <div className="text-xs px-2 py-1 rounded-full border border-yellow-500/40 text-yellow-300">
                            ~{strategy.avg_margin}% margin
                          </div>
                        </div>

                        <div className="mt-3 mb-3">
                          <span className="text-xs font-semibold px-2 py-1 rounded border border-yellow-500/40 text-yellow-300">
                            {strategy.profit_range === 'low' ? '1–2% Range' : strategy.profit_range === 'medium' ? '2–4% Range' : '4%+ Range'}
                          </span>
                        </div>

                        <p className="text-gray-300 text-sm mb-3">{strategy.description}</p>

                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-gray-400 text-xs">
                            Min Odds: {strategy.min_odds}
                          </span>
                          <span className="text-gray-400 text-xs">
                            Max Stake: ${strategy.max_stake}
                          </span>

                          {strategy.strategy_type && (
                            <span className="px-2 py-1 rounded text-xs font-medium border border-yellow-500/40 text-yellow-300">
                              {strategy.strategy_type === 'percentage' ? 'Percentage' :
                                strategy.strategy_type === 'timing' ? 'Timing' :
                                  'Bookmaker'}
                            </span>
                          )}
                        </div>

                        <button
                          onClick={() => addRecommendedStrategy(strategy)}
                          disabled={!isAvailable}
                          className={`mt-2 w-full py-2 rounded-lg font-medium text-sm ${isAvailable
                            ? 'bg-yellow-400 text-gray-900 hover:bg-yellow-500'
                            : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                            }`}
                        >
                          {isAvailable ? 'Add to My Strategies' : 'Premium Feature'}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="bg-gray-900/50 rounded-lg shadow-lg p-8 w-full border border-yellow-500/20">
                <h2 className="text-xl font-bold text-yellow-300 mb-4">My Arbitrage Strategies</h2>
                <p className="text-gray-400 text-sm mb-4">
                  Manage your custom arbitrage strategies. Set your preferred odds, profit ranges, and sports.
                </p>

                {/* Active Strategy and Live access summary (clean, minimal) */}
                <div className="mb-6 p-4 bg-gray-900/40 rounded-lg border border-yellow-500/10 flex flex-wrap items-center justify-between">
                  <div className="text-sm text-gray-300">
                    <span className="text-gray-200 font-semibold">Active Strategy:</span>
                    <span className="ml-2 text-yellow-300">{(strategies.find(s => s.is_active)?.name) || 'None'}</span>
                  </div>
                  <div className="text-xs text-gray-400">
                    {userTier === 'premium' ? 'Live access: Enabled' : 'Live access: Upgrade to Premium'}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {strategies.map(strategy => (
                    <div
                      key={strategy.id}
                      className="bg-gray-900/40 rounded-lg p-5 border border-yellow-500/10"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <h3 className="text-lg font-semibold text-white mb-1">{strategy.name}</h3>
                          <p className="text-gray-300 text-sm">{strategy.description}</p>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className={`text-xs font-semibold px-2 py-1 rounded border ${strategy.is_active ? 'border-green-400 text-green-300' : 'border-gray-500 text-gray-300'
                            }`}>
                            {strategy.is_active ? 'Active' : 'Inactive'}
                          </span>
                          <button
                            onClick={() => toggleStrategyActive(strategy.id)}
                            className="mt-2 text-xs px-3 py-1 rounded border border-yellow-500/40 text-yellow-300 hover:bg-yellow-500/10"
                          >
                            {strategy.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </div>

                      <div className="mt-3 mb-3">
                        <span className="text-xs font-semibold px-2 py-1 rounded border border-yellow-500/40 text-yellow-300">
                          {strategy.profit_range === 'low' ? '1–2% Range' : strategy.profit_range === 'medium' ? '2–4% Range' : '4%+ Range'}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-gray-400 text-xs">
                          Min Odds: {strategy.min_odds}
                        </span>
                        <span className="text-gray-400 text-xs">
                          Max Stake: ${strategy.max_stake}
                        </span>

                        {strategy.strategy_type && (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${strategy.strategy_type === 'percentage' ? 'bg-indigo-700 text-indigo-100' :
                            strategy.strategy_type === 'timing' ? 'bg-amber-700 text-amber-100' :
                              'bg-teal-700 text-teal-100'
                            }`}>
                            {strategy.strategy_type === 'percentage' ? 'Percentage-based' :
                              strategy.strategy_type === 'timing' ? 'Time-based' :
                                'Bookmaker-focused'}
                          </span>
                        )}
                      </div>

                      <div className="flex justify-end gap-2 mt-4">
                        <button
                          onClick={() => handleEditStrategy(strategy.id)}
                          className="bg-yellow-400 text-gray-900 font-semibold px-4 py-2 rounded-lg hover:bg-yellow-500 transition-colors text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteStrategy(strategy.id)}
                          className="bg-red-500 text-white font-semibold px-4 py-2 rounded-lg hover:bg-red-600 transition-colors text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        {activeTab === 'myArbitrage' && (
          <MyArbitrageTab />
        )}
      </div>
    </div >
  );
};

export default Profile;