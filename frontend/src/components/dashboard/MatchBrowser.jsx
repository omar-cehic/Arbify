import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { toast } from 'react-toastify';
import axios from 'axios';

const MatchBrowser = () => {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [detailedOdds, setDetailedOdds] = useState(null);
  const [loadingOdds, setLoadingOdds] = useState(false);
  const [selectedSport, setSelectedSport] = useState('');
  const { user } = useAuth();

  // Available sports for filtering
  const availableSports = [
    { key: 'soccer_epl', title: 'English Premier League' },
    { key: 'americanfootball_nfl', title: 'NFL' },
    { key: 'basketball_nba', title: 'NBA' },
    { key: 'baseball_mlb', title: 'MLB' },
    { key: 'icehockey_nhl', title: 'NHL' }
  ];

  // Fetch match summaries (API efficient)
  const fetchMatches = async (sportKey = null) => {
    try {
      setLoading(true);
      console.log('🔍 Fetching match summaries...', sportKey ? `for ${sportKey}` : 'for all sports');
      
      const params = sportKey ? { sport_key: sportKey } : {};
      const response = await axios.get('/api/matches', { params });
      
      console.log('✅ Match browser response:', response.data);
      setMatches(response.data.matches || []);
      
      toast.success(`Found ${response.data.total_matches} upcoming matches`);
    } catch (error) {
      console.error('❌ Error fetching matches:', error);
      toast.error('Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  // Load detailed odds for a specific match (on-demand)
  const loadMatchOdds = async (matchId) => {
    try {
      setLoadingOdds(true);
      console.log('🔍 Loading detailed odds for match:', matchId);
      
      const response = await axios.get(`/api/matches/${matchId}/odds`);
      console.log('✅ Detailed odds response:', response.data);
      
      setDetailedOdds(response.data.match_odds);
      toast.success('Detailed odds loaded');
    } catch (error) {
      console.error('❌ Error loading detailed odds:', error);
      toast.error('Failed to load detailed odds');
    } finally {
      setLoadingOdds(false);
    }
  };

  // Handle match selection
  const handleMatchSelect = (match) => {
    setSelectedMatch(match);
    setDetailedOdds(null); // Clear previous detailed odds
    if (match && match.id) {
      loadMatchOdds(match.id);
    }
  };

  // Format date/time
  const formatDateTime = (dateString) => {
    if (!dateString) return 'TBD';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return 'Invalid date';
    }
  };

  // Load matches on component mount
  useEffect(() => {
    fetchMatches();
  }, []);

  // Handle sport filter change
  const handleSportChange = (sportKey) => {
    setSelectedSport(sportKey);
    fetchMatches(sportKey || null);
    setSelectedMatch(null);
    setDetailedOdds(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Match Browser</h1>
          <p className="text-gray-300 text-lg">
            Browse upcoming matches and view detailed odds on-demand
          </p>
          <p className="text-gray-400 text-sm mt-2">
            API-efficient design: Match summaries cached for 10 minutes, detailed odds loaded only when requested
          </p>
        </div>

        {/* Sport Filter */}
        <div className="mb-6">
          <div className="flex flex-wrap items-center gap-4">
            <label className="text-gray-300 font-medium">Filter by Sport:</label>
            <select
              value={selectedSport}
              onChange={(e) => handleSportChange(e.target.value)}
              className="bg-gray-700 text-white px-4 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
            >
              <option value="">All Sports</option>
              {availableSports.map(sport => (
                <option key={sport.key} value={sport.key}>
                  {sport.title}
                </option>
              ))}
            </select>
            <button
              onClick={() => fetchMatches(selectedSport || null)}
              disabled={loading}
              className="bg-yellow-400 text-gray-900 px-4 py-2 rounded-lg font-medium hover:bg-yellow-500 transition-colors disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Match List */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-yellow-400 mb-6">
              Upcoming Matches ({matches.length})
            </h2>
            
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto"></div>
                <p className="mt-4 text-gray-400">Loading matches...</p>
              </div>
            ) : matches.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-400">No upcoming matches found</p>
                <button
                  onClick={() => fetchMatches()}
                  className="mt-4 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
                >
                  Try Again
                </button>
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {matches.map((match, index) => (
                  <div
                    key={`${match.id || index}`}
                    onClick={() => handleMatchSelect(match)}
                    className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                      selectedMatch?.id === match.id
                        ? 'border-yellow-400 bg-gray-700'
                        : 'border-gray-600 hover:border-gray-500 bg-gray-750'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h3 className="font-semibold text-white">{match.match_title}</h3>
                        <p className="text-sm text-gray-400">{match.sport_title}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-500">
                          {formatDateTime(match.commence_time)}
                        </p>
                        <p className="text-xs text-green-400">
                          {match.bookmaker_count} bookmakers
                        </p>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                        {match.sport_title}
                      </span>
                      {selectedMatch?.id === match.id && (
                        <span className="text-xs text-yellow-400">
                          Loading odds...
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Detailed Odds Panel */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-yellow-400 mb-6">
              Detailed Odds
            </h2>
            
            {!selectedMatch ? (
              <div className="text-center py-8">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.122 2.122" />
                  </svg>
                </div>
                <p className="text-gray-400">Select a match to view detailed odds</p>
                <p className="text-sm text-gray-500 mt-2">
                  Odds are loaded on-demand to save API quota
                </p>
              </div>
            ) : loadingOdds ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto"></div>
                <p className="mt-4 text-gray-400">Loading detailed odds...</p>
                <p className="text-sm text-gray-500 mt-2">
                  {selectedMatch.match_title}
                </p>
              </div>
            ) : detailedOdds ? (
              <div>
                <div className="mb-4 pb-4 border-b border-gray-700">
                  <h3 className="text-lg font-semibold text-white">{selectedMatch.match_title}</h3>
                  <p className="text-gray-400">{selectedMatch.sport_title}</p>
                  <p className="text-sm text-gray-500">{formatDateTime(selectedMatch.commence_time)}</p>
                </div>
                
                {/* Market availability */}
                <div className="space-y-4">
                  <h4 className="text-md font-medium text-gray-300">Available Markets:</h4>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(detailedOdds.markets || {}).map(([market, info]) => (
                      <div key={market} className="bg-gray-700 p-2 rounded text-center">
                        <div className="text-sm text-white capitalize">{market.replace('_', ' ')}</div>
                        <div className={`text-xs ${info.available ? 'text-green-400' : 'text-red-400'}`}>
                          {info.available ? 'Available' : 'Not Available'}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-6 p-4 bg-blue-900 border border-blue-700 rounded-lg">
                    <p className="text-blue-200 text-sm">
                      <strong>💡 Coming Soon:</strong> Full odds display, arbitrage detection, 
                      and comparison tools for selected matches.
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-red-400">Failed to load detailed odds</p>
                <button
                  onClick={() => selectedMatch && handleMatchSelect(selectedMatch)}
                  className="mt-2 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
                >
                  Retry
                </button>
              </div>
            )}
          </div>
        </div>

        {/* API Usage Info */}
        <div className="mt-8 bg-green-900 border border-green-700 rounded-xl p-6">
          <h3 className="text-green-200 font-semibold mb-2">📊 API-Efficient Design</h3>
          <div className="text-green-100 text-sm space-y-1">
            <p><strong>Match Summaries:</strong> Cached for 10 minutes • Low API usage</p>
            <p><strong>Detailed Odds:</strong> Loaded only on-demand • 2-minute cache</p>
            <p><strong>Cost Impact:</strong> ~80% less API calls vs showing all odds</p>
            <p><strong>User Experience:</strong> Fast browsing + detailed info when needed</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatchBrowser;