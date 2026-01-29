import React, { useEffect, useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../../context/AuthContext';

// Use relative URL - axios.defaults.baseURL is configured in main.jsx
const API_URL = '/api/my-arbitrage';

const MyArbitrageTab = () => {
  const { isAuthenticated } = useContext(AuthContext);
  const [arbitrages, setArbitrages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchArbitrages = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('🔍 MyArbitrageTab: Fetching arbitrages from:', API_URL);
      console.log('🔍 MyArbitrageTab: Axios base URL:', axios.defaults.baseURL);
      console.log('🔍 MyArbitrageTab: Full URL will be:', axios.defaults.baseURL + API_URL);

      const response = await axios.get(API_URL);
      console.log('✅ MyArbitrageTab: Successfully fetched arbitrages:', response.data);
      setArbitrages(response.data.arbitrages || []);
    } catch (error) {
      console.error('❌ MyArbitrageTab: Failed to fetch arbitrages:', error);
      console.error('❌ MyArbitrageTab: Error details:', {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        config: error.config
      });
      setError('Failed to load your arbitrage bets.');
    } finally {
      setLoading(false);
    }
  };

  const removeArbitrage = async (id) => {
    try {
      await axios.delete(`${API_URL}/${id}`);
      setArbitrages(arbitrages.filter(a => a.id !== id));
    } catch {
      alert('Failed to remove arbitrage.');
    }
  };

  // Add inline bet amount editing
  const updateBetAmount = async (id, newAmount) => {
    try {
      const response = await axios.patch(`${API_URL}/${id}`, {
        bet_amount: Number(newAmount)
      });
      // Update local state
      setArbitrages(arbitrages.map(a => a.id === id ? { ...a, bet_amount: Number(newAmount), profit: response.data.arbitrage.profit } : a));
    } catch {
      alert('Failed to update bet amount.');
    }
  };

  // Simplified profit calculation - just for percentage display
  const getGuaranteedProfit = (arb) => {
    const betAmount = Number(arb.bet_amount) || 0;
    return betAmount > 0 ? Number(arb.profit) || 0 : 0;
  };

  // Helper to calculate true arbitrage percentage or fallback to stored value
  const getTrueArbPercent = (arb) => {
    // Priority 1: Use stored percentage if available
    if (arb.profit_percentage) return Number(arb.profit_percentage);

    // Priority 2: Calculate from odds
    const odds = arb.odds || {};
    const oddsValues = Object.values(odds).filter(Number);
    if (oddsValues.length < 2) return 0;
    const totalProb = oddsValues.reduce((sum, o) => sum + 1 / o, 0);
    return ((1 / totalProb - 1) * 100);
  };

  useEffect(() => {
    if (isAuthenticated) fetchArbitrages();
  }, [isAuthenticated]);

  // Calculate total profit for last 7 and 30 days - only count profitable bets
  const now = new Date();

  const profit30 = arbitrages.reduce((sum, a) => sum + (Number(a.profit) || 0), 0);

  // Helper to calculate Average ROI
  const calculateAvgROI = () => {
    if (!arbitrages.length) return 0;
    const totalInvested = arbitrages.reduce((sum, a) => sum + (Number(a.bet_amount) || 0), 0);
    if (totalInvested === 0) return 0;
    return (profit30 / totalInvested) * 100;
  };

  const avgROI = calculateAvgROI();

  if (!isAuthenticated) {
    return <div className="p-6 text-center text-gray-400">Please log in to view your saved arbitrage bets.</div>;
  }

  if (loading) {
    return <div className="p-6 text-center text-gray-400">Loading your arbitrage bets...</div>;
  }

  if (error) {
    return <div className="p-6 text-center text-red-400">{error}</div>;
  }

  return (
    <div className="p-6 flex flex-col items-center">
      <h2 className="text-2xl font-bold mb-4 text-yellow-500/90 tracking-wide">My Arbitrage Bets</h2>

      {/* Redesigned Summary Card - Sleek Dark Theme */}
      <div className="w-full max-w-3xl bg-gray-900 border border-yellow-500/20 rounded-xl p-8 mb-8 shadow-2xl relative overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-yellow-500/5 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-8 relative z-10">
          <div className="flex items-center gap-5">
            <div>
              <div className="text-gray-500 text-xs font-semibold uppercase tracking-[0.2em] mb-1">Total Profit</div>
              <div className="text-5xl font-bold text-white tracking-tighter">
                ${profit30.toFixed(2)}
              </div>
            </div>
          </div>

          <div className="flex bg-gray-800/50 rounded-lg p-1 border border-gray-700/50">
            <div className="px-6 py-2 text-center border-r border-gray-700/50">
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold mb-1">Bets</div>
              <div className="text-lg font-bold text-yellow-500">{arbitrages.length}</div>
            </div>
            <div className="px-6 py-2 text-center">
              <div className="text-[10px] text-gray-500 uppercase tracking-widest font-semibold mb-1">Avg ROI</div>
              <div className={`text-lg font-bold ${avgROI >= 0 ? 'text-yellow-400' : 'text-red-400'}`}>
                {avgROI > 0 ? '+' : ''}{avgROI.toFixed(2)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full max-w-3xl space-y-4">
        {arbitrages.length === 0 ? (
          <div className="text-gray-500 text-center py-12 bg-gray-900/30 rounded-xl border border-dashed border-gray-800">
            <div className="text-lg font-medium text-gray-400 mb-2">No bets saved yet</div>
            <div className="text-sm">Go to the <span className="text-yellow-500/80">Arbitrage</span> section to save your first opportunity.</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {arbitrages.map(arb => {
              const truePercent = getTrueArbPercent(arb);
              return (
                <React.Fragment key={arb.id}>
                  <div key={arb.id} className="bg-gray-900 rounded-xl shadow-lg px-6 py-5 border border-gray-800 hover:border-yellow-500/30 transition-all duration-300 group">
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-5 gap-3">
                      <div>
                        <div className="text-lg font-bold text-gray-100 mb-1 group-hover:text-yellow-500/90 transition-colors">
                          {arb.home_team || 'Team A'} <span className="text-gray-600 font-normal text-sm mx-2">vs</span> {arb.away_team || 'Team B'}
                        </div>
                        <div className="text-gray-500 text-[10px] font-bold uppercase tracking-wider">
                          {arb.sport_title || 'Sport'}
                        </div>
                      </div>
                      <div className="px-3 py-1 bg-yellow-500/10 rounded border border-yellow-500/20 text-yellow-500 text-xs font-bold tracking-wide">
                        {truePercent.toFixed(2)}% ARB
                      </div>
                    </div>

                    <div className="border-b border-gray-800 mb-5"></div>

                    {/* Inputs Row */}
                    <div className="flex flex-col sm:flex-row items-end sm:items-center justify-between gap-6">
                      <div className="flex flex-col gap-1.5 w-full sm:w-auto">
                        <label className="text-gray-500 text-[10px] uppercase tracking-wider font-bold">Total Stake</label>
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">$</span>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={arb.bet_amount ?? ''}
                            onChange={e => updateBetAmount(arb.id, e.target.value)}
                            className="w-full sm:w-40 pl-7 pr-4 py-2 rounded bg-black/40 border border-gray-700 focus:outline-none focus:border-yellow-500/50 text-white font-medium placeholder-gray-700 transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                            placeholder="0.00"
                          />
                        </div>
                      </div>

                      <div className="flex items-center gap-6 w-full sm:w-auto justify-between sm:justify-end">
                        <div className="text-right">
                          <div className="text-gray-500 text-[10px] uppercase tracking-wider font-bold mb-0.5">Net Profit</div>
                          <div className={`text-xl font-bold tracking-tight ${arb.profit > 0 ? 'text-yellow-400' : 'text-gray-400'}`}>
                            {arb.profit > 0 ? '+' : ''}${arb.profit?.toFixed(2) || '0.00'}
                          </div>
                        </div>

                        <button
                          className="text-gray-600 hover:text-red-400 transition-colors p-2"
                          onClick={() => removeArbitrage(arb.id)}
                          title="Delete Bet"
                        >
                          <i className="fas fa-trash-alt text-sm"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </React.Fragment>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyArbitrageTab;
