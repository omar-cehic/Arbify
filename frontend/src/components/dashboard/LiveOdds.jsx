import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Helmet } from 'react-helmet-async';
import ArbitrageCard from './ArbitrageCard';
import { SGO_BOOKMAKERS } from '../../constants/sgoConstants';

const LiveOdds = () => {
  const [liveOpportunities, setLiveOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [minProfit, setMinProfit] = useState(2.0); // Higher minimum for live games
  const [minProfitInput, setMinProfitInput] = useState('2.0'); // Display value for input
  const [lastUpdated, setLastUpdated] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);
  const [sortBy, setSortBy] = useState('profit_desc');
  const [hasLoadedPreferences, setHasLoadedPreferences] = useState(false);

  // Load user preferences from localStorage
  const loadUserPreferences = useCallback(() => {
    try {
      const savedPreferences = localStorage.getItem('userPreferences');
      if (savedPreferences) {
        const preferences = JSON.parse(savedPreferences);
        console.log('🔧 LiveOdds: Loading user preferences:', preferences);

        // Load selected bookmakers from preferences (check multiple possible keys)
        const bookmakers = preferences.preferred_bookmakers || preferences.selectedBookmakers || [];
        if (bookmakers && bookmakers.length > 0) {
          setSelectedBookmakers(bookmakers);
          console.log('🔧 LiveOdds: Loaded bookmakers from preferences:', bookmakers.length);
        } else {
          // Fallback to all bookmakers if no preferences found
          const allBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
          setSelectedBookmakers(allBookmakers);
          console.log('🔧 LiveOdds: No bookmaker preferences found, using all bookmakers:', allBookmakers.length);
        }

        // Load minimum profit from preferences (check multiple possible keys)
        const minProfitFromPrefs = preferences.minimum_profit_threshold || preferences.minProfit;
        if (minProfitFromPrefs !== undefined) {
          setMinProfit(minProfitFromPrefs);
          setMinProfitInput(minProfitFromPrefs.toString());
          console.log('🔧 LiveOdds: Loaded min profit from preferences:', minProfitFromPrefs);
        }
      } else {
        // No preferences found, use all bookmakers
        const allBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
        setSelectedBookmakers(allBookmakers);
        console.log('🔧 LiveOdds: No preferences found, using all bookmakers:', allBookmakers.length);
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
      // Fallback to all bookmakers on error
      const allBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
      setSelectedBookmakers(allBookmakers);
      setHasLoadedPreferences(true);
    }
  }, []);

  // Save current filter state to localStorage for syncing between tabs (excluding minProfit)
  const saveFilterState = useCallback((filters) => {
    try {
      const filterState = {
        selectedBookmakers: filters.selectedBookmakers || selectedBookmakers,
        sortBy: filters.sortBy || sortBy,
        timestamp: Date.now()
      };
      localStorage.setItem('currentFilterState', JSON.stringify(filterState));
      console.log('💾 LiveOdds saved filter state (bookmakers only):', filterState);

      // Dispatch custom event to notify other tabs
      window.dispatchEvent(new CustomEvent('filterStateChanged', {
        detail: filterState
      }));
    } catch (error) {
      console.error('Error saving filter state:', error);
    }
  }, [selectedBookmakers, sortBy]);

  // Listen for filter changes from other tabs (excluding minProfit)
  useEffect(() => {
    const handleFilterChange = (event) => {
      const { selectedBookmakers: newBookmakers, sortBy: newSortBy } = event.detail;
      console.log('🔄 LiveOdds received filter change from other tab (bookmakers only):', event.detail);

      setSelectedBookmakers(newBookmakers || []);
      setSortBy(newSortBy || 'profit_desc');
    };

    window.addEventListener('filterStateChanged', handleFilterChange);
    return () => window.removeEventListener('filterStateChanged', handleFilterChange);
  }, []);

  // Initialize with user preferences (only on first load)
  useEffect(() => {
    if (!hasLoadedPreferences) {
      loadUserPreferences();
    }
  }, [loadUserPreferences, hasLoadedPreferences]);

  // This page shows LIVE ARBITRAGE OPPORTUNITIES - higher risk, higher profit
  // Focus on games that are currently live or starting very soon

  // Fetch live arbitrage opportunities
  const fetchLiveOpportunities = useCallback(async (forceRefresh = false) => {
    // Check cache first (2 minute cache for live data)
    const cacheKey = 'live_arbitrage_opportunities';
    const cached = localStorage.getItem(cacheKey);
    const cacheTime = localStorage.getItem(`${cacheKey}_time`);

    if (!forceRefresh && cached && cacheTime) {
      const timeDiff = Date.now() - parseInt(cacheTime);
      if (timeDiff < 120000) { // 2 minutes
        console.log('Loading live opportunities from cache...');
        setLiveOpportunities(JSON.parse(cached));
        setLastUpdated(new Date(parseInt(cacheTime)));
        return;
      }
    }

    setLoading(true);
    try {
      console.log('Fetching live arbitrage opportunities...');

      // Get live arbitrage opportunities from SGO Pro API
      const response = await axios.get('/api/arbitrage/sgo', {
        params: {
          live_only: true,
          min_profit: minProfit,
          force_refresh: forceRefresh
        }
      });

      if (response.data?.arbitrage_opportunities) {
        const opportunities = response.data.arbitrage_opportunities;

        // Filter for truly live/immediate opportunities
        const liveFiltered = opportunities.filter(opp => {
          // Only show LIVE games (game_type === 'LIVE')
          return opp.game_type === 'LIVE';
        });

        setLiveOpportunities(liveFiltered);

        // Cache the results
        localStorage.setItem(cacheKey, JSON.stringify(liveFiltered));
        localStorage.setItem(`${cacheKey}_time`, Date.now().toString());

        setLastUpdated(new Date());
        console.log(`Found ${liveFiltered.length} live opportunities`);
      }
    } catch (err) {
      console.error('Error fetching live opportunities:', err);
      setLiveOpportunities([]);
    } finally {
      setLoading(false);
    }
  }, [minProfit]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    fetchLiveOpportunities(); // Fetch immediately
    const interval = setInterval(() => {
      fetchLiveOpportunities();
    }, 60000);
    return () => clearInterval(interval);
  }, [minProfit]);

  // Show live opportunities with filtering
  const getFilteredOpportunities = () => {
    console.log('LiveOdds: Raw live opportunities:', liveOpportunities.length);
    console.log('LiveOdds: Sample live opportunity:', liveOpportunities[0]);

    let filtered = [...liveOpportunities];

    // Require at least 2 bookmakers selected for arbitrage to work
    if (selectedBookmakers.length < 2) {
      return [];
    }


    // Apply bookmaker filter - ALL bookmakers must be selected
    if (selectedBookmakers.length > 0) {
      filtered = filtered.filter(opp => {
        const bookmakers = opp.bookmakers_involved || [];
        // For arbitrage, ALL bookmakers in the opportunity must be selected
        const matches = bookmakers.every(bm => {
          const bookmakerKey = typeof bm === 'string' ? bm.toLowerCase() : bm.key?.toLowerCase();
          const bookmakerName = typeof bm === 'string' ? bm : bm.name;

          return selectedBookmakers.some(selected => {
            const selectedLower = selected.toLowerCase();
            // Match by key or by name (case insensitive)
            const keyMatch = selectedLower === bookmakerKey;
            const nameMatch = selectedLower === bookmakerName?.toLowerCase();

            // Special case for betfair_exchange vs betfairexchange
            const betfairMatch = (selectedLower === 'betfair_exchange' && bookmakerKey === 'betfairexchange') ||
              (selectedLower === 'betfairexchange' && bookmakerKey === 'betfair_exchange');

            return keyMatch || nameMatch || betfairMatch ||
              // Also check SGO_BOOKMAKERS mapping
              SGO_BOOKMAKERS.find(sgoBm =>
                sgoBm.key === selected &&
                (sgoBm.name.toLowerCase() === bookmakerName?.toLowerCase() ||
                  sgoBm.key === bookmakerKey)
              );
          });
        });
        return matches;
      });
    }

    // Apply minimum profit filter
    filtered = filtered.filter(opp => opp.profit_percentage >= minProfit);

    console.log('LiveOdds: After filtering:', filtered.length);

    // Sort opportunities
    switch (sortBy) {
      case 'profit':
        filtered.sort((a, b) => b.profit_percentage - a.profit_percentage);
        break;
      case 'time':
        filtered.sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
        break;
      case 'sport':
        filtered.sort((a, b) => a.sport.localeCompare(b.sport));
        break;
      default:
        break;
    }

    return filtered;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <Helmet>
        <title>Live Odds - Arbify</title>
        <meta name="description" content="Find live in-play sports arbitrage betting opportunities as the action happens." />
      </Helmet>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Odds Tab</h1>
          <p className="text-gray-300 text-lg">
            Live arbitrage opportunities from games currently in progress
          </p>
        </div>

        {/* Refresh Controls */}
        <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              {lastUpdated && (
                <span className="text-sm text-gray-400">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={() => fetchLiveOpportunities(true)}
                disabled={loading}
                className="bg-yellow-500 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-yellow-600 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Scanning...' : 'Refresh Live Odds'}
              </button>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                {showFilters ? 'Hide Filters' : 'Show Filters'}
              </button>
            </div>
          </div>
        </div>

        {/* Comprehensive Filter System */}
        {showFilters && (
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
            <h3 className="text-xl font-bold text-yellow-400 mb-4">Live Odds Filters</h3>

            {/* Min Profit and Sort By */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Min Profit %</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  step="0.1"
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
                  onFocus={(e) => e.target.select()}
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400 focus:ring-opacity-20 focus:outline-none transition-colors"
                  placeholder="0.5"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Sort By</label>
                <select
                  value={sortBy}
                  onChange={(e) => {
                    const newSortBy = e.target.value;
                    setSortBy(newSortBy);
                    saveFilterState({ sortBy: newSortBy });
                  }}
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400 focus:ring-opacity-20 focus:outline-none transition-colors"
                >
                  <option value="profit">Highest Profit</option>
                  <option value="time">Time (Soonest)</option>
                  <option value="sport">Sport</option>
                </select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
              <button
                onClick={() => {
                  const newBookmakers = [...new Set(SGO_BOOKMAKERS.map(bm => bm.key))];
                  setSelectedBookmakers(newBookmakers);
                  saveFilterState({ selectedBookmakers: newBookmakers });
                }}
                className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-gray-900 px-4 py-2 rounded-lg font-semibold hover:from-yellow-400 hover:to-yellow-500 transition-all duration-200 shadow-lg hover:shadow-yellow-500"
              >
                Select All ({SGO_BOOKMAKERS.length})
              </button>
              <button
                onClick={() => {
                  const newBookmakers = [];
                  setSelectedBookmakers(newBookmakers);
                  saveFilterState({ selectedBookmakers: newBookmakers });
                  console.log('LiveOdds Clear All clicked - cleared and saved filter state');
                }}
                className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-4 py-2 rounded-lg font-semibold hover:from-gray-500 hover:to-gray-600 transition-all duration-200 shadow-lg"
              >
                Clear All
              </button>
              <button
                onClick={() => setSelectedBookmakers([...new Set([...selectedBookmakers, ...SGO_BOOKMAKERS.filter(bm => bm.region === 'INTL').map(bm => bm.key)])])}
                className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-gray-900 px-4 py-2 rounded-lg font-semibold hover:from-yellow-400 hover:to-yellow-500 transition-all duration-200 shadow-lg"
              >
                Select Intl ({SGO_BOOKMAKERS.filter(bm => bm.region === 'INTL').length})
              </button>
              <button
                onClick={() => setSelectedBookmakers(selectedBookmakers.filter(bm => !SGO_BOOKMAKERS.filter(book => book.region === 'INTL').map(book => book.key).includes(bm)))}
                className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-4 py-2 rounded-lg font-semibold hover:from-gray-500 hover:to-gray-600 transition-all duration-200 shadow-lg"
              >
                Clear Intl
              </button>
            </div>

            {/* Bookmaker Count Display */}
            <div className="mb-6">
              <div className="text-center">
                <span className="text-white font-bold text-lg">{selectedBookmakers.length}</span>
                <span className="text-gray-300 ml-2">of {SGO_BOOKMAKERS.length} bookmakers selected</span>
              </div>
            </div>

            {/* Bookmaker Grid - Bigger and Organized */}
            <div className="space-y-6">
              {/* US Bookmakers */}
              <div>
                <h4 className="text-lg font-semibold text-yellow-400 mb-3">
                  US Bookmakers
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {SGO_BOOKMAKERS.filter(bm => bm.region === 'US').map(bookmaker => (
                    <label key={bookmaker.key} className="group flex items-center bg-gray-700 bg-opacity-50 hover:bg-yellow-500 hover:bg-opacity-10 border border-gray-600 hover:border-yellow-500 hover:border-opacity-50 rounded-lg p-3 cursor-pointer transition-all duration-200 hover:shadow-lg">
                      <input
                        type="checkbox"
                        checked={selectedBookmakers.includes(bookmaker.key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedBookmakers([...new Set([...selectedBookmakers, bookmaker.key])]);
                          } else {
                            setSelectedBookmakers(selectedBookmakers.filter(bm => bm !== bookmaker.key));
                          }
                        }}
                        className="w-4 h-4 mr-3 rounded border-2 border-gray-500 bg-gray-600 text-yellow-500 focus:ring-2 focus:ring-yellow-500 focus:ring-offset-0 transition-colors"
                      />
                      <div className="flex-1">
                        <div className="text-white font-medium text-sm">{bookmaker.name}</div>
                        <div className="text-gray-400 text-xs">{bookmaker.key}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* International Bookmakers */}
              <div>
                <h4 className="text-lg font-semibold text-yellow-400 mb-3">
                  International Bookmakers
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                  {SGO_BOOKMAKERS.filter(bm => bm.region === 'INTL').map(bookmaker => (
                    <label key={bookmaker.key} className="group flex items-center bg-gray-700 bg-opacity-50 hover:bg-yellow-500 hover:bg-opacity-10 border border-gray-600 hover:border-yellow-500 hover:border-opacity-50 rounded-lg p-3 cursor-pointer transition-all duration-200 hover:shadow-lg">
                      <input
                        type="checkbox"
                        checked={selectedBookmakers.includes(bookmaker.key)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedBookmakers([...new Set([...selectedBookmakers, bookmaker.key])]);
                          } else {
                            setSelectedBookmakers(selectedBookmakers.filter(bm => bm !== bookmaker.key));
                          }
                        }}
                        className="w-4 h-4 mr-3 rounded border-2 border-gray-500 bg-gray-600 text-yellow-500 focus:ring-2 focus:ring-yellow-500 focus:ring-offset-0 transition-colors"
                      />
                      <div className="flex-1">
                        <div className="text-white font-medium text-sm">{bookmaker.name}</div>
                        <div className="text-gray-400 text-xs">{bookmaker.key}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Live Opportunities */}
        {loading && liveOpportunities.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
            <span className="ml-2 text-gray-400">Scanning for live opportunities...</span>
          </div>
        ) : getFilteredOpportunities().length > 0 ? (
          <div>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-yellow-400">
                Live Opportunities ({getFilteredOpportunities().length} found)
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {getFilteredOpportunities().map((opportunity, index) => (
                <ArbitrageCard
                  key={`${opportunity.id || index}`}
                  opportunity={opportunity}
                  isLive={true}
                />
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <h3 className="text-2xl font-bold text-yellow-400 mb-4">No Live Opportunities Available</h3>
            <p className="text-gray-400 text-lg mb-6">
              Live arbitrage opportunities will appear here when games are currently in progress.
            </p>
            <button
              onClick={() => fetchLiveOpportunities(true)}
              className="bg-yellow-500 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-yellow-600 transition-colors"
            >
              Refresh Live Odds
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LiveOdds;