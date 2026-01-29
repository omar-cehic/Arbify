import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const OddsComparison = () => {
  const [selectedSport, setSelectedSport] = useState('all');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('compact'); // 'compact' or 'detailed'
  const [isLoading, setIsLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  // Complete sports data from Odds API
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

    // Lacrosse
    { key: 'lacrosse_pll', title: 'Premier Lacrosse League', category: 'Lacrosse' },
    { key: 'lacrosse_ncaa', title: 'NCAA Lacrosse', category: 'Lacrosse' },

    // Mixed Martial Arts
    { key: 'mma_mixed_martial_arts', title: 'MMA', category: 'Mixed Martial Arts' },

    // Politics
    { key: 'politics_us_presidential_election_winner', title: 'US Presidential Elections Winner', category: 'Politics' },

    // Rugby League
    { key: 'rugbyleague_nrl', title: 'NRL', category: 'Rugby League' },
    { key: 'rugbyleague_nrl_state_of_origin', title: 'NRL State of Origin', category: 'Rugby League' },

    // Rugby Union
    { key: 'rugbyunion_six_nations', title: 'Six Nations', category: 'Rugby Union' },

    // Soccer
    { key: 'soccer_africa_cup_of_nations', title: 'Africa Cup of Nations', category: 'Soccer' },
    { key: 'soccer_argentina_primera_division', title: 'Primera División - Argentina', category: 'Soccer' },
    { key: 'soccer_australia_aleague', title: 'A-League', category: 'Soccer' },
    { key: 'soccer_austria_bundesliga', title: 'Austrian Football Bundesliga', category: 'Soccer' },
    { key: 'soccer_belgium_first_div', title: 'Belgium First Div', category: 'Soccer' },
    { key: 'soccer_brazil_campeonato', title: 'Brazil Série A', category: 'Soccer' },
    { key: 'soccer_brazil_serie_b', title: 'Brazil Série B', category: 'Soccer' },
    { key: 'soccer_chile_campeonato', title: 'Primera División - Chile', category: 'Soccer' },
    { key: 'soccer_china_superleague', title: 'Super League - China', category: 'Soccer' },
    { key: 'soccer_denmark_superliga', title: 'Denmark Superliga', category: 'Soccer' },
    { key: 'soccer_efl_champ', title: 'Championship', category: 'Soccer' },
    { key: 'soccer_england_efl_cup', title: 'EFL Cup', category: 'Soccer' },
    { key: 'soccer_england_league1', title: 'League 1', category: 'Soccer' },
    { key: 'soccer_england_league2', title: 'League 2', category: 'Soccer' },
    { key: 'soccer_epl', title: 'English Premier League', category: 'Soccer' },
    { key: 'soccer_fa_cup', title: 'FA Cup', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup', title: 'FIFA World Cup', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_qualifiers_europe', title: 'FIFA World Cup Qualifiers - Europe', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_qualifiers_south_america', title: 'FIFA World Cup Qualifiers - South America', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_womens', title: 'FIFA Women\'s World Cup', category: 'Soccer' },
    { key: 'soccer_fifa_world_cup_winner', title: 'FIFA World Cup Winner', category: 'Soccer' },
    { key: 'soccer_fifa_club_world_cup', title: 'FIFA Club World Cup', category: 'Soccer' },
    { key: 'soccer_finland_veikkausliiga', title: 'Veikkausliiga - Finland', category: 'Soccer' },
    { key: 'soccer_france_ligue_one', title: 'Ligue 1 - France', category: 'Soccer' },
    { key: 'soccer_france_ligue_two', title: 'Ligue 2 - France', category: 'Soccer' },
    { key: 'soccer_germany_bundesliga', title: 'Bundesliga - Germany', category: 'Soccer' },
    { key: 'soccer_germany_bundesliga2', title: 'Bundesliga 2 - Germany', category: 'Soccer' },
    { key: 'soccer_germany_liga3', title: '3. Liga - Germany', category: 'Soccer' },
    { key: 'soccer_greece_super_league', title: 'Super League - Greece', category: 'Soccer' },
    { key: 'soccer_italy_serie_a', title: 'Serie A - Italy', category: 'Soccer' },
    { key: 'soccer_italy_serie_b', title: 'Serie B - Italy', category: 'Soccer' },
    { key: 'soccer_japan_j_league', title: 'J League', category: 'Soccer' },
    { key: 'soccer_korea_kleague1', title: 'K League 1', category: 'Soccer' },
    { key: 'soccer_league_of_ireland', title: 'League of Ireland', category: 'Soccer' },
    { key: 'soccer_mexico_ligamx', title: 'Liga MX', category: 'Soccer' },
    { key: 'soccer_netherlands_eredivisie', title: 'Dutch Eredivisie', category: 'Soccer' },
    { key: 'soccer_norway_eliteserien', title: 'Eliteserien - Norway', category: 'Soccer' },
    { key: 'soccer_poland_ekstraklasa', title: 'Ekstraklasa - Poland', category: 'Soccer' },
    { key: 'soccer_portugal_primeira_liga', title: 'Primeira Liga - Portugal', category: 'Soccer' },
    { key: 'soccer_spain_la_liga', title: 'La Liga - Spain', category: 'Soccer' },
    { key: 'soccer_spain_segunda_division', title: 'La Liga 2 - Spain', category: 'Soccer' },
    { key: 'soccer_spl', title: 'Premiership - Scotland', category: 'Soccer' },
    { key: 'soccer_sweden_allsvenskan', title: 'Allsvenskan - Sweden', category: 'Soccer' },
    { key: 'soccer_sweden_superettan', title: 'Superettan - Sweden', category: 'Soccer' },
    { key: 'soccer_switzerland_superleague', title: 'Swiss Superleague', category: 'Soccer' },
    { key: 'soccer_turkey_super_league', title: 'Turkey Super League', category: 'Soccer' },
    { key: 'soccer_uefa_europa_conference_league', title: 'UEFA Europa Conference League', category: 'Soccer' },
    { key: 'soccer_uefa_champs_league', title: 'UEFA Champions League', category: 'Soccer' },
    { key: 'soccer_uefa_champs_league_qualification', title: 'UEFA Champions League Qualification', category: 'Soccer' },
    { key: 'soccer_uefa_europa_league', title: 'UEFA Europa League', category: 'Soccer' },
    { key: 'soccer_uefa_european_championship', title: 'UEFA Euro 2024', category: 'Soccer' },
    { key: 'soccer_uefa_euro_qualification', title: 'UEFA Euro Qualification', category: 'Soccer' },
    { key: 'soccer_uefa_nations_league', title: 'UEFA Nations League', category: 'Soccer' },
    { key: 'soccer_concacaf_gold_cup', title: 'CONCACAF Gold Cup', category: 'Soccer' },
    { key: 'soccer_conmebol_copa_america', title: 'Copa América', category: 'Soccer' },
    { key: 'soccer_conmebol_copa_libertadores', title: 'Copa Libertadores', category: 'Soccer' },
    { key: 'soccer_conmebol_copa_sudamericana', title: 'Copa Sudamericana', category: 'Soccer' },
    { key: 'soccer_usa_mls', title: 'Major League Soccer', category: 'Soccer' },

    // Tennis
    { key: 'tennis_atp_aus_open_singles', title: 'ATP Australian Open', category: 'Tennis' },
    { key: 'tennis_atp_canadian_open', title: 'ATP Canadian Open', category: 'Tennis' },
    { key: 'tennis_atp_china_open', title: 'ATP China Open', category: 'Tennis' },
    { key: 'tennis_atp_cincinnati_open', title: 'ATP Cincinnati Open', category: 'Tennis' },
    { key: 'tennis_atp_dubai', title: 'ATP Dubai Championships', category: 'Tennis' },
    { key: 'tennis_atp_french_open', title: 'ATP French Open', category: 'Tennis' },
    { key: 'tennis_atp_indian_wells', title: 'ATP Indian Wells', category: 'Tennis' },
    { key: 'tennis_atp_italian_open', title: 'ATP Italian Open', category: 'Tennis' },
    { key: 'tennis_atp_madrid_open', title: 'ATP Madrid Open', category: 'Tennis' },
    { key: 'tennis_atp_miami_open', title: 'ATP Miami Open', category: 'Tennis' },
    { key: 'tennis_atp_monte_carlo_masters', title: 'ATP Monte-Carlo Masters', category: 'Tennis' },
    { key: 'tennis_atp_paris_masters', title: 'ATP Paris Masters', category: 'Tennis' },
    { key: 'tennis_atp_qatar_open', title: 'ATP Qatar Open', category: 'Tennis' },
    { key: 'tennis_atp_shanghai_masters', title: 'ATP Shanghai Masters', category: 'Tennis' },
    { key: 'tennis_atp_us_open', title: 'ATP US Open', category: 'Tennis' },
    { key: 'tennis_atp_wimbledon', title: 'ATP Wimbledon', category: 'Tennis' },
    { key: 'tennis_wta_aus_open_singles', title: 'WTA Australian Open', category: 'Tennis' },
    { key: 'tennis_wta_canadian_open', title: 'WTA Canadian Open', category: 'Tennis' },
    { key: 'tennis_wta_china_open', title: 'WTA China Open', category: 'Tennis' },
    { key: 'tennis_wta_cincinnati_open', title: 'WTA Cincinnati Open', category: 'Tennis' },
    { key: 'tennis_wta_dubai', title: 'WTA Dubai Championships', category: 'Tennis' },
    { key: 'tennis_wta_french_open', title: 'WTA French Open', category: 'Tennis' },
    { key: 'tennis_wta_indian_wells', title: 'WTA Indian Wells', category: 'Tennis' },
    { key: 'tennis_wta_italian_open', title: 'WTA Italian Open', category: 'Tennis' },
    { key: 'tennis_wta_madrid_open', title: 'WTA Madrid Open', category: 'Tennis' },
    { key: 'tennis_wta_miami_open', title: 'WTA Miami Open', category: 'Tennis' },
    { key: 'tennis_wta_qatar_open', title: 'WTA Qatar Open', category: 'Tennis' },
    { key: 'tennis_wta_us_open', title: 'WTA US Open', category: 'Tennis' },
    { key: 'tennis_wta_wimbledon', title: 'WTA Wimbledon', category: 'Tennis' },
    { key: 'tennis_wta_wuhan_open', title: 'WTA Wuhan Open', category: 'Tennis' },
  ];

  // Get sports grouped by category
  const sportsByCategory = allSports.reduce((acc, sport) => {
    if (!acc[sport.category]) {
      acc[sport.category] = [];
    }
    acc[sport.category].push(sport);
    return acc;
  }, {});

  // Complete bookmaker data from Odds API
  const allBookmakers = {
    us: [
      { key: 'betonlineag', name: 'BetOnline.ag', url: 'https://betonline.ag' },
      { key: 'betmgm', name: 'BetMGM', url: 'https://betmgm.com' },
      { key: 'betrivers', name: 'BetRivers', url: 'https://betrivers.com' },
      { key: 'betus', name: 'BetUS', url: 'https://betus.com.pa' },
      { key: 'bovada', name: 'Bovada', url: 'https://bovada.lv' },
      { key: 'williamhill_us', name: 'Caesars', url: 'https://caesars.com' },
      { key: 'draftkings', name: 'DraftKings', url: 'https://draftkings.com' },
      { key: 'fanatics', name: 'Fanatics', url: 'https://fanatics.com' },
      { key: 'fanduel', name: 'FanDuel', url: 'https://fanduel.com' },
      { key: 'lowvig', name: 'LowVig.ag', url: 'https://lowvig.ag' },
      { key: 'mybookieag', name: 'MyBookie.ag', url: 'https://mybookie.ag' },
      { key: 'ballybet', name: 'Bally Bet', url: 'https://ballysbet.com' },
      { key: 'betanysports', name: 'BetAnySports', url: 'https://betanysports.eu' },
      { key: 'betparx', name: 'betPARX', url: 'https://betparx.com' },
      { key: 'espnbet', name: 'ESPN BET', url: 'https://espnbet.com' },
      { key: 'fliff', name: 'Fliff', url: 'https://fliff.com' },
      { key: 'hardrockbet', name: 'Hard Rock Bet', url: 'https://hardrockbet.com' },
      { key: 'rebet', name: 'ReBet', url: 'https://rebet.com' },
      { key: 'windcreek', name: 'Wind Creek (Betfred PA)', url: 'https://windcreek.com' },
    ],
    uk: [
      { key: 'sport888', name: '888sport', url: 'https://888sport.com' },
      { key: 'betfair_ex_uk', name: 'Betfair Exchange', url: 'https://betfair.com' },
      { key: 'betfair_sb_uk', name: 'Betfair Sportsbook', url: 'https://betfair.com' },
      { key: 'betvictor', name: 'Bet Victor', url: 'https://betvictor.com' },
      { key: 'betway', name: 'Betway', url: 'https://betway.com' },
      { key: 'boylesports', name: 'BoyleSports', url: 'https://boylesports.com' },
      { key: 'casumo', name: 'Casumo', url: 'https://casumo.com' },
      { key: 'coral', name: 'Coral', url: 'https://coral.co.uk' },
      { key: 'grosvenor', name: 'Grosvenor', url: 'https://grosvenor.com' },
      { key: 'ladbrokes_uk', name: 'Ladbrokes', url: 'https://ladbrokes.com' },
      { key: 'leovegas', name: 'LeoVegas', url: 'https://leovegas.com' },
      { key: 'livescorebet', name: 'LiveScore Bet', url: 'https://livescorebet.com' },
      { key: 'matchbook', name: 'Matchbook', url: 'https://matchbook.com' },
      { key: 'paddypower', name: 'Paddy Power', url: 'https://paddypower.com' },
      { key: 'skybet', name: 'Sky Bet', url: 'https://skybet.com' },
      { key: 'smarkets', name: 'Smarkets', url: 'https://smarkets.com' },
      { key: 'unibet_uk', name: 'Unibet', url: 'https://unibet.co.uk' },
      { key: 'virginbet', name: 'Virgin Bet', url: 'https://virginbet.com' },
      { key: 'williamhill', name: 'William Hill (UK)', url: 'https://williamhill.com' },
    ],
    eu: [
      { key: 'onexbet', name: '1xBet', url: 'https://1xbet.com' },
      { key: 'sport888', name: '888sport', url: 'https://888sport.com' },
      { key: 'betclic_fr', name: 'Betclic (FR)', url: 'https://betclic.fr' },
      { key: 'betanysports', name: 'BetAnySports', url: 'https://betanysports.eu' },
      { key: 'betfair_ex_eu', name: 'Betfair Exchange', url: 'https://betfair.com' },
      { key: 'betonlineag', name: 'BetOnline.ag', url: 'https://betonline.ag' },
      { key: 'betsson', name: 'Betsson', url: 'https://betsson.com' },
      { key: 'betvictor', name: 'Bet Victor', url: 'https://betvictor.com' },
      { key: 'coolbet', name: 'Coolbet', url: 'https://coolbet.com' },
      { key: 'everygame', name: 'Everygame', url: 'https://everygame.eu' },
      { key: 'gtbets', name: 'GTbets', url: 'https://gtbets.eu' },
      { key: 'marathonbet', name: 'Marathon Bet', url: 'https://marathonbet.com' },
      { key: 'matchbook', name: 'Matchbook', url: 'https://matchbook.com' },
      { key: 'mybookieag', name: 'MyBookie.ag', url: 'https://mybookie.ag' },
      { key: 'nordicbet', name: 'NordicBet', url: 'https://nordicbet.com' },
      { key: 'parionssport_fr', name: 'Parions Sport (FR)', url: 'https://parionssport.fdj.fr' },
      { key: 'pinnacle', name: 'Pinnacle', url: 'https://pinnacle.com' },
      { key: 'suprabets', name: 'Suprabets', url: 'https://suprabets.co.za' },
      { key: 'tipico_de', name: 'Tipico (DE)', url: 'https://tipico.de' },
      { key: 'unibet_fr', name: 'Unibet (FR)', url: 'https://unibet.fr' },
      { key: 'unibet_it', name: 'Unibet (IT)', url: 'https://unibet.it' },
      { key: 'unibet_nl', name: 'Unibet (NL)', url: 'https://unibet.nl' },
      { key: 'williamhill', name: 'William Hill', url: 'https://williamhill.com' },
      { key: 'winamax_de', name: 'Winamax (DE)', url: 'https://winamax.de' },
      { key: 'winamax_fr', name: 'Winamax (FR)', url: 'https://winamax.fr' },
    ],
    au: [
      { key: 'betfair_ex_au', name: 'Betfair Exchange', url: 'https://betfair.com.au' },
      { key: 'betr_au', name: 'Betr', url: 'https://betr.com.au' },
      { key: 'betright', name: 'Bet Right', url: 'https://betright.com.au' },
      { key: 'bet365_au', name: 'Bet365 AU', url: 'https://bet365.com.au' },
      { key: 'boombet', name: 'BoomBet', url: 'https://boombet.com.au' },
      { key: 'dabble_au', name: 'Dabble AU', url: 'https://dabble.com.au' },
      { key: 'ladbrokes_au', name: 'Ladbrokes', url: 'https://ladbrokes.com.au' },
      { key: 'neds', name: 'Neds', url: 'https://neds.com.au' },
      { key: 'playup', name: 'PlayUp', url: 'https://playup.com' },
      { key: 'pointsbetau', name: 'PointsBet (AU)', url: 'https://pointsbet.com.au' },
      { key: 'sportsbet', name: 'SportsBet', url: 'https://sportsbet.com.au' },
      { key: 'tab', name: 'TAB', url: 'https://tab.com.au' },
      { key: 'tabtouch', name: 'TABtouch', url: 'https://tabtouch.mobi' },
      { key: 'unibet', name: 'Unibet', url: 'https://unibet.com.au' },
    ]
  };

  // Bookmaker regions
  const regions = [
    { key: 'all', title: 'All Regions' },
    { key: 'us', title: 'US' },
    { key: 'uk', title: 'UK' },
    { key: 'eu', title: 'Europe' },
    { key: 'au', title: 'Australia' }
  ];

  // Expanded mock data with more comprehensive examples
  const mockOddsData = {
    soccer_epl: [
      {
        id: 1,
        home_team: "Manchester City",
        away_team: "Arsenal",
        commence_time: new Date(Date.now() + 86400000),
        sport_title: "English Premier League",
        bookmakers: [
          { name: "Bet365", home: 2.10, draw: 3.40, away: 3.25, region: "uk" },
          { name: "William Hill (UK)", home: 2.05, draw: 3.50, away: 3.30, region: "uk" },
          { name: "DraftKings", home: 2.15, draw: 3.30, away: 3.20, region: "us" },
          { name: "FanDuel", home: 2.08, draw: 3.45, away: 3.28, region: "us" },
          { name: "Betway", home: 2.12, draw: 3.35, away: 3.22, region: "eu" },
          { name: "Pinnacle", home: 2.18, draw: 3.25, away: 3.15, region: "eu" }
        ]
      },
      {
        id: 2,
        home_team: "Liverpool",
        away_team: "Chelsea",
        commence_time: new Date(Date.now() + 172800000),
        sport_title: "English Premier League",
        bookmakers: [
          { name: "Bet365", home: 1.95, draw: 3.60, away: 3.80, region: "uk" },
          { name: "William Hill (UK)", home: 1.90, draw: 3.70, away: 3.85, region: "uk" },
          { name: "DraftKings", home: 2.00, draw: 3.55, away: 3.75, region: "us" },
          { name: "FanDuel", home: 1.92, draw: 3.65, away: 3.82, region: "us" },
          { name: "SportsBet", home: 1.88, draw: 3.75, away: 3.90, region: "au" }
        ]
      }
    ],
    basketball_nba: [
      {
        id: 5,
        home_team: "Lakers",
        away_team: "Warriors",
        commence_time: new Date(Date.now() + 86400000),
        sport_title: "NBA",
        bookmakers: [
          { name: "DraftKings", home: 1.85, away: 1.95, region: "us" },
          { name: "FanDuel", home: 1.88, away: 1.92, region: "us" },
          { name: "BetMGM", home: 1.82, away: 1.98, region: "us" },
          { name: "Caesars", home: 1.90, away: 1.90, region: "us" }
        ]
      }
    ],
    tennis_atp_wimbledon: [
      {
        id: 7,
        home_team: "Novak Djokovic",
        away_team: "Carlos Alcaraz",
        commence_time: new Date(Date.now() + 86400000),
        sport_title: "ATP Wimbledon",
        bookmakers: [
          { name: "Bet365", home: 2.20, away: 1.65, region: "uk" },
          { name: "William Hill (UK)", home: 2.15, away: 1.70, region: "uk" },
          { name: "DraftKings", home: 2.25, away: 1.62, region: "us" },
          { name: "Pinnacle", home: 2.30, away: 1.58, region: "eu" }
        ]
      }
    ],
    americanfootball_nfl: [
      {
        id: 8,
        home_team: "Kansas City Chiefs",
        away_team: "Buffalo Bills",
        commence_time: new Date(Date.now() + 259200000),
        sport_title: "NFL",
        bookmakers: [
          { name: "DraftKings", home: 1.75, away: 2.05, region: "us" },
          { name: "FanDuel", home: 1.78, away: 2.02, region: "us" },
          { name: "BetMGM", home: 1.72, away: 2.08, region: "us" },
          { name: "Caesars", home: 1.80, away: 2.00, region: "us" }
        ]
      }
    ]
  };

  // Get all available data (for "All Sports")
  const getAllSportsData = () => {
    const allData = [];
    Object.values(mockOddsData).forEach(sportData => {
      allData.push(...sportData);
    });
    return allData;
  };

  // Get current sport's odds data
  const getCurrentSportData = () => {
    if (selectedSport === 'all') {
      return getAllSportsData();
    }
    return mockOddsData[selectedSport] || [];
  };

  // Filter data based on search and region
  const getFilteredData = () => {
    let data = getCurrentSportData();
    
    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      data = data.filter(match => 
        match.home_team.toLowerCase().includes(query) || 
        match.away_team.toLowerCase().includes(query)
      );
    }
    
    // Filter by region
    if (selectedRegion !== 'all') {
      data = data.map(match => ({
        ...match,
        bookmakers: match.bookmakers.filter(bookie => bookie.region === selectedRegion)
      })).filter(match => match.bookmakers.length > 0);
    }
    
    return data;
  };

  // Get best odds for an outcome
  const getBestOdds = (bookmakers, outcome) => {
    const odds = bookmakers.map(b => b[outcome]).filter(odd => odd);
    return odds.length > 0 ? Math.max(...odds) : null;
  };

  // Get bookmaker with best odds
  const getBestBookmaker = (bookmakers, outcome) => {
    const bestOdd = getBestOdds(bookmakers, outcome);
    return bookmakers.find(b => b[outcome] === bestOdd)?.name || '';
  };

  const filteredData = getFilteredData();

  return (
    <div className="min-h-screen bg-gray-900 text-white py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-yellow-400 mb-4">Odds Comparison</h1>
          <p className="text-gray-300 text-lg">
            Compare odds across bookmakers to identify the highest payouts for your intended bets
          </p>
          <p className="text-gray-400 text-sm mt-2">
            Select your preferred sport and region to view real-time odds from multiple bookmakers, helping you maximize potential returns on individual wagers
          </p>
        </div>

        {/* Filters */}
        <div className="bg-gray-800 rounded-xl p-6 mb-8 border border-gray-700">
          {/* View Mode Toggle */}
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-semibold text-yellow-400">Filters</h3>
            <div className="flex bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setViewMode('compact')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  viewMode === 'compact'
                    ? 'bg-yellow-400 text-gray-900'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Compact View
              </button>
              <button
                onClick={() => setViewMode('detailed')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  viewMode === 'detailed'
                    ? 'bg-yellow-400 text-gray-900'
                    : 'text-gray-300 hover:text-white'
                }`}
              >
                Detailed View
              </button>
            </div>
          </div>

          {/* Top Row Filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Sport</h4>
              <select
                value={selectedSport}
                onChange={(e) => setSelectedSport(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
              >
                <option value="all">All Sports ({allSports.length} available)</option>
                {Object.entries(sportsByCategory).map(([category, sports]) => (
                  <optgroup key={category} label={category}>
                    {sports.map(sport => (
                      <option key={sport.key} value={sport.key}>{sport.title}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Region</h4>
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
              >
                {regions.map(region => (
                  <option key={region.key} value={region.key}>
                    {region.title} {region.key !== 'all' ? `(${allBookmakers[region.key]?.length || 0} bookmakers)` : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-2">Search Matches</h4>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search teams..."
                  className="flex-1 bg-gray-700 text-white px-4 py-3 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
                />
                <button
                  onClick={() => setSearchQuery('')}
                  className="bg-yellow-400 text-gray-900 px-4 py-3 rounded-lg font-medium hover:bg-yellow-500 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Odds Display */}
        {filteredData.length > 0 ? (
          <div className={viewMode === 'compact' ? 'space-y-4' : 'space-y-6'}>
            {filteredData.map(match => (
              <div key={match.id} className={`bg-gray-800 rounded-xl border border-gray-700 overflow-hidden ${viewMode === 'compact' ? 'hover:border-yellow-400 transition-colors' : ''}`}>
                {/* Compact View */}
                {viewMode === 'compact' ? (
                  <div className="p-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      {/* Match Info */}
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-white mb-1">
                          {match.home_team} vs {match.away_team}
                        </h3>
                        <p className="text-sm text-gray-400">
                          {match.sport_title} • {new Date(match.commence_time).toLocaleDateString()} {new Date(match.commence_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {match.bookmakers.length} bookmakers
                        </p>
                      </div>
                      
                      {/* Best Odds Summary */}
                      <div className="flex gap-4">
                        <div className="text-center">
                          <div className="text-xs text-yellow-400 font-medium mb-1">Best Home</div>
                          <div className="text-lg font-bold text-white">
                            {getBestOdds(match.bookmakers, 'home')?.toFixed(2) || 'N/A'}
                          </div>
                          <div className="text-xs text-gray-400">
                            {getBestBookmaker(match.bookmakers, 'home')}
                          </div>
                        </div>
                        
                        {match.bookmakers.some(b => b.draw) && (
                          <div className="text-center">
                            <div className="text-xs text-yellow-400 font-medium mb-1">Best Draw</div>
                            <div className="text-lg font-bold text-white">
                              {getBestOdds(match.bookmakers, 'draw')?.toFixed(2) || 'N/A'}
                            </div>
                            <div className="text-xs text-gray-400">
                              {getBestBookmaker(match.bookmakers, 'draw')}
                            </div>
                          </div>
                        )}
                        
                        <div className="text-center">
                          <div className="text-xs text-yellow-400 font-medium mb-1">Best Away</div>
                          <div className="text-lg font-bold text-white">
                            {getBestOdds(match.bookmakers, 'away')?.toFixed(2) || 'N/A'}
                          </div>
                          <div className="text-xs text-gray-400">
                            {getBestBookmaker(match.bookmakers, 'away')}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Detailed View - Original Design */
                  <>
                    <div className="bg-gray-700 px-6 py-4 border-b border-gray-600">
                      <div className="flex justify-between items-center">
                        <div>
                          <h3 className="text-xl font-bold text-white">
                            {match.home_team} vs {match.away_team}
                          </h3>
                          <p className="text-gray-400 text-sm">
                            {match.sport_title} • {new Date(match.commence_time).toLocaleDateString()} {new Date(match.commence_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="p-6">
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                        <div className="bg-gray-700 rounded-lg p-4 text-center">
                          <div className="text-yellow-400 font-medium mb-1">Best Home Odds</div>
                          <div className="text-2xl font-bold text-white">
                            {getBestOdds(match.bookmakers, 'home')?.toFixed(2) || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-400">
                            {getBestBookmaker(match.bookmakers, 'home')}
                          </div>
                        </div>
                        
                        {match.bookmakers.some(b => b.draw) && (
                          <div className="bg-gray-700 rounded-lg p-4 text-center">
                            <div className="text-yellow-400 font-medium mb-1">Best Draw Odds</div>
                            <div className="text-2xl font-bold text-white">
                              {getBestOdds(match.bookmakers, 'draw')?.toFixed(2) || 'N/A'}
                            </div>
                            <div className="text-sm text-gray-400">
                              {getBestBookmaker(match.bookmakers, 'draw')}
                            </div>
                          </div>
                        )}
                        
                        <div className="bg-gray-700 rounded-lg p-4 text-center">
                          <div className="text-yellow-400 font-medium mb-1">Best Away Odds</div>
                          <div className="text-2xl font-bold text-white">
                            {getBestOdds(match.bookmakers, 'away')?.toFixed(2) || 'N/A'}
                          </div>
                          <div className="text-sm text-gray-400">
                            {getBestBookmaker(match.bookmakers, 'away')}
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-lg font-semibold text-white mb-4">All Bookmakers</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {match.bookmakers.map((bookie, index) => (
                            <div key={index} className="bg-gray-750 rounded-lg p-4 border border-gray-600">
                              <div className="text-yellow-400 font-medium mb-3 text-center">{bookie.name}</div>
                              <div className="space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-gray-300">{match.home_team}:</span>
                                  <span className="font-medium text-white">{bookie.home?.toFixed(2) || 'N/A'}</span>
                                </div>
                                {bookie.draw && (
                                  <div className="flex justify-between">
                                    <span className="text-gray-300">Draw:</span>
                                    <span className="font-medium text-white">{bookie.draw.toFixed(2)}</span>
                                  </div>
                                )}
                                <div className="flex justify-between">
                                  <span className="text-gray-300">{match.away_team}:</span>
                                  <span className="font-medium text-white">{bookie.away?.toFixed(2) || 'N/A'}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-gray-800 rounded-xl p-12 text-center border border-gray-700">
            <div className="text-gray-400 mb-4">
              <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No Matches Found</h3>
            <p className="text-gray-400 mb-4">
              No matches found for your search criteria. Try a different sport or clear your search.
            </p>
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedRegion('all');
                setSelectedSport('all');
              }}
              className="bg-yellow-400 text-gray-900 px-6 py-3 rounded-lg font-medium hover:bg-yellow-500 transition-colors"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OddsComparison; 