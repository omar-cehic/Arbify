from fastapi import FastAPI, Request, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
import logging
import requests
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import sentry_sdk
from app.core.config import API_KEY, DATABASE_URL, BASE_API_URL, PORT, FRONTEND_URL, DEBUG, ENVIRONMENT, DEV_MODE, SENTRY_DSN
from app.core.sports_config import SUPPORTED_SPORTS
from app.api.v1.router import router as api_router, get_odds_from_api

# Initialize Sentry
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        profiles_sample_rate=1.0,
        environment=ENVIRONMENT
    )
    logging.info("✅ Sentry initialized")

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, BettingOdds, Base, engine
from scripts.mock_data import generate_mock_odds
from app.api.v1.subscriptions import router as subscription_router
from scripts.arbitrage_notifications import run_notification_checker

# Import all models to ensure they're registered with Base
from app.models.user import User, UserProfile, UserArbitrage, UserEmailNotificationLog
from app.models.subscription import SubscriptionPlan, UserSubscription, SubscriptionPayment, FeatureAccess

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# TEST: Database persistence check - account should survive this deployment
# This comment was added to trigger a redeploy and test if user accounts persist

def initialize_database():
    """Initialize database with proper error handling and verification"""
    try:
        logger.info(f"🔗 Initializing database: {DATABASE_URL[:50]}...")
        logger.info(f"🌍 Environment: {ENVIRONMENT}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully!")
        
        # Run auto-fix for missing columns (production only)
        try:
            from auto_fix_migration import auto_fix_database
            if auto_fix_database():
                logger.info("✅ Database auto-fix completed")
            else:
                logger.warning("⚠️ Database auto-fix failed, continuing anyway")
        except ImportError:
            logger.info("ℹ️ Auto-fix migration not available")
        except Exception as e:
            logger.warning(f"⚠️ Auto-fix error (continuing): {str(e)}")
        
        # Verify connection and tables (PostgreSQL-specific check)
        if "postgresql" in DATABASE_URL:
            with engine.connect() as conn:
                # Safe parameterized query for PostgreSQL table check
                result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = :schema"), {"schema": "public"})
                tables = [row[0] for row in result]
                logger.info(f"📋 Available tables: {', '.join(tables)}")
                
                # Ensure critical tables exist
                required_tables = ['users', 'subscription_plans', 'user_subscriptions']
                missing_tables = [table for table in required_tables if table not in tables]
                if missing_tables:
                    logger.error(f"❌ Missing required tables: {missing_tables}")
                    return False
                    
        # Seed subscription plans if they don't exist
        seed_subscription_plans()
        logger.info("🎯 Database initialization completed successfully")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        # Don't fail completely - let the app try to start
        return True  # Changed to True to allow startup even with DB issues
    except Exception as e:
        logger.error(f"❌ Unexpected database error: {str(e)}")
        return True  # Changed to True to allow startup even with unexpected issues

def seed_subscription_plans():
    """Ensure subscription plans exist in the database and are up to date"""
    try:
        db = SessionLocal()
        
        # Check/Update 'Pro' plan (ID 2 usually, or by name)
        pro_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == 'Pro').first()
        if pro_plan:
            # Force update price to $39.99
            if pro_plan.price_monthly != 39.99:
                pro_plan.price_monthly = 39.99
                pro_plan.features = 'Real-time Alerts,Unlimited Strategies,Advanced Calculator,All Sports,Instant Notifications'
                db.commit()
                logger.info("✅ Updated 'Pro' plan price to $39.99")
        else:
            # Create Pro plan
            pro_plan = SubscriptionPlan(
                name='Pro',
                price_monthly=39.99,
                price_annual=399.99,
                description='The ultimate tool for sports arbitrage',
                max_strategies=100,
                max_alerts=1000,
                refresh_rate=30,
                advanced_features=True
            )
            db.add(pro_plan)
            db.commit()
            logger.info("✅ Created 'Pro' plan with $39.99")

        # Create Basic plan if missing (optional)
        basic_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == 'Basic').first()
        if not basic_plan:
            basic_plan = SubscriptionPlan(
                name='Basic',
                price_monthly=19.99, 
                description='Get started with arbitrage betting',
                max_strategies=2,
                max_alerts=10
            )
            db.add(basic_plan)
            db.commit()

        db.close()
        
    except Exception as e:
        logger.error(f"❌ Error seeding subscription plans: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()

# Database will be initialized in the lifespan handler to avoid blocking app creation

# Create a single BackgroundScheduler instance
scheduler = BackgroundScheduler()

# Define a single lifespan handler to manage startup/shutdown tasks
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Quick initialization first, then background tasks
    logger.info("=== APPLICATION STARTUP ===")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Database URL: {DATABASE_URL[:50]}..." if DATABASE_URL else "No DATABASE_URL")
    logger.info(f"Frontend URL: {FRONTEND_URL}")
    
    # Initialize Sentry for error tracking (disabled - sentry_sdk not installed)
    # try:
    #     init_sentry()
    #     logger.info("✅ Sentry error tracking initialized")
    # except Exception as e:
    #     logger.error(f"❌ Failed to initialize Sentry: {e}")
    
    # Initialize database quickly and non-blocking
    async def init_database_async():
        """Initialize database in background"""
        try:
            if not initialize_database():
                logger.error("❌ Database initialization failed!")
            else:
                logger.info("✅ Database initialized successfully!")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
    
    # Start background tasks without blocking startup
    async def start_background_services():
        """Start background services"""
        try:
            # 1. Run emergency schema fix (ensures sport_title exists)
            logger.info("🔧 Running schema fix...")
            from app.core.schema_fix import check_and_fix_schema
            check_and_fix_schema()
            
            logger.info("Starting background scheduler...")
            scheduler.start()
            logger.info("✅ Background scheduler started!")
            
            # Start arbitrage notification service
            logger.info("🔔 Starting arbitrage notification service...")
            from scripts.arbitrage_notifications import run_notification_checker
            asyncio.create_task(run_notification_checker())
            logger.info("✅ Arbitrage notification service task created!")
            
            # Start SGO arbitrage detection service
            logger.info("🎯 Starting SGO arbitrage detection service...")
            from app.services.arbitrage_detector import start_arbitrage_detection
            asyncio.create_task(start_arbitrage_detection())
            logger.info("✅ SGO arbitrage detection service task created!")
            
        except Exception as e:
            logger.error(f"❌ Failed to start background services: {str(e)}")
    
    # Run initialization tasks in background
    asyncio.create_task(init_database_async())
    asyncio.create_task(start_background_services())
    
    logger.info("Application startup complete!")
    yield
    
    # Shutdown: shut down the scheduler
    logger.info("=== APPLICATION SHUTDOWN ===")
    try:
        scheduler.shutdown()
        logger.info("✅ Background scheduler stopped")
    except Exception as e:
        logger.error(f"❌ Error stopping scheduler: {e}")
    logger.info("Shutdown complete!")

# Create rate limiter (removed slowapi)
# limiter = Limiter(key_func=get_remote_address)

# Create the FastAPI app with the lifespan handler
app = FastAPI(title="Arbitrage Betting API", lifespan=lifespan)

# Add Custom Rate Limiting Middleware
from app.core.middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# Add Sentry middleware for error tracking (disabled - sentry_sdk not installed)
# app.middleware("http")(sentry_middleware)

# Add security middleware (will be imported after deployment)
try:
    from app.core.security_middleware import SecurityMiddleware, HTTPSRedirectMiddleware
    
    # Add comprehensive security middleware with error handling
    try:
        app.add_middleware(SecurityMiddleware, environment=ENVIRONMENT)
        logger.info("✅ Advanced SecurityMiddleware added successfully")
    except Exception as e:
        logger.error(f"❌ Failed to add SecurityMiddleware: {e}")
        raise  # Re-raise to trigger fallback
    
    # Add HTTPS redirect for production
    if ENVIRONMENT == "production":
        try:
            app.add_middleware(HTTPSRedirectMiddleware)
            logger.info("✅ HTTPSRedirectMiddleware added successfully")
        except Exception as e:
            logger.error(f"❌ Failed to add HTTPSRedirectMiddleware: {e}")
    
    logger.info("✅ Advanced security middleware loaded successfully")
    
except (ImportError, Exception) as e:
    logger.warning(f"⚠️  Security middleware failed, using fallback: {e}")
    # Fallback to basic security headers
    @app.middleware("http")
    async def add_basic_security_headers(request: Request, call_next):
        """Basic security headers fallback"""
        response = await call_next(request)
        
        # Basic security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Server"] = "Arbify-Fallback/1.0"  # Identify fallback mode
        
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.stripe.com https://arbify-beige.vercel.app https://web-production-af8b.up.railway.app; "
                "frame-src https://js.stripe.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        
        return response
    
    logger.warning("⚠️  Using basic security headers fallback mode")

# Add trusted host middleware for production
if ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=[
            "arbify.vercel.app", 
            "*.vercel.app",
            "web-production-af8b.up.railway.app",
            "*.railway.app",
            "*.railway.internal",
            "localhost",
            "127.0.0.1"
        ]
    )

app.include_router(subscription_router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(subscription_router, prefix="/api/subscription", tags=["Subscriptions"])
# Configure CORS
from app.core.config import FRONTEND_URL, DEBUG

# Set allowed origins based on environment
allowed_origins = [
    "http://localhost:5173",  # Local development
    "http://localhost:3000",  # Alternative local port
    "https://arbify-beige.vercel.app",  # Current Vercel deployment
    "https://arbify.vercel.app",  # Alternative Vercel domain
    "https://arbify.net",  # Future production domain
    "https://www.arbify.net",  # Future production domain with www
]

# Add dynamic frontend URL if set and not already included
if FRONTEND_URL and FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)

# Remove duplicates and None values, and clean up any formatting issues
allowed_origins = [origin.strip().rstrip(';').rstrip(',') for origin in allowed_origins if origin and origin.strip()]
allowed_origins = list(set(allowed_origins))

print(f"[CORS] Allowed origins: {allowed_origins}")
print(f"[CORS] DEBUG mode: {DEBUG}")
print(f"[CORS] FRONTEND_URL: {FRONTEND_URL}")

# Add CORS middleware with proper configuration
cors_allow_all = os.getenv("CORS_ALLOW_ALL", "true").lower() == "true"  # Default to true for now to fix connection issues

# Ensure critical origins are present
required_origins = [
    "https://arbify-beige.vercel.app",
    "https://arbify.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000"
]
for origin in required_origins:
    if origin not in allowed_origins:
        allowed_origins.append(origin)

if cors_allow_all:
    print("WARNING: CORS set to allow all origins (forcing wildcard for fix)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
elif ENVIRONMENT != "production":
    print("WARNING: CORS set to allow all origins (development mode)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using wildcard
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    print(f"CORS configured for production with {len(allowed_origins)} allowed origins")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
        expose_headers=["Content-Type", "Authorization"],
    )

# Mount static files for the dashboard
# app.mount("/static", StaticFiles(directory="static"), name="static")  # Removed - using React frontend

# Path to React app build
react_app_path = "frontend/dist"

# Mount the React app's assets directory if it exists
vite_assets_path = os.path.join(react_app_path, "assets")
if os.path.exists(vite_assets_path):
    logger.info(f"Mounting Vite assets from {vite_assets_path}")
    app.mount("/assets", StaticFiles(directory=vite_assets_path), name="vite-assets")
else:
    logger.warning(f"Vite assets directory {vite_assets_path} not found. If you're running the React app separately, ignore this warning.")

# Mount the React app's images directory
images_path = os.path.join(react_app_path, "images")
if os.path.exists(images_path):
    logger.info(f"Mounting Vite images from {images_path}")
    app.mount("/images", StaticFiles(directory=images_path), name="vite-images")
else:
    logger.warning(f"Vite images directory {images_path} not found. If you need images, ensure this directory exists.")

# Dashboard Home page (serving index.html)
@app.get("/", response_class=HTMLResponse, tags=["Home"])
def index():
    logger.info("Index endpoint hit")
    index_path = os.path.join(react_app_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Fallback if React build doesn't exist
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Arbify - Arbitrage Betting Platform</title></head>
        <body>
            <h1>Arbify</h1>
            <p>React app not built yet. Run 'npm run build' in the frontend directory.</p>
        </body>
        </html>
        """, status_code=200)

# Include our API routes under the /api prefix
app.include_router(api_router, prefix="/api")

# Health check endpoint for Railway
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for deployment monitoring"""
    return {
        "status": "healthy", 
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    }

# Simple status endpoint for Railway health checks
@app.get("/status", tags=["Health"])
async def railway_health_check():
    """Simple health check for Railway - responds immediately"""
    return {
        "status": "healthy",
        "service": "arbify-backend",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat()
    }

# Ultra-simple backup health endpoint (no middleware interference)
@app.get("/healthz", tags=["Health"])
def simple_health():
    """Ultra-simple health check - guaranteed to work"""
    return {"status": "ok"}

# Email test endpoint (no auth required)
@app.get("/test/email", tags=["Testing"])
async def test_email_notification():
    """Test endpoint to send a test email notification"""
    try:
        from scripts.arbitrage_notifications import ArbitrageNotificationService
        
        notification_service = ArbitrageNotificationService()
        
        # Create a test opportunity
        test_opportunity = {
            "home_team": "[TEST] Chiefs",
            "away_team": "[TEST] Bills",
            "profit_percentage": 2.5,
            "match": {
                "home_team": "[TEST] Chiefs",
                "away_team": "[TEST] Bills", 
                "commence_time": "2025-09-15T20:00:00.000Z"
            },
            "sport_title": "NFL Football",
            "best_odds": {
                "home": {"odds": 1.95, "bookmaker": "fanduel"},
                "away": {"odds": 2.05, "bookmaker": "draftkings"}
            }
        }
        
        # Send test email
        test_email = "omarcehic7@gmail.com"
        
        success = await notification_service.send_notification_email(
            email=test_email,
            opportunities=[test_opportunity],
            subscription_status="test"
        )
        
        return {
            "status": "success" if success else "failed",
            "message": f"Test email {'sent successfully' if success else 'failed to send'} to {test_email}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error sending test email: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Manual notification trigger endpoint (no auth required for testing)
@app.get("/test/trigger-notifications", tags=["Testing"])
async def trigger_notifications_manually():
    """Manually trigger the notification system to check for opportunities and send emails"""
    try:
        from scripts.arbitrage_notifications import notification_service
        
        # Manually trigger the notification check
        await notification_service.check_and_notify_users()
        
        return {
            "status": "success",
            "message": "Notification check completed - emails sent if opportunities found",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error triggering notifications: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Data quality test endpoint (no auth required)
@app.get("/test/data-quality", tags=["Testing"])
async def test_data_quality():
    """Test endpoint to check data quality without authentication"""
    try:
        from scripts.sgo_production_service import SGOProLiveService
        
        async with SGOProLiveService() as sgo_service:
            opportunities = await sgo_service.get_upcoming_arbitrage_opportunities()
            
            # Analyze data quality
            analysis = {
                "total_opportunities": len(opportunities),
                "fake_data_count": 0,
                "suspicious_count": 0,
                "clean_count": 0,
                "issues_found": []
            }
            
            for opp in opportunities:
                home = opp.get('home_team', 'Unknown')
                away = opp.get('away_team', 'Unknown')
                profit = opp.get('profit_percentage', 0)
                best_odds = opp.get('best_odds', {})
                
                # Check for fake data patterns
                if best_odds:
                    odds_values = []
                    for side_key, side_data in best_odds.items():
                        if isinstance(side_data, dict) and 'odds' in side_data:
                            odds_values.append(side_data['odds'])
                    
                    # Identical odds = fake data
                    if len(odds_values) >= 2 and len(set(odds_values)) == 1:
                        analysis["fake_data_count"] += 1
                        analysis["issues_found"].append({
                            "match": f"{home} vs {away}",
                            "issue": "FAKE DATA: Identical odds",
                            "profit": profit,
                            "odds": odds_values[0]
                        })
                    # Nearly identical = suspicious
                    elif len(odds_values) >= 2 and abs(max(odds_values) - min(odds_values)) < 0.01:
                        analysis["suspicious_count"] += 1
                        analysis["issues_found"].append({
                            "match": f"{home} vs {away}",
                            "issue": "SUSPICIOUS: Nearly identical odds",
                            "profit": profit,
                            "odds_range": f"{min(odds_values):.3f} - {max(odds_values):.3f}"
                        })
                    else:
                        analysis["clean_count"] += 1
            
            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "data_quality_analysis": analysis,
                "message": f"Found {analysis['fake_data_count']} fake and {analysis['suspicious_count']} suspicious opportunities out of {analysis['total_opportunities']} total"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error testing data quality: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Database migration endpoint for production
@app.post("/admin/migrate", tags=["Admin"])
async def run_migrations():
    """Run database migrations manually - for production use"""
    try:
        from alembic import command
        from alembic.config import Config
        
        # Get current working directory and run migrations
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        
        return {
            "status": "success",
            "message": "Database migrations completed successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        return {
            "status": "error", 
            "message": f"Migration failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Add auth router directly for password change functionality
from app.api.v1.auth import router as auth_router
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

# Add direct routes for verification pages
@app.get("/verification-success", response_class=HTMLResponse, tags=["Auth"])
def verification_success_page(username: str = None):
    """Serve the verification success page"""
    logger.info(f"Verification success page endpoint hit for user: {username}")
    
    # Customize message based on whether username is provided
    user_message = f"Account for <strong>{username}</strong> has been" if username else "Your email has been"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verified</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                background-color: #111111;
                max-width: 100%;
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background-color: #222222;
                border-radius: 10px;
                padding: 40px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                text-align: center;
            }}
            .logo {{
                margin-bottom: 20px;
                display: inline-block;
            }}
            .logo-img {{
                max-width: 180px;
                height: auto;
            }}
            .logo-placeholder {{
                background-color: #d4af37;
                color: #000000;
                font-weight: bold;
                padding: 12px 20px;
                font-size: 18px;
                letter-spacing: 1px;
                display: inline-block;
            }}
            h1 {{
                color: #d4af37;
                margin-bottom: 20px;
                font-size: 28px;
            }}
            .button {{
                display: inline-block;
                background-color: #d4af37;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 30px;
                transition: background-color 0.3s, transform 0.2s;
                border: none;
                font-size: 16px;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #e5be42;
                transform: translateY(-2px);
            }}
            .success-icon {{
                color: #00cc66;
                font-size: 64px;
                margin-bottom: 20px;
            }}
            .user-message {{
                color: #ffffff;
                font-size: 18px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img 
                    src="/images/arbify-logo.png" 
                    alt="Arbify" 
                    class="logo-img"
                    onerror="this.style.display='none'; this.parentNode.innerHTML='<div class=\'logo-placeholder\'>ARBIFY</div>';"
                />
            </div>
            <div class="success-icon">✓</div>
            <h1>Email Verified Successfully!</h1>
            <p class="user-message">{user_message} successfully verified. You can now log in to your account.</p>
            <a href="/login" class="button">Log In Now</a>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/verification-failed", response_class=HTMLResponse, tags=["Auth"])
def verification_failed_page(error: str = "Verification failed"):
    """Serve the verification failed page"""
    logger.info("Verification failed page endpoint hit")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verification Failed</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                background-color: #111111;
                max-width: 100%;
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background-color: #222222;
                border-radius: 10px;
                padding: 40px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                text-align: center;
            }}
            .logo {{
                margin-bottom: 20px;
                display: inline-block;
            }}
            .logo-img {{
                max-width: 180px;
                height: auto;
            }}
            .logo-placeholder {{
                background-color: #d4af37;
                color: #000000;
                font-weight: bold;
                padding: 12px 20px;
                font-size: 18px;
                letter-spacing: 1px;
                display: inline-block;
            }}
            h1 {{
                color: #cc4444;
                margin-bottom: 20px;
                font-size: 28px;
            }}
            .button {{
                display: inline-block;
                background-color: #d4af37;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 30px;
                transition: background-color 0.3s, transform 0.2s;
                border: none;
                font-size: 16px;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #e5be42;
                transform: translateY(-2px);
            }}
            .error-icon {{
                color: #cc4444;
                font-size: 64px;
                margin-bottom: 20px;
            }}
            .error-message {{
                background-color: rgba(204, 68, 68, 0.2);
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
                border: 1px solid rgba(204, 68, 68, 0.3);
            }}
            .secondary-link {{
                color: #d4af37;
                text-decoration: none;
                margin-top: 20px;
                display: inline-block;
                font-size: 15px;
                transition: color 0.3s;
            }}
            .secondary-link:hover {{
                color: #e5be42;
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img 
                    src="/images/arbify-logo.png" 
                    alt="Arbify" 
                    class="logo-img"
                    onerror="this.style.display='none'; this.parentNode.innerHTML='<div class=\'logo-placeholder\'>ARBIFY</div>';"
                />
            </div>
            <div class="error-icon">✗</div>
            <h1>Verification Failed</h1>
            <div class="error-message">
                {error}
            </div>
            <p>There was a problem verifying your email. Please try again or contact support.</p>
            <a href="/login" class="button">Return to Login</a>
            <div style="margin-top: 20px;">
                <a href="/direct-verify" class="secondary-link">Try Manual Verification</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

# Function to serve the React app for SPA routes
def serve_react_app():
    react_index_path = os.path.join(react_app_path, "index.html")
    if os.path.exists(react_index_path):
        logger.info(f"Serving React app from {react_index_path}")
        return FileResponse(react_index_path)
    else:
        logger.warning(f"React app index not found at {react_index_path}")
        return HTMLResponse("<html><body><h1>Not Available</h1><p>React app not built yet.</p></body></html>")

# React app routes
@app.get("/register", tags=["Auth"])
def register_page():
    logger.info("Register page endpoint hit - Serving React app")
    return serve_react_app()

@app.get("/login", tags=["Auth"])
def login_page():
    logger.info("Login page endpoint hit - Serving React app")
    return serve_react_app()

# Email verification page removed - users are auto-verified

# Existing routes
@app.get("/profile", response_class=HTMLResponse, tags=["Profile"])
def profile_page():
    logger.info("Profile page endpoint hit - Serving React app")
    return serve_react_app()

@app.get("/reset-password", response_class=HTMLResponse, tags=["Auth"])
def reset_password_page():
    logger.info("Reset password page endpoint hit - Serving React app")
    return serve_react_app()

@app.get("/subscriptions", response_class=HTMLResponse, tags=["Subscriptions"])
def subscription_page():
    """Render the subscription plans page"""
    logger.info("Subscription page endpoint hit - Serving React app")
    return serve_react_app()

# CRITICAL SECURITY: Block access to sensitive files and directories
@app.get("/.env")
@app.get("/config.py") 
@app.get("/.git/{path:path}")
@app.get("/debug") 
@app.get("/admin")
async def block_sensitive_paths():
    """Block access to sensitive files and directories"""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Not found"
    )

# A catch-all route to serve React app for any unhandled client-side routes
@app.get("/{full_path:path}")
async def catch_all(request: Request, full_path: str):
    # Skip API routes - return 404 explicitly
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # Skip static routes
    if full_path.startswith(("static/", "assets/")):
        raise HTTPException(status_code=404, detail="Not Found")
    
    # For all other routes, serve the React app if available
    logger.info(f"Serving React app for path: {full_path}")
    return serve_react_app()

# Development tools page
@app.get("/dev-tools", response_class=HTMLResponse, tags=["Development"])
def dev_tools_page():
    # Only return the development tools page if in development mode
    if os.getenv("ENVIRONMENT", "development") != "production":
        logger.info("Development tools page endpoint hit")
        # Return a simple dev tools page since static files were removed
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Arbify - Development Tools</title></head>
        <body>
            <h1>Development Tools</h1>
            <p>Development tools are available via the React frontend.</p>
            <a href="/">Back to Main App</a>
        </body>
        </html>
        """, status_code=200)
    else:
        # Redirect to home in production
        return RedirectResponse(url="/")

# Direct verification helper page
@app.get("/direct-verify", response_class=HTMLResponse, tags=["Auth"])
def direct_verify_helper():
    """Serve a helper page for direct verification"""
    logger.info("Direct verification helper page endpoint hit")
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Direct Email Verification</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                background-color: #1a1a1a;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
                text-align: center;
            }
            .container {
                background-color: #333;
                border-radius: 8px;
                padding: 30px;
                margin-top: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .logo {
                margin-bottom: 30px;
            }
            h1 {
                color: #d4af37;
                margin-bottom: 20px;
            }
            .button {
                display: inline-block;
                background-color: #d4af37;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 10px;
                transition: background-color 0.3s;
            }
            .button:hover {
                background-color: #b8971e;
            }
            input {
                width: 100%;
                padding: 12px;
                margin-bottom: 20px;
                border: 1px solid #555;
                background-color: #444;
                color: #fff;
                border-radius: 4px;
            }
            .info-icon {
                color: #3498db;
                font-size: 64px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img src="/images/arbify-logo.png" alt="Arbify" height="64">
            </div>
            <div class="info-icon">ℹ</div>
            <h1>Direct Email Verification</h1>
            <p>Enter your verification token below to verify your email address:</p>
            
            <div id="verification-form">
                <input type="text" id="token-input" placeholder="Paste your verification token here">
                <button class="button" onclick="verifyToken()">Verify Email</button>
            </div>
            
            <p style="margin-top: 30px; color: #888;">
                You can find your token in the verification email or in the console logs.
            </p>
            
            <script>
                function verifyToken() {
                    const token = document.getElementById('token-input').value.trim();
                    if (token) {
                        window.location.href = `/api/auth/email/dev-verify-token/${token}`;
                    } else {
                        alert('Please enter a verification token');
                    }
                }
            </script>
        </div>
    </body>
    </html>
    """
    return html_content

# User verification helper page
@app.get("/verify-user", response_class=HTMLResponse, tags=["Auth"])
def verify_user_helper():
    """Serve a helper page for user verification"""
    logger.info("User verification helper page endpoint hit")
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify User</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                background-color: #1a1a1a;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px 20px;
                text-align: center;
            }
            .container {
                background-color: #333;
                border-radius: 8px;
                padding: 30px;
                margin-top: 40px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .logo {
                margin-bottom: 30px;
            }
            h1 {
                color: #d4af37;
                margin-bottom: 20px;
            }
            .button {
                display: inline-block;
                background-color: #d4af37;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin-top: 10px;
                transition: background-color 0.3s;
            }
            .button:hover {
                background-color: #b8971e;
            }
            input {
                width: 100%;
                padding: 12px;
                margin-bottom: 20px;
                border: 1px solid #555;
                background-color: #444;
                color: #fff;
                border-radius: 4px;
            }
            .info-icon {
                color: #3498db;
                font-size: 64px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img src="/images/arbify-logo.png" alt="Arbify" height="64">
            </div>
            <div class="info-icon">ℹ</div>
            <h1>Verify User Account</h1>
            <p>Enter a username below to directly verify that user's account:</p>
            
            <div id="verification-form">
                <input type="text" id="username-input" placeholder="Enter username to verify">
                <button class="button" onclick="verifyUser()">Verify User</button>
            </div>
            
            <script>
                function verifyUser() {
                    const username = document.getElementById('username-input').value.trim();
                    if (username) {
                        window.location.href = `/api/auth/email/direct-verify/${username}`;
                    } else {
                        alert('Please enter a username');
                    }
                }
            </script>
        </div>
    </body>
    </html>
    """
    return html_content

# --- Background Scheduler Setup ---

async def update_odds(db: Session):
    """Update odds using SGOProLiveService (Unified Logic)"""
    try:
        logger.info("🔧 BACKGROUND SCHEDULER: Starting scheduled odds update via SGOProLiveService...")
        
        # Import the robust service
        from app.services.sgo_pro_live_service import SGOProLiveService
        
        total_count = 0
        
        # Use the service to fetch and save odds
        # The service's get_upcoming_arbitrage_opportunities method now calls save_odds_to_database internally
        async with SGOProLiveService() as service:
            # 1. Fetch upcoming opportunities (which saves odds)
            logger.info("🔧 BACKGROUND SCHEDULER: Fetching upcoming events...")
            upcoming_opps = await service.get_upcoming_arbitrage_opportunities()
            logger.info(f"🔧 BACKGROUND SCHEDULER: Found {len(upcoming_opps)} upcoming arbitrage opportunities")
            
            # 2. Fetch live opportunities (which saves odds)
            logger.info("🔧 BACKGROUND SCHEDULER: Fetching live events...")
            live_opps = await service.get_live_arbitrage_opportunities()
            logger.info(f"🔧 BACKGROUND SCHEDULER: Found {len(live_opps)} live arbitrage opportunities")
            
            # Check database count to confirm
            current_count = db.query(BettingOdds).count()
            logger.info(f"🔧 BACKGROUND SCHEDULER: Database now contains {current_count} odds records")
            
            return current_count
            
    except Exception as e:
        logger.error(f"Failed to update odds in background task: {e}")
        return 0

async def test_algorithm_with_sample_data():
    """Test the algorithm with sample SGO data to verify it works"""
    try:
        logger.error(f"🔴 ALGORITHM TEST: Starting sample data test")
        
        # Sample SGO-style odds data
        sample_sgo_odds = {
            "points-home-game-ml-home": {
                "byBookmaker": {
                    "bet365": {"americanOdds": "-110", "odds": 1.91},
                    "pinnacle": {"americanOdds": "+120", "odds": 2.20}
                }
            },
            "points-away-game-ml-away": {
                "byBookmaker": {
                    "bet365": {"americanOdds": "+105", "odds": 2.05},
                    "pinnacle": {"americanOdds": "-130", "odds": 1.77}
                }
            }
        }
        
        # Test if this creates arbitrage
        home_odds = [1.91, 2.20]  # bet365, pinnacle
        away_odds = [2.05, 1.77]  # bet365, pinnacle
        
        # Best odds: home=2.20 (pinnacle), away=2.05 (bet365)
        best_home = 2.20
        best_away = 2.05
        
        total_implied_prob = (1/best_home) + (1/best_away)
        if total_implied_prob < 1.0:
            profit = ((1/total_implied_prob) - 1) * 100
            logger.error(f"🔴 ALGORITHM TEST RESULT: ARBITRAGE FOUND - {profit:.2f}% profit")
            logger.error(f"🔴 ALGORITHM TEST: Home: {best_home} (Pinnacle), Away: {best_away} (Bet365)")
        else:
            logger.error(f"🔴 ALGORITHM TEST RESULT: No arbitrage - {total_implied_prob:.3f} implied prob")
            
    except Exception as e:
        logger.error(f"🔴 ALGORITHM TEST ERROR: {str(e)}")

def scheduled_job():
    logger.info("🔧 SCHEDULER DEBUG: Running scheduled job...")
    logger.info(f"🔧 SCHEDULER DEBUG: Scheduler is running: {scheduler.running}")
    logger.info(f"🔧 SCHEDULER DEBUG: Active jobs: {len(scheduler.get_jobs())}")
    
    db = SessionLocal()
    try:
        result = asyncio.run(update_odds(db))
        logger.info(f"🔧 SCHEDULER DEBUG: Scheduled job completed, result: {result}")
    except Exception as e:
        logger.error(f"🔧 SCHEDULER DEBUG: Scheduled job failed: {e}")
        import traceback
        logger.error(f"🔧 SCHEDULER DEBUG: Traceback: {traceback.format_exc()}")
    finally:
        db.close()

# API Quota Management - Reset for Pro Plan
API_USAGE_TRACKER = {
    "daily_calls": 0,
    "monthly_calls": 0,
    "last_reset_date": datetime.now().date(),
    "last_reset_month": datetime.now().month,
    "quota_exhausted": False
}

# SGO Pro Plan API limits - UNLIMITED objects, 300 requests/minute
# Pro plan specifications: UNLIMITED objects per month, 300 req/min rate limit
# Using realistic limits that allow full utilization of Pro plan capabilities
DAILY_LIMIT = 20000   # Pro plan daily limit (allows ~14 requests/minute average)
MONTHLY_LIMIT = 600000  # Pro plan monthly limit (UNLIMITED objects)

def check_and_update_api_quota():
    """Check API quota before making calls"""
    global API_USAGE_TRACKER
    
    current_date = datetime.now().date()
    current_month = datetime.now().month
    
    # Reset daily counter
    if API_USAGE_TRACKER["last_reset_date"] != current_date:
        API_USAGE_TRACKER["daily_calls"] = 0
        API_USAGE_TRACKER["last_reset_date"] = current_date
        logger.info(f"📅 Daily API quota reset. Used today: 0/{DAILY_LIMIT}")
    
    # Reset monthly counter
    if API_USAGE_TRACKER["last_reset_month"] != current_month:
        API_USAGE_TRACKER["monthly_calls"] = 0
        API_USAGE_TRACKER["last_reset_month"] = current_month
        API_USAGE_TRACKER["quota_exhausted"] = False
        logger.info(f"📅 Monthly API quota reset. Used this month: 0/{MONTHLY_LIMIT}")
    
    # Check if quota is exhausted
    if (API_USAGE_TRACKER["daily_calls"] >= DAILY_LIMIT or 
        API_USAGE_TRACKER["monthly_calls"] >= MONTHLY_LIMIT):
        API_USAGE_TRACKER["quota_exhausted"] = True
        logger.warning(f"⚠️ API QUOTA EXHAUSTED - Daily: {API_USAGE_TRACKER['daily_calls']}/{DAILY_LIMIT}, Monthly: {API_USAGE_TRACKER['monthly_calls']}/{MONTHLY_LIMIT}")
        return False
    
    return True

def increment_api_usage(calls_made=1):
    """Increment API usage counters"""
    global API_USAGE_TRACKER
    API_USAGE_TRACKER["daily_calls"] += calls_made
    API_USAGE_TRACKER["monthly_calls"] += calls_made
    
    logger.info(f"📊 API Usage - Daily: {API_USAGE_TRACKER['daily_calls']}/{DAILY_LIMIT} ({(API_USAGE_TRACKER['daily_calls']/DAILY_LIMIT)*100:.1f}%)")
    logger.info(f"📊 API Usage - Monthly: {API_USAGE_TRACKER['monthly_calls']}/{MONTHLY_LIMIT} ({(API_USAGE_TRACKER['monthly_calls']/MONTHLY_LIMIT)*100:.1f}%)")

def scheduled_job_with_quota_check():
    """Wrapper for scheduled job with quota management"""
    if not check_and_update_api_quota():
        logger.warning("⚠️ Skipping scheduled odds fetch - API quota exhausted")
        return
    
    # Estimate API calls needed (optimized for SGO Pro plan)
    # Pro plan: UNLIMITED objects, 300 req/min - can be more aggressive
    estimated_calls = 15  # Optimized estimate for Pro plan with unlimited objects
    
    if (API_USAGE_TRACKER["daily_calls"] + estimated_calls > DAILY_LIMIT or
        API_USAGE_TRACKER["monthly_calls"] + estimated_calls > MONTHLY_LIMIT):
        logger.warning(f"⚠️ Skipping odds fetch - would exceed quota (estimated {estimated_calls} calls needed)")
        return
    
    try:
        scheduled_job()
        # Increment usage based on estimated calls
        increment_api_usage(estimated_calls)
    except Exception as e:
        logger.error(f"Error in quota-managed scheduled job: {str(e)}")
        # Still increment to be safe
        increment_api_usage(estimated_calls)

# AGGRESSIVE: Use very frequent updates with unlimited API plan
# With unlimited objects and 300 req/min, we can update every 2 minutes safely
logger.info("🔧 SCHEDULER DEBUG: Adding scheduled job (2 minute intervals - maximum freshness)")
scheduler.add_job(scheduled_job_with_quota_check, 'interval', minutes=2, id='odds_update_job')
logger.info(f"🔧 SCHEDULER DEBUG: Job added with quota management. Total jobs: {len(scheduler.get_jobs())}")

# Add quota status endpoint
@app.get("/api/quota-status")
async def get_quota_status():
    """Get current API quota usage"""
    check_and_update_api_quota()  # Update counters
    return {
        "daily_usage": API_USAGE_TRACKER["daily_calls"],
        "daily_limit": DAILY_LIMIT,
        "daily_percentage": round((API_USAGE_TRACKER["daily_calls"] / DAILY_LIMIT) * 100, 1),
        "monthly_usage": API_USAGE_TRACKER["monthly_calls"],
        "monthly_limit": MONTHLY_LIMIT,
        "monthly_percentage": round((API_USAGE_TRACKER["monthly_calls"] / MONTHLY_LIMIT) * 100, 1),
        "quota_exhausted": API_USAGE_TRACKER["quota_exhausted"],
        "last_reset_date": str(API_USAGE_TRACKER["last_reset_date"]),
        "next_daily_reset": str(datetime.now().date() + timedelta(days=1))
    }

# Skip startup job to preserve quota
logger.info("🔧 SCHEDULER DEBUG: Skipping startup job to preserve API quota")

# Main application routes - Root is handled by index() at the top
# @app.get("/")
# async def root():
#     """Root endpoint - redirects to frontend"""
#     return RedirectResponse(url=FRONTEND_URL, status_code=301)

# Status endpoint moved above to avoid duplicate

# Remove duplicate lifespan handler - this is handled above

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)



