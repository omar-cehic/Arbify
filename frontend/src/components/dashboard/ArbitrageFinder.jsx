import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { Helmet } from 'react-helmet-async';
import { toast } from 'react-toastify';
import axios from 'axios';
import CleanArbitrageCard from './CleanArbitrageCard';
import SubscriptionCard from '../subscription/SubscriptionCard';
import { formatOdds, formatProfit, formatDate, extractBookmakerNames } from '../../utils/sgoDataUtils';
import {
  SGO_SPORTS,
  SGO_BOOKMAKERS,
  SGO_BOOKMAKERS_BY_REGION,
  SGO_SPORTS_BY_CATEGORY,
  SORT_OPTIONS
} from '../../constants/sgoConstants';

const ArbitrageFinder = () => {
  const [arbitrageOpportunities, setArbitrageOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();

  // Version Check
  useEffect(() => {
    console.log('🚀 Arbify Client Version: 2026-01-26 13:00 CST (Login & Notif Fix)');
  }, []);

  const [showFilters, setShowFilters] = useState(false);
  const [selectedSports, setSelectedSports] = useState([]);
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);
  const [sortBy, setSortBy] = useState('profit_desc');
  const [minProfit, setMinProfit] = useState(0.0);
  const [minProfitInput, setMinProfitInput] = useState('0.0'); // Display value for input
  const [hasLoadedPreferences, setHasLoadedPreferences] = useState(false);

  // Load user preferences from localStorage
  const loadUserPreferences = useCallback(() => {
    try {
      const savedPreferences = localStorage.getItem('userPreferences');
      let preferences = {};

      if (savedPreferences) {
        preferences = JSON.parse(savedPreferences);
        console.log('🔧 ArbitrageFinder: Loading user preferences:', preferences);
      }



      // 1. Bookmakers: Prioritize Profile Preferences
      // Check multiple keys to be safe
      const profileBookmakers = preferences.preferred_bookmakers || preferences.selectedBookmakers;

      if (profileBookmakers !== undefined) {
        // If defined (even if empty array), use it.
        // Ensure it's an array
        const booksToUse = Array.isArray(profileBookmakers) ? profileBookmakers : [];
        setSelectedBookmakers(booksToUse);
        console.log('🔧 ArbitrageFinder: Applied bookmakers from Profile:', booksToUse);
      } else {
        // Only fallback to ALL if absolutely no preferences exist (first time user)
        const allBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
        setSelectedBookmakers(allBookmakers);
        console.log('🔧 ArbitrageFinder: No profile preferences found (undefined), defaulting to ALL');
      }

      setHasLoadedPreferences(true);

      // 2. Sports
      const profileSports = preferences.preferred_sports || preferences.selectedSports;
      if (profileSports && Array.isArray(profileSports) && profileSports.length > 0) {
        setSelectedSports(profileSports);
      }

      // 3. Min Profit
      const minProfitFromPrefs = preferences.minimum_profit_threshold || preferences.minProfit;
      if (minProfitFromPrefs !== undefined) {
        setMinProfit(minProfitFromPrefs);
        setMinProfitInput(minProfitFromPrefs.toString());
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
      // Fallback
      const allBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
      setSelectedBookmakers(allBookmakers);
      setHasLoadedPreferences(true);
    }
  }, []);

  // Initialize with user preferences (only on first load)
  useEffect(() => {
    if (!hasLoadedPreferences) {
      loadUserPreferences();
    }
  }, [loadUserPreferences, hasLoadedPreferences]);

  // Save current filter state to localStorage for syncing between tabs (excluding minProfit)
  const saveFilterState = useCallback((filters) => {
    try {
      const filterState = {
        selectedSports: filters.selectedSports || selectedSports,
        selectedBookmakers: filters.selectedBookmakers || selectedBookmakers,
        sortBy: filters.sortBy || sortBy,
        timestamp: Date.now()
      };
      localStorage.setItem('currentFilterState', JSON.stringify(filterState));
      console.log('💾 Saved filter state (bookmakers & sports only):', filterState);

      // Dispatch custom event to notify other tabs
      window.dispatchEvent(new CustomEvent('filterStateChanged', {
        detail: filterState
      }));
    } catch (error) {
      console.error('Error saving filter state:', error);
    }
  }, [selectedSports, selectedBookmakers, sortBy]);

  // Load filter state from localStorage (for tab sync)
  const loadFilterState = useCallback(() => {
    try {
      const saved = localStorage.getItem('currentFilterState');
      if (saved) {
        const filterState = JSON.parse(saved);
        console.log('📥 Loading filter state:', filterState);

        setSelectedSports(filterState.selectedSports || []);
        setSelectedBookmakers(filterState.selectedBookmakers || []);
        setSortBy(filterState.sortBy || 'profit_desc');

        return true;
      }
    } catch (error) {
      console.error('Error loading filter state:', error);
    }
    return false;
  }, []);

  // Listen for filter changes from other tabs (excluding minProfit)
  useEffect(() => {
    const handleFilterChange = (event) => {
      const { selectedSports: newSports, selectedBookmakers: newBookmakers, sortBy: newSortBy } = event.detail;
      console.log('🔄 Received filter change from other tab (bookmakers & sports only):', event.detail);

      setSelectedSports(newSports || []);
      setSelectedBookmakers(newBookmakers || []);
      setSortBy(newSortBy || 'profit_desc');
    };

    window.addEventListener('filterStateChanged', handleFilterChange);
    return () => window.removeEventListener('filterStateChanged', handleFilterChange);
  }, []);

  const fetchSGOOpportunities = async (forceRefresh = false) => {
    try {
      console.log('Fetching pre-game arbitrage opportunities from SportsGameOdds API...');
      const response = await axios.get('/api/arbitrage/sgo', {
        params: {
          live_only: false,
          min_profit: 0.0,
          force_refresh: forceRefresh
        }
      });
      console.log('SGO API Response:', response.data);
      return response.data;
    } catch (error) {
      console.error('SGO API Error:', error);
      throw error;
    }
  };



  // Cache management with TTL
  const CACHE_TTL = 2 * 60 * 1000; // 2 minutes

  const setCacheWithTTL = (key, data) => {
    const item = {
      data: data,
      timestamp: Date.now(),
      ttl: CACHE_TTL
    };
    localStorage.setItem(key, JSON.stringify(item));
    console.log(`💾 Cached ${key} with TTL: ${CACHE_TTL / 1000}s`);
  };

  const getCacheWithTTL = (key) => {
    try {
      const item = JSON.parse(localStorage.getItem(key));
      if (!item) return null;

      const age = Date.now() - item.timestamp;
      if (age > item.ttl) {
        localStorage.removeItem(key); // Auto-expire
        console.log(`🗑️ Cache expired: ${key} (age: ${Math.round(age / 1000)}s)`);
        return null;
      }

      console.log(`📖 Cache hit: ${key} (age: ${Math.round(age / 1000)}s)`);
      return item.data;
    } catch (error) {
      console.error('Cache read error:', error);
      localStorage.removeItem(key);
      return null;
    }
  };

  const clearAllArbitrageCache = () => {
    // Clear ALL arbitrage-related cache keys
    Object.keys(localStorage).forEach(key => {
      if (key.includes('arbitrage') || key.includes('arb') || key.includes('opportunities')) {
        localStorage.removeItem(key);
      }
    });
    console.log('🧹 Cleared ALL arbitrage cache');
  };

  const loadOpportunities = useCallback(async (forceRefresh = false) => {
    const cacheKey = 'arbitrage_opportunities';

    // Clear all cache on force refresh
    if (forceRefresh) {
      clearAllArbitrageCache();
    } else {
      // Check cache with TTL
      const cached = getCacheWithTTL(cacheKey);
      if (cached) {
        setArbitrageOpportunities(cached);
        return;
      }
    }

    try {
      setLoading(true);
      console.log('Loading arbitrage opportunities...');

      try {
        const sgoData = await fetchSGOOpportunities(forceRefresh);

        if (sgoData.arbitrage_opportunities) {
          console.log('SGO API: Loaded', sgoData.arbitrage_opportunities.length, 'opportunities');
          setArbitrageOpportunities(sgoData.arbitrage_opportunities);

          // Cache with TTL
          setCacheWithTTL(cacheKey, sgoData.arbitrage_opportunities);

          if (sgoData.api_usage) {
            const usageMsg = 'SGO API: ' + sgoData.api_usage.daily_used + '/' + sgoData.api_usage.daily_budget + ' events used today';
            // Only show usage toast if usage is high
            if (sgoData.api_usage.daily_used > sgoData.api_usage.daily_budget * 0.8) {
              toast.info(usageMsg);
            }
          }
        } else {
          // SGO returned no data structure
          console.warn('SGO API returned unexpected structure, defaulting to empty list');
          setArbitrageOpportunities([]);
        }
      } catch (sgoError) {
        console.error('SGO API failed:', sgoError);
        toast.error('Failed to load arbitrage opportunities: ' + (sgoError.response?.data?.detail || sgoError.message));
        setArbitrageOpportunities([]);
      }

    } catch (error) {
      console.error('Error loading opportunities:', error);
      setArbitrageOpportunities([]);
    } finally {
      setLoading(false);
      // One-time log to confirm optimization
      if (!window.hasLoggedOptimization) {
        console.log('⚡ SGO Pro Optimized Mode: Active (Legacy API Disabled)');
        window.hasLoggedOptimization = true;
      }
    }
  }, []);

  useEffect(() => {
    // Performance Fix: Do NOT clear cache on mount. Use existing cache if valid.
    // Force refresh only if specifically requested or cache is expired (handled by loadOpportunities)
    loadOpportunities(false);

    // Auto-refresh every 60 seconds
    const refreshInterval = setInterval(() => loadOpportunities(false), 60000);
    return () => clearInterval(refreshInterval);
  }, [loadOpportunities]);

  const saveOpportunity = async (opportunity) => {
    console.log('Save button clicked for opportunity:', opportunity.id);

    if (!user) {
      toast.error('Please log in to save arbitrage opportunities');
      return;
    }

    try {
      const arbitrageData = {
        sport_key: opportunity.sport_key || 'unknown',
        sport_title: opportunity.sport_title || opportunity.sport,
        home_team: opportunity.home_team || 'Team A',
        away_team: opportunity.away_team || 'Team B',
        match_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        odds: opportunity.best_odds || {},
        bookmakers: opportunity.bookmakers_involved || [],
        profit_percentage: opportunity.profit_percentage,
        bet_amount: 0,
        status: 'open',
        notes: 'Saved from ArbitrageFinder - ' + (opportunity.market_type || 'Unknown Market')
      };

      await axios.post('/api/my-arbitrage', arbitrageData, {
        headers: {
          'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
          'Content-Type': 'application/json'
        }
      });

      console.log('Arbitrage opportunity saved');
      // Success toast handled by CleanArbitrageCard component

    } catch (error) {
      console.error('Error saving arbitrage opportunity:', error);
      toast.error('Failed to save arbitrage opportunity. Please try again.');
    }
  };


  const getFilteredOpportunities = () => {
    let filtered = arbitrageOpportunities;

    if (selectedBookmakers.length < 2) {
      return [];
    }

    // Filter out live games for arbitrage tab
    filtered = filtered.filter(opp => {
      const isLive = opp.game_type === 'LIVE' ||
        opp.status === 'live' ||
        opp.status === 'LIVE' ||
        opp.is_live === true ||
        opp.game_status === 'live' ||
        opp.game_status === 'LIVE';
      return !isLive;
    });

    // Filter by selected bookmakers - BOTH bookmakers must be selected
    if (selectedBookmakers.length > 0) {
      // Optimization: Create a Set of normalized selected bookmakers for O(1) lookup
      // Pre-calculating this once avoids doing it 23 * 2 * 82 times
      const normalize = (str) => {
        if (!str || typeof str !== 'string') return '';
        return str.toLowerCase().replace(/[^a-z0-9]/g, '');
      };

      const selectedSet = new Set(selectedBookmakers.map(normalize));

      // Also add special mappings to the set
      selectedBookmakers.forEach(bm => {
        const norm = normalize(bm);
        if (norm === 'betfair') selectedSet.add('betfairexchange');
        if (norm === 'betfairexchange') selectedSet.add('betfair');
      });

      console.time('ArbitrageFiltering');
      let debugLogCount = 0;

      filtered = filtered.filter(opp => {
        // Robustly extract bookmaker names to verify what's being displayed
        const extractedBookmakers = extractBookmakerNames(opp.best_odds);

        // Also get the raw keys as a fallback/validation source
        const rawBookmakerKeys = opp.bookmakers || opp.bookmakers_involved || [];

        // Combine unique bookmakers (both display names and keys) to check against
        const relevantBookmakers = [...new Set([...extractedBookmakers, ...rawBookmakerKeys])];

        // Critical Check: Opportunity must have at least 2 distinct bookmakers involved
        if (relevantBookmakers.length < 2) {
          return false;
        }

        // Strict Check: EVERY BOOKMAKER SIDE must be covered by selected bookmakers.
        const sidesToCheck = extractedBookmakers.includes('Unknown') && rawBookmakerKeys.length >= 2
          ? rawBookmakerKeys
          : extractedBookmakers;

        const isMatch = sidesToCheck.every(bm => {
          const bmNormalized = normalize(bm);

          // Fast O(1) lookup
          if (selectedSet.has(bmNormalized)) return true;

          // Partial match fallback (slower but rarely needed if keys are consistent)
          // Only check this if exact match fails
          // We can iterate the set or original array, but let's stick to the set if possible.
          // For partial match, we unfortunately need to iterate. 
          // However, we can optimize by only doing this for "unknown" or long strings.

          // Let's assume most matches are exact due to our normalization. 
          // If we really need partial match (e.g. williamhillus vs williamhill), we iterate.
          for (const selected of selectedSet) {
            if (selected.length > 3 && bmNormalized.length > 3) {
              if (bmNormalized.includes(selected) || selected.includes(bmNormalized)) return true;
            }
          }

          return false;
        });

        if (!isMatch && debugLogCount < 3) {
          // console.log(`❌ Filtered: ${opp.home_team} vs ${opp.away_team} | Has: ${cleanedSides.join(', ')}`); 
          // Reduced logging to avoid browser console lag
          debugLogCount++;
        }
        return isMatch;
      });
      console.timeEnd('ArbitrageFiltering');
    }

    // Filter by selected sports
    if (selectedSports.length > 0) {
      filtered = filtered.filter(opp => {
        // Check both sport key and explicit sport name
        const oppSport = (opp.sport_key || opp.sport || '').toLowerCase();
        const oppLeague = (opp.league || '').toLowerCase();

        return selectedSports.some(selected => {
          const selectedLower = selected.toLowerCase();
          return oppSport.includes(selectedLower) ||
            oppLeague.includes(selectedLower) ||
            // Handle mapped sports (e.g. 'americanfootball_nfl' matching 'football')
            (selectedLower === 'football' && (oppSport.includes('nfl') || oppSport.includes('ncaaf'))) ||
            (selectedLower === 'basketball' && (oppSport.includes('nba') || oppSport.includes('ncaab'))) ||
            (selectedLower === 'baseball' && oppSport.includes('mlb')) ||
            (selectedLower === 'hockey' && oppSport.includes('nhl'));
        });
      });
    }

    // Filter by minimum profit
    filtered = filtered.filter(opp => opp.profit_percentage >= minProfit);

    // Sort opportunities
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'profit_desc':
          return b.profit_percentage - a.profit_percentage;
        case 'profit_asc':
          return a.profit_percentage - b.profit_percentage;
        case 'time_asc':
          return new Date(a.start_time || a.commence_time) - new Date(b.start_time || b.commence_time);
        case 'time_desc':
          return new Date(b.start_time || b.commence_time) - new Date(a.start_time || a.commence_time);
        default:
          return b.profit_percentage - a.profit_percentage;
      }
    });

    return filtered;
  };

  const filteredOpportunities = getFilteredOpportunities();

  useEffect(() => {
    loadUserPreferences();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <Helmet>
        <title>Arbitrage Finder - Arbify</title>
        <meta name="description" content="Discover pre-game sports arbitrage opportunities across major bookmakers and sports leagues." />
      </Helmet>
      <div className="container mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Arbitrage Opportunities</h1>
          <p className="text-gray-300 text-lg">
            Pre-game arbitrage opportunities
          </p>
        </div>

        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">
              Arbitrage Opportunities ({filteredOpportunities.length} found)
            </h2>
            <div className="flex gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors flex items-center"
              >
                <i className={`fas fa-chevron-${showFilters ? 'up' : 'down'} mr-2`}></i>
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </button>
              <button
                onClick={() => loadOpportunities(true)}
                disabled={loading}
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading ? 'Loading...' : 'Refresh'}
              </button>
            </div>
          </div>

          {/* Comprehensive Filter System */}
          {showFilters && (
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
              <h3 className="text-xl font-bold text-yellow-400 mb-6">Arbitrage Filters</h3>

              {/* Top Row - Min Profit and Sort By */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Min Profit %
                  </label>
                  <input
                    type="number"
                    value={minProfitInput}
                    onChange={(e) => {
                      const value = e.target.value;
                      setMinProfitInput(value); // Allow any input including empty string

                      // Update the actual filter value for immediate filtering
                      if (value === '' || value === null) {
                        // Don't filter while typing, use 0 as temporary value
                        setMinProfit(0);
                      } else {
                        const parsedValue = parseFloat(value);
                        if (!isNaN(parsedValue)) {
                          setMinProfit(parsedValue);
                        }
                      }
                    }}
                    onBlur={(e) => {
                      const value = e.target.value;

                      if (value === '' || value === null) {
                        // If left blank, use 0 (show all opportunities)
                        setMinProfit(0);
                        setMinProfitInput('');
                      } else {
                        const parsedValue = parseFloat(value);
                        if (!isNaN(parsedValue)) {
                          setMinProfit(parsedValue);
                          setMinProfitInput(parsedValue.toString());
                        } else {
                          // Invalid input, reset to 0
                          setMinProfit(0);
                          setMinProfitInput('');
                        }
                      }
                    }}
                    onFocus={(e) => {
                      // Select all text when focused for easy editing
                      e.target.select();
                    }}
                    step="0.1"
                    min="0"
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500"
                    placeholder="0.5"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Sort By
                  </label>
                  <select
                    value={sortBy}
                    onChange={(e) => {
                      const newSortBy = e.target.value;
                      setSortBy(newSortBy);
                      saveFilterState({ sortBy: newSortBy });
                    }}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500"
                  >
                    {SORT_OPTIONS.map(option => (
                      <option key={option.key} value={option.key}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Bookmaker Selection - Full Width Below */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold text-yellow-400">Select Bookmakers</h4>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2 mb-4">
                  <button
                    onClick={() => {
                      const allKeys = SGO_BOOKMAKERS.map(bm => bm.key);
                      setSelectedBookmakers(allKeys);
                      saveFilterState({ selectedBookmakers: allKeys });
                    }}
                    className="px-3 py-1 bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30 rounded text-sm font-medium transition-colors border border-yellow-500/30"
                  >
                    Select All
                  </button>
                  <button
                    onClick={() => {
                      setSelectedBookmakers([]);
                      saveFilterState({ selectedBookmakers: [] });
                    }}
                    className="px-3 py-1 bg-gray-700 text-gray-300 hover:bg-gray-600 rounded text-sm font-medium transition-colors border border-gray-600"
                  >
                    Clear All
                  </button>
                </div>

                {/* US Bookmakers */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-yellow-200 font-medium text-sm">US Bookmakers</h5>
                    <button
                      onClick={() => {
                        const usKeys = SGO_BOOKMAKERS_BY_REGION.US.map(bm => bm.key);
                        const allSelected = usKeys.every(k => selectedBookmakers.includes(k));
                        const newSelection = allSelected
                          ? selectedBookmakers.filter(k => !usKeys.includes(k))
                          : [...new Set([...selectedBookmakers, ...usKeys])];
                        setSelectedBookmakers(newSelection);
                        saveFilterState({ selectedBookmakers: newSelection });
                      }}
                      className="text-xs text-yellow-500 hover:text-yellow-400 transition-colors"
                    >
                      {SGO_BOOKMAKERS_BY_REGION.US.every(k => selectedBookmakers.includes(k)) ? 'Clear US' : 'Select US'}
                    </button>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                    {SGO_BOOKMAKERS_BY_REGION.US.map(bm => {
                      const isSelected = selectedBookmakers.includes(bm.key);
                      return (
                        <div
                          key={bm.key}
                          onClick={() => {
                            const newSelection = isSelected
                              ? selectedBookmakers.filter(k => k !== bm.key)
                              : [...selectedBookmakers, bm.key];
                            setSelectedBookmakers(newSelection);
                            saveFilterState({ selectedBookmakers: newSelection });
                          }}
                          className={`cursor-pointer px-2 py-2 rounded border text-xs flex items-center gap-2 transition-all select-none ${isSelected ? 'bg-yellow-500/10 border-yellow-500 text-yellow-100' : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-500 hover:bg-gray-700/50'}`}
                        >
                          <div className={`w-3 h-3 rounded-sm border flex items-center justify-center flex-shrink-0 ${isSelected ? 'bg-yellow-500 border-yellow-500' : 'border-gray-500'}`}>
                            {isSelected && <i className="fas fa-check text-[8px] text-gray-900"></i>}
                          </div>
                          <span className="truncate">{bm.name}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* International Bookmakers */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h5 className="text-yellow-200 font-medium text-sm">International Bookmakers</h5>
                    <button
                      onClick={() => {
                        const intlKeys = SGO_BOOKMAKERS_BY_REGION.INTL.map(bm => bm.key);
                        const allSelected = intlKeys.every(k => selectedBookmakers.includes(k));
                        const newSelection = allSelected
                          ? selectedBookmakers.filter(k => !intlKeys.includes(k))
                          : [...new Set([...selectedBookmakers, ...intlKeys])];
                        setSelectedBookmakers(newSelection);
                        saveFilterState({ selectedBookmakers: newSelection });
                      }}
                      className="text-xs text-yellow-500 hover:text-yellow-400 transition-colors"
                    >
                      {SGO_BOOKMAKERS_BY_REGION.INTL.every(k => selectedBookmakers.includes(k)) ? 'Clear Intl' : 'Select Intl'}
                    </button>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                    {SGO_BOOKMAKERS_BY_REGION.INTL.map(bm => {
                      const isSelected = selectedBookmakers.includes(bm.key);
                      return (
                        <div
                          key={bm.key}
                          onClick={() => {
                            const newSelection = isSelected
                              ? selectedBookmakers.filter(k => k !== bm.key)
                              : [...selectedBookmakers, bm.key];
                            setSelectedBookmakers(newSelection);
                            saveFilterState({ selectedBookmakers: newSelection });
                          }}
                          className={`cursor-pointer px-2 py-2 rounded border text-xs flex items-center gap-2 transition-all select-none ${isSelected ? 'bg-yellow-500/10 border-yellow-500 text-yellow-100' : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-500 hover:bg-gray-700/50'}`}
                        >
                          <div className={`w-3 h-3 rounded-sm border flex items-center justify-center flex-shrink-0 ${isSelected ? 'bg-yellow-500 border-yellow-500' : 'border-gray-500'}`}>
                            {isSelected && <i className="fas fa-check text-[8px] text-gray-900"></i>}
                          </div>
                          <span className="truncate">{bm.name}</span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-12">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400 mr-3"></div>
                Loading arbitrage opportunities...
              </div>
            </div>
          ) : filteredOpportunities && filteredOpportunities.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredOpportunities.map((opportunity, index) => (
                <CleanArbitrageCard
                  key={opportunity.event_id || index + '-' + opportunity.profit_percentage}
                  opportunity={opportunity}
                  onSave={saveOpportunity}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-gray-400 text-lg mb-4">
                <div>No arbitrage opportunities found</div>
              </div>
            </div>
          )}
        </div>
      </div >
    </div >
  );
};

export default ArbitrageFinder;