# sgo_config.py - SportsGameOdds API Configuration
"""
Configuration file for SGO API integration.
Update this file when you add your API key and configure sports markets.
"""

# SGO API Configuration
SGO_API_KEY = os.getenv("SGO_API_KEY")  # Replace with your actual API key
SGO_BASE_URL = "https://api.sportsgameodds.com/v2"

# Rookie Plan Limits
ROOKIE_PLAN_LIMITS = {
    "requests_per_minute": 60,
    "objects_per_month": 5000000,  # 5M objects
    "update_frequency_minutes": 5
}

# Available Leagues in Rookie Plan
ROOKIE_PLAN_LEAGUES = [
    "NFL",      # National Football League
    "NBA",      # National Basketball Association  
    "MLB",      # Major League Baseball
    "NHL",      # National Hockey League
    # Note: EPL and other international leagues require higher tier
]

# Priority Markets for Arbitrage Detection
PRIORITY_MARKETS = {
    "moneyline_game": {
        "stat_id": "points",
        "bet_type_id": "ml", 
        "period_id": "game",
        "stat_entity_ids": ["home", "away"],
        "odd_ids": ["points-home-game-ml-home", "points-away-game-ml-away"],
        "description": "Moneyline (Full Game)"
    },
    "spread_game": {
        "stat_id": "points",
        "bet_type_id": "sp",
        "period_id": "game", 
        "stat_entity_ids": ["home", "away"],
        "odd_ids": ["points-home-game-sp-home", "points-away-game-sp-away"],
        "description": "Spread (Full Game)"
    },
    "totals_game": {
        "stat_id": "points",
        "bet_type_id": "ou",
        "period_id": "game",
        "stat_entity_ids": ["all"],
        "odd_ids": ["points-all-game-ou-over", "points-all-game-ou-under"], 
        "description": "Over/Under (Full Game)"
    }
}

# US Licensed Bookmakers (for legal compliance)
US_LICENSED_BOOKMAKERS = {
    'draftkings', 'fanduel', 'betmgm', 'caesars', 'espnbet', 'betrivers',
    'fanatics', 'hardrockbet', 'bovada', 'betus', 'mybookie', 'lowvig'
}

# Polling Strategy Configuration
POLLING_STRATEGY = {
    "daily_budget": 166667,  # ~5M/30 days
    "max_events_per_session": 100,
    "polling_times": ["08:00", "12:00", "16:00", "20:00", "00:00"],
    "priority_leagues": ["NFL", "NBA", "MLB", "NHL"]
}

# Rate Limiting Configuration
RATE_LIMITING = {
    "delay_between_requests": 0.1,  # 0.1 seconds (600 req/min)
    "cache_duration": 300,  # 5 minutes
    "retry_delay": 60  # 60 seconds on rate limit
}

# Data Processing Configuration
DATA_PROCESSING = {
    "min_profit_threshold": 0.1,  # Minimum 0.1% profit
    "max_opportunities_per_request": 50,
    "event_lookback_hours": 24  # Only events starting within 24 hours
}

# Error Handling Configuration
ERROR_HANDLING = {
    "max_retries": 3,
    "retry_delay": 5,  # seconds
    "fallback_to_cached": True,
    "log_errors": True
}

# Development/Testing Configuration
DEVELOPMENT = {
    "enable_debug_logging": True,
    "mock_data_fallback": False,  # Set to True for testing without API key
    "test_mode": False
}

def get_config():
    """Get the complete configuration dictionary"""
    return {
        "api_key": SGO_API_KEY,
        "base_url": SGO_BASE_URL,
        "rookie_plan_limits": ROOKIE_PLAN_LIMITS,
        "available_leagues": ROOKIE_PLAN_LEAGUES,
        "priority_markets": PRIORITY_MARKETS,
        "us_licensed_bookmakers": US_LICENSED_BOOKMAKERS,
        "polling_strategy": POLLING_STRATEGY,
        "rate_limiting": RATE_LIMITING,
        "data_processing": DATA_PROCESSING,
        "error_handling": ERROR_HANDLING,
        "development": DEVELOPMENT
    }

def validate_config():
    """Validate the configuration"""
    errors = []
    
    if not SGO_API_KEY or SGO_API_KEY == "beabe2dd7d51d5425f87eab97fbca604":
        errors.append("SGO_API_KEY not configured - please add your actual API key")
    
    if not ROOKIE_PLAN_LEAGUES:
        errors.append("No leagues configured for Rookie plan")
    
    if not PRIORITY_MARKETS:
        errors.append("No priority markets configured")
    
    return errors

if __name__ == "__main__":
    # Print configuration for review
    config = get_config()
    print("SGO Configuration:")
    print(f"API Key: {'***' + SGO_API_KEY[-4:] if SGO_API_KEY else 'NOT SET'}")
    print(f"Base URL: {SGO_BASE_URL}")
    print(f"Available Leagues: {ROOKIE_PLAN_LEAGUES}")
    print(f"Priority Markets: {list(PRIORITY_MARKETS.keys())}")
    
    # Validate configuration
    errors = validate_config()
    if errors:
        print("\nConfiguration Errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✅ Configuration is valid!")
