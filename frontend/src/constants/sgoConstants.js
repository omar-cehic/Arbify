// Complete SGO Pro Plan Data - 53 Leagues & 82 Bookmakers
// Based on the user's actual SGO Pro plan specifications

export const SGO_SPORTS = [
  // American Football
  { key: 'NFL', title: 'NFL', category: 'American Football' },
  { key: 'NCAAF', title: 'College Football', category: 'American Football' },
  { key: 'CFL', title: 'CFL', category: 'American Football' },
  { key: 'XFL', title: 'XFL', category: 'American Football' },
  { key: 'USFL', title: 'USFL', category: 'American Football' },

  // Basketball
  { key: 'NBA', title: 'NBA', category: 'Basketball' },
  { key: 'NCAAB', title: 'College Basketball', category: 'Basketball' },
  { key: 'WNBA', title: 'WNBA', category: 'Basketball' },
  { key: 'NBA_G_LEAGUE', title: 'NBA G-League', category: 'Basketball' },

  // Baseball
  { key: 'MLB', title: 'MLB', category: 'Baseball' },
  { key: 'NPB', title: 'NPB', category: 'Baseball' },
  { key: 'KBO', title: 'KBO', category: 'Baseball' },
  { key: 'MLB_MINORS', title: 'MLB Minors', category: 'Baseball' },
  { key: 'CPBL', title: 'CPBL', category: 'Baseball' },
  { key: 'LBPRC', title: 'LBPRC', category: 'Baseball' },
  { key: 'LIDOM', title: 'LIDOM', category: 'Baseball' },
  { key: 'LMP', title: 'LMP', category: 'Baseball' },
  { key: 'LVBP', title: 'LVBP', category: 'Baseball' },
  { key: 'WBC', title: 'WBC', category: 'Baseball' },

  // Ice Hockey
  { key: 'NHL', title: 'NHL', category: 'Ice Hockey' },
  { key: 'AHL', title: 'AHL', category: 'Ice Hockey' },
  { key: 'KHL', title: 'KHL', category: 'Ice Hockey' },
  { key: 'SHL', title: 'SHL', category: 'Ice Hockey' },

  // Soccer
  { key: 'PREMIER_LEAGUE', title: 'Premier League', category: 'Soccer' },
  { key: 'CHAMPIONS_LEAGUE', title: 'Champions League', category: 'Soccer' },
  { key: 'LA_LIGA', title: 'La Liga', category: 'Soccer' },
  { key: 'BUNDESLIGA', title: 'Bundesliga', category: 'Soccer' },
  { key: 'SERIE_A', title: 'Serie A Italy', category: 'Soccer' },
  { key: 'LIGUE_1', title: 'Ligue 1', category: 'Soccer' },
  { key: 'BRASILEIRO_SERIE_A', title: 'Brasileiro Série A', category: 'Soccer' },
  { key: 'LIGA_MX', title: 'Liga MX', category: 'Soccer' },
  { key: 'MLS', title: 'MLS', category: 'Soccer' },
  { key: 'UEFA_EUROPA_LEAGUE', title: 'UEFA Europa League', category: 'Soccer' },
  { key: 'INTERNATIONAL_SOCCER', title: 'International Soccer', category: 'Soccer' },

  // Tennis
  { key: 'ATP', title: 'ATP', category: 'Tennis' },
  { key: 'WTA', title: 'Women\'s Tennis', category: 'Tennis' },

  // Golf
  { key: 'PGA_MEN', title: 'PGA Men', category: 'Golf' },
  { key: 'LIV_GOLF', title: 'LIV Golf', category: 'Golf' },

  // Mixed Martial Arts
  { key: 'UFC', title: 'UFC', category: 'Mixed Martial Arts' },

  // Handball
  { key: 'EHF_EUROPEAN_LEAGUE', title: 'EHF European League', category: 'Handball' },
  { key: 'EHF_EUROPEAN_CUP', title: 'EHF European Cup', category: 'Handball' },
  { key: 'IHF_SUPER_GLOBE', title: 'IHF Super Globe', category: 'Handball' },
  { key: 'LIGA_ASOBAL', title: 'Liga ASOBAL', category: 'Handball' },
  { key: 'SEHA_LIGA', title: 'SEHA Liga', category: 'Handball' },

  // Entertainment & Politics
  { key: 'POLITICS', title: 'Politics', category: 'Markets' },
  { key: 'TV', title: 'TV', category: 'Markets' },
  { key: 'CELEBRITIES', title: 'Celebrities', category: 'Markets' },
  { key: 'EVENTS', title: 'Events', category: 'Markets' },
  { key: 'FUN', title: 'Fun', category: 'Markets' },
  { key: 'MOVIES', title: 'Movies', category: 'Markets' },
  { key: 'MUSIC', title: 'Music', category: 'Markets' },
  { key: 'WEATHER', title: 'Weather', category: 'Markets' }
];

// 82 Bookmakers from SGO Pro Plan - Properly categorized by region
export const SGO_BOOKMAKERS = [
  // US Bookmakers (Major licensed US sportsbooks)
  { key: 'fanduel', name: 'FanDuel', region: 'US' },
  { key: 'draftkings', name: 'DraftKings', region: 'US' },
  { key: 'betmgm', name: 'BetMGM', region: 'US' },
  { key: 'caesars', name: 'Caesars', region: 'US' },
  { key: 'espnbet', name: 'ESPN BET', region: 'US' },
  { key: 'bovada', name: 'Bovada', region: 'US' },
  { key: 'unibet', name: 'Unibet', region: 'US' },
  { key: 'pointsbet', name: 'PointsBet', region: 'US' },
  { key: 'williamhill', name: 'William Hill', region: 'US' },
  { key: 'ballybet', name: 'Bally Bet', region: 'US' },
  { key: 'barstool', name: 'Barstool', region: 'US' },
  { key: 'betonline', name: 'BetOnline', region: 'US' },
  { key: 'betparx', name: 'BetPARX', region: 'US' },
  { key: 'betrivers', name: 'BetRivers', region: 'US' },
  { key: 'betus', name: 'BetUS', region: 'US' },
  { key: 'betfred', name: 'Betfred', region: 'US' },
  { key: 'betr', name: 'Betr Sportsbook', region: 'US' },
  { key: 'betway', name: 'Betway', region: 'US' },
  { key: 'everygame', name: 'Everygame', region: 'US' },
  { key: 'foxbet', name: 'FOX Bet', region: 'US' },
  { key: 'fliff', name: 'Fliff', region: 'US' },
  { key: 'fourwinds', name: 'FourWinds', region: 'US' },
  { key: 'gtbets', name: 'GTbets', region: 'US' },
  { key: 'hardrockbet', name: 'Hard Rock Bet', region: 'US' },
  { key: 'hotstreak', name: 'HotStreak', region: 'US' },
  { key: 'leovegas', name: 'LeoVegas', region: 'US' },
  { key: 'livescorebet', name: 'LiveScore Bet', region: 'US' },
  { key: 'marathonbet', name: 'Marathon Bet', region: 'US' },
  { key: 'matchbook', name: 'Matchbook', region: 'US' },
  { key: 'mrgreen', name: 'Mr Green', region: 'US' },
  { key: 'mybookie', name: 'MyBookie', region: 'US' },
  { key: 'northstarbets', name: 'NorthStar Bets', region: 'US' },
  { key: 'parlayplay', name: 'ParlayPlay', region: 'US' },
  { key: 'playup', name: 'PlayUp', region: 'US' },
  { key: 'primesports', name: 'Prime Sports', region: 'US' },
  { key: 'sisportsbook', name: 'SI Sportsbook', region: 'US' },
  { key: 'sleeper', name: 'Sleeper', region: 'US' },
  { key: 'sportsbetting', name: 'SportsBetting.ag', region: 'US' },
  { key: 'sporttrade', name: 'Sporttrade', region: 'US' },
  { key: 'stake', name: 'Stake', region: 'US' },
  { key: 'superbook', name: 'Superbook', region: 'US' },
  { key: 'underdog', name: 'Underdog', region: 'US' },
  { key: 'windcreek', name: 'Wind Creek (Betfred PA)', region: 'US' },
  { key: 'wynnbet', name: 'WynnBet', region: 'US' },
  { key: 'thescorebet', name: 'theScore Bet', region: 'US' },
  { key: 'circa', name: 'Circa', region: 'US' },
  { key: 'fanatics', name: 'Fanatics', region: 'US' },
  { key: 'pinnacle', name: 'Pinnacle', region: 'US' },
  { key: 'prizepiicks', name: 'PrizePicks', region: 'US' },

  // International Bookmakers
  { key: '1xbet', name: '1xBet', region: 'INTL' },
  { key: 'sport888', name: '888 Sport', region: 'INTL' },
  { key: 'betvictor', name: 'Bet Victor', region: 'INTL' },
  { key: 'betanysports', name: 'BetAnySports', region: 'INTL' },
  { key: 'betclic', name: 'BetClic', region: 'INTL' },
  { key: 'betfairexchange', name: 'Betfair Exchange', region: 'INTL' },
  { key: 'betfair', name: 'Betfair Sportsbook', region: 'INTL' },
  { key: 'betsafe', name: 'Betsafe', region: 'INTL' },
  { key: 'betsson', name: 'Betsson', region: 'INTL' },
  { key: 'bluebet', name: 'BlueBet', region: 'INTL' },
  { key: 'bodog', name: 'Bodog', region: 'INTL' },
  { key: 'bookmakereu', name: 'Bookmaker.eu', region: 'INTL' },
  { key: 'boombet', name: 'BoomBet', region: 'INTL' },
  { key: 'boylesports', name: 'BoyleSports', region: 'INTL' },
  { key: 'casumo', name: 'Casumo', region: 'INTL' },
  { key: 'coolbet', name: 'Coolbet', region: 'INTL' },
  { key: 'coral', name: 'Coral', region: 'INTL' },
  { key: 'grosvenor', name: 'Grosvenor', region: 'INTL' },
  { key: 'ladbrokes', name: 'Ladbrokes', region: 'INTL' },
  { key: 'lowvig', name: 'LowVig', region: 'INTL' },
  { key: 'neds', name: 'Neds', region: 'INTL' },
  { key: 'nordicbet', name: 'NordicBet', region: 'INTL' },
  { key: 'paddypower', name: 'Paddy Power', region: 'INTL' },
  { key: 'prophetexchange', name: 'Prophet Exchange', region: 'INTL' },
  { key: 'skybet', name: 'Sky Bet', region: 'INTL' },
  { key: 'sportsbet', name: 'SportsBet', region: 'INTL' },
  { key: 'suprabets', name: 'Suprabets', region: 'INTL' },
  { key: 'tab', name: 'TAB', region: 'INTL' },
  { key: 'tabtouch', name: 'TABtouch', region: 'INTL' },
  { key: 'tipico', name: 'Tipico', region: 'INTL' },
  { key: 'topsport', name: 'TopSport', region: 'INTL' },
  { key: 'virginbet', name: 'Virgin Bet', region: 'INTL' },
  { key: 'bet365', name: 'Bet365', region: 'INTL' }
];

// Group sports by category for easier navigation
export const SGO_SPORTS_BY_CATEGORY = SGO_SPORTS.reduce((acc, sport) => {
  if (!acc[sport.category]) acc[sport.category] = [];
  acc[sport.category].push(sport);
  return acc;
}, {});

// Group bookmakers by region
export const SGO_BOOKMAKERS_BY_REGION = SGO_BOOKMAKERS.reduce((acc, bookmaker) => {
  if (!acc[bookmaker.region]) acc[bookmaker.region] = [];
  acc[bookmaker.region].push(bookmaker);
  return acc;
}, {});

// Default preferences for new users
// Default preferences for new users
export const DEFAULT_SGO_PREFERENCES = {
  // Default to ALL major sports categories
  preferred_sports: ['NFL', 'NBA', 'MLB', 'NHL', 'NCAAF', 'NCAAB', 'PREMIER_LEAGUE', 'LA_LIGA', 'BUNDESLIGA', 'SERIE_A', 'LIGUE_1', 'MLS', 'UFC', 'TENNIS'],
  // Default to ALL bookmakers to ensure no arbitrage is hidden
  preferred_bookmakers: SGO_BOOKMAKERS.map(bm => bm.key),
  minimum_profit_threshold: 0.0,
  odds_format: 'american'
};

// Sort options for opportunities
export const SORT_OPTIONS = [
  { key: 'profit_desc', label: 'Highest Profit' },
  { key: 'profit_asc', label: 'Lowest Profit' },
  { key: 'time_asc', label: 'Time (Soonest)' },
  { key: 'time_desc', label: 'Time (Latest)' }
];

// Profit percentage ranges for filtering
export const PROFIT_RANGES = [
  { key: 'low', label: '0.5% - 2%', min: 0.5, max: 2.0 },
  { key: 'medium', label: '2% - 5%', min: 2.0, max: 5.0 },
  { key: 'high', label: '5% - 10%', min: 5.0, max: 10.0 },
  { key: 'very_high', label: '10%+', min: 10.0, max: 100.0 }
];
