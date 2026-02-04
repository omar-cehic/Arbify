import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { HiExternalLink, HiCheckCircle, HiCalculator } from 'react-icons/hi';
import { Helmet } from 'react-helmet-async';

const BettingCalculator = () => {
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);

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

  // Comprehensive sportsbooks list organized by region
  const sportsbooksData = {
    'US - Main': [
      { name: 'DraftKings', key: 'draftkings', url: 'https://www.draftkings.com', region: 'us' },
      { name: 'FanDuel', key: 'fanduel', url: 'https://www.fanduel.com', region: 'us' },
      { name: 'BetMGM', key: 'betmgm', url: 'https://www.betmgm.com', region: 'us' },
      { name: 'Caesars', key: 'williamhill_us', url: 'https://www.caesars.com/sportsbook', region: 'us' },
      { name: 'BetRivers', key: 'betrivers', url: 'https://www.betrivers.com', region: 'us' },
      { name: 'BetOnline.ag', key: 'betonlineag', url: 'https://www.betonline.ag', region: 'us' },
      { name: 'BetUS', key: 'betus', url: 'https://www.betus.com.pa', region: 'us' },
      { name: 'Bovada', key: 'bovada', url: 'https://www.bovada.lv', region: 'us' },
      { name: 'Fanatics', key: 'fanatics', url: 'https://www.fanaticssportsbook.com', region: 'us' },
      { name: 'LowVig.ag', key: 'lowvig', url: 'https://www.lowvig.ag', region: 'us' },
      { name: 'MyBookie.ag', key: 'mybookieag', url: 'https://www.mybookie.ag', region: 'us' },
      { name: 'ProphetExchange', key: 'prophetexchange', url: 'https://www.prophetexchange.com', region: 'us' },
      { name: 'Hard Rock Bet', key: 'hardrockbet', url: 'https://www.hardrock.bet', region: 'us' },
      { name: 'ESPN Bet', key: 'espnbet', url: 'https://www.espnbet.com', region: 'us' }
    ],
    'US - Regional': [
      { name: 'Bally Bet', key: 'ballybet', url: 'https://www.ballysbet.com', region: 'us2' },
      { name: 'BetAnySports', key: 'betanysports', url: 'https://www.betanysports.com', region: 'us2' },
      { name: 'betPARX', key: 'betparx', url: 'https://www.betparx.com', region: 'us2' },
      { name: 'ESPN BET', key: 'espnbet', url: 'https://www.espnbet.com', region: 'us2' },
      { name: 'Fliff', key: 'fliff', url: 'https://www.fliff.com', region: 'us2' },
      { name: 'Hard Rock Bet', key: 'hardrockbet', url: 'https://www.hardrockbet.com', region: 'us2' },
      { name: 'ReBet', key: 'rebet', url: 'https://www.rebet.com', region: 'us2' },
      { name: 'Wind Creek', key: 'windcreek', url: 'https://www.windcreekbet.com', region: 'us2' }
    ],
    'US - DFS Sites': [
      { name: 'DraftKings Pick6', key: 'pick6', url: 'https://pick6.draftkings.com', region: 'us_dfs' },
      { name: 'PrizePicks', key: 'prizepicks', url: 'https://www.prizepicks.com', region: 'us_dfs' },
      { name: 'Underdog Fantasy', key: 'underdog', url: 'https://www.underdogfantasy.com', region: 'us_dfs' }
    ],
    'US - Exchanges': [
      { name: 'BetOpenly', key: 'betopenly', url: 'https://www.betopenly.com', region: 'us_ex' },
      { name: 'Novig', key: 'novig', url: 'https://www.novig.com', region: 'us_ex' },
      { name: 'ProphetX', key: 'prophetx', url: 'https://www.prophetx.com', region: 'us_ex' }
    ],
    'UK Bookmakers': [
      { name: '888sport', key: 'sport888', url: 'https://www.888sport.com', region: 'uk' },
      { name: 'Betfair Exchange', key: 'betfair_ex_uk', url: 'https://www.betfair.com/exchange', region: 'uk' },
      { name: 'Betfair Sportsbook', key: 'betfair_sb_uk', url: 'https://www.betfair.com/sport', region: 'uk' },
      { name: 'Bet Victor', key: 'betvictor', url: 'https://www.betvictor.com', region: 'uk' },
      { name: 'Betway', key: 'betway', url: 'https://www.betway.com', region: 'uk' },
      { name: 'BoyleSports', key: 'boylesports', url: 'https://www.boylesports.com', region: 'uk' },
      { name: 'Casumo', key: 'casumo', url: 'https://www.casumo.com', region: 'uk' },
      { name: 'Coral', key: 'coral', url: 'https://www.coral.co.uk', region: 'uk' },
      { name: 'Grosvenor', key: 'grosvenor', url: 'https://www.grosvenorcasinos.com', region: 'uk' },
      { name: 'Ladbrokes', key: 'ladbrokes_uk', url: 'https://www.ladbrokes.com', region: 'uk' },
      { name: 'LeoVegas', key: 'leovegas', url: 'https://www.leovegas.com', region: 'uk' },
      { name: 'LiveScore Bet', key: 'livescorebet', url: 'https://www.livescorebet.com', region: 'uk' },
      { name: 'Matchbook', key: 'matchbook', url: 'https://www.matchbook.com', region: 'uk' },
      { name: 'Paddy Power', key: 'paddypower', url: 'https://www.paddypower.com', region: 'uk' },
      { name: 'Sky Bet', key: 'skybet', url: 'https://www.skybet.com', region: 'uk' },
      { name: 'Smarkets', key: 'smarkets', url: 'https://www.smarkets.com', region: 'uk' },
      { name: 'Unibet', key: 'unibet_uk', url: 'https://www.unibet.co.uk', region: 'uk' },
      { name: 'Virgin Bet', key: 'virginbet', url: 'https://www.virginbet.com', region: 'uk' },
      { name: 'William Hill', key: 'williamhill', url: 'https://www.williamhill.com', region: 'uk' }
    ],
    'EU Bookmakers': [
      { name: '1xBet', key: 'onexbet', url: 'https://www.1xbet.com', region: 'eu' },
      { name: 'Betclic', key: 'betclic_fr', url: 'https://www.betclic.fr', region: 'eu' },
      { name: 'Betfair Exchange', key: 'betfair_ex_eu', url: 'https://www.betfair.com/exchange', region: 'eu' },
      { name: 'Betsson', key: 'betsson', url: 'https://www.betsson.com', region: 'eu' },
      { name: 'Coolbet', key: 'coolbet', url: 'https://www.coolbet.com', region: 'eu' },
      { name: 'Everygame', key: 'everygame', url: 'https://www.everygame.eu', region: 'eu' },
      { name: 'GTbets', key: 'gtbets', url: 'https://www.gtbets.eu', region: 'eu' },
      { name: 'Marathon Bet', key: 'marathonbet', url: 'https://www.marathonbet.com', region: 'eu' },
      { name: 'NordicBet', key: 'nordicbet', url: 'https://www.nordicbet.com', region: 'eu' },
      { name: 'Parions Sport', key: 'parionssport_fr', url: 'https://www.parionssport.fdj.fr', region: 'eu' },
      { name: 'Pinnacle', key: 'pinnacle', url: 'https://www.pinnacle.com', region: 'eu' },
      { name: 'Suprabets', key: 'suprabets', url: 'https://www.suprabets.com', region: 'eu' },
      { name: 'Tipico', key: 'tipico_de', url: 'https://www.tipico.de', region: 'eu' },
      { name: 'Winamax', key: 'winamax_fr', url: 'https://www.winamax.fr', region: 'eu' }
    ],
    'AU Bookmakers': [
      { name: 'Bet365 AU', key: 'bet365_au', url: 'https://www.bet365.com.au', region: 'au' },
      { name: 'Betfair Exchange', key: 'betfair_ex_au', url: 'https://www.betfair.com.au/exchange', region: 'au' },
      { name: 'Betr', key: 'betr_au', url: 'https://www.betr.com.au', region: 'au' },
      { name: 'Bet Right', key: 'betright', url: 'https://www.betright.com.au', region: 'au' },
      { name: 'BoomBet', key: 'boombet', url: 'https://www.boombet.com.au', region: 'au' },
      { name: 'Dabble', key: 'dabble_au', url: 'https://www.dabble.com.au', region: 'au' },
      { name: 'Ladbrokes AU', key: 'ladbrokes_au', url: 'https://www.ladbrokes.com.au', region: 'au' },
      { name: 'Neds', key: 'neds', url: 'https://www.neds.com.au', region: 'au' },
      { name: 'PlayUp', key: 'playup', url: 'https://www.playup.com.au', region: 'au' },
      { name: 'PointsBet AU', key: 'pointsbetau', url: 'https://www.pointsbet.com.au', region: 'au' },
      { name: 'SportsBet', key: 'sportsbet', url: 'https://www.sportsbet.com.au', region: 'au' },
      { name: 'TAB', key: 'tab', url: 'https://www.tab.com.au', region: 'au' },
      { name: 'TABtouch', key: 'tabtouch', url: 'https://www.tabtouch.com.au', region: 'au' },
      { name: 'Unibet AU', key: 'unibet', url: 'https://www.unibet.com.au', region: 'au' }
    ]
  };

  // Flatten all sportsbooks for easy access
  const allSportsbooks = Object.values(sportsbooksData).flat();

  // Helper function to find sportsbook by name
  const findSportsbookByName = (name) => {
    return allSportsbooks.find(sb => sb.name === name) || allSportsbooks[0];
  };

  // Check for pre-filled data from ArbitrageFinder
  const getPrefilledData = () => {
    try {
      // Check localStorage first (more persistent)
      let calculatorData = localStorage.getItem('calculatorData');
      if (!calculatorData) {
        // Fallback to sessionStorage
        calculatorData = sessionStorage.getItem('calculatorData');
      }

      if (calculatorData) {
        const data = JSON.parse(calculatorData);
        console.log('Found pre-filled calculator data:', data);

        if (data.prefillData && data.sportsbook1 && data.sportsbook2) {
          // Clear the data after reading to prevent re-using stale data
          localStorage.removeItem('calculatorData');
          sessionStorage.removeItem('calculatorData');

          return {
            investment: parseFloat(data.totalStake) || 1000,
            outcomes: [
              {
                name: data.match ? data.match.split(' vs ')[0] : 'Outcome 1',
                odds: parseFloat(data.odds1) || 2.0,
                sportsbook: findSportsbookByName(data.sportsbook1)
              },
              {
                name: data.match ? data.match.split(' vs ')[1] : 'Outcome 2',
                odds: parseFloat(data.odds2) || 2.0,
                sportsbook: findSportsbookByName(data.sportsbook2)
              }
            ]
          };
        }
      }
    } catch (error) {
      console.error('Error reading pre-filled data:', error);
    }

    return null;
  };

  // Initial state from URL parameters, localStorage, or defaults
  const prefilledData = getPrefilledData();
  const homeLabel = queryParams.get('homeLabel') || 'Team A';
  const awayLabel = queryParams.get('awayLabel') || 'Team B';
  const drawLabel = queryParams.get('drawLabel') || 'Draw';
  const matchup = queryParams.get('matchup');
  const sport = queryParams.get('sport');
  const league = queryParams.get('league');
  const market = queryParams.get('market');
  const expectedProfit = queryParams.get('expectedProfit');
  const gameTime = queryParams.get('gameTime');

  // Enhanced bookmaker matching function
  const findBookmakerByName = (bookmakerName, fallbackIndex = 0) => {
    if (!bookmakerName) return allSportsbooks[fallbackIndex];

    const cleanName = bookmakerName.toLowerCase().trim();

    // Try exact name match first
    let found = allSportsbooks.find(sb => sb.name.toLowerCase() === cleanName);
    if (found) return found;

    // Try key match (backend uses keys like 'prophetexchange', 'betmgm')
    found = allSportsbooks.find(sb => sb.key?.toLowerCase() === cleanName);
    if (found) return found;

    // Try partial name match
    found = allSportsbooks.find(sb =>
      sb.name.toLowerCase().includes(cleanName) ||
      cleanName.includes(sb.name.toLowerCase())
    );
    if (found) return found;

    // Special cases for known backend bookmaker names
    const specialMappings = {
      'prophetexchange': 'ProphetExchange',
      'hardrockbet': 'Hard Rock Bet',
      'draftkings': 'DraftKings',
      'betmgm': 'BetMGM',
      'fanduel': 'FanDuel',
      'caesars': 'Caesars',
      'pinnacle': 'Pinnacle',
      'bovada': 'Bovada',
      'fanatics': 'Fanatics',
      'ballybet': 'Bally Bet',
      'betparx': 'betPARX',
      'espnbet': 'ESPN Bet'
    };

    const mappedName = specialMappings[cleanName];
    if (mappedName) {
      found = allSportsbooks.find(sb => sb.name.toLowerCase().includes(mappedName.toLowerCase()));
      if (found) return found;
    }

    return allSportsbooks[fallbackIndex];
  };

  const initialOdds = prefilledData ? prefilledData : {
    outcomes: [
      {
        name: homeLabel.split('(')[0].trim() || 'Team A',
        odds: parseFloat(queryParams.get('homeOdds')) || parseFloat(queryParams.get('home')) || 2.0,
        sportsbook: findBookmakerByName(homeLabel.split('(')[1]?.replace(')', ''), 0)
      },
      {
        name: awayLabel.split('(')[0].trim() || 'Team B',
        odds: parseFloat(queryParams.get('awayOdds')) || parseFloat(queryParams.get('away')) || 2.0,
        sportsbook: findBookmakerByName(awayLabel.split('(')[1]?.replace(')', ''), 1)
      }
    ]
  };

  // Add draw if present in URL
  if (queryParams.get('draw') && !prefilledData) {
    initialOdds.outcomes.splice(1, 0, {
      name: drawLabel,
      odds: parseFloat(queryParams.get('draw')),
      sportsbook: allSportsbooks[2]
    });
  }

  const [investment, setInvestment] = useState(prefilledData ? prefilledData.investment : 100);
  const [outcomes, setOutcomes] = useState(initialOdds.outcomes);
  const [calculationResults, setCalculationResults] = useState(null);

  // Calculate results whenever investment or outcomes change
  useEffect(() => {
    calculateArbitrage();
  }, [investment, outcomes]);

  const handleInvestmentChange = (e) => {
    const value = parseFloat(e.target.value);
    setInvestment(isNaN(value) ? 0 : value);
  };

  const handleOutcomeChange = (index, field, value) => {
    const updatedOutcomes = [...outcomes];
    if (field === 'sportsbook') {
      updatedOutcomes[index][field] = value;
    } else {
      updatedOutcomes[index][field] = value;
    }
    setOutcomes(updatedOutcomes);
  };

  const addOutcome = () => {
    if (outcomes.length < 5) { // Limit to 5 outcomes
      setOutcomes([...outcomes, {
        name: `Outcome ${outcomes.length + 1}`,
        odds: 2.0,
        sportsbook: allSportsbooks[outcomes.length % allSportsbooks.length]
      }]);
    }
  };

  const removeOutcome = (index) => {
    if (outcomes.length > 2) { // Keep at least 2 outcomes
      const updatedOutcomes = outcomes.filter((_, i) => i !== index);
      setOutcomes(updatedOutcomes);
    }
  };

  const calculateArbitrage = () => {
    // Validate inputs
    const validOdds = outcomes.every(outcome =>
      outcome.odds && !isNaN(outcome.odds) && outcome.odds > 1
    );

    if (!validOdds || !investment || investment <= 0) {
      setCalculationResults({
        isArbitrage: false,
        totalProbability: 0,
        profitPercentage: 0,
        stakes: [],
        totalStake: 0,
        totalReturn: 0,
        profit: 0
      });
      return;
    }

    // Calculate implied probabilities
    const probabilities = outcomes.map(outcome => ({
      name: outcome.name,
      odds: outcome.odds,
      sportsbook: outcome.sportsbook,
      probability: 1 / outcome.odds
    }));

    const totalProbability = probabilities.reduce((sum, outcome) => sum + outcome.probability, 0);
    const isArbitrage = totalProbability < 1;
    const profitPercentage = ((1 / totalProbability) - 1) * 100;

    // Calculate optimal stakes
    const stakes = probabilities.map(outcome => ({
      name: outcome.name,
      odds: outcome.odds,
      sportsbook: outcome.sportsbook,
      probability: outcome.probability,
      percentage: (outcome.probability / totalProbability) * 100,
      stake: (outcome.probability / totalProbability) * investment
    }));

    const totalStake = stakes.reduce((sum, outcome) => sum + outcome.stake, 0);
    // For arbitrage, the guaranteed return is investment/totalProbability (same regardless of outcome)
    const totalReturn = isArbitrage ? investment / totalProbability : totalStake;
    const profit = totalReturn - totalStake;

    setCalculationResults({
      isArbitrage,
      totalProbability,
      profitPercentage,
      stakes,
      totalStake,
      totalReturn,
      profit
    });
  };

  return (
    <div className="min-h-screen bg-black text-white py-12">
      <Helmet>
        <title>Calculator | Arbify</title>
        <meta name="description" content="Calculate your arbitrage betting stakes and guaranteed profit." />
      </Helmet>

      <div className="container mx-auto px-4 max-w-7xl">
        {/* Simplified Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-medium tracking-wide text-white mb-2">
            Arbitrage Calculator
          </h1>
          <p className="text-gray-400 text-sm uppercase tracking-widest">
            Calculate Stakes • Secure Profit • Beat The Books
          </p>
        </div>

        {/* Opportunity Summary (if available) */}
        {matchup && (
          <div className="mb-8 p-6 bg-gray-900 border border-gray-800 rounded-xl max-w-4xl mx-auto shadow-2xl shadow-yellow-500/5">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div>
                <h2 className="text-xl text-white font-medium mb-1">{matchup}</h2>
                <div className="text-sm text-gray-500 flex gap-4">
                  <span>{sport}</span>
                  {market && <span>• {market}</span>}
                </div>
              </div>
              {expectedProfit && (
                <div className="px-4 py-2 bg-green-900/20 text-green-400 border border-green-800 rounded-lg">
                  <span className="text-xs text-green-500 block">EXPECTED RETURN</span>
                  <span className="text-lg font-bold">+{expectedProfit}%</span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-6xl mx-auto">
          {/* LEFT COLUMN - Calculator Inputs */}
          <div className="lg:col-span-4 space-y-6">
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-800 shadow-xl">
              <h3 className="text-yellow-500 text-xs font-bold uppercase tracking-widest mb-6 border-b border-gray-800 pb-2">
                Bet Configuration
              </h3>

              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-medium mb-2 text-gray-400 uppercase tracking-wide">Total Investment</label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-yellow-500 font-bold">$</span>
                    <input
                      type="number"
                      value={investment}
                      onChange={handleInvestmentChange}
                      className="bg-black text-white pl-8 pr-4 py-4 rounded-xl w-full border border-gray-700 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 text-lg font-medium transition-all"
                      placeholder="100"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <label className="block text-xs font-medium text-gray-400 uppercase tracking-wide">Outcomes</label>
                  </div>

                  {outcomes.map((outcome, index) => (
                    <div key={index} className="p-4 bg-black rounded-xl border border-gray-800 hover:border-gray-700 transition-colors">
                      <div className="mb-3">
                        <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Bookmaker</label>
                        <select
                          value={outcome.sportsbook?.name || allSportsbooks[0].name}
                          onChange={(e) => {
                            const selectedSportsbook = allSportsbooks.find(sb => sb.name === e.target.value);
                            handleOutcomeChange(index, 'sportsbook', selectedSportsbook);
                          }}
                          className="bg-gray-900 text-white px-3 py-2 rounded-lg w-full border border-gray-700 focus:border-yellow-500 text-sm appearance-none"
                        >
                          {Object.entries(sportsbooksData).map(([region, books]) => (
                            <optgroup key={region} label={region}>
                              {books.map(sb => (
                                <option key={sb.name} value={sb.name}>{sb.name}</option>
                              ))}
                            </optgroup>
                          ))}
                        </select>
                      </div>

                      <div className="flex gap-3">
                        <div className="flex-1">
                          <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Pick</label>
                          <input
                            type="text"
                            value={outcome.name}
                            onChange={(e) => handleOutcomeChange(index, 'name', e.target.value)}
                            className="bg-gray-900 text-white px-3 py-2 rounded-lg w-full border border-gray-700 focus:border-yellow-500 text-sm"
                            placeholder="Team/Outcome"
                          />
                        </div>
                        <div className="w-24">
                          <label className="text-[10px] text-gray-500 uppercase tracking-wider block mb-1">Odds</label>
                          <input
                            type="number"
                            value={outcome.odds}
                            min="1.01"
                            step="0.01"
                            onChange={(e) => handleOutcomeChange(index, 'odds', parseFloat(e.target.value))}
                            className="bg-gray-900 text-white px-3 py-2 text-center rounded-lg w-full border border-gray-700 focus:border-yellow-500 text-sm font-bold text-yellow-400"
                          />
                        </div>
                      </div>

                      {outcomes.length > 2 && (
                        <div className="mt-2 text-right">
                          <button onClick={() => removeOutcome(index)} className="text-xs text-red-500 hover:text-red-400">Remove</button>
                        </div>
                      )}
                    </div>
                  ))}

                  <button
                    onClick={addOutcome}
                    disabled={outcomes.length >= 5}
                    className="w-full py-2 rounded-lg border border-dashed border-gray-700 text-gray-400 text-sm hover:border-yellow-500 hover:text-yellow-500 transition-all"
                  >
                    + Add Outcome
                  </button>
                </div>
              </div>
            </div>

            {/* Quick Stats - Mobile Only (Stacks on bottom for desktop, but useful summary here) */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 lg:hidden">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Total Profit</span>
                <span className={`text-xl font-bold ${calculationResults?.profit > 0 ? 'text-green-400' : 'text-gray-500'}`}>
                  ${calculationResults?.profit.toFixed(2) || '0.00'}
                </span>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-gray-400">ROI</span>
                <span className={`text-lg font-medium ${calculationResults?.profitPercentage > 0 ? 'text-green-400' : 'text-gray-500'}`}>
                  {calculationResults?.profitPercentage.toFixed(2) || '0.00'}%
                </span>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN - Instructions & Results */}
          <div className="lg:col-span-8 flex flex-col h-full">
            <div className="bg-gradient-to-br from-gray-900 to-black rounded-3xl p-8 border border-gray-800 shadow-2xl relative overflow-hidden flex-grow">
              {/* Background decorative glow */}
              <div className="absolute top-0 right-0 w-64 h-64 bg-yellow-500/5 rounded-full filter blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none"></div>

              <div className="flex justify-between items-end mb-8 relative z-10">
                <div>
                  <h2 className="text-2xl text-white font-medium">Betting Instructions</h2>
                  <p className="text-gray-400 text-sm mt-1">
                    Find this bet under: <span className="text-yellow-500 font-medium">{sport} {league ? `> ${league}` : ''} {'>'} {market || 'Moneyline'}</span>
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">Guaranteed Profit</div>
                  <div className={`text-4xl font-bold ${calculationResults?.profit > 0 ? 'text-green-400' : 'text-gray-500'}`}>
                    ${calculationResults?.profit.toFixed(2) || '0.00'}
                  </div>
                </div>
              </div>

              {/* VISUAL BET SLIPS */}
              <div className="space-y-4 relative z-10">
                {calculationResults && calculationResults.stakes.length > 0 ? (
                  calculationResults.stakes.map((stake, index) => (
                    <div key={index} className="group bg-black rounded-xl p-0 border border-gray-800 overflow-hidden hover:border-yellow-500/50 transition-all duration-300">
                      <div className="flex flex-col md:flex-row h-full">
                        {/* Step Number & Bookmaker Brand */}
                        <div className="bg-gray-900 p-6 md:w-1/3 flex flex-col justify-center border-b md:border-b-0 md:border-r border-gray-800 group-hover:bg-gray-800 transition-colors">
                          <div className="text-xs text-yellow-500 font-bold uppercase tracking-widest mb-2">Step {index + 1}</div>
                          <div className="text-2xl text-white font-bold mb-1">{stake.sportsbook.name}</div>

                          <a
                            href={stake.sportsbook.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-xs text-gray-400 hover:text-yellow-400 mt-2 transition-colors"
                          >
                            Open Sportsbook <HiExternalLink />
                          </a>
                        </div>

                        {/* Bet Details - "The Ticket" */}
                        <div className="p-6 md:w-2/3 flex flex-col md:flex-row justify-between items-center gap-6">
                          <div className="flex-1">
                            <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Bet Selection</div>
                            <div className="text-xl text-white font-medium">{stake.name}</div>
                            <div className="text-sm text-gray-400 mt-1">Odds: <span className="text-white">{decimalToAmerican(stake.odds)}</span> <span className="text-gray-600">({stake.odds})</span></div>
                          </div>

                          <div className="text-center md:text-right bg-gray-900/50 p-4 rounded-lg border border-gray-800/50 min-w-[140px]">
                            <div className="text-[10px] text-gray-400 uppercase tracking-wider mb-1">Wager Amount</div>
                            <div className="text-2xl font-bold text-yellow-400">${stake.stake.toFixed(2)}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-20 bg-gray-900/30 rounded-xl border border-dashed border-gray-800">
                    <HiCalculator className="h-12 w-12 text-gray-700 mx-auto mb-4" />
                    <p className="text-gray-500">Enter odds to calculate optimal stakes</p>
                  </div>
                )}
              </div>

              {calculationResults?.isArbitrage && (
                <div className="mt-8 p-4 rounded-xl bg-green-900/10 border border-green-900/30 flex items-start gap-3">
                  <HiCheckCircle className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-green-400 font-bold text-sm uppercase tracking-wide mb-1">Arbitrage Opportunity Confirmed</h4>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      Use the exact wager amounts highlighted in yellow above. Place these bets simultaneously to lock in your <strong>${calculationResults.profit.toFixed(2)}</strong> profit.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* PRO TIPS SECTION */}
            <div className="mt-6 bg-gray-900 rounded-2xl p-6 border border-gray-800">
              <h3 className="text-sm font-bold text-white uppercase tracking-wide mb-4 flex items-center gap-2">
                ⚡ Pro Tips for this Bet
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 bg-black rounded-xl border border-gray-800">
                  <div className="text-yellow-500 text-xs font-bold uppercase tracking-wider mb-1">Avoid Limits</div>
                  <p className="text-gray-400 text-xs leading-relaxed">Round your bets to the nearest dollar (e.g., $50 instead of $50.59) to avoid suspicion from bookmakers.</p>
                </div>
                <div className="p-4 bg-black rounded-xl border border-gray-800">
                  <div className="text-blue-400 text-xs font-bold uppercase tracking-wider mb-1">Verification</div>
                  <p className="text-gray-400 text-xs leading-relaxed">Always verify lines match what you see here before placing <strong>any</strong> bets. Lines move fast.</p>
                </div>
                <div className="p-4 bg-black rounded-xl border border-gray-800">
                  <div className="text-green-400 text-xs font-bold uppercase tracking-wider mb-1">Execution</div>
                  <p className="text-gray-400 text-xs leading-relaxed">Open both sportsbooks first. Place the bet on the "Soft" book (slower to update) first, then the sharp one.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BettingCalculator;