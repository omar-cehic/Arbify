import React, { useState, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { toast } from 'react-toastify';
import axios from 'axios';

const ArbitrageFinder = () => {
  const [arbitrageOpportunities, setArbitrageOpportunities] = useState([]);
  const [filteredOpportunities, setFilteredOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedSports, setSelectedSports] = useState([]);
  const [selectedBookmakers, setSelectedBookmakers] = useState([]);
  const [minProfit, setMinProfit] = useState(0.5);
  const [oddsFormat, setOddsFormat] = useState('decimal');
  const [sortBy, setSortBy] = useState('profit_desc'); // Add sorting state
  const { user } = useAuth();

  // Helper function to format match timing
  const formatMatchTime = (commence_time) => {
    if (!commence_time) return 'Time TBD';
    
    try {
      const matchDate = new Date(commence_time);
      const now = new Date();
      const diffHours = (matchDate - now) / (1000 * 60 * 60);
      
      if (diffHours < 0) {
        return 'Live/Finished';
      } else if (diffHours < 1) {
        const diffMinutes = Math.round(diffHours * 60);
        return `Starting in ${diffMinutes}m`;
      } else if (diffHours < 24) {
        const hours = Math.round(diffHours);
        return `Starting in ${hours}h`;
      } else {
        return matchDate.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
      }
    } catch (error) {
      return 'Time TBD';
    }
  };

  // Sorting function for opportunities
  const sortOpportunities = (opportunities, sortMethod) => {
    const sorted = [...opportunities];
    
    switch (sortMethod) {
      case 'profit_desc':
        return sorted.sort((a, b) => b.profit_percentage - a.profit_percentage);
      case 'profit_asc':
        return sorted.sort((a, b) => a.profit_percentage - b.profit_percentage);
      case 'time_asc':
        return sorted.sort((a, b) => {
          if (!a.commence_time) return 1;
          if (!b.commence_time) return -1;
          return new Date(a.commence_time) - new Date(b.commence_time);
        });
      case 'time_desc':
        return sorted.sort((a, b) => {
          if (!a.commence_time) return 1;
          if (!b.commence_time) return -1;
          return new Date(b.commence_time) - new Date(a.commence_time);
        });
      case 'match_asc':
        return sorted.sort((a, b) => a.match.localeCompare(b.match));
      case 'match_desc':
        return sorted.sort((a, b) => b.match.localeCompare(a.match));
      default:
        return sorted;
    }
  };

  // Complete sports list from your API documentation
  const allSports = [
    // American Football
    { key: 'americanfootball_cfl', title: 'CFL', category: 'American Football' },
    { key: 'americanfootball_ncaaf', title: 'NCAAF', category: 'American Football' },
    { key: 'americanfootball_ncaaf_championship_winner', title: 'NCAAF Championship Winner', category: 'American Football' },
    { key: 'americanfootball_nfl', title: 'NFL', category: 'American Football' },
    { key: 'americanfootball_nfl_preseason', title: 'NFL Preseason', category: 'American Football' },
    { key: 'americanfootball_nfl_super_bowl_winner', title: 'NFL Super Bowl Winner', category: 'American Football' },
    { key: 'americanfootball_ufl', title: 'UFL', category: 'American Football' },
    
    // Aussie Rules
    { key: 'aussierules_afl', title: 'AFL', category: 'Aussie Rules' },
    
    // Baseball
    { key: 'baseball_mlb', title: 'MLB', category: 'Baseball' },
    { key: 'baseball_mlb_preseason', title: 'MLB Preseason', category: 'Baseball' },
    { key: 'baseball_mlb_world_series_winner', title: 'MLB World Series Winner', category: 'Baseball' },
    { key: 'baseball_milb', title: 'Minor League Baseball', category: 'Baseball' },
    { key: 'baseball_npb', title: 'NPB', category: 'Baseball' },
    { key: 'baseball_kbo', title: 'KBO League', category: 'Baseball' },
    { key: 'baseball_ncaa', title: 'NCAA Baseball', category: 'Baseball' },
    
    // Basketball
    { key: 'basketball_euroleague', title: 'Basketball Euroleague', category: 'Basketball' },
    { key: 'basketball_nba', title: 'NBA', category: 'Basketball' },
    { key: 'basketball_nba_preseason', title: 'NBA Preseason', category: 'Basketball' },
    { key: 'basketball_nba_summer_league', title: 'NBA Summer League', category: 'Basketball' },
    { key: 'basketball_nba_championship_winner', title: 'NBA Championship Winner', category: 'Basketball' },
    { key: 'basketball_wnba', title: 'WNBA', category: 'Basketball' },
    { key: 'basketball_ncaab', title: 'NCAAB', category: 'Basketball' },
    { key: 'basketball_wncaab', title: 'WNCAAB', category: 'Basketball' },
    { key: 'basketball_ncaab_championship_winner', title: 'NCAAB Championship Winner', category: 'Basketball' },
    { key: 'basketball_nbl', title: 'NBL (Australia)', category: 'Basketball' },
    
    // Boxing
    { key: 'boxing_boxing', title: 'Boxing', category: 'Boxing' },
    
    // Cricket
    { key: 'cricket_big_bash', title: 'Big Bash', category: 'Cricket' },
    { key: 'cricket_caribbean_premier_league', title: 'Caribbean Premier League', category: 'Cricket' },
    { key: 'cricket_icc_trophy', title: 'ICC Champions Trophy', category: 'Cricket' },
    { key: 'cricket_icc_world_cup', title: 'ICC World Cup', category: 'Cricket' },
    { key: 'cricket_international_t20', title: 'International Twenty20', category: 'Cricket' },
    { key: 'cricket_ipl', title: 'IPL', category: 'Cricket' },
    { key: 'cricket_odi', title: 'One Day Internationals', category: 'Cricket' },
    { key: 'cricket_psl', title: 'Pakistan Super League', category: 'Cricket' },
    { key: 'cricket_t20_blast', title: 'T20 Blast', category: 'Cricket' },
    { key: 'cricket_test_match', title: 'Test Matches', category: 'Cricket' },
    { key: 'cricket_the_hundred', title: 'The Hundred', category: 'Cricket' },
    
    // Golf
    { key: 'golf_masters_tournament_winner', title: 'Masters Tournament Winner', category: 'Golf' },
    { key: 'golf_pga_championship_winner', title: 'PGA Championship Winner', category: 'Golf' },
    { key: 'golf_the_open_championship_winner', title: 'The Open Winner', category: 'Golf' },
    { key: 'golf_us_open_winner', title: 'US Open Winner', category: 'Golf' },
    
    // Ice Hockey
    { key: 'icehockey_nhl', title: 'NHL', category: 'Ice Hockey' },
    { key: 'icehockey_ahl', title: 'AHL', category: 'Ice Hockey' },
    { key: 'icehockey_nhl_championship_winner', title: 'NHL Championship Winner', category: 'Ice Hockey' },
    { key: 'icehockey_liiga', title: 'Finnish Liiga', category: 'Ice Hockey' },
    { key: 'icehockey_mestis', title: 'Finnish Mestis', category: 'Ice Hockey' },
    { key: 'icehockey_sweden_hockey_league', title: 'SHL', category: 'Ice Hockey' },
    { key: 'icehockey_sweden_allsvenskan', title: 'HockeyAllsvenskan', category: 'Ice Hockey' },
    
    // Soccer (Major Leagues)
    { key: 'soccer_epl', title: 'English Premier League', category: 'Soccer' },
    { key: 'soccer_efl_champ', title: 'Championship', category: 'Soccer' },
    { key: 'soccer_england_league1', title: 'League 1', category: 'Soccer' },
    { key: 'soccer_england_league2', title: 'League 2', category: 'Soccer' },
    { key: 'soccer_fa_cup', title: 'FA Cup', category: 'Soccer' },
    { key: 'soccer_england_efl_cup', title: 'EFL Cup', category: 'Soccer' },
    { key: 'soccer_spain_la_liga', title: 'La Liga - Spain', category: 'Soccer' },
    { key: 'soccer_spain_segunda_division', title: 'La Liga 2 - Spain', category: 'Soccer' },
    { key: 'soccer_germany_bundesliga', title: 'Bundesliga - Germany', category: 'Soccer' },
    { key: 'soccer_germany_bundesliga2', title: 'Bundesliga 2 - Germany', category: 'Soccer' },
    { key: 'soccer_germany_liga3', title: '3. Liga - Germany', category: 'Soccer' },
    { key: 'soccer_italy_serie_a', title: 'Serie A - Italy', category: 'Soccer' },
    { key: 'soccer_italy_serie_b', title: 'Serie B - Italy', category: 'Soccer' },
    { key: 'soccer_france_ligue_one', title: 'Ligue 1 - France', category: 'Soccer' },
    { key: 'soccer_france_ligue_two', title: 'Ligue 2 - France', category: 'Soccer' },
    { key: 'soccer_netherlands_eredivisie', title: 'Dutch Eredivisie', category: 'Soccer' },
    { key: 'soccer_portugal_primeira_liga', title: 'Primeira Liga - Portugal', category: 'Soccer' },
    { key: 'soccer_usa_mls', title: 'MLS', category: 'Soccer' },
    { key: 'soccer_mexico_ligamx', title: 'Liga MX', category: 'Soccer' },
    { key: 'soccer_brazil_campeonato', title: 'Brazil Série A', category: 'Soccer' },
    { key: 'soccer_brazil_serie_b', title: 'Brazil Série B', category: 'Soccer' },
    { key: 'soccer_argentina_primera_division', title: 'Primera División - Argentina', category: 'Soccer' },
    { key: 'soccer_chile_campeonato', title: 'Primera División - Chile', category: 'Soccer' },
    { key: 'soccer_australia_aleague', title: 'A-League', category: 'Soccer' },
    { key: 'soccer_austria_bundesliga', title: 'Austrian Football Bundesliga', category: 'Soccer' },
    { key: 'soccer_belgium_first_div', title: 'Belgium First Div', category: 'Soccer' },
    { key: 'soccer_china_superleague', title: 'Super League - China', category: 'Soccer' },
    { key: 'soccer_denmark_superliga', title: 'Denmark Superliga', category: 'Soccer' },
    { key: 'soccer_finland_veikkausliiga', title: 'Veikkausliiga - Finland', category: 'Soccer' },
    { key: 'soccer_greece_super_league', title: 'Super League - Greece', category: 'Soccer' },
    { key: 'soccer_japan_j_league', title: 'J League', category: 'Soccer' },
    { key: 'soccer_korea_kleague1', title: 'K League 1', category: 'Soccer' },
    { key: 'soccer_league_of_ireland', title: 'League of Ireland', category: 'Soccer' },
    { key: 'soccer_norway_eliteserien', title: 'Eliteserien - Norway', category: 'Soccer' },
    { key: 'soccer_poland_ekstraklasa', title: 'Ekstraklasa - Poland', category: 'Soccer' },
    { key: 'soccer_spl', title: 'Premiership - Scotland', category: 'Soccer' },
    { key: 'soccer_sweden_allsvenskan', title: 'Allsvenskan - Sweden', category: 'Soccer' },
    { key: 'soccer_sweden_superettan', title: 'Superettan - Sweden', category: 'Soccer' },
    { key: 'soccer_switzerland_superleague', title: 'Swiss Superleague', category: 'Soccer' },
    { key: 'soccer_turkey_super_league', title: 'Turkey Super League', category: 'Soccer' },
    
    // UEFA Competitions
    { key: 'soccer_uefa_champs_league', title: 'UEFA Champions League', category: 'Soccer' },
    { key: 'soccer_uefa_champs_league_qualification', title: 'UEFA Champions League Qualification', category: 'Soccer' },
    { key: 'soccer_uefa_europa_league', title: 'UEFA Europa League', category: 'Soccer' },
    { key: 'soccer_uefa_europa_conference_league', title: 'UEFA Europa Conference League', category: 'Soccer' },
    { key: 'soccer_uefa_european_championship', title: 'UEFA Euro 2024', category: 'Soccer' },
    { key: 'soccer_uefa_euro_qualification', title: 'UEFA Euro Qualification', category: 'Soccer' },
    { key: 'soccer_uefa_nations_league', title: 'UEFA Nations League', category: 'Soccer' },
    
    // International Soccer
    { key: 'soccer_fifa_world_cup', title: 'FIFA World Cup', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_womens', title: 'FIFA Women\'s World Cup', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_winner', title: 'FIFA World Cup Winner', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_qualifiers_europe', title: 'FIFA World Cup Qualifiers - Europe', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_qualifiers_south_america', title: 'FIFA World Cup Qualifiers - South America', category: 'Soccer' },
    { key: 'soccer_fifa_club_world_cup', title: 'FIFA Club World Cup', category: 'Soccer' },
    { key: 'soccer_conmebol_copa_america', title: 'Copa América', category: 'Soccer' },
    { key: 'soccer_conmebol_copa_libertadores', title: 'Copa Libertadores', category: 'Soccer' },
    { key: 'soccer_conmebol_copa_sudamericana', title: 'Copa Sudamericana', category: 'Soccer' },
    { key: 'soccer_concacaf_gold_cup', title: 'CONCACAF Gold Cup', category: 'Soccer' },
    { key: 'soccer_concacaf_leagues_cup', title: 'CONCACAF Leagues Cup', category: 'Soccer' },
    { key: 'soccer_africa_cup_of_nations', title: 'Africa Cup of Nations', category: 'Soccer' },
    
    // Tennis
    { key: 'tennis_atp_aus_open_singles', title: 'ATP Australian Open', category: 'Tennis' },
    { key: 'tennis_atp_french_open', title: 'ATP French Open', category: 'Tennis' },
    { key: 'tennis_atp_wimbledon', title: 'ATP Wimbledon', category: 'Tennis' },
    { key: 'tennis_atp_us_open', title: 'ATP US Open', category: 'Tennis' },
    { key: 'tennis_atp_canadian_open', title: 'ATP Canadian Open', category: 'Tennis' },
    { key: 'tennis_atp_china_open', title: 'ATP China Open', category: 'Tennis' },
    { key: 'tennis_atp_cincinnati_open', title: 'ATP Cincinnati Open', category: 'Tennis' },
    { key: 'tennis_atp_dubai', title: 'ATP Dubai Championships', category: 'Tennis' },
    { key: 'tennis_atp_indian_wells', title: 'ATP Indian Wells', category: 'Tennis' },
    { key: 'tennis_atp_italian_open', title: 'ATP Italian Open', category: 'Tennis' },
    { key: 'tennis_atp_madrid_open', title: 'ATP Madrid Open', category: 'Tennis' },
    { key: 'tennis_atp_miami_open', title: 'ATP Miami Open', category: 'Tennis' },
    { key: 'tennis_atp_monte_carlo_masters', title: 'ATP Monte-Carlo Masters', category: 'Tennis' },
    { key: 'tennis_atp_paris_masters', title: 'ATP Paris Masters', category: 'Tennis' },
    { key: 'tennis_atp_qatar_open', title: 'ATP Qatar Open', category: 'Tennis' },
    { key: 'tennis_atp_shanghai_masters', title: 'ATP Shanghai Masters', category: 'Tennis' },
    { key: 'tennis_wta_aus_open_singles', title: 'WTA Australian Open', category: 'Tennis' },
    { key: 'tennis_wta_french_open', title: 'WTA French Open', category: 'Tennis' },
    { key: 'tennis_wta_wimbledon', title: 'WTA Wimbledon', category: 'Tennis' },
    { key: 'tennis_wta_us_open', title: 'WTA US Open', category: 'Tennis' },
    { key: 'tennis_wta_canadian_open', title: 'WTA Canadian Open', category: 'Tennis' },
    { key: 'tennis_wta_china_open', title: 'WTA China Open', category: 'Tennis' },
    { key: 'tennis_wta_cincinnati_open', title: 'WTA Cincinnati Open', category: 'Tennis' },
    { key: 'tennis_wta_dubai', title: 'WTA Dubai Championships', category: 'Tennis' },
    { key: 'tennis_wta_indian_wells', title: 'WTA Indian Wells', category: 'Tennis' },
    { key: 'tennis_wta_italian_open', title: 'WTA Italian Open', category: 'Tennis' },
    { key: 'tennis_wta_madrid_open', title: 'WTA Madrid Open', category: 'Tennis' },
    { key: 'tennis_wta_miami_open', title: 'WTA Miami Open', category: 'Tennis' },
    { key: 'tennis_wta_qatar_open', title: 'WTA Qatar Open', category: 'Tennis' },
    { key: 'tennis_wta_wuhan_open', title: 'WTA Wuhan Open', category: 'Tennis' },
    
    // Mixed Martial Arts
    { key: 'mma_mixed_martial_arts', title: 'MMA', category: 'Mixed Martial Arts' },
    
    // Lacrosse
    { key: 'lacrosse_pll', title: 'Premier Lacrosse League', category: 'Lacrosse' },
    { key: 'lacrosse_ncaa', title: 'NCAA Lacrosse', category: 'Lacrosse' },
    
    // Politics
    { key: 'politics_us_presidential_election_winner', title: 'US Presidential Elections Winner', category: 'Politics' },
    
    // Rugby
    { key: 'rugbyleague_nrl', title: 'NRL', category: 'Rugby League' },
    { key: 'rugbyleague_nrl_state_of_origin', title: 'NRL State of Origin', category: 'Rugby League' },
    { key: 'rugbyunion_six_nations', title: 'Six Nations', category: 'Rugby Union' },
  ];

  // Complete bookmakers list matching your exact website display
  const allBookmakers = [
    // US Bookmakers
    { key: 'betonlineag', title: 'BetOnline.ag', region: 'US' },
    { key: 'betmgm', title: 'BetMGM', region: 'US' },
    { key: 'betrivers', title: 'BetRivers', region: 'US' },
    { key: 'betus', title: 'BetUS', region: 'US' },
    { key: 'bovada', title: 'Bovada', region: 'US' },
    { key: 'williamhill_us', title: 'Caesars', region: 'US' },
    { key: 'draftkings', title: 'DraftKings', region: 'US' },
    { key: 'fanatics', title: 'Fanatics', region: 'US' },
    { key: 'fanduel', title: 'FanDuel', region: 'US' },
    { key: 'lowvig', title: 'LowVig.ag', region: 'US' },
    { key: 'mybookieag', title: 'MyBookie.ag', region: 'US' },
    { key: 'ballybet', title: 'Bally Bet', region: 'US' },
    { key: 'betanysports', title: 'BetAnySports', region: 'US' },
    { key: 'betparx', title: 'betPARX', region: 'US' },
    { key: 'espnbet', title: 'ESPN BET', region: 'US' },
    { key: 'fliff', title: 'Fliff', region: 'US' },
    { key: 'hardrockbet', title: 'Hard Rock Bet', region: 'US' },
    { key: 'rebet', title: 'ReBet', region: 'US' },
    { key: 'windcreek', title: 'Wind Creek (Betfred PA)', region: 'US' },
    
    // US_DFS Bookmakers
    { key: 'pick6', title: 'DraftKings Pick6', region: 'US_DFS' },
    { key: 'prizepicks', title: 'PrizePicks', region: 'US_DFS' },
    { key: 'underdog', title: 'Underdog Fantasy', region: 'US_DFS' },
    
    // US_EX Bookmakers
    { key: 'betopenly', title: 'BetOpenly', region: 'US_EX' },
    { key: 'novig', title: 'Novig', region: 'US_EX' },
    { key: 'prophetx', title: 'ProphetX', region: 'US_EX' },
    
    // UK Bookmakers (exact API keys)
    { key: 'sport888', title: '888sport', region: 'UK' },
    { key: 'betfair_ex_uk', title: 'Betfair Exchange', region: 'UK' },
    { key: 'betfair_sb_uk', title: 'Betfair Sportsbook', region: 'UK' },
    { key: 'betvictor', title: 'Bet Victor', region: 'UK' },
    { key: 'betway', title: 'Betway', region: 'UK' },
    { key: 'boylesports', title: 'BoyleSports', region: 'UK' },
    { key: 'casumo', title: 'Casumo', region: 'UK' },
    { key: 'coral', title: 'Coral', region: 'UK' },
    { key: 'grosvenor', title: 'Grosvenor', region: 'UK' },
    { key: 'ladbrokes_uk', title: 'Ladbrokes', region: 'UK' },
    { key: 'leovegas', title: 'LeoVegas', region: 'UK' },
    { key: 'livescorebet', title: 'LiveScore Bet', region: 'UK' },
    { key: 'matchbook', title: 'Matchbook', region: 'UK' },
    { key: 'paddypower', title: 'Paddy Power', region: 'UK' },
    { key: 'skybet', title: 'Sky Bet', region: 'UK' },
    { key: 'smarkets', title: 'Smarkets', region: 'UK' },
    { key: 'unibet_uk', title: 'Unibet', region: 'UK' },
    { key: 'virginbet', title: 'Virgin Bet', region: 'UK' },
    { key: 'williamhill', title: 'William Hill (UK)', region: 'UK' },
    
    // EU Bookmakers (in exact order from your list)
    { key: 'pinnacle', title: 'Pinnacle', region: 'EU' },
    { key: 'onexbet', title: '1xBet', region: 'EU' },
    { key: 'sport888', title: '888sport', region: 'EU' },
    { key: 'betanysports', title: 'BetAnySports', region: 'EU' },
    { key: 'betclic_fr', title: 'Betclic (FR)', region: 'EU' },
    { key: 'betfair_ex_eu', title: 'Betfair Exchange', region: 'EU' },
    { key: 'betonlineag', title: 'BetOnline.ag', region: 'EU' },
    { key: 'betsson', title: 'Betsson', region: 'EU' },
    { key: 'betvictor', title: 'Bet Victor', region: 'EU' },
    { key: 'coolbet', title: 'Coolbet', region: 'EU' },
    { key: 'everygame', title: 'Everygame', region: 'EU' },
    { key: 'gtbets', title: 'GTbets', region: 'EU' },
    { key: 'marathonbet', title: 'Marathon Bet', region: 'EU' },
    { key: 'matchbook', title: 'Matchbook', region: 'EU' },
    { key: 'mybookieag', title: 'MyBookie.ag', region: 'EU' },
    { key: 'nordicbet', title: 'NordicBet', region: 'EU' },
    { key: 'parionssport_fr', title: 'Parions Sport (FR)', region: 'EU' },
    { key: 'suprabets', title: 'Suprabets', region: 'EU' },
    { key: 'tipico_de', title: 'Tipico (DE)', region: 'EU' },
    { key: 'unibet_fr', title: 'Unibet (FR)', region: 'EU' },
    { key: 'unibet_it', title: 'Unibet (IT)', region: 'EU' },
    { key: 'unibet_nl', title: 'Unibet (NL)', region: 'EU' },
    { key: 'williamhill', title: 'William Hill', region: 'EU' },
    { key: 'winamax_de', title: 'Winamax (DE)', region: 'EU' },
    { key: 'winamax_fr', title: 'Winamax (FR)', region: 'EU' },
    
    // AU Bookmakers (exact order from your list)
    { key: 'sportsbet', title: 'SportsBet', region: 'AU' },
    { key: 'tab', title: 'TAB', region: 'AU' },
    { key: 'ladbrokes_au', title: 'Ladbrokes (AU)', region: 'AU' },
    { key: 'neds', title: 'Neds', region: 'AU' },
    { key: 'pointsbetau', title: 'PointsBet (AU)', region: 'AU' },
    { key: 'betright', title: 'Bet Right', region: 'AU' },
    { key: 'betr_au', title: 'Betr', region: 'AU' },
    { key: 'boombet', title: 'BoomBet', region: 'AU' },
    { key: 'playup', title: 'PlayUp', region: 'AU' },
    { key: 'tabtouch', title: 'TABtouch', region: 'AU' },
    { key: 'betfair_ex_au', title: 'Betfair Exchange (AU)', region: 'AU' },
    { key: 'bet365_au', title: 'Bet365 AU', region: 'AU' },
    { key: 'dabble_au', title: 'Dabble AU', region: 'AU' },
    { key: 'unibet', title: 'Unibet', region: 'AU' },
  ];

  // Fetch real arbitrage opportunities from API
  const fetchArbitrageOpportunities = async () => {
    try {
      setLoading(true);
      console.log('Fetching arbitrage opportunities...');
      
      const response = await axios.get('/api/arbitrage');
      console.log('API Response:', response.data);
      
      if (!response.data.arbitrage_opportunities) {
        console.error('Invalid API response - missing arbitrage_opportunities');
        return;
      }
      
      const opportunities = response.data.arbitrage_opportunities || [];
      console.log(`Received ${opportunities.length} opportunities from API`);
      
      // Transform the opportunities to our display format
      const transformedOpportunities = opportunities.map((opp, index) => {
        // Add detailed logging for the first few opportunities to debug data structure
        if (index < 3) {
          console.log(`DEBUGGING OPPORTUNITY ${index + 1}:`);
          console.log('Full opportunity object:', opp);
          console.log('Market key:', opp.market_key);
          console.log('Market name:', opp.market_name);
          console.log('Best odds object:', opp.best_odds);
          if (opp.best_odds) {
            Object.keys(opp.best_odds).forEach(outcome => {
              console.log(`Outcome "${outcome}":`, opp.best_odds[outcome]);
            });
          }
        }

        const outcomes = Object.keys(opp.best_odds || {});
        const bookmakers = outcomes.map(outcome => 
          opp.best_odds?.[outcome]?.bookmaker || 'Unknown'
        ).filter(b => b !== 'Unknown');
        
        // Validate profit percentage - flag unrealistic profits
        let profitPercentage = opp.profit_percentage || 0;
        
        // Calculate actual arbitrage profit to verify backend data
        const outcomeOdds = outcomes.map(outcome => 
          opp.best_odds[outcome]?.odds || 2.0
        ).filter(odds => odds > 0);
        
        if (outcomeOdds.length >= 2) {
          const totalImpliedProb = outcomeOdds.reduce((sum, odds) => sum + (1 / odds), 0);
          const calculatedProfit = totalImpliedProb < 1 ? ((1 - totalImpliedProb) / totalImpliedProb) * 100 : 0;
          
          // Flag suspiciously high profits and cap them
          if (profitPercentage > 20) {
            console.warn('SUSPICIOUS PROFIT detected:', profitPercentage, '% - calculated:', calculatedProfit.toFixed(2), '%');
            profitPercentage = Math.min(profitPercentage, Math.max(calculatedProfit, 0.5));
          }
        }
        
        // Skip opportunities with invalid profits (only negative/zero)
        if (profitPercentage <= 0) {
          return null;
        }

        // Validate point values for Over/Under and spread bets
        if (opp.market_key && (opp.market_key.includes('total') || opp.market_key.includes('spread'))) {
          const pointValues = outcomes.map(outcome => 
            opp.best_odds[outcome]?.point_value
          ).filter(pv => pv !== null && pv !== undefined);
          
          // For Over/Under and spreads, all point values should be the same (or opposite for spreads)
          if (pointValues.length >= 2) {
            const uniqueAbsValues = [...new Set(pointValues.map(pv => Math.abs(pv)))];
            if (uniqueAbsValues.length > 1) {
              console.warn('MISMATCHED POINT VALUES:', opp.market_key, pointValues, '- skipping opportunity');
              return null;
            }
          }
        }
        
        // Create enhanced details for each outcome with proper stake calculation
        const details = {};
        
        // Calculate proper stakes for arbitrage (total investment of $1000)
        const totalInverse = outcomeOdds.reduce((sum, odds) => sum + (1 / odds), 0);
        
        outcomes.forEach((outcome, idx) => {
          const outcomeData = opp.best_odds?.[outcome] || {};
          const odds = outcomeData.odds || 2.0;
          
          // Calculate proper arbitrage stake
          let stake;
          if (totalInverse < 1) {
            // True arbitrage opportunity - distribute stakes proportionally
            stake = ((1 / odds) / totalInverse) * 1000;
          } else {
            // Fallback to equal distribution
            stake = 1000 / outcomes.length;
          }
          
          // Ensure stake is reasonable (between $50 and $800)
          const clampedStake = Math.max(50, Math.min(800, Math.round(stake)));
          
          // Extract point value from different possible sources
          let pointValue = null;
          if (outcomeData.point_value !== undefined && outcomeData.point_value !== null) {
            pointValue = outcomeData.point_value;
          } else if (outcomeData.point !== undefined && outcomeData.point !== null) {
            pointValue = outcomeData.point;
          } else if (outcome.includes('_')) {
            // Try to extract from outcome name like "Over_5.5"
            const parts = outcome.split('_');
            const lastPart = parts[parts.length - 1];
            if (!isNaN(parseFloat(lastPart))) {
              pointValue = parseFloat(lastPart);
            }
          }
          
          // Clean outcome name for display
          let cleanOutcomeName = outcome;
          if (pointValue !== null && outcome.includes(`_${pointValue}`)) {
            cleanOutcomeName = outcome.replace(`_${pointValue}`, '');
          }

          details[`outcome${idx + 1}`] = {
            bookmaker: outcomeData.bookmaker || 'Unknown',
            odds: odds,
            stake: clampedStake,
            name: cleanOutcomeName,
            pointValue: pointValue,
            marketType: outcomeData.market_type || opp.market_key
          };
        });
        
        return {
          id: `${opp.sport_key}_${opp.match?.home_team}_${opp.match?.away_team}_${index}`,
          match: `${opp.match?.home_team || 'Team A'} vs ${opp.match?.away_team || 'Team B'}`,
          sport: opp.sport_title,
          sport_key: opp.sport_key,
          market_key: opp.market_key || "h2h",
          market_name: opp.market_name || "Head to Head",
          profit_percentage: profitPercentage,
          commence_time: opp.match?.commence_time, // Add match timing
          bookmakers: bookmakers,
          details: details
        };
      }).filter(Boolean); // Remove null entries from validation
      
      setArbitrageOpportunities(transformedOpportunities);
      console.log(`Processed ${transformedOpportunities.length} arbitrage opportunities (after validation)`);
      
    } catch (error) {
      console.error('Error fetching opportunities:', error);
      toast.error('Failed to fetch arbitrage opportunities');
    } finally {
      setLoading(false);
    }
  };

  // Apply filters to opportunities
  const applyFilters = () => {
    console.log(`Starting filter process with ${arbitrageOpportunities.length} total opportunities`);
    console.log(`Filters - Sports: ${selectedSports.length}, Bookmakers: ${selectedBookmakers.length}, MinProfit: ${minProfit}%`);

    // CRITICAL REQUIREMENT: User must select at least 1 sport AND 2+ bookmakers
    const hasRequiredFilters = selectedSports.length >= 1 && selectedBookmakers.length >= 2;
    
    if (!hasRequiredFilters) {
      console.log('🚨 FILTER REQUIREMENTS NOT MET:');
      console.log('🚨 Sports selected:', selectedSports.length, '(need ≥1)');
      console.log('🚨 Bookmakers selected:', selectedBookmakers.length, '(need ≥2)');
      console.log('🚨 SHOWING EMPTY RESULTS');
      setFilteredOpportunities([]);
      return;
    }

    console.log('Filter requirements met - proceeding with filtering');
    
    let filtered = arbitrageOpportunities;

    // Filter by selected sports
    const beforeSportsCount = filtered.length;
    filtered = filtered.filter(opp => selectedSports.includes(opp.sport_key));
    console.log(`After sports filter: ${filtered.length} (filtered out ${beforeSportsCount - filtered.length})`);
    
    if (filtered.length === 0) {
      console.log('🚨 Sport filter eliminated all opportunities');
      console.log('🚨 Selected sports:', selectedSports);
      console.log('🚨 Available sport keys:', [...new Set(arbitrageOpportunities.map(o => o.sport_key))]);
    }

    // Filter by selected bookmakers - only if bookmakers are selected
    const beforeBookmakersCount = filtered.length;
    if (selectedBookmakers.length > 0) {
      filtered = filtered.filter(opp => {
        if (!opp.bookmakers || opp.bookmakers.length === 0) return false;
        return opp.bookmakers.some(bookmaker => selectedBookmakers.includes(bookmaker));
      });
      console.log(`After bookmaker filter: ${filtered.length} (filtered out ${beforeBookmakersCount - filtered.length})`);
      
      if (filtered.length === 0 && beforeBookmakersCount > 0) {
        console.log('🚨 Bookmaker filter eliminated all opportunities');
        console.log('🚨 Selected bookmakers:', selectedBookmakers);
        console.log('🚨 Available bookmakers:', [...new Set(arbitrageOpportunities.flatMap(o => o.bookmakers || []))]);
      }
    } else {
      console.log('No bookmaker filter applied (none selected)');
    }

    // Filter by minimum profit
    const beforeProfitCount = filtered.length;
    filtered = filtered.filter(opp => opp.profit_percentage >= minProfit);
    console.log(`After profit filter: ${filtered.length} (filtered out ${beforeProfitCount - filtered.length})`);

    // Apply sorting
    const sortedFiltered = sortOpportunities(filtered, sortBy);

    console.log(`Filter process complete: ${sortedFiltered.length} opportunities match criteria`);
    setFilteredOpportunities(sortedFiltered);
  };

  // Format odds based on user preference
  const formatOdds = (decimalOdds) => {
    if (oddsFormat === 'american') {
      if (!decimalOdds || decimalOdds <= 1) return '+100';
      if (decimalOdds >= 2.0) {
        return '+' + Math.round((decimalOdds - 1) * 100);
      } else {
        return Math.round(-100 / (decimalOdds - 1));
      }
    }
    return decimalOdds.toFixed(2);
  };

  // Enhanced outcome name formatting with market details and betting instructions
  const formatEnhancedOutcomeName = (outcomeName, marketKey, pointValue) => {
    let displayName = outcomeName;
    
    // Enhanced display for spreads and totals
    if (pointValue !== null && pointValue !== undefined) {
      const point = parseFloat(pointValue);
      
      if (marketKey && marketKey.includes('spread')) {
        // For spreads, show the team with the spread and market type
        if (point > 0) {
          displayName = `${displayName} +${point} (Spread)`;
        } else {
          displayName = `${displayName} ${point} (Spread)`;
        }
      } else if (marketKey && marketKey.includes('total')) {
        // For totals, show Over/Under with point value and market type
        if (displayName.toLowerCase().includes('over')) {
          displayName = `Over ${point} (Total)`;
        } else if (displayName.toLowerCase().includes('under')) {
          displayName = `Under ${point} (Total)`;
        } else {
          displayName = `${displayName} ${point} (Total)`;
        }
      }
    } else if (marketKey && marketKey.includes('h2h')) {
      // For head-to-head (moneyline), add market type
      displayName = `${displayName} (Moneyline)`;
    }
    
    return displayName;
  };

  // Load user preferences from profile
  const loadUserPreferences = () => {
    try {
      // Use same key as profile page
      const storedPrefs = localStorage.getItem('userPreferences');
      if (storedPrefs) {
        const prefs = JSON.parse(storedPrefs);
        console.log('🔧 Loading user preferences:', prefs);
        
        if (prefs.preferred_sports && Array.isArray(prefs.preferred_sports)) {
          setSelectedSports(prefs.preferred_sports);
        }
        
        if (prefs.preferred_bookmakers && Array.isArray(prefs.preferred_bookmakers)) {
          // Convert bookmaker keys to titles for display
          const bookmarkerTitles = prefs.preferred_bookmakers.map(key => {
            const bookmaker = allBookmakers.find(bm => bm.key === key);
            return bookmaker ? bookmaker.title : key;
          }).filter(title => title);
          setSelectedBookmakers(bookmarkerTitles);
        }
        
        if (typeof prefs.minimum_profit_threshold === 'number') {
          setMinProfit(prefs.minimum_profit_threshold);
        }
        
        if (prefs.odds_format && ['decimal', 'american'].includes(prefs.odds_format)) {
          setOddsFormat(prefs.odds_format);
        }
        
        console.log('User preferences loaded successfully');
      }
    } catch (error) {
      console.error('Error loading user preferences:', error);
    }
  };

  // Save user preferences to profile
  const saveUserPreferences = () => {
    try {
      // Get existing preferences to preserve other fields
      const existingPrefs = JSON.parse(localStorage.getItem('userPreferences') || '{}');
      
      // Convert bookmaker titles back to keys for consistency with profile
      const bookmakerKeys = selectedBookmakers.map(title => {
        const bookmaker = allBookmakers.find(bm => bm.title === title);
        return bookmaker ? bookmaker.key : title;
      }).filter(key => key);
      
      const preferences = {
        ...existingPrefs,
        preferred_sports: selectedSports,
        preferred_bookmakers: bookmakerKeys,
        minimum_profit_threshold: minProfit,
        odds_format: oddsFormat,
        updated_at: new Date().toISOString()
      };
      
      // Use same key as profile page
      localStorage.setItem('userPreferences', JSON.stringify(preferences));
      console.log('💾 User preferences saved:', preferences);
    } catch (error) {
      console.error('Error saving user preferences:', error);
    }
  };

  // Load opportunities and preferences on mount
  useEffect(() => {
    loadUserPreferences();
    fetchArbitrageOpportunities();
    
    // Refresh every 5 minutes
    const interval = setInterval(fetchArbitrageOpportunities, 300000);
    return () => clearInterval(interval);
  }, []);

  // Apply filters whenever they change
  useEffect(() => {
    applyFilters();
  }, [arbitrageOpportunities, selectedSports, selectedBookmakers, minProfit, sortBy]);

  // Auto-save preferences whenever they change
  useEffect(() => {
    saveUserPreferences();
  }, [selectedSports, selectedBookmakers, minProfit, oddsFormat]);

  // Group sports by category
  const groupedSports = allSports.reduce((acc, sport) => {
    if (!acc[sport.category]) acc[sport.category] = [];
    acc[sport.category].push(sport);
    return acc;
  }, {});

  // Group bookmakers by region
  const groupedBookmakers = allBookmakers.reduce((acc, bookmaker) => {
    if (!acc[bookmaker.region]) acc[bookmaker.region] = [];
    acc[bookmaker.region].push(bookmaker);
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Arbitrage Finder</h1>
          <p className="text-gray-300 text-lg">
            Find and capitalize on betting arbitrage opportunities
          </p>
        </div>

        {/* Settings Panel */}
        <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
          <h2 className="text-xl font-semibold text-yellow-400 mb-6">Filter Settings</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {/* Min Profit Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Min Profit %</label>
              <input
                type="number"
                min="0"
                max="20"
                step="0.1"
                value={minProfit}
                onChange={(e) => setMinProfit(parseFloat(e.target.value) || 0)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 transition-colors"
              />
            </div>

            {/* Sort By */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400 transition-colors"
              >
                <option value="profit_desc">Highest Profit %</option>
                <option value="profit_asc">Lowest Profit %</option>
                <option value="time_asc">Starting Soon First</option>
                <option value="time_desc">Starting Later First</option>
                <option value="match_asc">Match (A-Z)</option>
                <option value="match_desc">Match (Z-A)</option>
              </select>
            </div>

            {/* Odds Format */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Odds Format</label>
              <div className="flex space-x-2">
                {['decimal', 'american'].map(format => (
                  <button
                    key={format}
                    onClick={() => setOddsFormat(format)}
                    className={`px-4 py-2 rounded border ${
                      oddsFormat === format 
                        ? 'bg-yellow-400 text-gray-900 border-yellow-400' 
                        : 'bg-gray-700 text-white border-gray-600 hover:bg-gray-600'
                    }`}
                  >
                    {format === 'decimal' ? 'Decimal (2.10)' : 'American (+110)'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Sports Selection */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-300">Select Sports</h3>
              <button
                onClick={() => {
                  if (selectedSports.length === allSports.length) {
                    setSelectedSports([]);
                  } else {
                    setSelectedSports(allSports.map(s => s.key));
                  }
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedSports.length === allSports.length
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {selectedSports.length === allSports.length ? 'Clear All' : 'Select All'}
              </button>
            </div>
            
            <div className="max-h-60 overflow-y-auto bg-gray-700 rounded-lg p-4">
              {Object.entries(groupedSports).map(([category, sports]) => {
                const categoryKeys = sports.map(s => s.key);
                const allSelected = categoryKeys.every(key => selectedSports.includes(key));
                
                return (
                  <div key={category} className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-semibold text-yellow-400 uppercase">{category}</h4>
                      <button
                        onClick={() => {
                          if (allSelected) {
                            setSelectedSports(selectedSports.filter(key => !categoryKeys.includes(key)));
                          } else {
                            setSelectedSports([...new Set([...selectedSports, ...categoryKeys])]);
                          }
                        }}
                        className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                          allSelected
                            ? 'bg-red-500 hover:bg-red-600 text-white'
                            : 'bg-green-500 hover:bg-green-600 text-white'
                        }`}
                      >
                        {allSelected ? 'Clear' : 'All'}
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1">
                    {sports.map(sport => (
                      <label key={sport.key} className="flex items-center hover:bg-gray-600 rounded p-1 transition-colors">
                        <input
                          type="checkbox"
                          checked={selectedSports.includes(sport.key)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedSports([...selectedSports, sport.key]);
                            } else {
                              setSelectedSports(selectedSports.filter(s => s !== sport.key));
                            }
                          }}
                          className="mr-2 h-4 w-4 text-yellow-400 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
                        />
                        <span className="text-sm text-gray-300 hover:text-white cursor-pointer">
                          {sport.title}
                        </span>
                      </label>
                    ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bookmakers Selection */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-300">Select Bookmakers (min 2 required)</h3>
              <button
                onClick={() => {
                  if (selectedBookmakers.length === allBookmakers.length) {
                    setSelectedBookmakers([]);
                  } else {
                    setSelectedBookmakers(allBookmakers.map(b => b.title));
                  }
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedBookmakers.length === allBookmakers.length
                    ? 'bg-red-600 hover:bg-red-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {selectedBookmakers.length === allBookmakers.length ? 'Clear All' : 'Select All'}
              </button>
            </div>
            
            <div className="max-h-80 overflow-y-auto bg-gray-700 rounded-lg p-4">
              {Object.entries(groupedBookmakers).map(([region, bookmakers]) => {
                const regionTitles = bookmakers.map(b => b.title);
                const allRegionSelected = regionTitles.every(title => selectedBookmakers.includes(title));
                
                return (
                  <div key={region} className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-semibold text-yellow-400 uppercase">{region} Bookmakers</h4>
                      <button
                        onClick={() => {
                          if (allRegionSelected) {
                            setSelectedBookmakers(selectedBookmakers.filter(title => !regionTitles.includes(title)));
                          } else {
                            setSelectedBookmakers([...new Set([...selectedBookmakers, ...regionTitles])]);
                          }
                        }}
                        className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                          allRegionSelected
                            ? 'bg-red-500 hover:bg-red-600 text-white'
                            : 'bg-green-500 hover:bg-green-600 text-white'
                        }`}
                      >
                        {allRegionSelected ? 'Clear' : 'All'}
                      </button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1">
                    {bookmakers.map(bookmaker => (
                      <label key={bookmaker.key} className="flex items-center hover:bg-gray-600 rounded p-1 transition-colors">
                        <input
                          type="checkbox"
                          checked={selectedBookmakers.includes(bookmaker.title)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedBookmakers([...selectedBookmakers, bookmaker.title]);
                            } else {
                              setSelectedBookmakers(selectedBookmakers.filter(b => b !== bookmaker.title));
                            }
                          }}
                          className="mr-2 h-4 w-4 text-yellow-400 border-gray-600 rounded focus:ring-yellow-400 focus:ring-2"
                        />
                        <span className="text-sm text-gray-300 hover:text-white cursor-pointer">
                          {bookmaker.title}
                        </span>
                      </label>
                    ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Status Info */}
        <div className={`border rounded-lg p-4 mb-6 ${
          selectedSports.length >= 1 && selectedBookmakers.length >= 2
            ? 'bg-green-900 border-green-600'
            : 'bg-red-900 border-red-600'
        }`}>
          <div className="text-sm space-y-1">
            <div className="flex items-center space-x-2">
              <span className={`inline-block w-2 h-2 rounded-full ${
                selectedSports.length >= 1 ? 'bg-green-400' : 'bg-red-400'
              }`}></span>
              <span className={selectedSports.length >= 1 ? 'text-green-100' : 'text-red-100'}>
                <strong>Sports:</strong> {selectedSports.length} / {allSports.length} (need ≥1)
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-block w-2 h-2 rounded-full ${
                selectedBookmakers.length >= 2 ? 'bg-green-400' : 'bg-red-400'
              }`}></span>
              <span className={selectedBookmakers.length >= 2 ? 'text-green-100' : 'text-red-100'}>
                <strong>Bookmakers:</strong> {selectedBookmakers.length} / {allBookmakers.length} (need ≥2)
              </span>
            </div>
            <div className="text-blue-100">
              <strong>Total Opportunities:</strong> {arbitrageOpportunities.length}
            </div>
            <div className="text-blue-100">
              <strong>Filtered Opportunities:</strong> {filteredOpportunities.length}
            </div>
            <div className="text-blue-100">
              <strong>Status:</strong> {loading ? 'Loading...' : 'Live Data'}
            </div>
            {selectedSports.length < 1 || selectedBookmakers.length < 2 ? (
              <div className="text-red-200 font-semibold mt-2">
                Select at least 1 sport and 2 bookmakers to see opportunities
              </div>
            ) : null}
          </div>
        </div>

        {/* Opportunities List */}
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-yellow-400">
              Found {filteredOpportunities.length} Arbitrage Opportunities
            </h2>
            <button
              onClick={fetchArbitrageOpportunities}
              disabled={loading}
              className="bg-yellow-400 text-gray-900 px-6 py-2 rounded-lg font-medium hover:bg-yellow-500 transition-colors disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          {filteredOpportunities.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredOpportunities.map((opportunity, index) => (
                <div key={opportunity.id} className="bg-gray-800 rounded-lg border border-yellow-400/60 hover:border-yellow-400 transition-colors p-4">
                  {/* Header */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="bg-yellow-400 text-black text-xs px-2 py-1 rounded font-bold">
                        {opportunity.profit_percentage.toFixed(2)}% PROFIT
                      </span>
                      <span className="bg-orange-600 text-white text-xs px-2 py-1 rounded font-bold">
                        ⏰ {formatMatchTime(opportunity.commence_time)}
                      </span>
                    </div>
                    <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded font-bold">
                      {opportunity.sport}
                    </span>
                  </div>

                  <div className="bg-green-600 text-white text-sm px-3 py-1 rounded font-bold mb-3">
                    {opportunity.match}
                  </div>

                  {/* Enhanced Betting Options */}
                  {opportunity.details.outcome1 && opportunity.details.outcome2 && (
                    <div className="space-y-3 mb-4">
                      {/* Market Type Header */}
                      {opportunity.market_name && (
                        <div className="text-center text-sm font-medium text-yellow-400 bg-gray-700/30 rounded-lg py-2 px-3 mb-3">
                          {opportunity.market_name}
                        </div>
                      )}
                      
                      <div className="grid grid-cols-2 gap-3">
                        {/* Enhanced Outcome 1 */}
                        <div className="bg-gray-700/50 border border-gray-600 hover:border-yellow-400/50 transition-colors rounded-lg p-3">
                          <div className="text-xs font-medium text-gray-400 mb-1">
                            Place bet at: {opportunity.details.outcome1.bookmaker}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-medium text-white text-sm mb-1">
                              {formatEnhancedOutcomeName(opportunity.details.outcome1.name, opportunity.market_key, opportunity.details.outcome1.pointValue)}
                            </span>
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-yellow-400 font-bold text-lg">
                                {formatOdds(opportunity.details.outcome1.odds)}
                              </span>
                              {opportunity.details.outcome1.pointValue !== null && opportunity.details.outcome1.pointValue !== undefined && (
                                <span className="text-xs text-blue-400 bg-blue-400/20 px-2 py-1 rounded">
                                  {opportunity.details.outcome1.pointValue > 0 ? `+${opportunity.details.outcome1.pointValue}` : opportunity.details.outcome1.pointValue}
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-green-400">
                              Stake: ${opportunity.details.outcome1.stake.toFixed(2)}
                            </div>
                          </div>
                        </div>

                        {/* Enhanced Outcome 2 */}
                        <div className="bg-gray-700/50 border border-gray-600 hover:border-yellow-400/50 transition-colors rounded-lg p-3">
                          <div className="text-xs font-medium text-gray-400 mb-1">
                            Place bet at: {opportunity.details.outcome2.bookmaker}
                          </div>
                          <div className="flex flex-col">
                            <span className="font-medium text-white text-sm mb-1">
                              {formatEnhancedOutcomeName(opportunity.details.outcome2.name, opportunity.market_key, opportunity.details.outcome2.pointValue)}
                            </span>
                            <div className="flex justify-between items-center mb-2">
                              <span className="text-yellow-400 font-bold text-lg">
                                {formatOdds(opportunity.details.outcome2.odds)}
                              </span>
                              {opportunity.details.outcome2.pointValue !== null && opportunity.details.outcome2.pointValue !== undefined && (
                                <span className="text-xs text-blue-400 bg-blue-400/20 px-2 py-1 rounded">
                                  {opportunity.details.outcome2.pointValue > 0 ? `+${opportunity.details.outcome2.pointValue}` : opportunity.details.outcome2.pointValue}
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-green-400">
                              Stake: ${opportunity.details.outcome2.stake.toFixed(2)}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* Additional Market Info */}
                      <div className="flex justify-between items-center text-xs text-gray-500 bg-gray-800/30 rounded px-3 py-2">
                        <span>{opportunity.profit_percentage.toFixed(2)}% Profit</span>
                      </div>
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex space-x-2">
                    <button
                      className="bg-gray-700 text-white px-4 py-2 rounded-lg font-bold hover:bg-gray-600 transition-colors text-sm flex-1"
                      onClick={() => toast.success('Save functionality available for premium users!')}
                    >
                      Save
                    </button>
                    <button
                      className="bg-yellow-400 text-black px-4 py-2 rounded-lg font-bold hover:bg-yellow-500 transition-colors text-sm flex-1"
                      onClick={() => toast.info('Calculator opening soon!')}
                    >
                      Calculate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-800 rounded-xl p-12 text-center border border-gray-700">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No Arbitrage Opportunities Found</h3>
              <p className="text-gray-400 mb-4">
                {selectedSports.length === 0 && selectedBookmakers.length === 0
                  ? 'Select some sports and bookmakers to see opportunities.'
                  : 'Try adjusting your filters or check back later for new opportunities.'
                }
              </p>
              <button
                onClick={() => {
                  setSelectedSports([]);
                  setSelectedBookmakers([]);
                  setMinProfit(0.5);
                }}
                className="bg-yellow-400 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-yellow-500 transition-colors"
              >
                Reset Filters
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArbitrageFinder;