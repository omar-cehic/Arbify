import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';

const ArbitrageCard = ({ opportunity, onSave, userTier }) => {
  const [expanded, setExpanded] = useState(false);
  const [calculatedStake, setCalculatedStake] = useState(100);
  const [isSaved, setIsSaved] = useState(false);
  const navigate = useNavigate();

  const handleSave = () => {
    if (onSave) {
      onSave(opportunity);
      setIsSaved(true);
      toast.success('Arbitrage saved successfully!');
    }
  };

  // Format time until match starts with live status
  const formatTimeUntilMatch = (commence_time, game_type) => {
    if (!commence_time) return 'Time TBD';

    try {
      const matchDate = new Date(commence_time);
      const now = new Date();
      const diffHours = (matchDate - now) / (1000 * 60 * 60);

      // Check if it's a live game
      if (game_type === 'LIVE' || diffHours < 0) {
        return 'LIVE';
      }

      if (diffHours < 1) return `${Math.round(diffHours * 60)}m`;
      if (diffHours < 24) return `${Math.round(diffHours)}h`;

      return matchDate.toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      });
    } catch {
      return 'Time TBD';
    }
  };

  // Get sport abbreviation for the yellow pill
  const getSportAbbreviation = (sport, league) => {
    if (sport === 'BASEBALL') return 'MLB';
    if (sport === 'FOOTBALL') {
      if (league === 'NFL') return 'NFL';
      if (league === 'NCAAF') return 'NCAAF';
      return 'NFL';
    }
    if (sport === 'BASKETBALL') {
      if (league === 'NBA') return 'NBA';
      if (league === 'WNBA') return 'WNBA';
      return 'NBA';
    }
    return sport.substring(0, 4);
  };

  // Get team name for betting boxes
  const getTeamName = (side, home_team, away_team, team_name) => {
    // Use team_name if provided (from new backend structure)
    if (team_name) return team_name;

    // Fallback to side-based logic
    if (side === 'home' || side === 'side1') return home_team;
    if (side === 'away' || side === 'side2') return away_team;
    return side;
  };

  // Get betting instruction text based on market type and side  
  const getBettingInstruction = (side, sideData, marketType, marketDescription) => {
    const line = sideData?.line;

    // For player props, show "Over/Under X.X [Stat Name]" 
    if (marketType?.includes('player_') || marketDescription?.includes('Total Bases') ||
      marketDescription?.includes('Hits') || marketDescription?.includes('Singles') ||
      marketDescription?.includes('Home Runs') || marketDescription?.includes('RBI') ||
      marketDescription?.includes('Strikeouts') || marketDescription?.includes('Doubles') ||
      marketDescription?.includes('Triples')) {

      // Extract stat name from market description (e.g., "Jackson Merrill Total Bases" -> "Total Bases")
      const words = marketDescription?.split(' ') || [];
      const statName = words.length >= 2 ? words.slice(-2).join(' ') : 'Stat';

      if (side?.toLowerCase().includes('over') && line) {
        return `Over ${line} ${statName}`;
      } else if (side?.toLowerCase().includes('under') && line) {
        return `Under ${line} ${statName}`;
      }
    }

    // For team-based markets, show team + line if available
    const teamName = getTeamName(side, opportunity.home_team, opportunity.away_team, sideData?.team_name);

    if (line && line !== '0') {
      if (marketType?.includes('spread') || marketType?.includes('sp')) {
        return `${teamName} ${line > 0 ? '+' : ''}${line}`;
      } else if (marketType?.includes('total') || marketType?.includes('ou')) {
        if (side?.toLowerCase().includes('over')) {
          return `Over ${line}`;
        } else if (side?.toLowerCase().includes('under')) {
          return `Under ${line}`;
        }
        return `${teamName} ${line}`;
      }
    }

    return teamName;
  };

  // Get market type description with specific details
  const getMarketDescription = (marketType, oddsData, side1, side2) => {
    // Debug logging to see what data we have
    console.log('Market Description Debug:', {
      marketType,
      side1: side1,
      side2: side2,
      oddsData: oddsData
    });

    // Check for specific line information in multiple places
    const line1 = side1?.line || side1?.handicap || side1?.point;
    const line2 = side2?.line || side2?.handicap || side2?.point;
    const marketLine = oddsData?.line || oddsData?.handicap || oddsData?.point;

    // Use the most specific line available
    const line = line1 || line2 || marketLine;

    console.log('Line extraction:', { line1, line2, marketLine, finalLine: line });

    // Try to use market description from backend first
    if (opportunity?.market_description) {
      console.log('🎯 Using backend market description:', opportunity.market_description);
      return opportunity.market_description;
    } else if (opportunity?.detailed_market_description) {
      console.log('🎯 Using backend detailed description:', opportunity.detailed_market_description);
      return opportunity.detailed_market_description;
    } else {
      console.log('⚠️ No backend market description available for opportunity:', opportunity?.id);
    }

    // Fallback: Try to extract detailed market info from the opportunity ID or market data
    const opportunityId = opportunity?.id || '';
    const detailedInfo = parseDetailedMarketInfo(opportunityId, marketType, line);

    if (detailedInfo) {
      return detailedInfo;
    }

    // Standard market descriptions
    if (marketType === 'spread' && line) {
      return `Spread ${line > 0 ? '+' : ''}${line}`;
    }

    if (marketType === 'totals' && line) {
      return `Over/Under ${line}`;
    }

    if (marketType === 'lead_after_innings' && line) {
      return `Lead After ${line} Innings`;
    }

    // Check for specific market descriptions
    if (side1?.side === 'Over' && side2?.side === 'Under' && line) {
      return `Over/Under ${line}`;
    }

    if (side1?.side === 'Over' && line) {
      return `Over/Under ${line}`;
    }

    // Fallback: If no line is available, show generic market type
    if (marketType === 'totals' && !line) {
      return 'Over/Under (Line TBD)';
    }

    if (marketType === 'spread' && !line) {
      return 'Point Spread (Line TBD)';
    }

    const marketNames = {
      'moneyline': 'Moneyline',
      'spread': 'Point Spread',
      'totals': 'Over/Under',
      'moneyline_3way': '3-Way Moneyline'
    };
    return marketNames[marketType] || marketType;
  };

  // Parse detailed market information from SGO odd_id patterns
  const parseDetailedMarketInfo = (opportunityId, marketType, line) => {
    if (!opportunityId) return null;

    // Extract stat type and period from opportunity ID
    const statTypeMap = {
      'points': 'Points',
      'receiving_receptions': 'Receptions',
      'receiving_yards': 'Receiving Yards',
      'rushing_yards': 'Rushing Yards',
      'rushing_attempts': 'Rushing Attempts',
      'touchdowns': 'Touchdowns',
      'passing_yards': 'Passing Yards',
      'passing_touchdowns': 'Passing TDs',
      'interceptions': 'Interceptions',
      'fumbles': 'Fumbles',
      'turnovers': 'Turnovers',
      'firstBasket': 'First Basket',
      'doubleDouble': 'Double-Double',
      'tripleDouble': 'Triple-Double',
      'assists': 'Assists',
      'rebounds': 'Rebounds',
      'steals': 'Steals',
      'blocks': 'Blocks',
      'batting_hits': 'Hits',
      'batting_homeRuns': 'Home Runs',
      'batting_RBI': 'RBI',
      'batting_stolenBases': 'Stolen Bases',
      'batting_strikeouts': 'Strikeouts',
      'batting_basesOnBalls': 'Walks',
      'batting_singles': 'Singles',
      'batting_doubles': 'Doubles',
      'batting_triples': 'Triples',
      'batting_totalBases': 'Total Bases',
      'batting_hits+runs+rbi': 'Hits + Runs + RBI',
      'extraPoints_kicksMade': 'Extra Points Made',
      'kicking_totalPoints': 'Kicking Points',
      'games': 'Games'
    };

    const periodMap = {
      'game': 'Game',
      '1h': '1st Half',
      '2h': '2nd Half',
      '1q': '1st Quarter',
      '2q': '2nd Quarter',
      '3q': '3rd Quarter',
      '4q': '4th Quarter',
      '1i': '1st Inning',
      '2i': '2nd Inning',
      '3i': '3rd Inning',
      '4i': '4th Inning',
      '5i': '5th Inning',
      '6i': '6th Inning',
      '7i': '7th Inning',
      '8i': '8th Inning',
      '9i': '9th Inning',
      '1ix7': '1st 7 Innings',
      'reg': 'Regulation'
    };

    // Try to extract stat type and period from the opportunity ID
    let statType = null;
    let period = 'Game';

    // Look for stat type patterns
    for (const [key, value] of Object.entries(statTypeMap)) {
      if (opportunityId.includes(key)) {
        statType = value;
        break;
      }
    }

    // Look for period patterns
    for (const [key, value] of Object.entries(periodMap)) {
      if (opportunityId.includes(`-${key}-`) || opportunityId.includes(`_${key}_`)) {
        period = value;
        break;
      }
    }

    // Build detailed description
    if (statType) {
      if (marketType === 'totals' && line) {
        return `${statType} Over/Under ${line} (${period})`;
      } else if (marketType === 'spread' && line) {
        return `${statType} Spread ${line > 0 ? '+' : ''}${line} (${period})`;
      } else if (marketType === 'moneyline') {
        return `${statType} (${period})`;
      } else if (marketType === 'yn' || marketType === 'yes_no') {
        return `${statType} Yes/No (${period})`;
      } else {
        return `${statType} (${period})`;
      }
    }

    return null;
  };

  // Calculate bet amounts for custom stake
  const calculateBetAmounts = (totalStake) => {
    if (!opportunity.best_odds) return {};

    const amounts = {};
    const outcomes = Object.keys(opportunity.best_odds);

    // Calculate total inverse odds
    let totalInverseOdds = 0;
    outcomes.forEach(outcome => {
      const odds = opportunity.best_odds[outcome]?.odds || 0;
      if (odds > 0) totalInverseOdds += 1 / odds;
    });

    // Calculate individual bet amounts
    outcomes.forEach(outcome => {
      const odds = opportunity.best_odds[outcome]?.odds || 0;
      if (odds > 0) {
        amounts[outcome] = (totalStake / totalInverseOdds) / odds;
      }
    });

    return amounts;
  };

  const betAmounts = calculateBetAmounts(calculatedStake);
  const guaranteedProfit = calculatedStake * (opportunity.profit_percentage / 100);

  // Get market display name
  const getMarketDisplayName = (marketType) => {
    const names = {
      'moneyline': 'Moneyline (Winner)',
      'spread': 'Point Spread',
      'totals': 'Over/Under (Total Points)',
      'moneyline_3way': '3-Way Moneyline'
    };
    return names[marketType] || marketType;
  };

  // Get outcome display name
  const getOutcomeDisplayName = (outcome, marketType) => {
    if (marketType === 'totals') {
      return outcome === 'over' ? 'Over' : 'Under';
    }
    if (marketType === 'moneyline_3way' && outcome === 'draw') {
      return 'Draw';
    }
    return outcome.charAt(0).toUpperCase() + outcome.slice(1);
  };

  // Navigate to calculator with pre-populated data
  const navigateToCalculator = () => {
    // Debug log to see the opportunity structure
    console.log('🔍 Calculator Debug - Full opportunity:', opportunity);
    console.log('🔍 Calculator Debug - Best odds:', opportunity.best_odds);

    // Extract odds data from the opportunity
    const oddsData = opportunity.best_odds || {};

    // Build query parameters for the calculator
    const params = new URLSearchParams();

    // Handle different data structures
    let side1, side2;

    // Check if we have side1/side2 structure
    if (oddsData.side1 && oddsData.side2) {
      side1 = oddsData.side1;
      side2 = oddsData.side2;
    } else {
      // Handle key-based structure (like 'over', 'under', 'home', 'away')
      const outcomes = Object.keys(oddsData);
      if (outcomes.length >= 2) {
        side1 = oddsData[outcomes[0]];
        side2 = oddsData[outcomes[1]];
      }
    }

    console.log('🔍 Calculator Debug - Side1:', side1);
    console.log('🔍 Calculator Debug - Side2:', side2);

    if (side1?.odds && side2?.odds) {
      params.append('homeOdds', side1.odds.toString());
      params.append('awayOdds', side2.odds.toString());

      // Add labels for better UX
      const side1Label = `${getTeamName(side1?.side || 'side1', opportunity.home_team, opportunity.away_team, side1?.team_name)} (${side1?.bookmaker || 'Unknown'})`;
      const side2Label = `${getTeamName(side2?.side || 'side2', opportunity.home_team, opportunity.away_team, side2?.team_name)} (${side2?.bookmaker || 'Unknown'})`;

      params.append('homeLabel', side1Label);
      params.append('awayLabel', side2Label);

      console.log('🔍 Calculator Debug - Params will be:', params.toString());
    } else {
      console.warn('⚠️ Calculator Debug - No valid odds found in opportunity');
      toast.error('Unable to extract odds data from this opportunity');
      return;
    }

    // Add match information
    params.append('matchup', `${opportunity.home_team} vs ${opportunity.away_team}`);
    params.append('sport', opportunity.sport || opportunity.sport_title || 'Unknown');
    params.append('league', opportunity.league || '');

    // Prefer detailed market description if available for clarity
    const marketDesc = opportunity.detailed_market_description ||
      opportunity.market_description ||
      getMarketDescription(opportunity.market_type, oddsData, side1, side2);

    params.append('market', marketDesc);
    params.append('expectedProfit', opportunity.profit_percentage.toFixed(2));

    // Navigate to calculator with pre-populated data
    const calculatorUrl = `/calculator?${params.toString()}`;
    console.log('🔍 Calculator Debug - Final URL:', calculatorUrl);
    navigate(calculatorUrl);

    // Show success message
    toast.success('Redirecting to calculator with opportunity details...');
  };

  // Copy bet instructions to clipboard
  const copyBetInstructions = () => {
    const instructions = Object.entries(opportunity.best_odds || {}).map(([outcome, data]) => {
      const amount = betAmounts[outcome] || 0;
      return `${data.bookmaker}: Bet $${amount.toFixed(2)} on ${getOutcomeDisplayName(outcome, opportunity.market_type)} @ ${data.odds}`;
    }).join('\n');

    const fullInstructions = `🎯 ARBITRAGE OPPORTUNITY
${opportunity.home_team} vs ${opportunity.away_team}
Market: ${getMarketDisplayName(opportunity.market_type)}
Profit: ${opportunity.profit_percentage.toFixed(2)}%

BETTING INSTRUCTIONS:
${instructions}

Total Stake: $${calculatedStake}
Profit: $${guaranteedProfit.toFixed(2)}`;

    navigator.clipboard.writeText(fullInstructions);
    toast.success('Betting instructions copied to clipboard!');
  };

  // Handle both old and new data structures
  const oddsData = opportunity.best_odds || {};
  const side1Data = oddsData.side1 || {};
  const side2Data = oddsData.side2 || {};

  // Fallback for old data structure
  const outcomes = Object.keys(oddsData);
  const side1Fallback = outcomes.length > 0 ? oddsData[outcomes[0]] : {};
  const side2Fallback = outcomes.length > 1 ? oddsData[outcomes[1]] : {};

  const side1 = side1Data.bookmaker ? side1Data : side1Fallback;
  const side2 = side2Data.bookmaker ? side2Data : side2Fallback;

  return (
    <div className="bg-gray-900 rounded-lg border-2 border-yellow-400 p-4 hover:border-yellow-300 transition-colors">
      {/* Header with Yellow Sport Pill and Green Profit Pill */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-2">
          <span className="bg-yellow-400 text-black text-xs px-2 py-1 rounded font-bold">
            {getSportAbbreviation(opportunity.sport, opportunity.league)}
          </span>
        </div>
        <div className="bg-green-600 text-white text-sm px-3 py-1 rounded font-bold">
          {opportunity.profit_percentage.toFixed(2)}% Profit
        </div>
      </div>

      {/* Matchup Title */}
      <h3 className="text-lg font-bold text-white mb-4">
        {opportunity.home_team} vs {opportunity.away_team}
      </h3>

      {/* Two Dark Betting Boxes */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Side 1 Box */}
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
          <div className="text-sm font-medium text-white mb-1">
            {getTeamName(side1.side || 'side1', opportunity.home_team, opportunity.away_team, side1.team_name)}
          </div>
          <div className="text-xl font-bold text-yellow-400 mb-1">
            {side1.american_odds || side1.odds || 'N/A'}
          </div>
          <div className="text-xs text-gray-400">
            ({side1.bookmaker || 'Unknown'})
          </div>
          {side1.line && side1.line !== '0' && (
            <div className="text-xs text-blue-400 mt-1">
              Line: {side1.line > 0 ? '+' : ''}{side1.line}
            </div>
          )}
        </div>

        {/* Side 2 Box */}
        <div className="bg-gray-800 rounded-lg p-3 border border-gray-600">
          <div className="text-sm font-medium text-white mb-1">
            {getTeamName(side2.side || 'side2', opportunity.home_team, opportunity.away_team, side2.team_name)}
          </div>
          <div className="text-xl font-bold text-yellow-400 mb-1">
            {side2.american_odds || side2.odds || 'N/A'}
          </div>
          <div className="text-xs text-gray-400">
            ({side2.bookmaker || 'Unknown'})
          </div>
          {side2.line && side2.line !== '0' && (
            <div className="text-xs text-blue-400 mt-1">
              Line: {side2.line > 0 ? '+' : ''}{side2.line}
            </div>
          )}
        </div>
      </div>

      {/* Market Type and Time */}
      <div className="text-center text-gray-400 text-sm mb-4">
        {getMarketDescription(opportunity.market_type, oddsData, side1, side2)} • {formatTimeUntilMatch(opportunity.start_time || opportunity.commence_time, opportunity.game_type)}
      </div>

      {/* Action Buttons - Save and Calculate */}
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={isSaved}
          className={`flex-1 px-4 py-2 rounded text-sm font-medium transition-colors ${isSaved
            ? 'bg-green-600 text-white cursor-default'
            : 'bg-gray-600 hover:bg-gray-700 text-white'
            }`}
        >
          {isSaved ? 'Saved' : 'Save'}
        </button>

        <button
          onClick={navigateToCalculator}
          className="flex-1 bg-yellow-400 hover:bg-yellow-500 text-black px-4 py-2 rounded text-sm font-bold transition-colors"
        >
          Calculate
        </button>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-gray-700">
          {/* Stake Calculator */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Total Stake Amount ($)
            </label>
            <input
              type="number"
              value={calculatedStake}
              onChange={(e) => setCalculatedStake(Number(e.target.value) || 100)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              min="1"
              max="10000"
            />
            <div className="text-sm text-green-400 mt-1">
              Profit: ${guaranteedProfit.toFixed(2)}
            </div>
          </div>

          {/* Detailed Betting Instructions */}
          <div className="space-y-3">
            <h4 className="font-semibold text-white">🎯 Where to Place Your Bets:</h4>

            {/* Side 1 Instructions */}
            <div className="bg-gray-700/30 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-medium text-white">
                    Step 1: Go to {side1.bookmaker || 'Unknown Bookmaker'}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    Find: <span className="text-yellow-400 font-medium">
                      {opportunity.home_team} vs {opportunity.away_team}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300">
                    Bet on: <span className="text-blue-400 font-medium">
                      {getBettingInstruction(side1.side || 'side1', side1, opportunity.market_type, opportunity.market_description)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    💡 Look for: {getMarketDescription(opportunity.market_type, oddsData, side1, side2)}
                    {side1.line && side1.line !== '0' && (
                      <span> • Line: {side1.line > 0 ? '+' : ''}{side1.line}</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-400">
                    ${calculatedStake.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-400">
                    @ {side1.odds || side1.american_odds || 'N/A'}
                  </div>
                </div>
              </div>
            </div>

            {/* Side 2 Instructions */}
            <div className="bg-gray-700/30 rounded-lg p-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-medium text-white">
                    Step 2: Go to {side2.bookmaker || 'Unknown Bookmaker'}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    Find: <span className="text-yellow-400 font-medium">
                      {opportunity.home_team} vs {opportunity.away_team}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300">
                    Bet on: <span className="text-blue-400 font-medium">
                      {getBettingInstruction(side2.side || 'side2', side2, opportunity.market_type, opportunity.market_description)}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    💡 Look for: {getMarketDescription(opportunity.market_type, oddsData, side1, side2)}
                    {side2.line && side2.line !== '0' && (
                      <span> • Line: {side2.line > 0 ? '+' : ''}{side2.line}</span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold text-green-400">
                    ${calculatedStake.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-400">
                    @ {side2.odds || side2.american_odds || 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Profit Breakdown */}
          <div className="mt-4 p-3 bg-green-900/20 rounded-lg border border-green-600/30">
            <div className="text-sm text-green-400 font-medium">Profit Breakdown:</div>
            <div className="text-sm text-gray-300 mt-1">
              • Total Stake: ${calculatedStake.toFixed(2)}
            </div>
            <div className="text-sm text-gray-300">
              • Total Return: ${(calculatedStake + guaranteedProfit).toFixed(2)}
            </div>
            <div className="text-sm text-green-400 font-bold">
              • Pure Profit: ${guaranteedProfit.toFixed(2)} ({opportunity.profit_percentage.toFixed(2)}%)
            </div>
          </div>

          {/* Important Notes */}
          <div className="mt-4 p-3 bg-yellow-900/20 rounded-lg border border-yellow-600/30">
            <div className="text-sm text-yellow-400 font-medium">⚠️ Important Notes:</div>
            <ul className="text-xs text-gray-300 mt-1 space-y-1">
              <li>• Place all bets quickly - odds can change rapidly</li>
              <li>• Ensure you have accounts at all required bookmakers</li>
              <li>• Double-check odds before placing bets</li>
              <li>• This is risk-free profit regardless of game outcome</li>
              {userTier === 'basic' && (
                <li className="text-orange-400">• Upgrade to Premium for unlimited opportunities</li>
              )}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArbitrageCard;

