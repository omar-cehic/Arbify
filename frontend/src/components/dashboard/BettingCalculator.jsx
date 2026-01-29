import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { HiExternalLink, HiCash, HiCalculator, HiCheckCircle, HiInformationCircle, HiGlobeAlt } from 'react-icons/hi';
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

  // Debug log to see what URL parameters we received
  console.log('🔍 BettingCalculator Debug - URL params:', {
    homeOdds: queryParams.get('homeOdds'),
    awayOdds: queryParams.get('awayOdds'),
    homeLabel,
    awayLabel,
    matchup,
    sport,
    market,
    expectedProfit
  });

  // Enhanced bookmaker matching function
  const findBookmakerByName = (bookmakerName, fallbackIndex = 0) => {
    if (!bookmakerName) return allSportsbooks[fallbackIndex];

    const cleanName = bookmakerName.toLowerCase().trim();
    console.log(`🔍 Looking for bookmaker: "${cleanName}"`);

    // Try exact name match first
    let found = allSportsbooks.find(sb => sb.name.toLowerCase() === cleanName);
    if (found) {
      console.log(`✅ Found exact match: ${found.name}`);
      return found;
    }

    // Try key match (backend uses keys like 'prophetexchange', 'betmgm')
    found = allSportsbooks.find(sb => sb.key?.toLowerCase() === cleanName);
    if (found) {
      console.log(`✅ Found key match: ${found.name} (key: ${found.key})`);
      return found;
    }

    // Try partial name match
    found = allSportsbooks.find(sb =>
      sb.name.toLowerCase().includes(cleanName) ||
      cleanName.includes(sb.name.toLowerCase())
    );
    if (found) {
      console.log(`✅ Found partial match: ${found.name}`);
      return found;
    }

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
      if (found) {
        console.log(`✅ Found via special mapping: ${found.name}`);
        return found;
      }
    }

    console.warn(`❌ No bookmaker found for "${cleanName}", using fallback: ${allSportsbooks[fallbackIndex].name}`);
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

  const getRegionColor = (region) => {
    const colors = {
      'us': 'border-yellow-500 text-yellow-400',
      'us2': 'border-yellow-600 text-yellow-400',
      'us_dfs': 'border-amber-500 text-amber-400',
      'us_ex': 'border-yellow-400 text-yellow-300',
      'uk': 'border-yellow-500 text-yellow-400',
      'eu': 'border-amber-600 text-amber-400',
      'au': 'border-yellow-600 text-yellow-500'
    };
    return colors[region] || 'border-yellow-500 text-yellow-400';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white py-10">
      <Helmet>
        <title>Arbitrage Calculator - Arbify</title>
        <meta name="description" content="Calculate your arbitrage betting stakes and guaranteed profit with our advanced betting calculator." />
      </Helmet>
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-extrabold text-yellow-400 mb-4 flex items-center justify-center gap-3">
            <HiCalculator className="h-12 w-12" />
            Arbitrage Calculator
          </h1>
        </div>


        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          {/* Input Section */}
          <div className="xl:col-span-1">
            <div className="bg-gray-900 rounded-2xl p-6 border border-yellow-500/30 shadow-2xl">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <HiCash className="h-6 w-6 text-yellow-400" />
                Bet Configuration
              </h2>

              {/* Opportunity Info */}
              {matchup && (
                <div className="bg-gray-800/50 rounded-lg p-4 mb-6 border border-gray-700">
                  <h3 className="text-yellow-400 font-semibold text-lg mb-2">{matchup}</h3>
                  <div className="space-y-1 text-sm text-gray-300">
                    {sport && league && <div><span className="text-gray-400">League:</span> {league}</div>}
                    {gameTime && <div><span className="text-gray-400">Game Time:</span> {gameTime}</div>}
                    {market && <div><span className="text-gray-400">Market:</span> {market}</div>}
                    {expectedProfit && <div><span className="text-gray-400">Expected Profit:</span> <span className="text-green-400 font-medium">{expectedProfit}%</span></div>}
                  </div>
                </div>
              )}

              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-300">Total Investment Amount</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-yellow-400 font-bold">$</span>
                    <input
                      type="number"
                      value={investment}
                      onChange={handleInvestmentChange}
                      className="bg-black text-white pl-8 pr-4 py-3 rounded-lg w-full border border-yellow-500/50 focus:outline-none focus:border-yellow-400 focus:ring-2 focus:ring-yellow-400/20 transition-all"
                      placeholder="100"
                    />
                  </div>
                </div>

                {/* Outcomes */}
                <div className="space-y-4">
                  <label className="block text-sm font-medium text-gray-300">Betting Outcomes</label>
                  {outcomes.map((outcome, index) => (
                    <div key={index} className="p-4 bg-black rounded-xl border border-gray-700 hover:border-yellow-500/50 transition-all">
                      <div className="flex justify-between items-center mb-3">
                        <input
                          type="text"
                          value={outcome.name}
                          onChange={(e) => handleOutcomeChange(index, 'name', e.target.value)}
                          className="bg-gray-800 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 text-sm font-medium"
                          placeholder="Outcome name"
                        />
                        {outcomes.length > 2 && (
                          <button
                            onClick={() => removeOutcome(index)}
                            className="text-red-400 hover:text-red-300 text-sm transition-colors font-medium"
                          >
                            Remove
                          </button>
                        )}
                      </div>

                      <div className="grid grid-cols-1 gap-3">
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Odds</label>
                          <input
                            type="number"
                            value={outcome.odds}
                            min="1.01"
                            step="0.01"
                            onChange={(e) => handleOutcomeChange(index, 'odds', parseFloat(e.target.value))}
                            className="bg-gray-800 text-white px-3 py-2 rounded-lg w-full border border-gray-600 focus:outline-none focus:border-yellow-400"
                            placeholder="2.00"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Sportsbook</label>
                          <select
                            value={outcome.sportsbook?.name || allSportsbooks[0].name}
                            onChange={(e) => {
                              const selectedSportsbook = allSportsbooks.find(sb => sb.name === e.target.value);
                              handleOutcomeChange(index, 'sportsbook', selectedSportsbook);
                            }}
                            className="bg-gray-800 text-white px-3 py-2 rounded-lg w-full border border-gray-600 focus:outline-none focus:border-yellow-400"
                          >
                            {Object.entries(sportsbooksData).map(([region, books]) => (
                              <optgroup key={region} label={`━━━ ${region.toUpperCase()} ━━━`} className="bg-gray-900 text-yellow-400 font-bold">
                                {books.map(sb => (
                                  <option key={sb.name} value={sb.name} className="bg-gray-800 text-white font-normal pl-4">
                                    {sb.name}
                                  </option>
                                ))}
                              </optgroup>
                            ))}
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={addOutcome}
                    disabled={outcomes.length >= 5}
                    className={`w-full py-3 rounded-lg border-2 border-dashed transition-all ${outcomes.length >= 5
                      ? 'border-gray-600 text-gray-500 cursor-not-allowed'
                      : 'border-yellow-500/50 text-yellow-400 hover:border-yellow-400 hover:bg-yellow-400/10'
                      }`}
                  >
                    + Add Another Outcome
                  </button>
                </div>

                <button
                  onClick={calculateArbitrage}
                  className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-black w-full py-3 rounded-lg font-bold hover:from-yellow-300 hover:to-yellow-400 transition-all transform hover:scale-105 shadow-lg"
                >
                  Calculate Arbitrage
                </button>
              </div>
            </div>
          </div>

          {/* Results Section */}
          <div className="xl:col-span-2 space-y-6">
            {/* Quick Results */}
            <div className="bg-gray-900 rounded-2xl p-6 border border-gray-700 shadow-2xl">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                {calculationResults?.isArbitrage ? (
                  <HiCheckCircle className="h-6 w-6 text-green-400" />
                ) : (
                  <HiCalculator className="h-6 w-6 text-yellow-400" />
                )}
                Calculation Results
              </h2>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-black rounded-xl border border-gray-700">
                  <div className="text-2xl font-bold text-yellow-400">
                    ${calculationResults?.profit.toFixed(2) || '0.00'}
                  </div>
                  <div className="text-sm text-gray-400">Guaranteed Profit</div>
                </div>

                <div className="text-center p-4 bg-black rounded-xl border border-gray-700">
                  <div className={`text-2xl font-bold ${calculationResults?.profitPercentage > 0 ? 'text-green-400' : 'text-gray-400'
                    }`}>
                    {calculationResults?.profitPercentage.toFixed(2) || '0.00'}%
                  </div>
                  <div className="text-sm text-gray-400">Profit Margin</div>
                </div>

                <div className="text-center p-4 bg-black rounded-xl border border-gray-700">
                  <div className="text-2xl font-bold text-yellow-400">
                    ${calculationResults?.totalReturn.toFixed(2) || '100.00'}
                  </div>
                  <div className="text-sm text-gray-400">Total Return</div>
                </div>

                <div className="text-center p-4 bg-black rounded-xl border border-gray-700">
                  <div className={`text-2xl font-bold ${calculationResults?.isArbitrage ? 'text-green-400' : 'text-red-400'
                    }`}>
                    {calculationResults?.isArbitrage ? 'YES' : 'NO'}
                  </div>
                  <div className="text-sm text-gray-400">Is Arbitrage?</div>
                </div>
              </div>

              {calculationResults?.isArbitrage && (
                <div className="mb-6">
                  <div className="flex items-center gap-2 text-green-400 mb-2">
                    <HiCheckCircle className="h-5 w-5" />
                    <span className="font-semibold text-lg">Arbitrage Opportunity Detected</span>
                  </div>
                  <p className="text-gray-300">
                    This is a guaranteed profit opportunity. Follow the betting instructions below to secure your ${calculationResults.profit.toFixed(2)} profit.
                  </p>
                </div>
              )}
            </div>

            {/* Betting Instructions */}
            {calculationResults && calculationResults.stakes.length > 0 && (
              <div className="bg-gray-900 rounded-2xl p-6 border border-gray-700 shadow-2xl">
                <h2 className="text-2xl font-semibold mb-6">Betting Instructions</h2>

                <div className="space-y-4">
                  {calculationResults.stakes.map((stake, index) => (
                    <div key={index} className={`p-5 rounded-xl border-2 ${getRegionColor(stake.sportsbook.region)} bg-black hover:bg-gray-900 transition-all`}>
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="text-lg font-semibold text-white">{stake.name}</h3>
                          <p className="text-sm text-gray-400">Step {index + 1} of {calculationResults.stakes.length}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-yellow-400">${stake.stake.toFixed(2)}</div>
                          <div className="text-sm text-gray-400">{stake.percentage.toFixed(1)}% of total</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                        <div>
                          <p className="text-sm text-gray-400 mb-1">Bet on</p>
                          <p className="font-semibold">{stake.name} @ {decimalToAmerican(stake.odds)}</p>
                        </div>

                        <div>
                          <p className="text-sm text-gray-400 mb-1">Amount to bet</p>
                          <p className="font-semibold text-yellow-400">${stake.stake.toFixed(2)}</p>
                        </div>

                        <div className="flex justify-end">
                          <a
                            href={stake.sportsbook.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border-2 ${getRegionColor(stake.sportsbook.region)} hover:bg-gray-800 transition-all transform hover:scale-105 font-medium`}
                          >
                            <span className="font-semibold">{stake.sportsbook.name}</span>
                            <HiExternalLink className="h-4 w-4" />
                          </a>
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <p className="text-sm text-gray-400">
                          Potential return: <span className="text-white font-semibold">${(stake.stake * stake.odds).toFixed(2)}</span>
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {calculationResults.isArbitrage && (
                  <div className="mt-6 p-4 bg-gray-800 rounded-xl border border-gray-600">
                    <h4 className="font-semibold text-yellow-400 mb-2">Pro Tips:</h4>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• Place all bets as quickly as possible to avoid odds changes</li>
                      <li>• Double-check the odds before placing each bet</li>
                      <li>• Consider using different devices/browsers for each sportsbook</li>
                      <li>• Make sure you have sufficient funds in each account</li>
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BettingCalculator; 