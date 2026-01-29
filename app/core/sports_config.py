# sports_config.py - Comprehensive sports coverage matching The Odds API

SUPPORTED_SPORTS = {
    # === AMERICAN FOOTBALL ===
    "americanfootball_cfl": {
        "title": "CFL",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 2
    },
    "americanfootball_ncaaf": {
        "title": "NCAAF",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 1
    },
    "americanfootball_ncaaf_championship_winner": {
        "title": "NCAAF Championship Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 3
    },
    "americanfootball_nfl": {
        "title": "NFL",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 1
    },
    "americanfootball_nfl_preseason": {
        "title": "NFL Preseason",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 3
    },
    "americanfootball_nfl_super_bowl_winner": {
        "title": "NFL Super Bowl Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },
    "americanfootball_ufl": {
        "title": "UFL",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 3
    },

    # === AUSSIE RULES ===
    "aussierules_afl": {
        "title": "AFL",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 2
    },

    # === BASEBALL ===
    "baseball_mlb": {
        "title": "MLB",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 1
    },
    "baseball_mlb_preseason": {
        "title": "MLB Preseason",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 3
    },
    "baseball_mlb_world_series_winner": {
        "title": "MLB World Series Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 2
    },
    "baseball_milb": {
        "title": "Minor League Baseball",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "baseball_npb": {
        "title": "NPB",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "baseball_kbo": {
        "title": "KBO League",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "baseball_ncaa": {
        "title": "NCAA Baseball",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },

    # === BASKETBALL ===
    "basketball_euroleague": {
        "title": "Basketball Euroleague",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 2
    },
    "basketball_nba": {
        "title": "NBA",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 1
    },
    "basketball_nba_preseason": {
        "title": "NBA Preseason",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 3
    },
    "basketball_nba_summer_league": {
        "title": "NBA Summer League",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 3
    },
    "basketball_nba_championship_winner": {
        "title": "NBA Championship Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },
    "basketball_wnba": {
        "title": "WNBA",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 2
    },
    "basketball_ncaab": {
        "title": "NCAAB",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 1
    },
    "basketball_wncaab": {
        "title": "WNCAAB",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 2
    },
    "basketball_ncaab_championship_winner": {
        "title": "NCAAB Championship Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 2
    },
    "basketball_nbl": {
        "title": "NBL (Australia)",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },

    # === BOXING ===
    "boxing_boxing": {
        "title": "Boxing",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },

    # === CRICKET ===
    "cricket_big_bash": {
        "title": "Big Bash",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "cricket_caribbean_premier_league": {
        "title": "Caribbean Premier League",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "cricket_icc_trophy": {
        "title": "ICC Champions Trophy",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "cricket_icc_world_cup": {
        "title": "ICC World Cup",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "cricket_international_t20": {
        "title": "International Twenty20",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "cricket_ipl": {
        "title": "IPL",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "cricket_odi": {
        "title": "One Day Internationals",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "cricket_psl": {
        "title": "Pakistan Super League",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "cricket_t20_blast": {
        "title": "T20 Blast",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "cricket_test_match": {
        "title": "Test Matches",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "cricket_the_hundred": {
        "title": "The Hundred",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },

    # === GOLF ===
    "golf_masters_tournament_winner": {
        "title": "Masters Tournament Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },
    "golf_pga_championship_winner": {
        "title": "PGA Championship Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },
    "golf_the_open_championship_winner": {
        "title": "The Open Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },
    "golf_us_open_winner": {
        "title": "US Open Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },

    # === ICE HOCKEY === (DISABLED - Not in SGO Pro plan yet)
    "icehockey_nhl": {
        "title": "NHL",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": False,  # Disabled until SGO Pro plan supports it
        "priority": 1
    },
    "icehockey_ahl": {
        "title": "AHL",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "icehockey_nhl_championship_winner": {
        "title": "NHL Championship Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": False,  # Disabled - no NHL data allowed
        "priority": 1
    },
    "icehockey_liiga": {
        "title": "Finnish Liiga",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "icehockey_mestis": {
        "title": "Finnish Mestis",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "icehockey_sweden_hockey_league": {
        "title": "SHL",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "icehockey_sweden_allsvenskan": {
        "title": "HockeyAllsvenskan",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },

    # === LACROSSE === (DISABLED - Not in SGO Pro plan)
    "lacrosse_pll": {
        "title": "Premier Lacrosse League",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": False,  # Disabled - not in SGO Pro plan
        "priority": 3
    },
    "lacrosse_ncaa": {
        "title": "NCAA Lacrosse",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },

    # === MIXED MARTIAL ARTS === (DISABLED - Not in SGO Pro plan)
    "mma_mixed_martial_arts": {
        "title": "MMA",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": False,  # Disabled - not in SGO Pro plan
        "priority": 2
    },

    # === POLITICS ===
    "politics_us_presidential_election_winner": {
        "title": "US Presidential Elections Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 3
    },

    # === RUGBY LEAGUE ===
    "rugbyleague_nrl": {
        "title": "NRL",
        "outcomes": 2,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 2
    },
    "rugbyleague_nrl_state_of_origin": {
        "title": "NRL State of Origin",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },

    # === RUGBY UNION ===
    "rugbyunion_six_nations": {
        "title": "Six Nations",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },

    # === SOCCER ===
    "soccer_africa_cup_of_nations": {
        "title": "Africa Cup of Nations",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_argentina_primera_division": {
        "title": "Primera División - Argentina",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_australia_aleague": {
        "title": "A-League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_austria_bundesliga": {
        "title": "Austrian Football Bundesliga",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_belgium_first_div": {
        "title": "Belgium First Div",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_brazil_campeonato": {
        "title": "Brazil Série A",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_brazil_serie_b": {
        "title": "Brazil Série B",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_chile_campeonato": {
        "title": "Primera División - Chile",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_china_superleague": {
        "title": "Super League - China",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_denmark_superliga": {
        "title": "Denmark Superliga",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_efl_champ": {
        "title": "Championship",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_england_efl_cup": {
        "title": "EFL Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_england_league1": {
        "title": "League 1",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_england_league2": {
        "title": "League 2",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_epl": {
        "title": "English Premier League",
        "outcomes": 3,
        "markets": ["h2h", "spreads", "totals"],
        "active": True,
        "priority": 1
    },
    "soccer_fa_cup": {
        "title": "FA Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_fifa_world_cup": {
        "title": "FIFA World Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_fifa_world_cup_qualifiers_europe": {
        "title": "FIFA World Cup Qualifiers - Europe",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_fifa_world_cup_qualifiers_south_america": {
        "title": "FIFA World Cup Qualifiers - South America",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_fifa_world_cup_womens": {
        "title": "FIFA Women's World Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_fifa_world_cup_winner": {
        "title": "FIFA World Cup Winner",
        "outcomes": 2,
        "markets": ["outrights"],
        "active": True,
        "priority": 1
    },
    "soccer_fifa_club_world_cup": {
        "title": "FIFA Club World Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_finland_veikkausliiga": {
        "title": "Veikkausliiga - Finland",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_france_ligue_one": {
        "title": "Ligue 1 - France",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_france_ligue_two": {
        "title": "Ligue 2 - France",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_germany_bundesliga": {
        "title": "Bundesliga - Germany",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_germany_bundesliga2": {
        "title": "Bundesliga 2 - Germany",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_germany_liga3": {
        "title": "3. Liga - Germany",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_greece_super_league": {
        "title": "Super League - Greece",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_italy_serie_a": {
        "title": "Serie A - Italy",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_italy_serie_b": {
        "title": "Serie B - Italy",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_japan_j_league": {
        "title": "J League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_korea_kleague1": {
        "title": "K League 1",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_league_of_ireland": {
        "title": "League of Ireland",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_mexico_ligamx": {
        "title": "Liga MX",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_netherlands_eredivisie": {
        "title": "Dutch Eredivisie",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_norway_eliteserien": {
        "title": "Eliteserien - Norway",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_poland_ekstraklasa": {
        "title": "Ekstraklasa - Poland",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_portugal_primeira_liga": {
        "title": "Primeira Liga - Portugal",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_spain_la_liga": {
        "title": "La Liga - Spain",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_spain_segunda_division": {
        "title": "La Liga 2 - Spain",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_spl": {
        "title": "Premiership - Scotland",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_sweden_allsvenskan": {
        "title": "Allsvenskan - Sweden",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_sweden_superettan": {
        "title": "Superettan - Sweden",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_switzerland_superleague": {
        "title": "Swiss Superleague",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_turkey_super_league": {
        "title": "Turkey Super League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_uefa_europa_conference_league": {
        "title": "UEFA Europa Conference League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_uefa_champs_league": {
        "title": "UEFA Champions League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_uefa_champs_league_qualification": {
        "title": "UEFA Champions League Qualification",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_uefa_europa_league": {
        "title": "UEFA Europa League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_uefa_european_championship": {
        "title": "UEFA Euro 2024",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_uefa_euro_qualification": {
        "title": "UEFA Euro Qualification",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_uefa_nations_league": {
        "title": "UEFA Nations League",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_concacaf_gold_cup": {
        "title": "CONCACAF Gold Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_concacaf_leagues_cup": {
        "title": "CONCACAF Leagues Cup",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_conmebol_copa_america": {
        "title": "Copa América",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "soccer_conmebol_copa_libertadores": {
        "title": "Copa Libertadores",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "soccer_conmebol_copa_sudamericana": {
        "title": "Copa Sudamericana",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "soccer_usa_mls": {
        "title": "MLS",
        "outcomes": 3,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },

    # === TENNIS ===
    "tennis_atp_aus_open_singles": {
        "title": "ATP Australian Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_atp_canadian_open": {
        "title": "ATP Canadian Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_china_open": {
        "title": "ATP China Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "tennis_atp_cincinnati_open": {
        "title": "ATP Cincinnati Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_dubai": {
        "title": "ATP Dubai Championships",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_french_open": {
        "title": "ATP French Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_atp_indian_wells": {
        "title": "ATP Indian Wells",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_italian_open": {
        "title": "ATP Italian Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_madrid_open": {
        "title": "ATP Madrid Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_miami_open": {
        "title": "ATP Miami Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_monte_carlo_masters": {
        "title": "ATP Monte-Carlo Masters",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_paris_masters": {
        "title": "ATP Paris Masters",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_qatar_open": {
        "title": "ATP Qatar Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "tennis_atp_shanghai_masters": {
        "title": "ATP Shanghai Masters",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_atp_us_open": {
        "title": "ATP US Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_atp_wimbledon": {
        "title": "ATP Wimbledon",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_wta_aus_open_singles": {
        "title": "WTA Australian Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_wta_canadian_open": {
        "title": "WTA Canadian Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_china_open": {
        "title": "WTA China Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "tennis_wta_cincinnati_open": {
        "title": "WTA Cincinnati Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_dubai": {
        "title": "WTA Dubai Championships",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_french_open": {
        "title": "WTA French Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_wta_indian_wells": {
        "title": "WTA Indian Wells",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_italian_open": {
        "title": "WTA Italian Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_madrid_open": {
        "title": "WTA Madrid Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_miami_open": {
        "title": "WTA Miami Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 2
    },
    "tennis_wta_qatar_open": {
        "title": "WTA Qatar Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    },
    "tennis_wta_us_open": {
        "title": "WTA US Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_wta_wimbledon": {
        "title": "WTA Wimbledon",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 1
    },
    "tennis_wta_wuhan_open": {
        "title": "WTA Wuhan Open",
        "outcomes": 2,
        "markets": ["h2h"],
        "active": True,
        "priority": 3
    }
}

# Helper functions
def get_active_sports():
    """Get all active sports"""
    return {k: v for k, v in SUPPORTED_SPORTS.items() if v["active"]}

def get_priority_sports(priority=1):
    """Get sports by priority level (1=highest, 3=lowest)"""
    return {k: v for k, v in SUPPORTED_SPORTS.items() 
            if v["active"] and v["priority"] == priority}

def get_sports_by_category():
    """Group sports by category for display"""
    categories = {
        "Soccer": [k for k, v in SUPPORTED_SPORTS.items() if "soccer" in k and v["active"]],
        "American Football": [k for k, v in SUPPORTED_SPORTS.items() if "americanfootball" in k and v["active"]],
        "Basketball": [k for k, v in SUPPORTED_SPORTS.items() if "basketball" in k and v["active"]],
        "Hockey": [k for k, v in SUPPORTED_SPORTS.items() if "icehockey" in k and v["active"]],
        "Baseball": [k for k, v in SUPPORTED_SPORTS.items() if "baseball" in k and v["active"]],
        "Tennis": [k for k, v in SUPPORTED_SPORTS.items() if "tennis" in k and v["active"]],
        "Other": [k for k, v in SUPPORTED_SPORTS.items() if not any(sport in k for sport in ["soccer", "americanfootball", "basketball", "icehockey", "baseball", "tennis"]) and v["active"]]
    }
    return {k: v for k, v in categories.items() if v}  # Remove empty categories