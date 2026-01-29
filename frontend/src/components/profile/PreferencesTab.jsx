import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { requestNotificationPermission, sendTestNotification } from '../../utils/notifications';
import notificationService from '../../services/notificationService';
import {
  SGO_SPORTS,
  SGO_BOOKMAKERS,
  SGO_BOOKMAKERS_BY_REGION,
  SGO_SPORTS_BY_CATEGORY,
  DEFAULT_SGO_PREFERENCES
} from '../../constants/sgoConstants';

// Use SGO-specific data from constants

const PreferencesTab = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [activeTab, setActiveTab] = useState('bookmakers'); // 'bookmakers', 'settings'
  const [subscriptionTier, setSubscriptionTier] = useState('basic'); // Track user's subscription tier
  const [testEmailSending, setTestEmailSending] = useState(false); // Track test email status
  const [testEmailResult, setTestEmailResult] = useState(''); // Test email result message
  const [prefs, setPrefs] = useState({
    notification_email: true,
    notification_browser: false,
    preferred_sports: [],
    preferred_bookmakers: [],
    minimum_profit_threshold: 1.0,
    odds_format: 'american', // Default to American for SGO
    live_arbitrage_enabled: false,
    pregame_arbitrage_enabled: true,
  });

  // Use SGO data directly
  const sportsByCategory = SGO_SPORTS_BY_CATEGORY;


  // Fetch subscription tier
  useEffect(() => {
    const fetchSubscriptionTier = async () => {
      try {
        const res = await axios.get('/api/subscription/my-subscription');
        const status = res?.data?.status;
        const planName = (res?.data?.plan?.name || '').toLowerCase();
        // Treat trial as premium; premium plan name indicates premium as well
        const isPremium = status === 'trialing' || planName.includes('premium');
        const tier = isPremium ? 'premium' : 'basic';
        setSubscriptionTier(tier);
        // Store in localStorage for notification service
        localStorage.setItem('subscription_tier', tier);
        console.log('🎯 Subscription tier determined:', tier, { status, planName });
      } catch (err) {
        console.error('Error fetching subscription tier:', err);
        // Default to basic tier on error
        setSubscriptionTier('basic');
        localStorage.setItem('subscription_tier', 'basic');
      }
    };
    fetchSubscriptionTier();
  }, []);

  // Set up notification polling when browser notifications are enabled
  useEffect(() => {
    // Update notification service with current preferences and subscription tier
    const prefsWithTier = { ...prefs, subscriptionTier };
    notificationService.updatePreferences(prefsWithTier);

    return () => {
      // Clean up is handled by the notification service
    };
  }, [prefs, subscriptionTier]);

  // Fetch preferences on mount - prefer localStorage over API for immediate loading
  useEffect(() => {
    const fetchPrefs = async () => {
      setLoading(true);
      try {
        // First, try to load from localStorage for immediate UI update
        const savedPreferences = localStorage.getItem('userPreferences');
        if (savedPreferences) {
          try {
            const localPrefs = JSON.parse(savedPreferences);
            console.log('Loading preferences from localStorage:', localPrefs);

            // Convert localStorage data to component state format
            setPrefs({
              notification_email: localPrefs.notification_email !== undefined ? localPrefs.notification_email : true,
              notification_browser: localPrefs.notification_browser !== undefined ? localPrefs.notification_browser : false,
              preferred_sports: Array.isArray(localPrefs.preferred_sports) ? localPrefs.preferred_sports :
                (localPrefs.preferred_sports ? localPrefs.preferred_sports.split(',').filter(s => s) : []),
              preferred_bookmakers: Array.isArray(localPrefs.preferred_bookmakers) ? localPrefs.preferred_bookmakers :
                (localPrefs.preferred_bookmakers ? localPrefs.preferred_bookmakers.split(',').filter(s => s) : []),
              minimum_profit_threshold: localPrefs.minimum_profit_threshold || 1.0,
              odds_format: localPrefs.odds_format || 'decimal',
            });

            console.log('Loaded preferences from localStorage:', {
              sports_count: Array.isArray(localPrefs.preferred_sports) ? localPrefs.preferred_sports.length :
                (localPrefs.preferred_sports ? localPrefs.preferred_sports.split(',').filter(s => s).length : 0),
              bookmakers_count: Array.isArray(localPrefs.preferred_bookmakers) ? localPrefs.preferred_bookmakers.length :
                (localPrefs.preferred_bookmakers ? localPrefs.preferred_bookmakers.split(',').filter(s => s).length : 0)
            });

            setLoading(false);
            return; // Skip API call if localStorage data exists
          } catch (localError) {
            console.error('Error parsing localStorage preferences:', localError);
          }
        }

        // Fallback to API if localStorage is empty or corrupted
        console.log('No localStorage data found, fetching from API...');
        const token = localStorage.getItem('access_token');
        const res = await axios.get('/api/auth/user/profile', {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = res.data;
        console.log('Fetched user profile data from API:', data);

        const prefsFromAPI = {
          notification_email: data.notification_email !== undefined ? data.notification_email : true,
          notification_browser: data.notification_browser !== undefined ? data.notification_browser : false,
          preferred_sports: data.preferred_sports ? data.preferred_sports.split(',').filter(s => s) : [],
          preferred_bookmakers: data.preferred_bookmakers ? data.preferred_bookmakers.split(',').filter(s => s) : [],
          minimum_profit_threshold: data.minimum_profit_threshold || 1.0,
          odds_format: (data.odds_format || 'decimal'),
        };

        setPrefs(prefsFromAPI);

        // Also save to localStorage for future loads
        localStorage.setItem('userPreferences', JSON.stringify({
          notification_email: prefsFromAPI.notification_email,
          notification_browser: prefsFromAPI.notification_browser,
          preferred_sports: prefsFromAPI.preferred_sports,
          preferred_bookmakers: prefsFromAPI.preferred_bookmakers,
          minimum_profit_threshold: prefsFromAPI.minimum_profit_threshold,
          odds_format: prefsFromAPI.odds_format,
        }));

        console.log('Set preferences state from API:', {
          notification_email: data.notification_email,
          notification_browser: data.notification_browser,
          sports_count: prefsFromAPI.preferred_sports.length,
          bookmakers_count: prefsFromAPI.preferred_bookmakers.length
        });
      } catch (error) {
        console.error('Error fetching preferences:', error);
        setFeedback('Failed to load preferences.');
      } finally {
        setLoading(false);
      }
    };
    fetchPrefs();
  }, []);

  // Save to localStorage immediately when preferences change (for persistence across navigation)
  // Save to localStorage with debounce to prevent performance issues
  useEffect(() => {
    if (!loading) { // Don't save during initial load
      const timeoutId = setTimeout(() => {
        const preferencesData = {
          notification_email: prefs.notification_email,
          notification_browser: prefs.notification_browser,
          preferred_sports: prefs.preferred_sports,
          preferred_bookmakers: prefs.preferred_bookmakers,
          minimum_profit_threshold: prefs.minimum_profit_threshold,
          odds_format: prefs.odds_format,
        };
        localStorage.setItem('userPreferences', JSON.stringify(preferencesData));
        console.log('Saved preferences to localStorage (debounced):', preferencesData);

        // Notify notification service of update
        if (prefs.notification_browser) {
          import('../../services/notificationService').then(module => {
            module.default.updatePreferences(preferencesData);
          });
        }
      }, 1000); // Wait 1 second after last change

      return () => clearTimeout(timeoutId);
    }
  }, [prefs, loading]);

  // Handle browser notification permission
  const handleBrowserNotifToggle = async (checked) => {
    if (checked) {
      try {
        const granted = await requestNotificationPermission();
        if (!granted) {
          setFeedback('Browser notification permission denied. Please enable in browser settings.');
          return;
        }

        setFeedback('✅ Browser notifications enabled! Click "Test" to try it out.');
      } catch (error) {
        setFeedback(`Unable to enable browser notifications: ${error.message}`);
        return;
      }
    } else {
      setFeedback('Browser notifications disabled.');
    }

    const newPrefs = { ...prefs, notification_browser: checked };
    setPrefs(newPrefs);

    // Update notification service
    notificationService.updatePreferences(newPrefs);
  };

  // Test email function
  const handleTestEmail = async () => {
    if (!prefs.notification_email) {
      setTestEmailResult('Please enable email notifications first');
      return;
    }

    setTestEmailSending(true);
    setTestEmailResult('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post('/api/test-email-notification', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.success) {
        setTestEmailResult('Test email sent successfully! Check your inbox.');
      } else {
        setTestEmailResult(response.data.message || 'Failed to send test email');
      }
    } catch (error) {
      console.error('Test email error:', error);
      if (error.response?.data?.detail) {
        setTestEmailResult(error.response.data.detail);
      } else {
        setTestEmailResult('Failed to send test email. Please try again later.');
      }
    } finally {
      setTestEmailSending(false);
      // Clear result after 5 seconds
      setTimeout(() => setTestEmailResult(''), 5000);
    }
  };

  // Manual save function
  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFeedback('');
    try {
      const token = localStorage.getItem('access_token');

      console.log('🚀 DETAILED SAVE DEBUG:');
      console.log('- Original prefs.preferred_sports array:', prefs.preferred_sports);
      console.log('- Array length:', prefs.preferred_sports.length);
      console.log('- First 5 sports:', prefs.preferred_sports.slice(0, 5));
      console.log('- Last 5 sports:', prefs.preferred_sports.slice(-5));
      console.log('- Joined string:', prefs.preferred_sports.join(','));
      console.log('- String length:', prefs.preferred_sports.join(',').length);

      console.log('Manually saving preferences to backend:', {
        email: prefs.notification_email,
        browser: prefs.notification_browser,
        threshold: prefs.minimum_profit_threshold,
        preferred_sports: prefs.preferred_sports.join(','),
        preferred_bookmakers: prefs.preferred_bookmakers.join(','),
        odds_format: prefs.odds_format,
      });

      // Save to backend
      const response = await axios.post('/api/notifications/preferences', {
        email: prefs.notification_email,
        browser: prefs.notification_browser,
        threshold: prefs.minimum_profit_threshold,
        preferred_sports: prefs.preferred_sports.join(','),
        preferred_bookmakers: prefs.preferred_bookmakers.join(','),
        odds_format: prefs.odds_format,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });

      console.log('Backend save response:', response.data);

      // Trigger a custom event to notify other components that preferences changed
      window.dispatchEvent(new CustomEvent('preferencesUpdated', {
        detail: {
          preferred_sports: prefs.preferred_sports,
          preferred_bookmakers: prefs.preferred_bookmakers,
          minimum_profit_threshold: prefs.minimum_profit_threshold,
          notification_email: prefs.notification_email,
          notification_browser: prefs.notification_browser,
          odds_format: prefs.odds_format,
        }
      }));

      setFeedback('✅ Preferences saved successfully!');
      setTimeout(() => setFeedback(''), 4000);
    } catch (error) {
      console.error('Error saving preferences:', error);
      setFeedback('❌ Failed to save preferences. Please try again.');
    } finally {
      setSaving(false);
    }
  };


  // Helper functions for bulk selection
  const toggleAllSports = () => {
    const allSportKeys = SGO_SPORTS.map(sport => sport.key);
    setPrefs(prev => ({
      ...prev,
      preferred_sports: prev.preferred_sports.length === allSportKeys.length ? [] : allSportKeys,
    }));
  };

  const toggleCategorySports = (category) => {
    const categorySports = sportsByCategory[category].map(sport => sport.key);
    const allSelected = categorySports.every(key => prefs.preferred_sports.includes(key));

    setPrefs(prev => ({
      ...prev,
      preferred_sports: allSelected
        ? prev.preferred_sports.filter(key => !categorySports.includes(key))
        : [...new Set([...prev.preferred_sports, ...categorySports])]
    }));
  };

  const toggleAllBookmakers = () => {
    const allBookmakerKeys = SGO_BOOKMAKERS.map(bm => bm.key);
    setPrefs(prev => ({
      ...prev,
      preferred_bookmakers: prev.preferred_bookmakers.length === allBookmakerKeys.length ? [] : allBookmakerKeys,
    }));
  };

  const toggleRegionBookmakers = (region) => {
    const regionBookmakers = SGO_BOOKMAKERS_BY_REGION[region].map(bm => bm.key);
    const allSelected = regionBookmakers.every(key => prefs.preferred_bookmakers.includes(key));

    setPrefs(prev => ({
      ...prev,
      preferred_bookmakers: allSelected
        ? prev.preferred_bookmakers.filter(key => !regionBookmakers.includes(key))
        : [...new Set([...prev.preferred_bookmakers, ...regionBookmakers])]
    }));
  };

  if (loading) return (
    <div className="flex items-center justify-center p-12">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-yellow-400"></div>
      <span className="ml-4 text-gray-300 text-lg">Loading preferences...</span>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto w-full">
      <div className="bg-gray-800 rounded-xl shadow-xl border border-yellow-400/20">
        {/* Header */}
        <div className="bg-gray-900/60 border-b border-yellow-500/20 p-6 rounded-t-xl">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-yellow-300">Arbitrage Preferences</h2>
              <p className="text-gray-400 mt-1 text-sm">Configure your preferred sports, bookmakers, and notification settings. Your preferences will automatically filter opportunities across all pages.</p>
            </div>
            {feedback && (
              <div className={`text-sm font-medium ${feedback.includes('✅') ? 'text-green-400' : 'text-red-400'
                }`}>
                {feedback}
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'bookmakers', name: `Bookmakers (${prefs.preferred_bookmakers.length})` },
              { id: 'settings', name: 'Arbitrage Settings' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`${activeTab === tab.id
                  ? 'border-yellow-400 text-yellow-400'
                  : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        <form onSubmit={handleSave} className="p-6">


          {/* Bookmakers Tab */}
          {/* Bookmakers Tab */}
          {activeTab === 'bookmakers' && (
            <div className="space-y-6">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-xl font-semibold text-yellow-300">Select Your Preferred Bookmakers</h3>
                  <p className="text-gray-400 mt-1">
                    Choose from {SGO_BOOKMAKERS.length} bookmakers available ({SGO_BOOKMAKERS_BY_REGION.US?.length || 0} US, {SGO_BOOKMAKERS_BY_REGION.INTL?.length || 0} International)
                  </p>
                </div>
                <button
                  type="button"
                  onClick={toggleAllBookmakers}
                  className="px-4 py-2 bg-yellow-400 text-gray-900 rounded-lg font-medium hover:bg-yellow-500 transition-colors shadow-lg hover:shadow-yellow-400/20"
                >
                  {prefs.preferred_bookmakers.length === SGO_BOOKMAKERS.length ? 'Clear All' : 'Select All'}
                </button>
              </div>

              <div className="space-y-4">
                {/* US Bookmakers Collapsible */}
                <details className="group bg-gray-700/50 rounded-xl border border-gray-600 overflow-hidden open:pb-4 transition-all" open>
                  <summary className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-700 transition-colors list-none select-none">
                    <div className="flex items-center gap-3">
                      <span className="text-xl group-open:rotate-90 transition-transform duration-200 text-yellow-400">►</span>
                      <h4 className="text-lg font-medium text-yellow-200">
                        US Bookmakers
                        <span className="ml-2 text-sm text-gray-400 font-normal">
                          ({SGO_BOOKMAKERS_BY_REGION.US?.length || 0} available)
                        </span>
                      </h4>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault(); // Prevent closing details
                        toggleRegionBookmakers('US');
                      }}
                      className="text-sm px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors z-10"
                    >
                      {SGO_BOOKMAKERS_BY_REGION.US?.every(bm => prefs.preferred_bookmakers.includes(bm.key)) ? 'Clear US' : 'Select US'}
                    </button>
                  </summary>

                  <div className="px-4 pt-2 pb-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
                      {(SGO_BOOKMAKERS_BY_REGION.US || []).map(bm => {
                        const selected = prefs.preferred_bookmakers.includes(bm.key);
                        return (
                          <label
                            key={bm.key}
                            className={`group relative flex items-center p-2 rounded-lg cursor-pointer transition-all duration-300 border backdrop-blur-sm ${selected
                              ? 'bg-yellow-500/10 border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.1)]'
                              : 'bg-gray-800/40 border-gray-700/50 hover:border-gray-500 hover:bg-gray-800/80'
                              }`}
                          >
                            <div className={`absolute inset-0 rounded-lg transition-opacity duration-300 ${selected ? 'bg-gradient-to-br from-yellow-400/5 to-transparent opacity-100' : 'opacity-0'}`}></div>

                            <div className="relative flex items-center justify-center min-w-[1rem] h-4 mr-2">
                              <input
                                type="checkbox"
                                checked={selected}
                                onChange={e => {
                                  setPrefs(prev => ({
                                    ...prev,
                                    preferred_bookmakers: e.target.checked
                                      ? [...prev.preferred_bookmakers, bm.key]
                                      : prev.preferred_bookmakers.filter(k => k !== bm.key),
                                  }));
                                }}
                                className="peer appearance-none w-4 h-4 border border-gray-500 rounded bg-gray-900/50 checked:bg-yellow-400 checked:border-yellow-400 transition-all cursor-pointer"
                              />
                              <i className="fas fa-check text-gray-900 text-[0.6rem] absolute opacity-0 peer-checked:opacity-100 pointer-events-none transition-all scale-50 peer-checked:scale-100"></i>
                            </div>
                            <div className="flex-1 min-w-0 z-10">
                              <div className={`font-medium text-xs truncate transition-colors ${selected ? 'text-yellow-100' : 'text-gray-400 group-hover:text-white'}`}>
                                {bm.name}
                              </div>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                </details>

                {/* International Bookmakers Collapsible */}
                <details className="group bg-gray-700/50 rounded-xl border border-gray-600 overflow-hidden open:pb-4 transition-all">
                  <summary className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-700 transition-colors list-none select-none">
                    <div className="flex items-center gap-3">
                      <span className="text-xl group-open:rotate-90 transition-transform duration-200 text-yellow-400">►</span>
                      <h4 className="text-lg font-medium text-yellow-200">
                        International Bookmakers
                        <span className="ml-2 text-sm text-gray-400 font-normal">
                          ({SGO_BOOKMAKERS_BY_REGION.INTL?.length || 0} available)
                        </span>
                      </h4>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        toggleRegionBookmakers('INTL');
                      }}
                      className="text-sm px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded transition-colors z-10"
                    >
                      {SGO_BOOKMAKERS_BY_REGION.INTL?.every(bm => prefs.preferred_bookmakers.includes(bm.key)) ? "Clear Int'l" : "Select Int'l"}
                    </button>
                  </summary>

                  <div className="px-4 pt-2 pb-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
                      {(SGO_BOOKMAKERS_BY_REGION.INTL || []).map(bm => {
                        const selected = prefs.preferred_bookmakers.includes(bm.key);
                        return (
                          <label
                            key={bm.key}
                            className={`group relative flex items-center p-2 rounded-lg cursor-pointer transition-all duration-300 border backdrop-blur-sm ${selected
                              ? 'bg-yellow-500/10 border-yellow-500/50 shadow-[0_0_10px_rgba(234,179,8,0.1)]'
                              : 'bg-gray-800/40 border-gray-700/50 hover:border-gray-500 hover:bg-gray-800/80'
                              }`}
                          >
                            <div className={`absolute inset-0 rounded-lg transition-opacity duration-300 ${selected ? 'bg-gradient-to-br from-yellow-400/5 to-transparent opacity-100' : 'opacity-0'}`}></div>

                            <div className="relative flex items-center justify-center min-w-[1rem] h-4 mr-2">
                              <input
                                type="checkbox"
                                checked={selected}
                                onChange={e => {
                                  setPrefs(prev => ({
                                    ...prev,
                                    preferred_bookmakers: e.target.checked
                                      ? [...prev.preferred_bookmakers, bm.key]
                                      : prev.preferred_bookmakers.filter(k => k !== bm.key),
                                  }));
                                }}
                                className="peer appearance-none w-4 h-4 border border-gray-500 rounded bg-gray-900/50 checked:bg-yellow-400 checked:border-yellow-400 transition-all cursor-pointer"
                              />
                              <i className="fas fa-check text-gray-900 text-[0.6rem] absolute opacity-0 peer-checked:opacity-100 pointer-events-none transition-all scale-50 peer-checked:scale-100"></i>
                            </div>
                            <div className="flex-1 min-w-0 z-10">
                              <div className={`font-medium text-xs truncate transition-colors ${selected ? 'text-yellow-100' : 'text-gray-400 group-hover:text-white'}`}>
                                {bm.name}
                              </div>
                            </div>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                </details>
              </div>
            </div>
          )}

          {/* Settings Tab */}
          {activeTab === 'settings' && (
            <div className="space-y-8">


              {/* Minimum Profit Threshold */}
              <div className="bg-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-yellow-300 mb-4">Minimum Profit Threshold</h3>
                <p className="text-gray-400 mb-6">
                  Set the minimum profit percentage for opportunities you want to see and receive notifications about.
                </p>
                <div className="flex items-center gap-6">
                  <div className="flex-1">
                    <input
                      type="range"
                      min={0.5}
                      max={10}
                      step={0.1}
                      value={prefs.minimum_profit_threshold}
                      onChange={e => setPrefs(prev => ({ ...prev, minimum_profit_threshold: parseFloat(e.target.value) }))}
                      className="w-full h-3 bg-gray-600 rounded-lg appearance-none cursor-pointer slider"
                      style={{
                        background: `linear-gradient(to right, #facc15 0%, #facc15 ${(prefs.minimum_profit_threshold - 0.5) / 9.5 * 100}%, #4b5563 ${(prefs.minimum_profit_threshold - 0.5) / 9.5 * 100}%, #4b5563 100%)`
                      }}
                    />
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-yellow-300">{prefs.minimum_profit_threshold.toFixed(1)}%</div>
                    <div className="text-sm text-gray-400">Minimum</div>
                  </div>
                </div>
              </div>

              {/* Notification Settings */}
              <div className="bg-gray-700 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-yellow-300 mb-4">Notification Settings</h3>
                <p className="text-gray-400 mb-6">
                  Choose how you want to be notified when new arbitrage opportunities are found that match your preferences.
                </p>

                <div className="space-y-4">


                  <label className="flex items-start gap-4 p-4 bg-gray-600 rounded-lg hover:bg-gray-500 transition-colors cursor-pointer">
                    <input
                      type="checkbox"
                      checked={prefs.notification_browser}
                      onChange={e => handleBrowserNotifToggle(e.target.checked)}
                      className="mt-1 w-5 h-5 text-yellow-400 bg-gray-700 border-gray-500 rounded focus:ring-yellow-400"
                    />
                    <div>
                      <div className="text-white font-semibold">Browser Notifications</div>
                      <div className="text-gray-300 text-sm">Get instant browser pop-ups for time-sensitive opportunities that match your sports, bookmakers, and profit threshold</div>
                      {prefs.notification_browser && Notification && Notification.permission !== 'granted' && (
                        <div className="text-red-400 text-xs mt-1">Permission required - please allow in your browser</div>
                      )}
                      {prefs.notification_browser && Notification && Notification.permission === 'granted' && (
                        <div className="text-green-400 text-xs mt-1 flex items-center justify-between">
                          <span>Browser notifications enabled - checking every {subscriptionTier === 'premium' ? '30' : '60'} seconds</span>
                          <button
                            onClick={() => sendTestNotification()}
                            className="ml-2 px-2 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-700 transition-colors"
                          >
                            Test
                          </button>
                        </div>
                      )}
                    </div>
                  </label>
                </div>
              </div>
            </div>
          )}


        </form>
      </div>
    </div>
  );
};

export default PreferencesTab;
