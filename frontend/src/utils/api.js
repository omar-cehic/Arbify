// API base URL - this will work when your backend is running
const isDevelopment = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8001' 
  : ''; // Use relative URLs in production - Vercel will proxy to backend

console.log('🔧 API Configuration:', {
  isDevelopment,
  hostname: typeof window !== 'undefined' ? window.location.hostname : 'undefined',
  API_BASE_URL: API_BASE_URL || 'relative URLs (proxied by Vercel)'
});

// Helper function for API calls
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const config = {
    ...options,
    headers,
  };
  
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  console.log('🚀 API Call:', {
    endpoint,
    fullUrl,
    method: options.method || 'GET'
  });
  
  try {
    const response = await fetch(fullUrl, config);
    console.log('📡 API Response:', {
      url: fullUrl,
      status: response.status,
      ok: response.ok
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || 'API call failed');
    }
    
    return data;
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

// Auth API calls
export const login = async (username, password) => {
  return apiCall('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
};

export const register = async (userData) => {
  return apiCall('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(userData),
  });
};

export const changePassword = async (currentPassword, newPassword) => {
  return apiCall('/api/auth/direct-change-password', {
    method: 'POST',
    body: JSON.stringify({ 
      username: JSON.parse(localStorage.getItem('user'))?.username,
      current_password: currentPassword, 
      new_password: newPassword 
    }),
  });
};

// Odds API calls  
export const getOdds = async () => {
  // Always use real API data - no mock data fallback
  return await apiCall('/api/odds');
};

// Arbitrage API calls
export const getArbitrage = async () => {
  // Always use real API data - no mock data fallback
  return await apiCall('/api/arbitrage');
};

// SGO Arbitrage API calls
export const getSGOArbitrage = async (sportKey = null, minProfit = 1.0) => {
  const params = new URLSearchParams();
  if (sportKey) params.append('sport_key', sportKey);
  if (minProfit) params.append('min_profit', minProfit.toString());
  
  const queryString = params.toString();
  const endpoint = `/api/arbitrage/sgo${queryString ? `?${queryString}` : ''}`;
  
  return await apiCall(endpoint);
};

// Profile API calls
export const getUserProfile = async () => {
  return apiCall('/api/auth/user/profile');
};

export const updateUserProfile = async (profileData) => {
  return apiCall('/api/auth/user/profile', {
    method: 'PUT',
    body: JSON.stringify(profileData),
  });
};

// Strategies API calls
export const getStrategies = async () => {
  return apiCall('/api/strategies');
};

export const createStrategy = async (strategyData) => {
  return apiCall('/api/strategies', {
    method: 'POST',
    body: JSON.stringify(strategyData),
  });
};

export const updateStrategy = async (strategyId, strategyData) => {
  return apiCall(`/api/strategies/${strategyId}`, {
    method: 'PUT',
    body: JSON.stringify(strategyData),
  });
};

export const deleteStrategy = async (strategyId) => {
  return apiCall(`/api/strategies/${strategyId}`, {
    method: 'DELETE',
  });
};

// Mock data for development
const mockOddsData = {
  odds: [
    {
      sport_key: "soccer_epl",
      sport_title: "English Premier League",
      commence_time: "2025-04-27T12:00:00Z",
      home_team: "Arsenal",
      away_team: "Manchester United",
      bookmakers: [
        {
          title: "Caesars",
          markets: [
            {
              key: "h2h",
              outcomes: [
                { name: "Arsenal", price: 2.82 }
              ]
            }
          ]
        },
        {
          title: "BetMGM",
          markets: [
            {
              key: "h2h",
              outcomes: [
                { name: "Draw", price: 3.49 }
              ]
            }
          ]
        },
        {
          title: "BetUS",
          markets: [
            {
              key: "h2h",
              outcomes: [
                { name: "Manchester United", price: 3.17 }
              ]
            }
          ]
        }
      ]
    }
  ]
};

const mockArbitrageData = {
  arbitrage_opportunities: [
    {
      match: {
        home_team: "Arsenal",
        away_team: "Manchester United",
        commence_time: "2025-04-27T12:00:00Z"
      },
      sport_title: "English Premier League",
      profit_percentage: 2.49,
      outcomes: 3,
      best_odds: {
        home: 2.82,
        home_bookmaker: "Caesars",
        away: 3.17,
        away_bookmaker: "BetUS",
        draw: 3.49,
        draw_bookmaker: "BetMGM"
      }
    }
  ]
};