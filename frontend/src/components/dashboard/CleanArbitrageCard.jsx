import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { generateCleanCardData } from '../../utils/sgoDataUtils';

/**
 * Clean, minimal arbitrage card focusing on essential information
 * Follows the design: SportIcon League | Profit% | Time
 *                    Team A vs Team B  
 *                    Bookmaker1 vs Bookmaker2 | Market
 *                    [Save] [Calculate]
 */
const CleanArbitrageCard = ({ opportunity, onSave }) => {
  const navigate = useNavigate();
  const [isSaved, setIsSaved] = useState(false);

  // Transform raw opportunity data into clean display format
  const cardData = generateCleanCardData(opportunity);

  // Get betting instruction text for calculator
  const getBettingInstructionText = (outcome, side, marketDesc) => {
    if (!side) return outcome;

    const line = side.line;

    // For player props, show "Over/Under X.X Player Name Stat"
    if (opportunity.market_type?.includes('player_') || marketDesc?.includes('Total Bases') ||
      marketDesc?.includes('Hits') || marketDesc?.includes('Singles') ||
      marketDesc?.includes('Home Runs') || marketDesc?.includes('RBI') ||
      marketDesc?.includes('Strikeouts') || marketDesc?.includes('Doubles') ||
      marketDesc?.includes('Triples')) {

      // Use the full market description which includes player name (e.g., "Jackson Merrill Total Bases")
      const fullDescription = marketDesc || 'Player Stat';

      if (outcome?.toLowerCase().includes('over') && line) {
        return `Over ${line} ${fullDescription}`;
      } else if (outcome?.toLowerCase().includes('under') && line) {
        return `Under ${line} ${fullDescription}`;
      }
    }

    // For team-based markets, show team + line if available
    if (line && line !== '0') {
      if (opportunity.market_type?.includes('spread') || opportunity.market_type?.includes('sp')) {
        return `${cardData.homeTeam || cardData.awayTeam} ${line > 0 ? '+' : ''}${line}`;
      } else if (opportunity.market_type?.includes('total') || opportunity.market_type?.includes('ou')) {
        if (outcome?.toLowerCase().includes('over')) {
          return `Over ${line}`;
        } else if (outcome?.toLowerCase().includes('under')) {
          return `Under ${line}`;
        }
      }
    }

    // Fallback to team names for simple markets
    if (outcome?.toLowerCase().includes('home') || outcome === 'side1') {
      return cardData.homeTeam;
    } else if (outcome?.toLowerCase().includes('away') || outcome === 'side2') {
      return cardData.awayTeam;
    }

    return outcome;
  };

  const handleCalculate = () => {
    // Extract odds data from the opportunity for calculator
    const oddsData = opportunity.best_odds || {};
    const params = new URLSearchParams();

    // Handle different data structures (side1/side2 vs key-based)
    let side1, side2, outcome1, outcome2;

    if (oddsData.side1 && oddsData.side2) {
      side1 = oddsData.side1;
      side2 = oddsData.side2;
      outcome1 = 'side1';
      outcome2 = 'side2';
    } else {
      // Handle key-based structure (over/under, home/away, etc.)
      const outcomes = Object.keys(oddsData);
      if (outcomes.length >= 2) {
        side1 = oddsData[outcomes[0]];
        side2 = oddsData[outcomes[1]];
        outcome1 = outcomes[0];
        outcome2 = outcomes[1];
      }
    }

    if (side1?.odds && side2?.odds) {
      params.append('homeOdds', side1.odds.toString());
      params.append('awayOdds', side2.odds.toString());
      params.append('homeLabel', `${getBettingInstructionText(outcome1, side1, cardData.market)} (${side1.bookmaker || 'Unknown'})`);
      params.append('awayLabel', `${getBettingInstructionText(outcome2, side2, cardData.market)} (${side2.bookmaker || 'Unknown'})`);
    }

    // Add comprehensive opportunity info for calculator
    params.append('matchup', `${cardData.homeTeam} vs ${cardData.awayTeam}`);
    params.append('sport', opportunity.sport || 'Unknown');
    params.append('league', cardData.league);
    params.append('market', cardData.market);
    params.append('expectedProfit', cardData.profit.toFixed(2));
    params.append('gameTime', cardData.gameTime);

    // Navigate to calculator with all data
    navigate(`/calculator?${params.toString()}`);

  };

  const handleSave = async () => {
    try {
      if (onSave) {
        await onSave(opportunity);
        setIsSaved(true);
        toast.success('Saved');
      }
    } catch (error) {
      console.error('Error saving opportunity:', error);
      toast.error('Failed to save opportunity. Please try again.');
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 hover:border-yellow-500 hover:border-opacity-50 transition-all duration-200 hover:shadow-lg">
      {/* Header: Sport Icon + League | Profit% | Time */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{cardData.sportIcon}</span>
          <span className="text-yellow-400 font-semibold text-sm">{cardData.league}</span>
        </div>

        <div className="flex items-center space-x-3">
          <div className="bg-green-600 bg-opacity-20 text-green-400 px-2 py-1 rounded text-sm font-bold">
            {cardData.profit.toFixed(2)}%
          </div>
          <div className="text-gray-400 text-xs">
            {cardData.gameTime}
          </div>
        </div>
      </div>

      {/* Teams */}
      <div className="mb-3">
        <h3 className="text-white font-semibold text-lg leading-tight">
          {cardData.homeTeam} vs {cardData.awayTeam}
        </h3>
      </div>

      {/* Bookmakers and Market */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-gray-300 text-sm">
          <span className="text-yellow-400">{cardData.bookmaker1}</span>
          <span className="text-gray-500 mx-1">vs</span>
          <span className="text-yellow-400">{cardData.bookmaker2}</span>
        </div>

        <div className="text-gray-400 text-xs bg-gray-700 bg-opacity-50 px-2 py-1 rounded">
          {cardData.market}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button
          onClick={handleSave}
          disabled={isSaved}
          className={`flex-1 font-medium py-2 px-4 rounded-lg transition-colors text-sm ${isSaved
            ? 'bg-green-600 text-white cursor-default hover:bg-green-600'
            : 'bg-gray-700 hover:bg-gray-600 text-white'
            }`}
        >
          {isSaved ? 'Saved' : 'Save'}
        </button>

        <button
          onClick={handleCalculate}
          className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold py-2 px-4 rounded-lg transition-colors text-sm"
        >
          Calculate
        </button>
      </div>
    </div>
  );
};

export default CleanArbitrageCard;
