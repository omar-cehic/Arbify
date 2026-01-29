import React, { useState, useEffect } from 'react';
import { SGO_BOOKMAKERS } from '../../constants/sgoConstants';

const mockLeagues = [
  {
    id: "epl",
    name: "English Premier League",
    matches: [
      {
        id: "match1",
        homeTeam: "Arsenal",
        awayTeam: "Manchester United",
        date: "5/22/2025",
        time: "2:00:00 PM",
        outcomes: [
          { name: "Arsenal", odds: { FanDuel: 2.86, DraftKings: 2.89, BetMGM: 2.85 } },
          { name: "Manchester United", odds: { FanDuel: 3.71, DraftKings: 3.72, BetMGM: 3.70 } },
          { name: "Draw", odds: { FanDuel: 2.78, DraftKings: 2.83, BetMGM: 2.80 } }
        ]
      },
      {
        id: "match2",
        homeTeam: "Liverpool",
        awayTeam: "Manchester City",
        date: "5/18/2025",
        time: "6:00:00 PM",
        outcomes: [
          { name: "Liverpool", odds: { FanDuel: 2.94, DraftKings: 2.92, BetMGM: 2.90 } },
          { name: "Manchester City", odds: { FanDuel: 3.90, DraftKings: 3.93, BetMGM: 3.80 } },
          { name: "Draw", odds: { FanDuel: 2.79, DraftKings: 2.74, BetMGM: 2.70 } }
        ]
      },
      {
        id: "match3",
        homeTeam: "Chelsea",
        awayTeam: "Tottenham",
        date: "5/18/2025",
        time: "7:30:00 PM",
        outcomes: [
          { name: "Chelsea", odds: { FanDuel: 2.40, DraftKings: 2.39, BetMGM: 2.39 } },
          { name: "Tottenham", odds: { FanDuel: 3.60, DraftKings: 3.61, BetMGM: 3.59 } },
          { name: "Draw", odds: { FanDuel: 3.36, DraftKings: 3.31, BetMGM: 3.33 } }
        ]
      },
      {
        id: "match4",
        homeTeam: "Newcastle",
        awayTeam: "Aston Villa",
        date: "5/24/2025",
        time: "7:00:00 PM",
        outcomes: [
          { name: "Newcastle", odds: { FanDuel: 3.01, DraftKings: 3.00, BetMGM: 2.99 } },
          { name: "Aston Villa", odds: { FanDuel: 3.14, DraftKings: 3.10, BetMGM: 3.07 } },
          { name: "Draw", odds: { FanDuel: 3.37, DraftKings: 3.37, BetMGM: 3.42, highlight: true } }
        ]
      },
      {
        id: "match5",
        homeTeam: "Brighton",
        awayTeam: "West Ham",
        date: "5/19/2025",
        time: "8:00:00 PM",
        outcomes: [
          { name: "Brighton", odds: { FanDuel: 2.28, DraftKings: 2.30, BetMGM: 2.33 } },
          { name: "West Ham", odds: { FanDuel: 3.82, DraftKings: 3.77, BetMGM: 3.77 } },
          { name: "Draw", odds: { FanDuel: 3.40, DraftKings: 3.44, BetMGM: 3.38, highlight: true } }
        ]
      }
    ]
  },
  {
    id: "ucl",
    name: "UEFA Champions League",
    matches: [
      {
        id: "match6",
        homeTeam: "Real Madrid",
        awayTeam: "Bayern Munich",
        date: "5/25/2025",
        time: "8:00:00 PM",
        outcomes: [
          { name: "Real Madrid", odds: { FanDuel: 2.10, DraftKings: 2.15, BetMGM: 2.12 } },
          { name: "Bayern Munich", odds: { FanDuel: 3.40, DraftKings: 3.35, BetMGM: 3.38 } },
          { name: "Draw", odds: { FanDuel: 3.50, DraftKings: 3.55, BetMGM: 3.52 } }
        ]
      },
      {
        id: "match7",
        homeTeam: "PSG",
        awayTeam: "Barcelona",
        date: "5/26/2025",
        time: "9:00:00 PM",
        outcomes: [
          { name: "PSG", odds: { FanDuel: 2.30, DraftKings: 2.25, BetMGM: 2.28 } },
          { name: "Barcelona", odds: { FanDuel: 3.10, DraftKings: 3.15, BetMGM: 3.12 } },
          { name: "Draw", odds: { FanDuel: 3.30, DraftKings: 3.35, BetMGM: 3.32 } }
        ]
      }
    ]
  }
];

const OddsTab = ({ loading: parentLoading }) => {
  const [leagues, setLeagues] = useState(mockLeagues);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [showFilters, setShowFilters] = useState(false);
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);

  // Load user preferences on component mount
  const loadUserPreferences = () => {
    try {
      const storedPrefs = localStorage.getItem('userPreferences');
      if (storedPrefs) {
        const prefs = JSON.parse(storedPrefs);
        if (prefs.preferred_bookmakers && prefs.preferred_bookmakers.length > 0) {
          setSelectedBookmakers(prefs.preferred_bookmakers);
          return;
        }
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
    
    // Fallback to all bookmakers if no preferences found
    const defaultBookmakers = SGO_BOOKMAKERS.map(bm => bm.key);
    setSelectedBookmakers([...new Set(defaultBookmakers)]);
  };

  useEffect(() => {
    loadUserPreferences();
  }, []);

  const handleRefresh = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLastUpdated(new Date());
      setLoading(false);
    }, 1000);
  };

  const getBestOdds = (outcomes) => {
    return outcomes.map(outcome => {
      const odds = outcome.odds;
      const bookmakers = Object.keys(odds);
      const bestBookmaker = bookmakers.reduce((best, current) => 
        odds[current] > odds[best] ? current : best, bookmakers[0]);
      
      return {
        ...outcome,
        bestOdds: odds[bestBookmaker],
        bestBookmaker
      };
    });
  };

  if (loading || parentLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
        <span className="ml-3 text-gray-400">Loading odds...</span>
      </div>
    );
  }

  return (
    <div className="space-y-12">
      {/* Comprehensive Filter System */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-yellow-400">Live Odds Filters</h3>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors flex items-center"
          >
            <i className={`fas fa-chevron-${showFilters ? 'up' : 'down'} mr-2`}></i>
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>

        {showFilters && (
          <div>
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
      </div>

      {leagues.map(league => (
        <div key={league.id} className="league-section">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-2xl font-bold text-yellow-400">{league.name}</h3>
            <div className="flex items-center text-sm text-gray-400">
              <i className="far fa-clock mr-2"></i>
              Last updated: {lastUpdated.toLocaleTimeString()}
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {league.matches.map(match => (
              <div key={match.id} className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700 hover:border-yellow-400 transition-all shadow-lg">
                <div className="flex justify-between items-center p-4 border-b border-gray-700">
                  <div>
                    <h4 className="text-lg font-semibold text-white">
                      {match.homeTeam} <span className="text-gray-400">vs</span> {match.awayTeam}
                    </h4>
                  </div>
                  <div className="text-sm text-gray-400">
                    <i className="far fa-calendar-alt mr-1"></i>
                    {match.date}, {match.time}
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="grid grid-cols-4 gap-2 text-sm mb-2">
                    <div className="font-medium text-gray-300">Outcome</div>
                    <div className="text-center font-medium text-gray-300">FanDuel</div>
                    <div className="text-center font-medium text-gray-300">DraftKings</div>
                    <div className="text-center font-medium text-gray-300">BetMGM</div>
                  </div>
                  
                  {match.outcomes.map((outcome, i) => {
                    // Find best odds for this outcome
                    const bookmakers = Object.keys(outcome.odds);
                    const bestBookmaker = bookmakers.reduce((best, current) => 
                      outcome.odds[current] > outcome.odds[best] ? current : best, bookmakers[0]);
                    
                    return (
                      <div key={i} className="grid grid-cols-4 gap-2 text-sm py-2 border-b border-gray-700 last:border-0">
                        <div className="font-medium text-white">{outcome.name}</div>
                        
                        {bookmakers.map(bookmaker => {
                          const isHighlighted = bookmaker === bestBookmaker || outcome.highlight;
                          return (
                            <div 
                              key={bookmaker} 
                              className={`text-center ${isHighlighted ? 'bg-yellow-400 text-gray-900 font-bold rounded' : 'text-gray-200'}`}
                            >
                              {outcome.odds[bookmaker].toFixed(2)}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
                
                <div className="p-2">
                  <input 
                    type="range" 
                    className="w-full" 
                    min="0" 
                    max="100" 
                    defaultValue="50" 
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Floating refresh button */}
      <button
        onClick={handleRefresh}
        className="fixed bottom-8 right-8 z-10 bg-yellow-400 text-gray-900 p-3 rounded-full shadow-lg hover:bg-yellow-500 transition-colors"
        title="Refresh Odds"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>
  );
};

export default OddsTab;