import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { toast } from 'react-toastify';
import axios from 'axios';
import ArbitrageCard from './ArbitrageCard';
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
  
  // Filtering state
  const [showFilters, setShowFilters] = useState(false);
  const [selectedSports, setSelectedSports] = useState([]);
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);
  
  // Initialize with all US bookmakers by default
  useEffect(() => {
    if (selectedBookmakers.length === 0) {
      const defaultBookmakers = SGO_BOOKMAKERS.map(bm => bm.key); // Include all bookmakers
      setSelectedBookmakers([...new Set(defaultBookmakers)]);
      console.log('🔧 Initialized bookmakers:', defaultBookmakers.length, 'total bookmakers');
    }
  }, []);
  const [sortBy, setSortBy] = useState('profit_desc');
  const [minProfit, setMinProfit] = useState(0.1); // Lowered to show more opportunities

  // Function to fetch arbitrage opportunities from SGO API (NEW) - Pre-game only
  const fetchSGOOpportunities = async (forceRefresh = false) => {
    try {
      console.log('Fetching pre-game arbitrage opportunities from SportsGameOdds API...');
      const response = await axios.get('/api/arbitrage/sgo', {
        params: {
          live_only: false, // Only pre-game opportunities
          min_profit: 0.5,   // Lower minimum for pre-game
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

  // Function to fetch real arbitrage opportunities from API (LEGACY)
  const fetchRealOpportunities = async () => {
    try {
      console.log('Fetching real arbitrage opportunities from legacy API...');
      const response = await axios.get('/api/arbitrage');
      console.log('Legacy API Response:', response.data);
      
    if (!response.data.arbitrage_opportunities) {
        console.error('Invalid API response - missing arbitrage_opportunities');
        return [];
      }
      
      return response.data.arbitrage_opportunities || [];
    } catch (error) {
      console.error('Error fetching real opportunities:', error);
      return [];
    }
  };

  // Enhanced function to fetch opportunities with SGO first, legacy fallback
  const loadOpportunities = useCallback(async (forceRefresh = false) => {
    // Check cache first (5 minute cache)
    const cacheKey = 'arbitrage_opportunities';
    const cached = localStorage.getItem(cacheKey);
    const cacheTime = localStorage.getItem(`${cacheKey}_time`);
    
    // TEMPORARY: Always force refresh to bypass cache during debugging
    if (false && !forceRefresh && cached && cacheTime) {
      const timeDiff = Date.now() - parseInt(cacheTime);
      if (timeDiff < 600000) { // 10 minutes - increased cache time
        console.log('Loading opportunities from cache...');
        setArbitrageOpportunities(JSON.parse(cached));
        return;
      }
    }

    try {
      setLoading(true);
      console.log('Loading arbitrage opportunities...');
      
      // Try SGO API first
      try {
        const sgoData = await fetchSGOOpportunities(forceRefresh);
        
        if (sgoData.arbitrage_opportunities && sgoData.arbitrage_opportunities.length > 0) {
          console.log('SGO API: Loaded', sgoData.arbitrage_opportunities.length, 'opportunities');
          setArbitrageOpportunities(sgoData.arbitrage_opportunities);
          
          // Cache the results
          localStorage.setItem(cacheKey, JSON.stringify(sgoData.arbitrage_opportunities));
          localStorage.setItem(`${cacheKey}_time`, Date.now().toString());
          
          // Show API usage info
          if (sgoData.api_usage) {
            toast.info(`SGO API: ${sgoData.api_usage.daily_used}/${sgoData.api_usage.daily_budget} events used today`);
          }
          return;
        } else if (sgoData.data_source === 'rate_limited') {
          console.log('SGO API: Rate limited, trying legacy...');
          toast.info('SGO API rate limited - using cached data');
        }
      } catch (sgoError) {
        console.warn('SGO API failed, falling back to legacy:', sgoError.message);
      }
      
      // Fallback to legacy API
      const legacyOpportunities = await fetchRealOpportunities();
      console.log('Legacy API: Loaded', legacyOpportunities.length, 'opportunities');
      setArbitrageOpportunities(legacyOpportunities);
      
      // Cache legacy results too
      localStorage.setItem(cacheKey, JSON.stringify(legacyOpportunities));
      localStorage.setItem(`${cacheKey}_time`, Date.now().toString());
      
      } catch (error) {
      console.error('All APIs failed:', error);
      setArbitrageOpportunities([]);
      toast.error('Failed to load arbitrage opportunities');
      } finally {
        setLoading(false);
      }
  }, []);

  // Fetch arbitrage opportunities on component mount and refresh
  useEffect(() => {
    loadOpportunities();
    
    // Refresh every 3 minutes
    const refreshInterval = setInterval(loadOpportunities, 60000); // 1 minute to match SGO's update frequency
    
    return () => clearInterval(refreshInterval);
  }, [loadOpportunities]);

  // Save arbitrage opportunity to profile
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
        notes: `Saved from ArbitrageFinder - ${opportunity.market_type || 'Unknown Market'}`
      };

      await axios.post('/api/my-arbitrage', arbitrageData, {
        headers: { 
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });

      toast.success(`Arbitrage opportunity saved: ${opportunity.home_team} vs ${opportunity.away_team}`);
      
    } catch (error) {
      console.error('Error saving arbitrage opportunity:', error);
        toast.error('Failed to save arbitrage opportunity. Please try again.');
    }
  };

  // Load user preferences from localStorage
  const loadUserPreferences = () => {
    try {
      const storedPrefs = localStorage.getItem('userPreferences');
      if (storedPrefs) {
        const prefs = JSON.parse(storedPrefs);
        // Load user preferences
        setSelectedSports(prefs.preferred_sports || []); // Load preferred sports
        setSelectedBookmakers(prefs.preferred_bookmakers || []); // Load preferred bookmakers
        setMinProfit(prefs.minimum_profit_threshold || 0.1); // Load minimum profit
        console.log('Loaded user preferences:', prefs);
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  };

  // Filter opportunities based on active tab and filters
  const getFilteredOpportunities = () => {
    console.log('Raw opportunities:', arbitrageOpportunities.length);
    console.log('Sample opportunity:', arbitrageOpportunities[0]);
    console.log('Current filters:', {
      selectedSports: selectedSports.length,
      selectedBookmakers: selectedBookmakers.length,
      minProfit: minProfit,
      sortBy: sortBy
    });
    
    let filtered = arbitrageOpportunities;
    console.log('After initial load:', filtered.length);

    // Require at least 2 bookmakers selected for arbitrage to work
    if (selectedBookmakers.length < 2) {
      console.log('Less than 2 bookmakers selected, showing no opportunities');
      return [];
    }

    // Filter out LIVE games - they should only appear in Live Odds tab
    filtered = filtered.filter(opp => {
      const isLive = opp.game_type === 'LIVE' || 
                    opp.status === 'live' || 
                    opp.status === 'LIVE' ||
                    opp.is_live === true ||
                    opp.game_status === 'live' ||
                    opp.game_status === 'LIVE';
      return !isLive; // Exclude live games from arbitrage tab
    });

    // Filter by sports (currently disabled for debugging)
    console.log('DEBUG: Sports filter disabled to show all opportunities');

    // Filter by bookmakers
    if (selectedBookmakers.length > 0) {
      const beforeBookmakers = filtered.length;
      filtered = filtered.filter(opp => {
        const bookmakers = opp.bookmakers_involved || [];
        // Check if any of the opportunity's bookmakers match our selected ones
        // Handle both string and object formats for bookmakers
        const matches = bookmakers.some(bm => {
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
        
        if (!matches && bookmakers.length > 0) {
          console.log('Filtered out by bookmakers:', opp.home_team, 'vs', opp.away_team);
        }
        
        return matches;
      });
      console.log('After bookmakers filter:', beforeBookmakers, '->', filtered.length);
    }

    // Filter by minimum profit
    const beforeProfit = filtered.length;
    filtered = filtered.filter(opp => {
      const matches = opp.profit_percentage >= minProfit;
      
      if (!matches) {
        console.log('Filtered out by profit:', opp.home_team, 'vs', opp.away_team, 'profit:', opp.profit_percentage, 'min:', minProfit);
      }
      
      return matches;
    });
    console.log('After profit filter:', beforeProfit, '->', filtered.length);

    // Apply sorting
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

    console.log('Final filtered opportunities:', filtered.length);
    return filtered;
  };

  const filteredOpportunities = getFilteredOpportunities();

  // Load preferences on mount
  useEffect(() => {
    loadUserPreferences();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Arbitrage Opportunities</h1>
          <p className="text-gray-300 text-lg">
            Pre-game arbitrage opportunities
          </p>
          <p className="text-gray-400 text-sm mt-2">
          </p>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
            <h2 className="text-xl font-semibold text-yellow-400 mb-6">Arbitrage Filters</h2>
            
            {/* First Row - Basic Filters */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6">
              {/* Min Profit Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Min Profit %</label>
                <input
                  type="number"
                  min="0"
                  max="50"
                  step="0.1"
                  value={minProfit}
                  onChange={(e) => setMinProfit(parseFloat(e.target.value) || 0)}
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 transition-colors"
                />
              </div>
              {/* Sort By */}
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">Sort By</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 transition-colors"
                >
                  <option value="profit_desc">Highest Profit</option>
                  <option value="profit_asc">Lowest Profit</option>
                  <option value="time_asc">Time (Soonest)</option>
                  <option value="time_desc">Time (Latest)</option>
                </select>
              </div>
            </div>

            {/* Bookmaker Filter - Full Width */}
            <div>
                <label className="block text-lg font-bold text-yellow-400 mb-4">Select Bookmakers</label>
                <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border-2 border-yellow-500 border-opacity-20 p-6 shadow-xl">
                  {/* Action Buttons */}
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
                    <button
                      onClick={() => setSelectedBookmakers([...new Set(SGO_BOOKMAKERS.map(bm => bm.key))])}
                      className="bg-gradient-to-r from-yellow-500 to-yellow-600 text-gray-900 px-4 py-2 rounded-lg font-semibold hover:from-yellow-400 hover:to-yellow-500 transition-all duration-200 shadow-lg hover:shadow-yellow-500"
                    >
                      Select All ({SGO_BOOKMAKERS.length})
                    </button>
                    <button
                      onClick={() => setSelectedBookmakers([])}
                      className="bg-gradient-to-r from-gray-600 to-gray-700 text-white px-4 py-2 rounded-lg font-semibold hover:from-gray-500 hover:to-gray-600 transition-all duration-200 shadow-lg"
                    >
                      Clear All
                    </button>
                    <button
                      onClick={() => setSelectedBookmakers([...new Set([...selectedBookmakers, ...SGO_BOOKMAKERS.filter(bm => bm.region === 'INTL').map(bm => bm.key)])])}
                      className="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-blue-400 hover:to-blue-500 transition-all duration-200 shadow-lg"
                    >
                      Select Intl ({SGO_BOOKMAKERS.filter(bm => bm.region === 'INTL').length})
                    </button>
                    <button
                      onClick={() => setSelectedBookmakers(selectedBookmakers.filter(bm => !SGO_BOOKMAKERS.filter(book => book.region === 'INTL').map(book => book.key).includes(bm)))}
                      className="bg-gradient-to-r from-red-500 to-red-600 text-white px-4 py-2 rounded-lg font-semibold hover:from-red-400 hover:to-red-500 transition-all duration-200 shadow-lg"
                    >
                      Clear Intl
                    </button>
                  </div>
                  
                  {/* Selected Count */}
                  <div className="mb-4">
                    <div className="text-center">
                      <span className="text-white font-bold text-lg">{selectedBookmakers.length}</span>
                      <span className="text-gray-300 ml-2">of {SGO_BOOKMAKERS.length} bookmakers selected</span>
                      <div className="text-sm text-gray-400 mt-1">
                        US: {selectedBookmakers.filter(bm => SGO_BOOKMAKERS.find(book => book.key === bm)?.region === 'US').length}/{SGO_BOOKMAKERS.filter(bm => bm.region === 'US').length} | 
                        Intl: {selectedBookmakers.filter(bm => SGO_BOOKMAKERS.find(book => book.key === bm)?.region === 'INTL').length}/{SGO_BOOKMAKERS.filter(bm => bm.region === 'INTL').length}
                      </div>
                      {selectedBookmakers.length < 2 && (
                        <div className="text-red-400 text-sm mt-1">Select at least 2 bookmakers for arbitrage</div>
                      )}
                    </div>
                  </div>
                  
                  {/* Bookmaker Grid - Organized by Region */}
                  <div className="max-h-96 overflow-y-auto pr-2" style={{scrollbarWidth: 'thin', scrollbarColor: '#eab308 #374151'}}>
                    
                    {/* US Bookmakers */}
                    <div className="mb-6">
                      <h4 className="text-gray-300 font-semibold mb-3 text-sm">US Bookmakers</h4>
                      <div className="grid grid-cols-3 lg:grid-cols-4 gap-3">
                        {SGO_BOOKMAKERS.filter(bookmaker => bookmaker.region === 'US').map(bookmaker => (
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
                            <span className="text-sm font-medium text-gray-200 group-hover:text-yellow-200 transition-colors leading-tight">
                              {bookmaker.name}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                    
                    {/* International Bookmakers */}
                    <div>
                      <h4 className="text-gray-300 font-semibold mb-3 text-sm">International Bookmakers</h4>
                      <div className="grid grid-cols-3 lg:grid-cols-4 gap-3">
                        {SGO_BOOKMAKERS.filter(bookmaker => bookmaker.region === 'INTL').map(bookmaker => (
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
                            <span className="text-sm font-medium text-gray-200 group-hover:text-yellow-200 transition-colors leading-tight">
                              {bookmaker.name}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                    
                  </div>
                </div>
              </div>
            </div>

          </div>
        )}

        {/* Results */}
            <div>

          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">
              Arbitrage Opportunities ({filteredOpportunities.length} found)
            </h2>
            <div className="flex gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                {showFilters && 'Hide Filters'}
                {!showFilters && 'Show Filters'}
              </button>
              <button
                onClick={() => loadOpportunities(true)}
                disabled={loading}
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {loading && 'Loading...'}
                {!loading && 'Refresh'}
              </button>
            </div>
            </div>
            
          {/* Arbitrage Opportunities Display */}
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
                <ArbitrageCard
                  key={`${opportunity.event_id || index}-${opportunity.profit_percentage}`}
                  opportunity={opportunity}
                  onSave={saveOpportunity}
                  userTier={user?.subscription?.tier || 'basic'}
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
      </div>
    </div>
  );
};

export default ArbitrageFinder;
