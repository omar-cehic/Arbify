import React, { useState } from 'react';
import ArbitrageModal from '../common/Modal';

const ArbitrageTab = ({ opportunities, currentSort, onSortChange, loading }) => {
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const openModal = (opp) => {
    setSelectedOpp(opp);
    setShowModal(true);
  };
  const closeModal = () => {
    setShowModal(false);
    setSelectedOpp(null);
  };

  const generateArbGrid = (opportunity) => {
    // Enhanced: handle the new data structure with detailed market information
    let oddsArray = [];
    
    if (opportunity.best_odds && typeof opportunity.best_odds === 'object') {
      // New enhanced structure - extract all outcome data
      oddsArray = Object.entries(opportunity.best_odds)
        .filter(([key, value]) => typeof value === 'object' && value.bookmaker && value.odds)
        .map(([outcomeKey, outcomeData]) => {
          // Format outcome name with market details
          let displayName = outcomeKey;
          
          // Enhanced display for spreads and totals
          if (outcomeData.point_value !== null && outcomeData.point_value !== undefined) {
            const pointValue = parseFloat(outcomeData.point_value);
            
            if (opportunity.market_key && opportunity.market_key.includes('spread')) {
              // For spreads, show the team with the spread
              if (pointValue > 0) {
                displayName = `${displayName} +${pointValue}`;
              } else {
                displayName = `${displayName} ${pointValue}`;
              }
            } else if (opportunity.market_key && opportunity.market_key.includes('total')) {
              // For totals, show Over/Under with the line
              if (displayName.toLowerCase().includes('over')) {
                displayName = `Over ${pointValue}`;
              } else if (displayName.toLowerCase().includes('under')) {
                displayName = `Under ${pointValue}`;
              } else {
                displayName = `${displayName} ${pointValue}`;
              }
            }
          }
          
          return {
            outcome: displayName,
            price: parseFloat(outcomeData.odds).toFixed(2),
            bookmaker: outcomeData.bookmaker,
            pointValue: outcomeData.point_value,
            marketType: outcomeData.market_type
          };
        });
    }
    
    // Fallback to legacy structure if new structure not available
    if (!oddsArray.length && opportunity.best_odds) {
      oddsArray = Object.entries(opportunity.best_odds)
        .filter(([key]) => ['home', 'away', 'draw'].includes(key) || key.endsWith('_bookmaker'))
        .map(([key, value]) => {
          if (key.endsWith('_bookmaker')) return null;
          return {
            outcome: key.charAt(0).toUpperCase() + key.slice(1),
            price: parseFloat(value).toFixed(2),
            bookmaker: opportunity.best_odds[`${key}_bookmaker`] || '',
            pointValue: null,
            marketType: opportunity.market_key
          };
        })
        .filter(Boolean);
    }
    
    if (!oddsArray.length) {
      return <div className="text-gray-400">No odds data available.</div>;
    }
    
    return (
      <div className="space-y-3">
        {/* Market Type Header */}
        {opportunity.market_name && (
          <div className="text-center text-sm font-medium text-yellow-400 bg-gray-700/30 rounded-lg py-2 px-3">
            📊 {opportunity.market_name}
          </div>
        )}
        
        {/* Odds Grid */}
        <div className="grid grid-cols-2 gap-3">
          {oddsArray.map((odds, index) => (
            <div key={index} className="bg-gray-700/50 rounded-lg p-4 border border-gray-600 hover:border-yellow-400/50 transition-colors">
              <div className="text-xs font-medium text-gray-400 mb-1">{odds.bookmaker}</div>
              <div className="flex flex-col">
                <span className="font-medium text-white text-sm mb-1">{odds.outcome}</span>
                <div className="flex justify-between items-center">
                  <span className="text-yellow-400 font-bold text-lg">{odds.price}</span>
                  {odds.pointValue !== null && odds.pointValue !== undefined && (
                    <span className="text-xs text-blue-400 bg-blue-400/20 px-2 py-1 rounded">
                      {odds.pointValue > 0 ? `+${odds.pointValue}` : odds.pointValue}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Additional Market Info */}
        <div className="flex justify-between items-center text-xs text-gray-500 bg-gray-800/30 rounded px-3 py-2">
          <span>💰 {opportunity.profit_percentage.toFixed(2)}% guaranteed profit</span>
          <span>🎯 {oddsArray.length} outcomes</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
        <span className="ml-3 text-gray-400">Loading opportunities...</span>
      </div>
    );
  }

  if (!opportunities || opportunities.length === 0) {
    return (
      <div className="bg-gray-700/50 rounded-lg p-8 text-center border border-gray-600">
        <div className="text-gray-400 mb-4">
          <i className="fas fa-search text-4xl"></i>
        </div>
        <p className="text-gray-300 text-lg">No arbitrage opportunities found. Try refreshing or adjusting your filters.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-2xl font-bold text-yellow-400">Arbitrage Opportunities</h3>
        <select 
          className="bg-gray-700 text-white rounded-lg px-4 py-2 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-yellow-400/20 focus:border-yellow-400 transition-colors"
          value={currentSort}
          onChange={onSortChange}
        >
          <option value="profitDesc">Highest Profit</option>
          <option value="profitAsc">Lowest Profit</option>
          <option value="timeAsc">Earliest First</option>
          <option value="timeDesc">Latest First</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {opportunities.map((opp, index) => (
          <div 
            key={index} 
            className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-yellow-400 transition-colors shadow-lg"
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h5 className="text-lg font-semibold text-white">
                  {opp.match.home_team} vs {opp.match.away_team}
                </h5>
                <span className="bg-green-500/20 text-green-400 px-3 py-1 rounded-full text-sm font-medium border border-green-500/30">
                  {opp.profit_percentage.toFixed(2)}% Profit
                </span>
              </div>
              <p className="text-gray-400 mb-4 flex items-center">
                <i className="far fa-calendar-alt mr-2"></i>
                {new Date(opp.match.commence_time).toLocaleString()}
              </p>
              <div className="mb-6">
                {generateArbGrid(opp)}
              </div>
              <button 
                className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
                onClick={() => openModal(opp)}
              >
                <i className="fas fa-calculator mr-2"></i>
                Calculate Stakes
              </button>
            </div>
          </div>
        ))}
      </div>
      {showModal && selectedOpp && (
        <ArbitrageModal show={showModal} onClose={closeModal} opportunity={selectedOpp} />
      )}
    </div>
  );
};

export default ArbitrageTab;