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
  
  const [showFilters, setShowFilters] = useState(false);
  const [selectedSports, setSelectedSports] = useState([]);
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);
  const [sortBy, setSortBy] = useState('profit_desc');
  const [minProfit, setMinProfit] = useState(0.1);

  useEffect(() => {
    if (selectedBookmakers.length === 0) {
      const defaultBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
      setSelectedBookmakers([...new Set(defaultBookmakers)]);
      console.log('Initialized bookmakers:', defaultBookmakers.length, 'total bookmakers');
    }
  }, []);

  const fetchSGOOpportunities = async (forceRefresh = false) => {
    try {
      console.log('Fetching pre-game arbitrage opportunities from SportsGameOdds API...');
      const response = await axios.get('/api/arbitrage/sgo', {
        params: {
          live_only: false,
          min_profit: 0.5,
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

  const loadOpportunities = useCallback(async (forceRefresh = false) => {
    const cacheKey = 'arbitrage_opportunities';
    const cached = localStorage.getItem(cacheKey);
    const cacheTime = localStorage.getItem(cacheKey + '_time');
    
    if (false && !forceRefresh && cached && cacheTime) {
      const timeDiff = Date.now() - parseInt(cacheTime);
      if (timeDiff < 600000) {
        console.log('Loading opportunities from cache...');
        setArbitrageOpportunities(JSON.parse(cached));
        return;
      }
    }

    try {
      setLoading(true);
      console.log('Loading arbitrage opportunities...');
      
      try {
        const sgoData = await fetchSGOOpportunities(forceRefresh);
        
        if (sgoData.arbitrage_opportunities && sgoData.arbitrage_opportunities.length > 0) {
          console.log('SGO API: Loaded', sgoData.arbitrage_opportunities.length, 'opportunities');
          setArbitrageOpportunities(sgoData.arbitrage_opportunities);
          
          localStorage.setItem(cacheKey, JSON.stringify(sgoData.arbitrage_opportunities));
          localStorage.setItem(cacheKey + '_time', Date.now().toString());
          
          if (sgoData.api_usage) {
            const usageMsg = 'SGO API: ' + sgoData.api_usage.daily_used + '/' + sgoData.api_usage.daily_budget + ' events used today';
            toast.info(usageMsg);
          }
          return;
        } else if (sgoData.data_source === 'rate_limited') {
          console.log('SGO API: Rate limited, trying legacy...');
          toast.info('SGO API rate limited - using cached data');
        }
      } catch (sgoError) {
        console.warn('SGO API failed, falling back to legacy:', sgoError.message);
      }
      
      const legacyOpportunities = await fetchRealOpportunities();
      console.log('Legacy API: Loaded', legacyOpportunities.length, 'opportunities');
      setArbitrageOpportunities(legacyOpportunities);
      
      localStorage.setItem(cacheKey, JSON.stringify(legacyOpportunities));
      localStorage.setItem(cacheKey + '_time', Date.now().toString());
      
    } catch (error) {
      console.error('All APIs failed:', error);
      setArbitrageOpportunities([]);
      toast.error('Failed to load arbitrage opportunities');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOpportunities();
    const refreshInterval = setInterval(loadOpportunities, 60000);
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

      const successMsg = 'Arbitrage opportunity saved: ' + opportunity.home_team + ' vs ' + opportunity.away_team;
      toast.success(successMsg);
      
    } catch (error) {
      console.error('Error saving arbitrage opportunity:', error);
      toast.error('Failed to save arbitrage opportunity. Please try again.');
    }
  };

  const loadUserPreferences = () => {
    try {
      const storedPrefs = localStorage.getItem('userPreferences');
      if (storedPrefs) {
        const prefs = JSON.parse(storedPrefs);
        setSelectedSports(prefs.preferred_sports || []);
        setSelectedBookmakers(prefs.preferred_bookmakers || []);
        setMinProfit(prefs.minimum_profit_threshold || 0.1);
        console.log('Loaded user preferences:', prefs);
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  };

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

    if (selectedBookmakers.length < 2) {
      console.log('Less than 2 bookmakers selected, showing no opportunities');
      return [];
    }

    filtered = filtered.filter(opp => {
      const isLive = opp.game_type === 'LIVE' || 
                    opp.status === 'live' || 
                    opp.status === 'LIVE' ||
                    opp.is_live === true ||
                    opp.game_status === 'live' ||
                    opp.game_status === 'LIVE';
      return !isLive;
    });

    console.log('DEBUG: Sports filter disabled to show all opportunities');

    if (selectedBookmakers.length > 0) {
      const beforeBookmakers = filtered.length;
      filtered = filtered.filter(opp => {
        const bookmakers = opp.bookmakers_involved || [];
        const matches = bookmakers.some(bm => {
          const bookmakerKey = typeof bm === 'string' ? bm.toLowerCase() : bm.key?.toLowerCase();
          const bookmakerName = typeof bm === 'string' ? bm : bm.name;
          
          return selectedBookmakers.some(selected => {
            const selectedLower = selected.toLowerCase();
            const keyMatch = selectedLower === bookmakerKey;
            const nameMatch = selectedLower === bookmakerName?.toLowerCase();
            
            const betfairMatch = (selectedLower === 'betfair_exchange' && bookmakerKey === 'betfairexchange') ||
                                (selectedLower === 'betfairexchange' && bookmakerKey === 'betfair_exchange');
            
            return keyMatch || nameMatch || betfairMatch ||
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

    const beforeProfit = filtered.length;
    filtered = filtered.filter(opp => {
      const matches = opp.profit_percentage >= minProfit;
      
      if (!matches) {
        console.log('Filtered out by profit:', opp.home_team, 'vs', opp.away_team, 'profit:', opp.profit_percentage, 'min:', minProfit);
      }
      
      return matches;
    });
    console.log('After profit filter:', beforeProfit, '->', filtered.length);

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

  useEffect(() => {
    loadUserPreferences();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
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
                className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
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
                  key={opportunity.event_id || index + '-' + opportunity.profit_percentage}
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