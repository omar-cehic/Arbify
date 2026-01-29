import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { toast } from 'react-toastify';
import axios from 'axios';

const ArbitrageFinder = () => {
  const [filters, setFilters] = useState({
    sports: [],
    market: '',
    minProfit: 0.5,
    region: ''
  });
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);
  const [arbitrageOpportunities, setArbitrageOpportunities] = useState([]);
  const [filteredOpportunities, setFilteredOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [oddsFormat, setOddsFormat] = useState('decimal');
  const { user } = useAuth();

  // Fetch real arbitrage opportunities from API
  const fetchRealOpportunities = async () => {
    try {
      console.log('🔍 Fetching real arbitrage opportunities from API...');
      const response = await axios.get('/api/arbitrage');
      console.log('✅ API Response:', response.data);
      
      if (!response.data.arbitrage_opportunities) {
        console.error('❌ Invalid API response - missing arbitrage_opportunities');
        return [];
      }
      
      const realOpportunities = response.data.arbitrage_opportunities || [];
      
      // Transform API data to component format
      const transformedOpportunities = realOpportunities.map((opp, index) => {
        const outcomes = Object.keys(opp.best_odds || {});
        const profitPercentage = opp.profit_percentage || 0;
        const bookmakers = outcomes.map(outcome => 
          opp.best_odds?.[outcome]?.bookmaker || 'Unknown'
        ).filter(b => b !== 'Unknown');
        
        const details = {};
        outcomes.forEach((outcome, idx) => {
          const outcomeData = opp.best_odds?.[outcome] || {};
          const odds = outcomeData.odds || 2.0;
          const bookmaker = outcomeData.bookmaker || 'Unknown';
          const stake = 500; // Simplified stake calculation
          
          details[`outcome${idx + 1}`] = {
            bookmaker: bookmaker,
            odds: odds,
            stake: stake,
            name: outcome,
            market_type: opp.market_key || "h2h"
          };
        });
        
        return {
          id: `${opp.sport_key}_${opp.match.home_team}_${opp.match.away_team}_${index}`,
          match: `${opp.match.home_team} vs ${opp.match.away_team}`,
          sport: opp.sport_title,
          sport_key: opp.sport_key,
          market_key: opp.market_key || "h2h",
          market_name: opp.market_name || "Head to Head",
          profit_percentage: profitPercentage,
          home_team: opp.match.home_team,
          away_team: opp.match.away_team,
          bookmakers: bookmakers,
          details: details
        };
      }).filter(Boolean);

      return transformedOpportunities;
    } catch (error) {
      console.error('❌ Error fetching real opportunities:', error);
      return [];
    }
  };

  // Load opportunities on mount and set up refresh
  useEffect(() => {
    const loadRealOpportunities = async () => {
      try {
        setLoading(true);
        const realOpportunities = await fetchRealOpportunities();
        console.log('🚀 ArbitrageFinder: Loaded', realOpportunities.length, 'real opportunities');
        setArbitrageOpportunities(realOpportunities);
      } catch (error) {
        console.error('❌ ArbitrageFinder: Error loading real opportunities:', error);
        setArbitrageOpportunities([]);
      } finally {
        setLoading(false);
      }
    };

    loadRealOpportunities();
    
    // Refresh every 5 minutes
    const refreshInterval = setInterval(loadRealOpportunities, 300000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  // Filter opportunities based on current settings
  const filterOpportunities = useCallback(() => {
    let filtered = arbitrageOpportunities;

    // Basic filtering requirements
    const hasRequiredFilters = (filters.sports && filters.sports.length > 0) && 
                              (selectedBookmakers && selectedBookmakers.length >= 2);
    
    if (!hasRequiredFilters) {
      console.log('🚨 Filter requirements not met - showing empty results');
      setFilteredOpportunities([]);
      return;
    }

    // Filter by sports
    if (filters.sports && filters.sports.length > 0) {
      filtered = filtered.filter(opp => 
        filters.sports.includes(opp.sport_key)
      );
    }

    // Filter by minimum profit
    if (filters.minProfit && filters.minProfit > 0) {
      filtered = filtered.filter(opp => 
        opp.profit_percentage >= filters.minProfit
      );
    }

    // Filter by bookmakers
    if (selectedBookmakers && selectedBookmakers.length > 0) {
      filtered = filtered.filter(opportunity => {
        const usedBookmakers = opportunity.bookmakers || [];
        return usedBookmakers.some(bookmaker => 
          selectedBookmakers.includes(bookmaker)
        );
      });
    }

    // Sort by profit percentage (highest first)
    filtered.sort((a, b) => b.profit_percentage - a.profit_percentage);

    console.log(`✅ Filtered ${filtered.length} opportunities from ${arbitrageOpportunities.length} total`);
    setFilteredOpportunities(filtered);
  }, [arbitrageOpportunities, filters, selectedBookmakers]);

  // Apply filters whenever dependencies change
  useEffect(() => {
    filterOpportunities();
  }, [filterOpportunities]);

  // Format odds based on user preference
  const formatOdds = (decimalOdds) => {
    if (oddsFormat === 'american') {
      if (!decimalOdds || decimalOdds <= 1) return '+100';
      if (decimalOdds >= 2.0) {
        return '+' + Math.round((decimalOdds - 1) * 100);
      } else {
        return Math.round(-100 / (decimalOdds - 1));
      }
    }
    return decimalOdds.toFixed(2);
  };

  // Sports data
  const allSports = [
    { key: 'soccer_epl', title: 'English Premier League', category: 'Soccer' },
    { key: 'americanfootball_nfl', title: 'NFL', category: 'American Football' },
    { key: 'basketball_nba', title: 'NBA', category: 'Basketball' },
    { key: 'baseball_mlb', title: 'MLB', category: 'Baseball' },
    { key: 'icehockey_nhl', title: 'NHL', category: 'Ice Hockey' },
  ];

  // Bookmakers data
  const allSportsbooks = [
    { key: 'draftkings', title: 'DraftKings', region: 'US' },
    { key: 'fanduel', title: 'FanDuel', region: 'US' },
    { key: 'betmgm', title: 'BetMGM', region: 'US' },
    { key: 'caesars', title: 'Caesars', region: 'US' },
    { key: 'bet365', title: 'Bet365', region: 'UK' },
    { key: 'williamhill', title: 'William Hill', region: 'UK' },
    { key: 'pinnacle', title: 'Pinnacle', region: 'EU' },
    { key: 'unibet', title: 'Unibet', region: 'EU' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Arbitrage Finder</h1>
          <p className="text-gray-300 text-lg">
            Find and capitalize on betting arbitrage opportunities
          </p>
        </div>

        {/* Settings Panel */}
        <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
          <h2 className="text-xl font-semibold text-yellow-400 mb-6">Filter Settings</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Market Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Betting Market</label>
              <select
                value={filters.market}
                onChange={(e) => setFilters(prev => ({ ...prev, market: e.target.value }))}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 transition-colors"
              >
                <option value="">All Markets</option>
                <option value="h2h">Head to Head</option>
                <option value="spreads">Point Spread</option>
                <option value="totals">Over/Under</option>
              </select>
            </div>

            {/* Min Profit Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Min Profit %</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={filters.minProfit}
                onChange={(e) => setFilters(prev => ({ ...prev, minProfit: parseFloat(e.target.value) || 0 }))}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 transition-colors"
              />
            </div>

            {/* Odds Format */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Odds Format</label>
              <div className="flex space-x-2">
                {['decimal', 'american'].map(fmt => (
                  <button
                    key={fmt}
                    onClick={() => setOddsFormat(fmt)}
                    className={`px-4 py-2 rounded border ${oddsFormat === fmt ? 'bg-yellow-400 text-gray-900 border-yellow-400' : 'bg-gray-700 text-white border-gray-600 hover:bg-gray-600'}`}
                    type="button"
                  >
                    {fmt === 'decimal' ? 'Decimal (2.10)' : 'American (+110)'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Sports Selection */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-300">Select Sports</h3>
              <button
                onClick={() => {
                  const allKeys = allSports.map(sport => sport.key);
                  setFilters(prev => ({
                    ...prev,
                    sports: filters.sports.length === allKeys.length ? [] : allKeys
                  }));
                }}
                className="px-4 py-2 rounded-lg font-medium transition-colors bg-green-600 hover:bg-green-700 text-white"
              >
                {filters.sports.length === allSports.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            
            <div className="max-h-60 overflow-y-auto bg-gray-700 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {allSports.map(sport => (
                  <label key={sport.key} className="flex items-center hover:bg-gray-600 rounded p-1 transition-colors">
                    <input
                      type="checkbox"
                      checked={filters.sports.includes(sport.key)}
                      onChange={(e) => {
                        const newSports = e.target.checked 
                          ? [...filters.sports, sport.key]
                          : filters.sports.filter(s => s !== sport.key);
                        setFilters(prev => ({ ...prev, sports: newSports }));
                      }}
                      className="mr-2 h-4 w-4 text-yellow-400 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
                    />
                    <span className="text-sm text-gray-300 hover:text-white cursor-pointer">
                      {sport.title}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Bookmakers Selection */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-300">Select Bookmakers (min 2 required)</h3>
              <button
                onClick={() => {
                  const allKeys = allSportsbooks.map(book => book.key);
                  setSelectedBookmakers(
                    selectedBookmakers.length === allKeys.length ? [] : allKeys
                  );
                }}
                className="px-4 py-2 rounded-lg font-medium transition-colors bg-green-600 hover:bg-green-700 text-white"
              >
                {selectedBookmakers.length === allSportsbooks.length ? 'Deselect All' : 'Select All'}
              </button>
            </div>
            
            <div className="max-h-80 overflow-y-auto bg-gray-700 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {allSportsbooks.map(sportsbook => (
                  <label key={sportsbook.key} className="flex items-center hover:bg-gray-600 rounded p-1 transition-colors">
                    <input
                      type="checkbox"
                      checked={selectedBookmakers.includes(sportsbook.key)}
                      onChange={(e) => {
                        const newBookmakers = e.target.checked 
                          ? [...selectedBookmakers, sportsbook.key]
                          : selectedBookmakers.filter(b => b !== sportsbook.key);
                        setSelectedBookmakers(newBookmakers);
                      }}
                      className="mr-2 h-4 w-4 text-yellow-400 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
                    />
                    <span className="text-sm text-gray-300 hover:text-white cursor-pointer">
                      {sportsbook.title} ({sportsbook.region})
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Status Info */}
        <div className="bg-blue-900 border border-blue-600 rounded-lg p-4 mb-6">
          <div className="text-blue-100 text-sm space-y-1">
            <div><strong>Total Opportunities:</strong> {arbitrageOpportunities.length}</div>
            <div><strong>Filtered Opportunities:</strong> {filteredOpportunities.length}</div>
            <div><strong>Sports Selected:</strong> {filters.sports?.length || 0} sports</div>
            <div><strong>Bookmakers Selected:</strong> {selectedBookmakers?.length || 0} bookmakers</div>
          </div>
        </div>

        {/* Opportunities List */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-yellow-400">
              Found {filteredOpportunities.length} Arbitrage Opportunities
            </h2>
            <div className="text-sm text-gray-400">
              Updated every 5 minutes • {loading ? 'Refreshing...' : 'Live data'}
            </div>
          </div>

          {filteredOpportunities && filteredOpportunities.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredOpportunities.map((opportunity, index) => (
                <div key={`${opportunity.id}-${index}`} className="bg-gray-800 rounded-lg border border-yellow-400/60 hover:border-yellow-400 transition-colors p-4">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <span className="bg-yellow-400 text-black text-xs px-2 py-1 rounded font-bold">
                      {opportunity.profit_percentage.toFixed(2)}% PROFIT
                    </span>
                    <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded font-bold">
                      {opportunity.sport}
                    </span>
                  </div>

                  <div className="bg-green-600 text-white text-sm px-3 py-1 rounded font-bold mb-3">
                    {opportunity.match}
                  </div>

                  <div className="text-center text-yellow-400 font-semibold mb-3">
                    {opportunity.market_name}
                  </div>

                  {/* Betting Options */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {/* Outcome 1 */}
                    <div className="bg-black border border-gray-600 rounded-lg p-3">
                      <div className="text-gray-400 text-xs mb-1">
                        BET 1: {opportunity.details.outcome1?.name || 'Option 1'}
                      </div>
                      <div className="text-white font-bold">
                        {formatOdds(opportunity.details.outcome1?.odds || 2.0)} 
                        <span className="text-gray-400 text-sm ml-1">
                          ({opportunity.details.outcome1?.bookmaker || 'Unknown'})
                        </span>
                      </div>
                      <div className="text-xs text-green-400 mt-1">
                        Stake: {opportunity.details.outcome1?.stake?.toFixed(2) || '500.00'}
                      </div>
                    </div>

                    {/* Outcome 2 */}
                    <div className="bg-black border border-gray-600 rounded-lg p-3">
                      <div className="text-gray-400 text-xs mb-1">
                        BET 2: {opportunity.details.outcome2?.name || 'Option 2'}
                      </div>
                      <div className="text-white font-bold">
                        {formatOdds(opportunity.details.outcome2?.odds || 2.0)} 
                        <span className="text-gray-400 text-sm ml-1">
                          ({opportunity.details.outcome2?.bookmaker || 'Unknown'})
                        </span>
                      </div>
                      <div className="text-xs text-green-400 mt-1">
                        Stake: {opportunity.details.outcome2?.stake?.toFixed(2) || '500.00'}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-2">
                    <button
                      className="bg-gray-700 text-white px-4 py-2 rounded-lg font-bold hover:bg-gray-600 transition-colors disabled:opacity-50 text-sm"
                      onClick={() => toast.info('Save functionality coming soon!')}
                    >
                      Save
                    </button>
                    <button
                      className="bg-yellow-400 text-black px-4 py-2 rounded-lg font-bold hover:bg-yellow-500 transition-colors text-sm"
                      onClick={() => toast.info('Calculator integration coming soon!')}
                    >
                      Calculate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-800 rounded-xl p-12 text-center border border-gray-700">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No Arbitrage Opportunities Found</h3>
              <p className="text-gray-400 mb-4">
                Try adjusting your filters or check back later for new opportunities.
              </p>
              <button
                onClick={() => {
                  setFilters({ sports: [], market: '', minProfit: 0.5, region: '' });
                  setSelectedBookmakers([]);
                }}
                className="bg-yellow-400 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-yellow-500 transition-colors"
              >
                Reset Filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArbitrageFinder;