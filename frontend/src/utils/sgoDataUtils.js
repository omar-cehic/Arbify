/**
 * SGO Data Utilities - Clean data transformation for user-friendly display
 * Based on SGO API documentation and league/market specifications
 */

/**
 * League ID to display name mapping based on SGO documentation
 */
export const LEAGUE_DISPLAY_NAMES = {
  // Hockey Leagues
  'NHL': 'NHL',
  'SHL': 'SHL', 
  'KHL': 'KHL',
  'AHL': 'AHL',
  
  // Soccer Leagues
  'EPL': 'Premier League',
  'BUNDESLIGA': 'Bundesliga',
  'LA_LIGA': 'La Liga',
  'FR_LIGUE_1': 'Ligue 1',
  'IT_SERIE_A': 'Serie A',
  'BR_SERIE_A': 'Serie A (Brazil)',
  'MLS': 'MLS',
  'LIGA_MX': 'Liga MX',
  'UEFA_CHAMPIONS_LEAGUE': 'Champions League',
  'UEFA_EUROPA_LEAGUE': 'Europa League',
  'INTERNATIONAL_SOCCER': 'International',
  
  // Handball Leagues
  'IHF_SUPER_GLOBE': 'IHF Super Globe',
  'EHF_EURO_CUP': 'EHF Euro Cup',
  'ASOBAL': 'ASOBAL',
  'SEHA': 'SEHA League',
  'EHF_EURO': 'EHF Euro',
  
  // Add more as needed...
};

/**
 * Sport icons mapping
 */
export const SPORT_ICONS = {
  'HOCKEY': '🏒',
  'SOCCER': '⚽',
  'FOOTBALL': '🏈',
  'BASKETBALL': '🏀',
  'BASEBALL': '⚾',
  'TENNIS': '🎾',
  'HANDBALL': '🤾',
  'MMA': '🥊'
};

/**
 * Get clean league display name
 * @param {string} leagueId - SGO league ID
 * @param {string} sport - Sport type for fallback
 * @returns {string} User-friendly league name
 */
export const getLeagueDisplayName = (leagueId, sport = '') => {
  if (!leagueId || leagueId === 'unknown') {
    return sport ? `${sport} League` : 'Unknown League';
  }
  
  return LEAGUE_DISPLAY_NAMES[leagueId] || leagueId;
};

/**
 * Get sport icon
 * @param {string} sport - Sport type
 * @returns {string} Emoji icon
 */
export const getSportIcon = (sport) => {
  return SPORT_ICONS[sport?.toUpperCase()] || '🏆';
};

/**
 * Simplify market description for user-friendly display
 * @param {string} marketType - Technical market type
 * @param {string} sport - Sport type for context
 * @param {Object} marketData - Additional market data (line, etc.)
 * @returns {string} Simplified market name
 */
export const simplifyMarketName = (marketType, sport = '', marketData = {}) => {
  const sportUpper = sport?.toUpperCase();
  const marketLower = marketType?.toLowerCase();
  
  // Handle Over/Under markets
  if (marketLower.includes('over/under') || marketLower.includes('ou') || marketType === 'totals') {
    if (sportUpper === 'HOCKEY' || sportUpper === 'SOCCER' || sportUpper === 'HANDBALL') {
      return 'Total Goals O/U';
    }
    if (sportUpper === 'BASKETBALL' || sportUpper === 'FOOTBALL') {
      return 'Total Points O/U';
    }
    if (sportUpper === 'BASEBALL') {
      return 'Total Runs O/U';
    }
    if (sportUpper === 'TENNIS') {
      return 'Total Games O/U';
    }
    return 'Total O/U';
  }
  
  // Handle Team Goals Over/Under (specific to hockey/soccer)
  if (marketLower.includes('team goals') || marketLower.includes('team points')) {
    if (sportUpper === 'HOCKEY' || sportUpper === 'SOCCER') {
      return 'Team Goals O/U';
    }
    return 'Team Points O/U';
  }
  
  // Keep standard betting terms as-is
  if (marketLower.includes('moneyline') || marketLower.includes('ml')) {
    return 'Moneyline';
  }
  
  if (marketLower.includes('spread') || marketLower.includes('sp')) {
    return 'Point Spread';
  }
  
  // Handle 3-way markets
  if (marketLower.includes('3way') || marketLower.includes('3-way')) {
    return '3-Way Moneyline';
  }
  
  // Default: clean up technical jargon
  return marketType
    .replace(/\(Game\)/g, '')
    .replace(/\(Full Match\)/g, '')
    .replace(/\(Full Game\)/g, '')
    .replace(/- \*Check.*?\*/g, '')
    .trim();
};

/**
 * Format game time to EST with user-friendly display
 * @param {string} isoTimeString - ISO datetime string
 * @returns {string} Formatted time in EST
 */
export const formatGameTime = (isoTimeString) => {
  if (!isoTimeString) return 'Time TBD';
  
  try {
    const date = new Date(isoTimeString);
    
    // Convert to EST (UTC-5) or EDT (UTC-4) automatically
    const options = {
      timeZone: 'America/New_York',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      month: 'short',
      day: 'numeric'
    };
    
    const formatter = new Intl.DateTimeFormat('en-US', options);
    const formatted = formatter.format(date);
    
    // Add EST/EDT suffix
    const now = new Date();
    const isEDT = now.getTimezoneOffset() === 240; // EDT is UTC-4 (240 minutes)
    const timezone = isEDT ? 'EDT' : 'EST';
    
    return `${formatted} ${timezone}`;
  } catch (error) {
    console.error('Error formatting game time:', error);
    return 'Time TBD';
  }
};

/**
 * Extract bookmaker names from best odds structure
 * @param {Object} bestOdds - SGO best odds object
 * @returns {Array} Array of bookmaker names [bookmaker1, bookmaker2]
 */
export const extractBookmakerNames = (bestOdds) => {
  if (!bestOdds) return ['Unknown', 'Unknown'];
  
  const bookmakers = [];
  
  if (bestOdds.side1?.bookmaker) {
    bookmakers.push(bestOdds.side1.bookmaker);
  }
  
  if (bestOdds.side2?.bookmaker) {
    bookmakers.push(bestOdds.side2.bookmaker);
  }
  
  // Handle key-based structure (over/under, home/away, etc.)
  if (bookmakers.length === 0) {
    const sides = Object.values(bestOdds);
    sides.forEach(side => {
      if (side?.bookmaker && !bookmakers.includes(side.bookmaker)) {
        bookmakers.push(side.bookmaker);
      }
    });
  }
  
  // Ensure we have exactly 2 bookmakers - if we have less than 2, it's likely an error
  if (bookmakers.length >= 2) {
    return bookmakers.slice(0, 2);
  } else if (bookmakers.length === 1) {
    // If only one bookmaker found, this is suspicious - log it but don't add 'Unknown'
    console.warn('Only one bookmaker found for arbitrage opportunity:', bookmakers[0]);
    return [bookmakers[0], 'Error: Same bookmaker'];
  } else {
    return ['Unknown', 'Unknown'];
  }
};

/**
 * Clean bookmaker name for display
 * @param {string} bookmakerName - Raw bookmaker name
 * @returns {string} Cleaned bookmaker name
 */
export const cleanBookmakerName = (bookmakerName) => {
  if (!bookmakerName) return 'Unknown';
  
  // Capitalize first letter and handle common variations
  const cleanName = bookmakerName
    .replace(/([a-z])([A-Z])/g, '$1 $2') // Add space before capitals
    .replace(/^./, str => str.toUpperCase()); // Capitalize first letter
  
  // Handle specific cases
  const nameMap = {
    'draftkings': 'DraftKings',
    'fanduel': 'FanDuel',
    'betmgm': 'BetMGM',
    'bet365': 'Bet365',
    'caesars': 'Caesars',
    'pinnacle': 'Pinnacle',
    'bovada': 'Bovada',
    'betonline': 'BetOnline',
    'mybookie': 'MyBookie'
  };
  
  return nameMap[bookmakerName.toLowerCase()] || cleanName;
};

/**
 * Generate clean opportunity card data
 * @param {Object} opportunity - Raw SGO opportunity data
 * @returns {Object} Clean card data for display
 */
export const generateCleanCardData = (opportunity) => {
  const sport = opportunity.sport || 'UNKNOWN';
  const league = opportunity.league || 'unknown';
  const bookmakers = extractBookmakerNames(opportunity.best_odds);
  
  // Use backend market_description if available, otherwise fall back to simplifyMarketName
  let marketDisplay;
  if (opportunity.market_description) {
    marketDisplay = opportunity.market_description;
  } else if (opportunity.detailed_market_description) {
    marketDisplay = opportunity.detailed_market_description;
  } else {
    marketDisplay = simplifyMarketName(opportunity.market_type, sport, opportunity.best_odds);
  }
  
  return {
    id: opportunity.id,
    sportIcon: getSportIcon(sport),
    league: getLeagueDisplayName(league, sport),
    profit: opportunity.profit_percentage,
    gameTime: formatGameTime(opportunity.start_time || opportunity.commence_time),
    homeTeam: opportunity.home_team,
    awayTeam: opportunity.away_team,
    bookmaker1: cleanBookmakerName(bookmakers[0]),
    bookmaker2: cleanBookmakerName(bookmakers[1]),
    market: marketDisplay,
    rawOpportunity: opportunity // Keep original data for calculator
  };
};
