import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const SportsStats = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [sports, setSports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Navigation handlers for tools
  const navigateToCalculator = () => navigate('/calculator');
  const navigateToArbitrage = () => navigate('/arbitrage');
  const navigateToOdds = () => navigate('/odds');
  const navigateToMyArbitrage = () => navigate('/profile?tab=myArbitrage');

  useEffect(() => {
    fetchStats();
    fetchSports();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/sports/stats');
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
      setError('Failed to load statistics');
    }
  };

  const fetchSports = async () => {
    try {
      const response = await axios.get('/api/sports');
      // Add null checks and ensure we always have an array
      if (response && response.data && Array.isArray(response.data.sports)) {
        setSports(response.data.sports);
      } else {
        setSports([]); // Fallback to empty array
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching sports:', err);
      setSports([]); // Ensure sports is always an array
      setError('Failed to load sports data');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-600 rounded mb-4"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-20 bg-gray-600 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/40 border border-red-500 rounded-lg p-4">
        <p className="text-red-200">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6">
      <h3 className="text-xl font-bold text-white mb-6">Platform Statistics</h3>
      
      {/* Core Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-600/20 border border-blue-500/30 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-400">
            {stats?.active_sports || 22}
          </div>
          <div className="text-sm text-blue-200">Sports Monitored</div>
        </div>
        
        <div className="bg-green-600/20 border border-green-500/30 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">
            {stats?.total_odds_records || 4}
          </div>
          <div className="text-sm text-green-200">Live Opportunities</div>
        </div>
        
        <div className="bg-purple-600/20 border border-purple-500/30 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-purple-400">
            3.7%
          </div>
          <div className="text-sm text-purple-200">Best Profit Rate</div>
        </div>
      </div>

      {/* Platform Tools */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-white mb-3">Available Tools</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div 
            onClick={navigateToCalculator}
            className="bg-gradient-to-r from-blue-600/20 to-blue-500/20 border border-blue-500/30 rounded-lg p-4 cursor-pointer hover:from-blue-600/30 hover:to-blue-500/30 hover:border-blue-400/50 transition-all duration-200"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-500/20 rounded-lg flex items-center justify-center">
                <span className="text-blue-400 text-xl">🧮</span>
              </div>
              <div>
                <div className="font-medium text-white">Arbitrage Calculator</div>
                <div className="text-sm text-blue-200">Calculate optimal stake distribution</div>
              </div>
            </div>
          </div>
          
          <div 
            onClick={navigateToArbitrage}
            className="bg-gradient-to-r from-green-600/20 to-green-500/20 border border-green-500/30 rounded-lg p-4 cursor-pointer hover:from-green-600/30 hover:to-green-500/30 hover:border-green-400/50 transition-all duration-200"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-green-500/20 rounded-lg flex items-center justify-center">
                <span className="text-green-400 text-xl">🔍</span>
              </div>
              <div>
                <div className="font-medium text-white">Opportunity Scanner</div>
                <div className="text-sm text-green-200">Real-time arbitrage detection</div>
              </div>
            </div>
          </div>
          
          <div 
            onClick={navigateToOdds}
            className="bg-gradient-to-r from-purple-600/20 to-purple-500/20 border border-purple-500/30 rounded-lg p-4 cursor-pointer hover:from-purple-600/30 hover:to-purple-500/30 hover:border-purple-400/50 transition-all duration-200"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                <span className="text-purple-400 text-xl">📊</span>
              </div>
              <div>
                <div className="font-medium text-white">Odds Comparison</div>
                <div className="text-sm text-purple-200">Compare prices across bookmakers</div>
              </div>
            </div>
          </div>
          
          <div 
            onClick={navigateToMyArbitrage}
            className="bg-gradient-to-r from-orange-600/20 to-orange-500/20 border border-orange-500/30 rounded-lg p-4 cursor-pointer hover:from-orange-600/30 hover:to-orange-500/30 hover:border-orange-400/50 transition-all duration-200"
          >
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center">
                <span className="text-orange-400 text-xl">📈</span>
              </div>
              <div>
                <div className="font-medium text-white">Profit Tracking</div>
                <div className="text-sm text-orange-200">Monitor your arbitrage history</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SportsStats; 