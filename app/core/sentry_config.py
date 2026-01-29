"""
Sentry Configuration for Error Tracking and Performance Monitoring
"""
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from app.core.config import IS_RAILWAY_DEPLOYMENT, DEV_MODE

def init_sentry():
    """Initialize Sentry for error tracking and performance monitoring"""
    
    # Get Sentry DSN from environment variables
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    print(f"🔧 SENTRY INIT: DSN found: {bool(sentry_dsn)}")
    print(f"🔧 SENTRY INIT: DSN length: {len(sentry_dsn) if sentry_dsn else 0}")
    print(f"🔧 SENTRY INIT: Railway deployment: {IS_RAILWAY_DEPLOYMENT}")
    
    if not sentry_dsn:
        if IS_RAILWAY_DEPLOYMENT:
            print("⚠️  WARNING: SENTRY_DSN not found in production environment")
        else:
            print("ℹ️  Sentry not configured for local development")
        return
    
    # Determine environment
    environment = "production" if IS_RAILWAY_DEPLOYMENT else "development"
    
    # Configure Sentry
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        
        # Performance Monitoring
        traces_sample_rate=1.0 if not IS_RAILWAY_DEPLOYMENT else 0.1,  # 100% in dev, 10% in prod
        profiles_sample_rate=1.0 if not IS_RAILWAY_DEPLOYMENT else 0.1,
        
        # Error Sampling
        sample_rate=1.0,  # Capture 100% of errors
        
        # Integrations
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=None,        # Capture records from all log levels
                event_level=None   # Send no logs as events (only errors)
            ),
            AsyncioIntegration(),
        ],
        
        # Additional Configuration
        debug=DEV_MODE,
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send personally identifiable information
        max_breadcrumbs=50,
        
        # Custom tags
        before_send=before_send_filter,
    )
    
    # Set custom tags
    sentry_sdk.set_tag("service", "arbify-backend")
    sentry_sdk.set_tag("version", "1.0.0")
    
    print(f"✅ Sentry initialized for {environment} environment")
    
    # Test Sentry in development
    if DEV_MODE:
        print("🧪 Testing Sentry integration...")
        try:
            # This will create a test error in Sentry
            sentry_sdk.capture_message("Sentry test message from Arbify backend", level="info")
            print("✅ Sentry test message sent successfully")
        except Exception as e:
            print(f"❌ Sentry test failed: {e}")
    
    # Always test in production too for debugging
    print("🧪 Testing Sentry integration (production)...")
    try:
        sentry_sdk.capture_message("Sentry initialization test from Arbify backend", level="info")
        print("✅ Sentry initialization test message sent successfully")
    except Exception as e:
        print(f"❌ Sentry initialization test failed: {e}")

def before_send_filter(event, hint):
    """Filter and enhance events before sending to Sentry"""
    
    # Don't send certain errors to Sentry
    if 'exception' in event:
        exc_info = hint.get('exc_info')
        if exc_info:
            exc_type, exc_value, exc_traceback = exc_info
            
            # Filter out common/expected errors
            if exc_type.__name__ in ['HTTPException', 'ValidationError']:
                # These are usually client errors, not server errors
                return None
            
    # Filter out rate limiting errors (Exception based)
    if 'exception' in event:
        exc_info = hint.get('exc_info')
        if exc_info:
            exc_type, exc_value, exc_traceback = exc_info
            if 'rate limit' in str(exc_value).lower():
                return None

    # Filter out rate limiting logs (Text based)
    log_entry = event.get('logentry', {})
    message = log_entry.get('message', '') if isinstance(log_entry, dict) else str(log_entry)
    
    # Check top-level message if logentry is empty
    if not message:
        message = event.get('message', '')
        
    if message and ('rate limit' in message.lower() or '429' in message):
        return None
    
    # Add custom context
    sentry_sdk.set_context("application", {
        "name": "Arbify",
        "version": "1.0.0",
        "environment": "production" if IS_RAILWAY_DEPLOYMENT else "development"
    })
    
    return event

def capture_arbitrage_error(error_type: str, details: dict):
    """Capture arbitrage-specific errors with context"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("error_category", "arbitrage")
        scope.set_tag("arbitrage_error_type", error_type)
        scope.set_context("arbitrage_details", details)
        
        sentry_sdk.capture_exception()

def capture_api_error(api_name: str, endpoint: str, status_code: int, error_details: dict):
    """Capture API-related errors with context"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("error_category", "api")
        scope.set_tag("api_name", api_name)
        scope.set_tag("api_endpoint", endpoint)
        scope.set_tag("api_status_code", status_code)
        scope.set_context("api_error_details", error_details)
        
        sentry_sdk.capture_message(
            f"API Error: {api_name} - {endpoint} returned {status_code}",
            level="error"
        )

def capture_user_action(user_id: int, action: str, details: dict = None):
    """Capture important user actions for monitoring"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_user({"id": user_id})
        scope.set_tag("user_action", action)
        if details:
            scope.set_context("action_details", details)
        
        sentry_sdk.capture_message(
            f"User Action: {action}",
            level="info"
        )
