import { useState } from 'react';

const ArbitrageModal = ({ show, onClose, opportunity }) => {
  const [totalStake, setTotalStake] = useState('100');
  const [result, setResult] = useState(null);

  if (!show || !opportunity) return null;

  const calculateBets = () => {
    const stake = parseFloat(totalStake);
    
    if (isNaN(stake) || stake <= 0) {
      setResult({
        type: 'error',
        message: 'Please enter a valid stake amount.'
      });
      return;
    }
    
    const isDraw = opportunity.outcomes === 3;
    const probHome = 1 / opportunity.best_odds.home;
    const probAway = 1 / opportunity.best_odds.away;
    const probDraw = isDraw ? 1 / opportunity.best_odds.draw : 0;
    
    const totalProb = probHome + probAway + probDraw;
    
    // Calculate stakes
    const stakeHome = (stake * probHome) / totalProb;
    const stakeAway = (stake * probAway) / totalProb;
    const stakeDraw = isDraw ? (stake * probDraw) / totalProb : 0;
    
    // Calculate guaranteed profit
    const guaranteedReturn = stake / totalProb;
    const guaranteedProfit = guaranteedReturn - stake;
    
    setResult({
      type: 'success',
      stakes: {
        home: stakeHome,
        away: stakeAway,
        draw: stakeDraw
      },
      totalStake: stake,
      guaranteedReturn,
      guaranteedProfit,
      roi: (guaranteedProfit / stake) * 100
    });
  };

  const generateBookmakerLink = (bookmakerName) => {
    const BOOKMAKER_URLS = {
      "FanDuel": "https://sportsbook.fanduel.com/",
      "DraftKings": "https://sportsbook.draftkings.com/",
      "BetMGM": "https://sports.betmgm.com/",
      "Caesars": "https://www.caesars.com/sportsbook-and-casino",
      "PointsBet": "https://pointsbet.com/",
      "BetRivers": "https://betrivers.com/",
      "Bovada": "https://www.bovada.lv/sports",
      "LowVig.ag": "https://lowvig.ag/",
      "BetUS": "https://www.betus.com.pa/"
    };
    
    return BOOKMAKER_URLS[bookmakerName] || '#';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="border-b border-gray-700 p-4">
          <div className="flex justify-between items-center">
            <h5 className="text-lg font-medium text-white">
              Bet Calculator: {opportunity.match.home_team} vs {opportunity.match.away_team}
            </h5>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white"
            >
              <i className="fas fa-xmark"></i>
            </button>
          </div>
        </div>
        
        <div className="p-4">
          <div className="mb-4 bg-gray-700 rounded-lg p-4">
            <h6 className="text-white font-medium mb-2">
              Arbitrage Opportunity: {opportunity.profit_percentage.toFixed(2)}% profit
            </h6>
            
            {/* Market Information */}
            {opportunity.market_name && (
              <div className="mb-3 text-center">
                <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-sm">
                  📊 {opportunity.market_name}
                </span>
              </div>
            )}
            
            {/* Enhanced odds display */}
            <div className="space-y-2">
              {Object.entries(opportunity.best_odds).map(([outcomeKey, outcomeData], index) => {
                // Skip if this is the legacy bookmaker format or not a proper outcome
                if (typeof outcomeData !== 'object' || !outcomeData.bookmaker || !outcomeData.odds) {
                  return null;
                }
                
                // Format outcome name with market details
                let displayName = outcomeKey;
                if (outcomeData.point_value !== null && outcomeData.point_value !== undefined) {
                  const pointValue = parseFloat(outcomeData.point_value);
                  
                  if (opportunity.market_key && opportunity.market_key.includes('spread')) {
                    if (pointValue > 0) {
                      displayName = `${displayName} +${pointValue}`;
                    } else {
                      displayName = `${displayName} ${pointValue}`;
                    }
                  } else if (opportunity.market_key && opportunity.market_key.includes('total')) {
                    if (displayName.toLowerCase().includes('over')) {
                      displayName = `Over ${pointValue}`;
                    } else if (displayName.toLowerCase().includes('under')) {
                      displayName = `Under ${pointValue}`;
                    } else {
                      displayName = `${displayName} ${pointValue}`;
                    }
                  }
                }
                
                return (
                  <div key={index} className="bg-gray-600 rounded p-3 flex justify-between items-center">
                    <div>
                      <div className="text-sm font-medium text-white">{displayName}</div>
                      <div className="text-xs text-gray-400">{outcomeData.bookmaker}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-yellow-400">{parseFloat(outcomeData.odds).toFixed(2)}</div>
                      {outcomeData.point_value !== null && outcomeData.point_value !== undefined && (
                        <div className="text-xs text-blue-400">
                          Line: {outcomeData.point_value > 0 ? `+${outcomeData.point_value}` : outcomeData.point_value}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Fallback to legacy display if new structure not available */}
            {!Object.values(opportunity.best_odds).some(val => typeof val === 'object' && val.bookmaker) && (
              <div className={`grid ${opportunity.outcomes === 3 ? 'grid-cols-3' : 'grid-cols-2'} gap-2`}>
                <div className="bg-gray-600 rounded p-2 text-center">
                  <div className="text-sm text-gray-300">Home</div>
                  <div className="text-lg font-bold text-yellow-400">{opportunity.best_odds.home?.toFixed(2)}</div>
                  <div className="text-xs text-gray-400">{opportunity.best_odds.home_bookmaker}</div>
                </div>
                
                {opportunity.outcomes === 3 && (
                  <div className="bg-gray-600 rounded p-2 text-center">
                    <div className="text-sm text-gray-300">Draw</div>
                    <div className="text-lg font-bold text-yellow-400">{opportunity.best_odds.draw?.toFixed(2)}</div>
                    <div className="text-xs text-gray-400">{opportunity.best_odds.draw_bookmaker}</div>
                  </div>
                )}
                
                <div className="bg-gray-600 rounded p-2 text-center">
                  <div className="text-sm text-gray-300">Away</div>
                  <div className="text-lg font-bold text-yellow-400">{opportunity.best_odds.away?.toFixed(2)}</div>
                  <div className="text-xs text-gray-400">{opportunity.best_odds.away_bookmaker}</div>
                </div>
              </div>
            )}
          </div>
          
          <form onSubmit={(e) => { e.preventDefault(); calculateBets(); }}>
            <div className="mb-4">
              <label className="block text-yellow-400 text-sm font-medium mb-2">
                Total Stake ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={totalStake}
                onChange={(e) => setTotalStake(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 text-white rounded-md border border-gray-600 focus:border-yellow-400 focus:outline-none"
                placeholder="Enter total stake"
                required
              />
            </div>
            
            <button type="submit" className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold py-2 px-4 rounded-lg transition-colors">
              Calculate Bet Distribution
            </button>
          </form>
          
          {result && (
            <div className="mt-4">
              {result.type === 'error' ? (
                <div className="bg-red-900 border border-red-700 rounded-md p-3">
                  <p className="text-white text-sm">{result.message}</p>
                </div>
              ) : (
                <div className="bg-gray-700 rounded-lg p-4">
                  <h5 className="text-white font-medium mb-3">Bet Distribution</h5>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-medium">Home ({opportunity.best_odds.home_bookmaker}):</span>
                        <span className="ml-2">${result.stakes.home.toFixed(2)}</span>
                      </div>
                      <a
                        href={generateBookmakerLink(opportunity.best_odds.home_bookmaker)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-yellow-400 border border-yellow-400 hover:bg-yellow-400 hover:text-gray-900 text-xs px-2 py-1 rounded transition-colors"
                      >
                        <i className="fas fa-external-link-alt mr-1"></i>
                        Bet Now
                      </a>
                    </div>
                    
                    {opportunity.outcomes === 3 && (
                      <div className="flex justify-between items-center">
                        <div>
                          <span className="font-medium">Draw ({opportunity.best_odds.draw_bookmaker}):</span>
                          <span className="ml-2">${result.stakes.draw.toFixed(2)}</span>
                        </div>
                        <a
                          href={generateBookmakerLink(opportunity.best_odds.draw_bookmaker)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-yellow-400 border border-yellow-400 hover:bg-yellow-400 hover:text-gray-900 text-xs px-2 py-1 rounded transition-colors"
                        >
                          <i className="fas fa-external-link-alt mr-1"></i>
                          Bet Now
                        </a>
                      </div>
                    )}
                    
                    <div className="flex justify-between items-center">
                      <div>
                        <span className="font-medium">Away ({opportunity.best_odds.away_bookmaker}):</span>
                        <span className="ml-2">${result.stakes.away.toFixed(2)}</span>
                      </div>
                      <a
                        href={generateBookmakerLink(opportunity.best_odds.away_bookmaker)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-yellow-400 border border-yellow-400 hover:bg-yellow-400 hover:text-gray-900 text-xs px-2 py-1 rounded transition-colors"
                      >
                        <i className="fas fa-external-link-alt mr-1"></i>
                        Bet Now
                      </a>
                    </div>
                  </div>
                  
                  <hr className="border-gray-600 my-3" />
                  
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="font-medium">Total Investment:</span>
                      <span>${result.totalStake.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Guaranteed Return:</span>
                      <span>${result.guaranteedReturn.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Guaranteed Profit:</span>
                      <span className="text-green-400">${result.guaranteedProfit.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">ROI:</span>
                      <span className="text-green-400">{result.roi.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArbitrageModal;