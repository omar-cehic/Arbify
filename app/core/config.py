# config.py
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PRIVATE_URL") or "sqlite:///./arbitrage.db"

# Railway deployment detection - look for Railway environment variables
IS_RAILWAY_DEPLOYMENT = bool(
    os.getenv("RAILWAY_ENVIRONMENT") or 
    os.getenv("RAILWAY_PROJECT_ID") or
    os.getenv("RAILWAY_SERVICE_ID") or
    (DATABASE_URL and "postgres" in DATABASE_URL and not "localhost" in DATABASE_URL)
)

# If using Railway's PostgreSQL, it might provide DATABASE_URL with postgres:// 
# but SQLAlchemy 2.0 requires postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# API Configuration - MIGRATED TO SPORTSGAMEODDS
# Legacy Odds API (being phased out)
LEGACY_ODDS_API_KEY = os.getenv("ODDS_API_KEY", "your_odds_api_key_here") 
LEGACY_BASE_API_URL = "https://api.the-odds-api.com/v4"

# SportsGameOdds API (new primary API)
SGO_API_KEY = os.getenv("SGO_API_KEY")
SGO_BASE_URL = "https://api.sportsgameodds.com/v2"

# Use SGO as primary API
API_KEY = SGO_API_KEY
BASE_API_URL = SGO_BASE_URL

# Security & Reliability
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    import secrets
    print("⚠️  WARNING: SECRET_KEY not set! Generating temporary key...")
    print("🔑 Add this to your environment: SECRET_KEY=" + secrets.token_urlsafe(32))
    SECRET_KEY = secrets.token_urlsafe(32)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

# Rate Limiting
RATE_LIMIT_PER_USER: int = 100  # Requests per minute per user
SGO_RATE_LIMIT: int = 290       # Requests per minute (SGO Limit is 300, keep buffer)

STALE_DATA_THRESHOLD_MINUTES: int = 15  # Reject odds older than 15 minutes

# Email Configuration (Resend)
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("EMAIL_FROM", "notifications@arbify.net")

# Sentry Configuration
SENTRY_DSN = os.getenv("SENTRY_DSN", "https://80ffc795adf5f0ed33917683608635ca@o4509956621139968.ingest.us.sentry.io/4509956632477696")

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Frontend URL (for CORS and redirects)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Force production mode if deployed on Railway (override local .env files)
if IS_RAILWAY_DEPLOYMENT and ENVIRONMENT == "development":
    ENVIRONMENT = "production"
    print("[CONFIG] Detected Railway deployment - forcing ENVIRONMENT to production")

DEBUG = ENVIRONMENT == "development"

# Port configuration for Railway
PORT = int(os.getenv("PORT", 8001))

# Development Mode Settings
DEV_MODE = ENVIRONMENT == "development"
CACHE_DURATION = timedelta(hours=24)

print(f"[CONFIG] ENVIRONMENT={ENVIRONMENT} DEV_MODE={DEV_MODE}")
print(f"[CONFIG] IS_RAILWAY_DEPLOYMENT={IS_RAILWAY_DEPLOYMENT}")
print(f"[CONFIG] DATABASE_URL prefix: {DATABASE_URL[:50] if DATABASE_URL else 'None'}...")
print(f"[CONFIG] RAILWAY_ENVIRONMENT={os.getenv('RAILWAY_ENVIRONMENT')}")
print(f"[CONFIG] RAILWAY_PROJECT_ID={os.getenv('RAILWAY_PROJECT_ID')}")

# Define leagues and mock data
MOCK_LEAGUES = [
    {"key": "soccer_epl", "title": "English Premier League"},
    {"key": "soccer_spain_la_liga", "title": "La Liga"},
    {"key": "soccer_italy_serie_a", "title": "Serie A"},
    {"key": "soccer_germany_bundesliga", "title": "Bundesliga"},
    {"key": "soccer_france_ligue_one", "title": "Ligue 1"}
]

# Comprehensive list of bookmakers available through The Odds API
ALL_AVAILABLE_BOOKMAKERS = [
    # === US BOOKMAKERS ===
    "BetOnline.ag", "BetMGM", "BetRivers", "BetUS", "Bovada", "Caesars", "DraftKings", 
    "Fanatics", "FanDuel", "LowVig.ag", "MyBookie.ag",
    
    # === US2 BOOKMAKERS ===
    "Bally Bet", "BetAnySports", "betPARX", "ESPN BET", "Fliff", "Hard Rock Bet", 
    "ReBet", "Wind Creek", "Betfred PA",
    
    # === US DFS SITES ===
    "DraftKings Pick6", "PrizePicks", "Underdog Fantasy",
    
    # === US EXCHANGES ===
    "BetOpenly", "Novig", "ProphetX",
    
    # === UK BOOKMAKERS ===
    "888sport", "Betfair Exchange", "Betfair Sportsbook", "Bet Victor", "Betway", 
    "BoyleSports", "Casumo", "Coral", "Grosvenor", "Ladbrokes", "LeoVegas", 
    "LiveScore Bet", "Matchbook", "Paddy Power", "Sky Bet", "Smarkets", "Unibet", 
    "Virgin Bet", "William Hill", "Bet365",
    
    # === EU BOOKMAKERS ===
    "1xBet", "888sport", "Betclic (FR)", "BetAnySports", "Betfair Exchange", 
    "BetOnline.ag", "Betsson", "Bet Victor", "Coolbet", "Everygame", "GTbets", 
    "Marathon Bet", "Matchbook", "MyBookie.ag", "NordicBet", "Nordic Bet", 
    "Parions Sport (FR)", "Pinnacle", "Suprabets", "Tipico (DE)", "Unibet (FR)", 
    "Unibet (IT)", "Unibet (NL)", "William Hill", "Winamax (DE)", "Winamax (FR)",
    "Winamax", "Betclic", "Tipico", "Parions Sport",
    
    # === AU BOOKMAKERS ===
    "Betfair Exchange (AU)", "Betr", "Bet Right", "Bet365 AU", "BoomBet", "Dabble AU", 
    "Ladbrokes (AU)", "Neds", "PlayUp", "PointsBet (AU)", "SportsBet", "TAB", 
    "TABtouch", "Unibet"
]

# Mock data for development (smaller subset for testing)
MOCK_BOOKMAKERS = [
    "FanDuel", "DraftKings", "BetMGM", "Caesars", "PointsBet",
    "BetRivers", "Bovada", "LowVig.ag", "BetUS"
]

# Sample matches for development
MOCK_MATCHES = {
    "soccer_epl": [
        ("Arsenal", "Manchester United"),
        ("Liverpool", "Manchester City"),
        ("Chelsea", "Tottenham"),
        ("Newcastle", "Aston Villa"),
        ("Brighton", "West Ham"),
    ],
    "soccer_spain_la_liga": [
        ("Real Madrid", "Barcelona"),
        ("Atletico Madrid", "Sevilla"),
        ("Real Sociedad", "Athletic Bilbao"),
        ("Valencia", "Villarreal"),
        ("Real Betis", "Getafe"),
    ],
    "soccer_italy_serie_a": [
        ("Inter Milan", "AC Milan"),
        ("Juventus", "Napoli"),
        ("Roma", "Lazio"),
        ("Atalanta", "Fiorentina"),
        ("Bologna", "Torino"),
    ],
    "soccer_germany_bundesliga": [
        ("Bayern Munich", "Borussia Dortmund"),
        ("RB Leipzig", "Bayer Leverkusen"),
        ("Eintracht Frankfurt", "VfL Wolfsburg"),
        ("SC Freiburg", "VfB Stuttgart"),
        ("FC Koln", "Union Berlin"),
    ],
    "soccer_france_ligue_one": [
        ("PSG", "Marseille"),
        ("Lyon", "Monaco"),
        ("Lille", "Rennes"),
        ("Nice", "Lens"),
        ("Strasbourg", "Montpellier"),
    ]
}

def get_mock_match_time():
    """Generate a realistic future match time"""
    now = datetime.now()
    days_ahead = random.randint(1, 14)  # Match within next 2 weeks
    hours = random.choice([12, 14, 15, 16, 17, 19, 20])  # Common match times
    minutes = random.choice([0, 30])  # Matches usually start on hour or half hour
    
    future_date = now + timedelta(days=days_ahead)
    return datetime(
        future_date.year,
        future_date.month,
        future_date.day,
        hours,
        minutes
    )

def generate_realistic_odds():
    """Generate realistic odds with occasional arbitrage opportunities"""
    if random.random() < 0.1:  # 10% chance of arbitrage opportunity
        # Generate odds that create an arbitrage opportunity
        total_prob = random.uniform(0.97, 0.99)  # Ensure total probability < 1
        prob_home = random.uniform(0.3, 0.5) * total_prob
        prob_away = random.uniform(0.2, 0.4) * total_prob
        prob_draw = (1 - prob_home - prob_away) * total_prob
        
        return {
            "home": round(1 / prob_home, 2),
            "away": round(1 / prob_away, 2),
            "draw": round(1 / prob_draw, 2)
        }
    else:
        # Generate normal odds with bookmaker margin
        margin = random.uniform(0.02, 0.05)  # 2-5% margin
        prob_home = random.uniform(0.3, 0.5)
        prob_away = random.uniform(0.2, 0.4)
        prob_draw = 1 - prob_home - prob_away
        
        # Add margin to odds
        total = (prob_home + prob_away + prob_draw) * (1 + margin)
        return {
            "home": round(total / prob_home, 2),
            "away": round(total / prob_away, 2),
            "draw": round(total / prob_draw, 2)
        }

# Development mode configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEV_MODE = ENVIRONMENT == "development"

# API request limits
MAX_REQUESTS_PER_HOUR = 25  # Adjust based on your API plan
REQUESTS_TIMEOUT = 60  # seconds between requests