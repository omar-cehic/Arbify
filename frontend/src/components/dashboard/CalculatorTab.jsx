import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

const CalculatorTab = () => {
  const [searchParams] = useSearchParams();
  const [totalStake, setTotalStake] = useState('100');
  const [homeOdds, setHomeOdds] = useState('2.82');
  const [awayOdds, setAwayOdds] = useState('3.17');
  const [drawOdds, setDrawOdds] = useState('3.49');
  const [result, setResult] = useState(null);
  const [opportunityInfo, setOpportunityInfo] = useState(null);

  // Load data from URL parameters when component mounts
  useEffect(() => {
    const homeOddsParam = searchParams.get('homeOdds');
    const awayOddsParam = searchParams.get('awayOdds');
    const drawOddsParam = searchParams.get('drawOdds');
    const matchup = searchParams.get('matchup');
    const sport = searchParams.get('sport');
    const market = searchParams.get('market');
    const expectedProfit = searchParams.get('expectedProfit');
    const homeLabel = searchParams.get('homeLabel');
    const awayLabel = searchParams.get('awayLabel');

    if (homeOddsParam) setHomeOdds(homeOddsParam);
    if (awayOddsParam) setAwayOdds(awayOddsParam);
    if (drawOddsParam) setDrawOdds(drawOddsParam);

    // Store opportunity info for display
    if (matchup || sport || market) {
      setOpportunityInfo({
        matchup,
        sport,
        market,
        expectedProfit,
        homeLabel,
        awayLabel
      });
    }
  }, [searchParams]);

  // Convert decimal odds to American odds for display
  const decimalToAmerican = (decimal) => {
    if (!decimal || decimal <= 1) return '+100';
    
    const odds = parseFloat(decimal);
    if (odds >= 2) {
      return `+${Math.round((odds - 1) * 100)}`;
    } else {
      return `-${Math.round(100 / (odds - 1))}`;
    }
  };

  // Get betting instruction text for calculator
  const getBettingInstructionText = (label, market) => {
    if (!label) return 'Option';
    
    const labelText = label.split('(')[0]?.trim() || label;
    
    // For player props, use the full market description which includes player name
    if (market?.includes('player_') || market?.includes('Total Bases') || 
        market?.includes('Hits') || market?.includes('Singles') ||
        market?.includes('Home Runs') || market?.includes('RBI')) {
      
      // If label contains Over/Under info, use it directly
      if (labelText.toLowerCase().includes('over') || labelText.toLowerCase().includes('under')) {
        return labelText;
      }
      
      // Use the full market description (e.g., "Jackson Merrill Total Bases")
      const fullDescription = market || 'Player Stat';
      
      // Try to determine Over/Under from label context
      if (labelText.toLowerCase().includes('yes') || labelText.toLowerCase().includes('positive')) {
        return `Over ${fullDescription}`;
      } else if (labelText.toLowerCase().includes('no') || labelText.toLowerCase().includes('negative')) {
        return `Under ${fullDescription}`;
      }
    }
    
    return labelText;
  };

  const calculateArbitrage = (e) => {
    e.preventDefault();
    
    const stake = parseFloat(totalStake);
    const home = parseFloat(homeOdds);
    const away = parseFloat(awayOdds);
    const draw = parseFloat(drawOdds) || 0;
    
    // Validate inputs
    if (isNaN(stake) || stake <= 0 || isNaN(home) || home <= 1 || isNaN(away) || away <= 1) {
      setResult({
        type: 'error',
        message: 'Please enter valid values. Odds must be greater than 1 and stake must be positive.'
      });
      return;
    }
    
    // Determine if it's a 2-way or 3-way market
    const isDraw = !isNaN(draw) && draw > 1;
    
    // Calculate implied probabilities
    const probHome = 1 / home;
    const probAway = 1 / away;
    const probDraw = isDraw ? 1 / draw : 0;
    
    const totalProb = probHome + probAway + probDraw;
    
    // Check if arbitrage exists
    if (totalProb >= 1) {
      setResult({
        type: 'warning',
        message: `No arbitrage opportunity. Total implied probability: ${(totalProb * 100).toFixed(2)}%${totalProb > 1 ? " (greater than 100%)" : ""}`
      });
      return;
    }
    
    // Calculate profits and stakes
    const profit = ((1 / totalProb) - 1) * 100;
    
    // Calculate stakes
    const stakeHome = (stake * probHome) / totalProb;
    const stakeAway = (stake * probAway) / totalProb;
    const stakeDraw = isDraw ? (stake * probDraw) / totalProb : 0;
    
    // Calculate guaranteed return
    const guaranteedReturn = stake / totalProb;
    const guaranteedProfit = guaranteedReturn - stake;
    
    setResult({
      type: 'success',
      profit: profit,
      stakes: {
        home: stakeHome,
        away: stakeAway,
        draw: stakeDraw
      },
      odds: { home, away, draw: isDraw ? draw : null },
      totalStake: stake,
      guaranteedReturn,
      guaranteedProfit,
      roi: (guaranteedProfit / stake) * 100
    });
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Opportunity Info Banner */}
      {opportunityInfo && (
        <div className="bg-gradient-to-r from-yellow-600/20 to-yellow-500/20 border border-yellow-500/30 rounded-xl p-6 mb-6">
          <div className="text-center">
            <h2 className="text-xl font-bold text-white mb-2">{opportunityInfo.matchup}</h2>
            <div className="flex items-center justify-center gap-4 text-sm text-gray-300">
              {opportunityInfo.sport && (
                <span className="bg-yellow-400/20 text-yellow-300 px-2 py-1 rounded">
                  {opportunityInfo.sport}
                </span>
              )}
              {opportunityInfo.market && (
                <span className="text-gray-300">{opportunityInfo.market}</span>
              )}
              {opportunityInfo.expectedProfit && (
                <span className="bg-green-600/20 text-green-300 px-2 py-1 rounded font-medium">
                  Expected: {opportunityInfo.expectedProfit}% profit
                </span>
              )}
            </div>
            <p className="text-sm text-gray-400 mt-2">
              Pre-populated from arbitrage opportunity. Verify odds before placing bets.
            </p>
          </div>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 shadow-lg">
        <div className="text-center mb-8">
          <h3 className="text-2xl font-bold text-yellow-400">Arbitrage Calculator</h3>
          <p className="text-gray-400 mt-2">Calculate optimal stakes for arbitrage opportunities</p>
        </div>
        
        <form onSubmit={calculateArbitrage} className="space-y-6">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Total Stake ($)
            </label>
            <input
              type="number"
              step="0.01"
              value={totalStake}
              onChange={(e) => setTotalStake(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter total stake"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              {opportunityInfo?.homeLabel || 'Home Odds'}
            </label>
            <input
              type="number"
              step="0.01"
              value={homeOdds}
              onChange={(e) => setHomeOdds(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter home odds"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              {opportunityInfo?.awayLabel || 'Away Odds'}
            </label>
            <input
              type="number"
              step="0.01"
              value={awayOdds}
              onChange={(e) => setAwayOdds(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter away odds"
              required
            />
          </div>
          
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Draw Odds (optional for 3-way markets)
            </label>
            <input
              type="number"
              step="0.01"
              value={drawOdds}
              onChange={(e) => setDrawOdds(e.target.value)}
              className="w-full px-4 py-3 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 focus:outline-none transition-colors"
              placeholder="Enter draw odds"
            />
          </div>
          
          <button 
            type="submit" 
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
          >
            <i className="fas fa-calculator mr-2"></i>
            Calculate Stakes
          </button>
        </form>
      </div>
      
      {/* Results */}
      {result && (
        <div className="mt-8">
          {result.type === 'error' || result.type === 'warning' ? (
            <div className={`p-6 rounded-lg ${
              result.type === 'error' ? 'bg-red-900/50 border border-red-700' : 'bg-yellow-900/50 border border-yellow-700'
            }`}>
              <div className="flex items-center">
                <i className={`fas ${result.type === 'error' ? 'fa-exclamation-circle text-red-400' : 'fa-exclamation-triangle text-yellow-400'} mr-3 text-xl`}></i>
                <p className="text-white">{result.message}</p>
              </div>
            </div>
          ) : (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 shadow-lg">
              <div className="bg-green-900/50 border border-green-700 rounded-lg p-6 mb-8">
                <div className="flex items-center justify-between">
                  <h5 className="text-xl font-bold text-white">
                    Arbitrage Found
                  </h5>
                  <span className="text-2xl font-bold text-green-400">
                    {result.profit.toFixed(2)}% profit
                  </span>
                </div>
              </div>
              
              <div className="mb-8">
                <h5 className="text-lg font-semibold text-yellow-400 mb-4">Bet Distribution</h5>
                <div className="space-y-3">
                  <div className="flex justify-between items-center bg-gray-700/50 rounded-lg p-4 border border-gray-600">
                    <span className="text-gray-300">Home ({result.odds.home.toFixed(2)})</span>
                    <span className="font-medium text-white">${result.stakes.home.toFixed(2)}</span>
                  </div>
                  
                  {result.odds.draw && (
                    <div className="flex justify-between items-center bg-gray-700/50 rounded-lg p-4 border border-gray-600">
                      <span className="text-gray-300">Draw ({result.odds.draw.toFixed(2)})</span>
                      <span className="font-medium text-white">${result.stakes.draw.toFixed(2)}</span>
                    </div>
                  )}
                  
                  <div className="flex justify-between items-center bg-gray-700/50 rounded-lg p-4 border border-gray-600">
                    <span className="text-gray-300">Away ({result.odds.away.toFixed(2)})</span>
                    <span className="font-medium text-white">${result.stakes.away.toFixed(2)}</span>
                  </div>
                </div>
              </div>
              
              {/* Step-by-Step Betting Instructions */}
              {opportunityInfo && (
                <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-6 mb-6">
                  <h5 className="text-lg font-semibold text-blue-300 mb-4 flex items-center">
                    <i className="fas fa-list-ol mr-2"></i>
                    Step-by-Step Betting Instructions
                  </h5>
                  <div className="space-y-4">
                    <div className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-yellow-400">
                      <div className="flex items-start">
                        <span className="bg-yellow-400 text-gray-900 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">1</span>
                        <div className="flex-1">
                          <p className="text-white font-medium">
                            Go to <span className="text-yellow-400">{opportunityInfo.homeLabel?.split('(')[1]?.replace(')', '') || 'First Bookmaker'}</span>
                          </p>
                          <p className="text-gray-300 text-sm mt-1">
                            Find: <span className="font-medium">{opportunityInfo.matchup}</span>
                          </p>
                          <p className="text-gray-300 text-sm">
                            Place <span className="text-green-400 font-bold">${result.stakes.home.toFixed(2)}</span> on <span className="text-blue-400 font-medium">{getBettingInstructionText(opportunityInfo.homeLabel, opportunityInfo.market)}</span>
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            Market: {opportunityInfo.market} • Expected odds: {decimalToAmerican(result.odds.home)}
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-blue-400">
                      <div className="flex items-start">
                        <span className="bg-blue-400 text-gray-900 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">2</span>
                        <div className="flex-1">
                          <p className="text-white font-medium">
                            Go to <span className="text-blue-400">{opportunityInfo.awayLabel?.split('(')[1]?.replace(')', '') || 'Second Bookmaker'}</span>
                          </p>
                          <p className="text-gray-300 text-sm mt-1">
                            Find: <span className="font-medium">{opportunityInfo.matchup}</span>
                          </p>
                          <p className="text-gray-300 text-sm">
                            Place <span className="text-green-400 font-bold">${result.stakes.away.toFixed(2)}</span> on <span className="text-blue-400 font-medium">{getBettingInstructionText(opportunityInfo.awayLabel, opportunityInfo.market)}</span>
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            Market: {opportunityInfo.market} • Expected odds: {decimalToAmerican(result.odds.away)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {result.odds.draw && (
                      <div className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-purple-400">
                        <div className="flex items-start">
                          <span className="bg-purple-400 text-gray-900 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">3</span>
                          <div className="flex-1">
                            <p className="text-white font-medium">
                              Go to <span className="text-purple-400">Draw Bookmaker</span>
                            </p>
                            <p className="text-gray-300 text-sm mt-1">
                              Find: <span className="font-medium">{opportunityInfo.matchup}</span>
                            </p>
                            <p className="text-gray-300 text-sm">
                              Place <span className="text-green-400 font-bold">${result.stakes.draw.toFixed(2)}</span> on <span className="text-purple-400 font-medium">Draw</span>
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              Market: {opportunityInfo.market} • Expected odds: {decimalToAmerican(result.odds.draw)}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="bg-gray-700/50 rounded-lg p-4 border-l-4 border-green-400">
                      <div className="flex items-start">
                        <span className="bg-green-400 text-gray-900 rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold mr-3 mt-0.5">{result.odds.draw ? '4' : '3'}</span>
                        <div className="flex-1">
                          <p className="text-white font-medium">Verify and Double-Check</p>
                          <ul className="text-gray-300 text-sm mt-1 space-y-1">
                            <li>• Confirm all odds match the expected values above</li>
                            <li>• Ensure bet amounts are exactly as calculated</li>
                            <li>• Verify you're betting on the correct market/line</li>
                            <li>• Place all bets as quickly as possible</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-4">
                      <div className="flex items-center justify-center">
                        <div className="text-center">
                          <p className="text-green-400 font-bold text-lg">Guaranteed Profit: ${result.guaranteedProfit.toFixed(2)}</p>
                          <p className="text-gray-300 text-sm">Regardless of game outcome</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="bg-gray-700/50 rounded-lg p-6 space-y-4 border border-gray-600">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Total Investment</span>
                  <span className="font-medium text-white">${result.totalStake.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Guaranteed Return</span>
                  <span className="font-medium text-white">${result.guaranteedReturn.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Guaranteed Profit</span>
                  <span className="font-medium text-green-400">${result.guaranteedProfit.toFixed(2)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">ROI</span>
                  <span className="font-medium text-green-400">{result.roi.toFixed(2)}%</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CalculatorTab;