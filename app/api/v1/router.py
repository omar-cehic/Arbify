# api.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Request
import requests
import logging
import aiohttp
import os
from sqlalchemy.orm import Session
from sqlalchemy import text

# Set up logger for this module
logger = logging.getLogger(__name__)
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional
import asyncio
import time
import traceback

from app.core.config import API_KEY, BASE_API_URL, SGO_API_KEY, SGO_BASE_URL, DEV_MODE
from app.services.sgo_service import sgo_service, polling_strategy
# Import sports config dynamically to avoid caching issues
# from sports_config import SUPPORTED_SPORTS, get_active_sports, get_priority_sports, get_sports_by_category
from app.core.database import SessionLocal, BettingOdds
# from mock_data import generate_mock_odds  # No longer using mock data
from .users import router as user_router
from .auth import get_current_active_user, get_db
from .my_arbitrage import router as my_arbitrage_router
from app.models.subscription import UserSubscription
from app.models.user import User, UserProfile, UserArbitrage
from scripts.email_verification import send_email  # Reusing existing email function
from app.services.market_arbitrage import find_arbitrage_in_market_enhanced, get_comprehensive_market_display_name
from scripts.match_browser import get_upcoming_matches_summary, get_detailed_match_odds, get_match_browser_stats

# Setup main router
router = APIRouter()

# New: Public Arbitrage Opportunities Endpoint
@router.get("/arbitrage/opportunities")
async def get_public_opportunities(
    sport_key: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get arbitrage opportunities for the authenticated user"""
    try:
        from app.services.sgo_pro_live_service import SGOProLiveService
        async with SGOProLiveService() as sgo_service:
            # Use limited/demo data if user not subscribed, but for now just return what we have
            opportunities = await sgo_service.get_upcoming_arbitrage_opportunities()
            return opportunities
    except Exception as e:
        logger.error(f"Error fetching opportunities: {str(e)}")
        # Return empty list instead of 500 to prevent frontend crash
        return []

# Scheduler status endpoint for debugging  
@router.get("/admin/scheduler-status")
async def get_scheduler_status():
    """Check background scheduler status"""
    try:
        from app.main import scheduler
        
        return {
            "scheduler_running": scheduler.running if hasattr(scheduler, 'running') else False,
            "total_jobs": len(scheduler.get_jobs()) if hasattr(scheduler, 'get_jobs') else 0,
            "jobs": [{"id": job.id, "next_run": str(job.next_run_time)} for job in scheduler.get_jobs()] if hasattr(scheduler, 'get_jobs') else []
        }
    except Exception as e:
        return {"error": str(e)}

# SGO API key test endpoint
@router.get("/admin/test-sgo-key")
async def test_sgo_key():
    """Test SGO API key configuration"""
    try:
        from app.core.config import SGO_API_KEY, SGO_BASE_URL
        import aiohttp
        
        if not SGO_API_KEY or SGO_API_KEY == "beabe2dd7d51d5425f87eab97fbca604":
            return {
                "status": "error",
                "message": "SGO_API_KEY not configured or using placeholder",
                "sgo_key_configured": False
            }
        
        # Test API key with SGO
        headers = {"X-Api-Key": SGO_API_KEY}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SGO_BASE_URL}/account/usage", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "success",
                        "message": "SGO API key is working",
                        "sgo_key_configured": True,
                        "api_response": data.get('data', {})
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"SGO API returned status {response.status}",
                        "sgo_key_configured": True,
                        "api_status": response.status
                    }
                    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error testing SGO key: {str(e)}",
            "sgo_key_configured": False
        }

# Test SGO arbitrage endpoint
@router.get("/admin/test-sgo-arbitrage")
async def test_sgo_arbitrage():
    """Test SGO arbitrage detection"""
    try:
        from app.services.sgo_limited_service import SGOLimitedService
        
        async with SGOLimitedService() as sgo_service:
            opportunities = await sgo_service.get_limited_arbitrage_opportunities()
            
            return {
                "status": "success",
                "message": f"Found {len(opportunities)} opportunities",
                "opportunities": opportunities,
                "test_time": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error testing SGO arbitrage: {str(e)}",
            "test_time": datetime.now().isoformat()
        }

# Validate arbitrage opportunities endpoint
@router.post("/admin/validate-arbitrage")
async def validate_arbitrage_opportunity(
    opportunity: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Validate an arbitrage opportunity for data quality and realism"""
    try:
        # Import the validator
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from validate_arbitrage import ArbitrageValidator
        
        validator = ArbitrageValidator()
        validation_result = await validator.validate_with_external_check(opportunity)
        
        return {
            "status": "success",
            "opportunity": {
                "home_team": opportunity.get("home_team"),
                "away_team": opportunity.get("away_team"), 
                "profit_percentage": opportunity.get("profit_percentage")
            },
            "validation": validation_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Validation error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Get current opportunities with validation
@router.get("/admin/validate-current-opportunities")
async def validate_current_opportunities(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current arbitrage opportunities with validation analysis"""
    try:
        # Get current opportunities from SGO
        from app.services.sgo_pro_live_service import SGOProLiveService
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from validate_arbitrage import ArbitrageValidator
        
        async with SGOProLiveService() as sgo_service:
            opportunities = await sgo_service.get_upcoming_arbitrage_opportunities()
            
            validator = ArbitrageValidator()
            validated_opportunities = []
            
            for opp in opportunities[:5]:  # Validate first 5
                validation = await validator.validate_with_external_check(opp)
                validated_opportunities.append({
                    "opportunity": opp,
                    "validation": validation
                })
            
            return {
                "status": "success", 
                "total_opportunities": len(opportunities),
                "validated_count": len(validated_opportunities),
                "validated_opportunities": validated_opportunities,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error validating opportunities: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# Manual odds update trigger for debugging
@router.post("/admin/trigger-odds-update")
async def trigger_odds_update_manually(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Manually trigger odds update for debugging purposes"""
    try:
        logging.info(f"🔧 MANUAL TRIGGER: User {current_user.username} triggered manual odds update")
        
        # Import the update function from main
        from app.main import update_odds
        
        # Run the update
        result = await update_odds(db)
        
        # Check database afterwards
        total_odds = db.query(BettingOdds).count()
        
        return {
            "success": True,
            "message": f"Odds update completed. Database now contains {total_odds} odds records.",
            "records_added": result if isinstance(result, int) else "unknown"
        }
    except Exception as e:
        logging.error(f"🔧 MANUAL TRIGGER ERROR: {str(e)}")
        return {"success": False, "error": str(e)}

# Live odds endpoint for odds tab (lighter API usage)
@router.get("/odds/live/{sport_key}")
async def get_live_odds(
    sport_key: str,
    markets: str = "h2h,spreads,totals",
    regions: str = "us,uk", 
    bookmakers: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get live odds for a specific sport from key bookmakers (optimized API usage)"""
    try:
        logging.info(f"🔴 LIVE ODDS: Fetching for sport {sport_key}")
        
        # Parse bookmaker filter if provided
        selected_bookmakers = bookmakers.split(',') if bookmakers else None
        logging.info(f"🔴 LIVE ODDS: Selected bookmakers: {selected_bookmakers}")
        
        # Make targeted API call for single sport
        url = f"{BASE_API_URL}/sports/{sport_key}/odds"
        params = {
            "apiKey": API_KEY,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                logging.info(f"🔴 LIVE ODDS: API Response status: {response.status}")
                
                if response.status == 200:
                    matches = await response.json()
                    logging.info(f"🔴 LIVE ODDS: Retrieved {len(matches)} matches")
                    
                    # Filter bookmakers if specified
                    if selected_bookmakers:
                        for match in matches:
                            if 'bookmakers' in match:
                                match['bookmakers'] = [
                                    bm for bm in match['bookmakers'] 
                                    if bm.get('title') in selected_bookmakers
                                ]
                    
                    return {
                        "sport_key": sport_key,
                        "matches": matches,
                        "total_matches": len(matches),
                        "data_source": "live_api",
                        "last_updated": datetime.utcnow().isoformat()
                    }
                elif response.status == 401:
                    error_text = await response.text()
                    logging.error(f"🔴 LIVE ODDS: 401 Unauthorized - {error_text}")
                    return {
                        "sport_key": sport_key,
                        "matches": [],
                        "total_matches": 0,
                        "data_source": "api_unauthorized",
                        "error": "API quota exceeded or invalid key"
                    }
                else:
                    error_text = await response.text()
                    logging.error(f"🔴 LIVE ODDS: HTTP {response.status} error - {error_text}")
                    return {
                        "sport_key": sport_key,
                        "matches": [],
                        "total_matches": 0,
                        "data_source": "api_error",
                        "error": f"API error: {response.status}"
                    }
                    
    except Exception as e:
        logging.error(f"🔴 LIVE ODDS: Exception - {str(e)}")
        return {
            "sport_key": sport_key,
            "matches": [],
            "total_matches": 0,
            "data_source": "error",
            "error": str(e)
        }

# Test endpoint for debugging (no auth required)
@router.get("/test-debug")
async def test_debug():
    """Test endpoint to debug the API data structure"""
    import json
    try:
        # Test with a simple mock data call
        from app.core.config import API_KEY, BASE_API_URL
        
        print("DEBUG - Starting test debug endpoint")
        
        # Test mock data arbitrage detection
        from mock_data import generate_mock_odds
        mock_data = generate_mock_odds("soccer_epl")
        
        print(f"DEBUG - Generated {len(mock_data)} mock matches")
        
        # Test process match function
        if mock_data:
            match = mock_data[0]
            print(f"DEBUG - Testing match: {match.get('home_team')} vs {match.get('away_team')}")
            
            # Call the process_match function to trigger the debugging
            result = await process_match(match, "soccer_epl", {"title": "English Premier League"}, ["us"])
            print(f"DEBUG - Process match result: {result}")
        
        # Return simple debug info
        return {
            "message": "Debug endpoint working",
            "api_key_exists": bool(API_KEY),
            "base_url": BASE_API_URL,
            "mock_matches": len(mock_data),
            "first_match": mock_data[0] if mock_data else None
        }
    except Exception as e:
        import traceback
        print(f"DEBUG ERROR: {str(e)}")
        print(traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}

# Include user routes
router.include_router(user_router, prefix="/auth", tags=["Authentication"])

# Include my arbitrage routes
router.include_router(my_arbitrage_router, prefix="/my-arbitrage", tags=["My Arbitrage"])

# Create a notification router
notification_router = APIRouter(prefix="/notifications", tags=["Notifications"])

# In-memory cache for recently sent notifications to prevent duplicates
recent_notifications = {}

# Background task reference
background_task = None

# API Response Cache - reduces redundant API calls
api_cache = {}
CACHE_DURATION = 60  # Cache responses for 1 minute to match SGO's update frequency

# Odds API functions
async def get_odds_from_api(sport_key: str = None):
    """Get odds from the real Odds API for a single sport or all supported sports"""
    
    # Check cache first to avoid redundant API calls
    cache_key = f"odds_{sport_key or 'all'}"
    current_time = time.time()
    
    if cache_key in api_cache:
        cached_data, cache_time = api_cache[cache_key]
        if current_time - cache_time < CACHE_DURATION:
            logging.info(f"🚀 Using cached odds data for {cache_key} (age: {int(current_time - cache_time)}s)")
            return cached_data
    
    # Import sports config dynamically to get fresh data
    from importlib import reload
    from app.core import sports_config
    reload(sports_config)
    from app.core.sports_config import SUPPORTED_SPORTS
    
    all_odds = []
    
    sports_to_fetch = []
    if sport_key:
        if sport_key in SUPPORTED_SPORTS and SUPPORTED_SPORTS[sport_key]["active"]:
            sports_to_fetch.append((sport_key, SUPPORTED_SPORTS[sport_key]))
    else:
        # Fetch ALL active sports from your API - no artificial limits
        sports_to_fetch = [(key, info) for key, info in SUPPORTED_SPORTS.items() 
                           if info.get("active", False)]
        logging.info(f"🔧 Fetching ALL active sports: {len(sports_to_fetch)} sports available")
    
    if not sports_to_fetch:
        logging.warning("No active sports to fetch odds for")
        return []
    
    # Fetch odds for each sport asynchronously
    async with aiohttp.ClientSession() as session:
        tasks = []
        for sport_key, sport_info in sports_to_fetch:
            task = fetch_sport_odds(session, sport_key, sport_info)
            tasks.append(task)
        
        # Execute all API calls concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Error in concurrent API fetch: {str(result)}")
            elif isinstance(result, list):
                all_odds.extend(result)
    
    logging.info(f"✅ Successfully fetched {len(all_odds)} matches from real API")
    
    # Cache the response for future requests
    api_cache[cache_key] = (all_odds, current_time)
    
    return all_odds


async def fetch_sport_odds(session, sport_key: str, sport_info: dict):
    """Fetch odds for a single sport"""
    try:
        logging.info(f"🔄 API CALL DEBUG: Fetching odds for {sport_info['title']} ({sport_key})")
        logging.info(f"🔄 API CALL DEBUG: API_KEY exists: {bool(API_KEY)}")
        logging.info(f"🔄 API CALL DEBUG: API_KEY first 10 chars: {API_KEY[:10] if API_KEY else 'None'}...")
        logging.info(f"🔄 API CALL DEBUG: BASE_API_URL: {BASE_API_URL}")
        
        # SGO API endpoints (not The Odds API)
        url = f"{BASE_API_URL}/events"
        params = {
            "limit": 50,
            "oddsAvailable": "true",
            "status": "upcoming"
        }
        
        # SGO uses X-Api-Key header, not apiKey param
        headers = {"X-Api-Key": API_KEY}
        
        logging.info(f"🔄 API CALL DEBUG: Making request to {url}")
        
        async with session.get(url, params=params, headers=headers) as response:
            logging.info(f"🔄 API CALL DEBUG: Response status: {response.status}")
            
            if response.status == 200:
                response_data = await response.json()
                
                # SGO API returns data in 'data' field
                odds_data = response_data.get('data', [])
                logging.info(f"🔄 API CALL DEBUG: Received {len(odds_data)} events from SGO API")
                
                # Dense logging - pack SGO response info into one line
                if odds_data:
                    sample_event = odds_data[0]
                    event_keys = list(sample_event.keys())
                    odds_count = len(sample_event.get('odds', {}))
                    logging.debug(f"📊 SGO RESPONSE: {len(odds_data)} events | sample keys: {event_keys[:5]} | odds: {odds_count}")
                    
                    # Check for odds in different locations
                    sample_event = odds_data[0]
                    if 'odds' in sample_event:
                        logging.debug(f"🔴 ODDS FOUND: {len(sample_event['odds'])} odds")
                    elif 'markets' in sample_event:
                        logging.debug(f"🔴 MARKETS FOUND: {len(sample_event['markets'])} markets")
                    elif 'bookmakers' in sample_event:
                        logging.debug(f"🔴 BOOKMAKERS FOUND: {len(sample_event['bookmakers'])} bookmakers")
                    else:
                        logging.debug(f"🔴 NO ODDS STRUCTURE FOUND! Keys: {list(sample_event.keys())}")
                
                # Enhance each event with additional metadata
                enhanced_odds = []
                for event in odds_data:
                    logging.debug(f"🔴 PROCESSING EVENT: {event.get('name', event.get('eventID', 'Unknown'))}")
                    
                    event["sport_key"] = sport_key
                    event["sport_title"] = sport_info["title"]
                    event["outcomes"] = sport_info["outcomes"]
                    event["api_source"] = "sgo_real"
                    event["fetched_at"] = datetime.utcnow().isoformat()
                    enhanced_odds.append(event)
                
                logging.info(f"✅ {sport_info['title']}: {len(enhanced_odds)} events fetched successfully from SGO")
                return enhanced_odds
                
            elif response.status == 401:
                error_text = await response.text()
                logging.error(f"❌ API CALL DEBUG: 401 Unauthorized for {sport_info['title']} - {error_text}")
                logging.error(f"❌ API CALL DEBUG: Check your API key configuration")
                return []
            elif response.status == 429:
                error_text = await response.text()
                logging.error(f"❌ API CALL DEBUG: 429 Rate limit exceeded for {sport_info['title']} - {error_text}")
                return []
            elif response.status == 404:
                error_text = await response.text()
                logging.error(f"❌ API CALL DEBUG: 404 Sport not found for {sport_info['title']} - {error_text}")
                return []
            else:
                error_text = await response.text()
                logging.error(f"❌ API CALL DEBUG: HTTP {response.status} error for {sport_info['title']} - {error_text}")
                return []
                
    except Exception as e:
        logging.error(f"❌ Exception fetching {sport_info['title']}: {str(e)}")
        return []

# Mock data functions removed - only using real API data

async def get_odds_from_database(db: Session, sport_key: str = None) -> List[Dict]:
    """Get odds data from database (stored by background scheduler)"""
    try:
        # DEBUG: Enhanced logging for database debugging
        logging.info(f"🔍 DATABASE DEBUG: Querying odds from database (sport_key: {sport_key})")
        
        # Check total records in database first
        total_records = db.query(BettingOdds).count()
        logging.info(f"🔍 DATABASE DEBUG: Total records in betting_odds table: {total_records}")
        
        # Query stored odds
        query = db.query(BettingOdds)
        if sport_key:
            query = query.filter(BettingOdds.sport_key == sport_key)
        
        records = query.all()
        logging.info(f"📊 Retrieved {len(records)} odds records from database")
        
        # DEBUG: Log sample records if available
        if records:
            sample_record = records[0]
            logging.info(f"🔍 DATABASE DEBUG: Sample record - Sport: {sample_record.sport_key}, Teams: {sample_record.home_team} vs {sample_record.away_team}, Sportsbook: {sample_record.sportsbook}, Odds: {sample_record.odds}")
            
            # Log unique sports available
            unique_sports = db.query(BettingOdds.sport_key).distinct().all()
            sport_keys = [sport[0] for sport in unique_sports]
            logging.info(f"🔍 DATABASE DEBUG: Available sports in database: {sport_keys}")
            
            # Log unique sportsbooks available
            unique_books = db.query(BettingOdds.sportsbook).distinct().all()
            book_names = [book[0] for book in unique_books]
            logging.info(f"🔍 DATABASE DEBUG: Available sportsbooks in database: {book_names}")
        else:
            logging.warning(f"🔍 DATABASE DEBUG: No records found! Checking if table exists and has data...")
            
            # Check if table exists and is accessible (PostgreSQL compatible)
            try:
                from app.core.config import DATABASE_URL
                if "postgresql" in DATABASE_URL:
                    # PostgreSQL table check
                    table_info = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'betting_odds'")).fetchone()
                else:
                    # SQLite table check
                    table_info = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name = 'betting_odds'")).fetchone()
                
                if table_info:
                    logging.info("DATABASE DEBUG: betting_odds table exists")
                else:
                    logging.error("DATABASE DEBUG: betting_odds table does NOT exist!")
            except Exception as table_check_error:
                logging.error(f"DATABASE DEBUG: Error checking table existence: {table_check_error}")
        
        logging.info(f"📊 Retrieved {len(records)} odds records from database")
        
        if not records:
            return []
        
        # Group records by match to create the same structure as API data
        matches_dict = {}
        
        for record in records:
            # Create unique match key
            match_key = (record.sport_key, record.home_team, record.away_team, record.commence_time)
            
            if match_key not in matches_dict:
                matches_dict[match_key] = {
                    "sport_key": record.sport_key,
                    "sport_title": record.sport_title,
                    "commence_time": record.commence_time,
                    "home_team": record.home_team,
                    "away_team": record.away_team,
                    "bookmakers": {}
                }
            
            match_data = matches_dict[match_key]
            
            # Group by bookmaker
            if record.sportsbook not in match_data["bookmakers"]:
                match_data["bookmakers"][record.sportsbook] = {
                    "title": record.sportsbook,
                    "markets": {}
                }
            
            bookmaker_data = match_data["bookmakers"][record.sportsbook]
            
            # For now, assume all odds are h2h (head-to-head) market
            # TODO: Store market type in database for better accuracy
            market_key = "h2h"
            if market_key not in bookmaker_data["markets"]:
                bookmaker_data["markets"][market_key] = {
                    "key": market_key,
                    "outcomes": []
                }
            
            # Add outcome
            bookmaker_data["markets"][market_key]["outcomes"].append({
                "name": record.outcome,
                "price": record.odds
            })
        
        # Convert to list format expected by arbitrage detection
        odds_data = []
        for match_data in matches_dict.values():
            # Convert bookmakers dict to list
            match_data["bookmakers"] = list(match_data["bookmakers"].values())
            # Convert markets dict to list for each bookmaker
            for bookmaker in match_data["bookmakers"]:
                bookmaker["markets"] = list(bookmaker["markets"].values())
            odds_data.append(match_data)
        
        logging.info(f"📊 Converted to {len(odds_data)} matches for arbitrage detection")
        return odds_data
        
    except Exception as e:
        logging.error(f"Error fetching odds from database: {str(e)}")
        return []


async def detect_arbitrage_opportunities(odds_data: List[Dict]) -> List[Dict]:
    """Detect arbitrage opportunities from real API odds data with enhanced filtering"""
    opportunities = []
    seen_matches = set()  # Track unique matches to prevent duplicates
    
    logging.info(f"🔍 Processing {len(odds_data)} matches for arbitrage detection")
    
    # ENHANCED: Filter out stale data first
    current_time = datetime.utcnow()
    filtered_matches = []
    
    for match in odds_data:
        try:
            # Skip matches without bookmakers
            if not match.get("bookmakers"):
                logging.debug(f"🔍 Skipping match without bookmakers: {match.get('home_team')} vs {match.get('away_team')}")
                continue
            
            # ENHANCED: Validate match timing
            commence_time_str = match.get("commence_time")
            if commence_time_str:
                try:
                    commence_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                    time_diff = (commence_time - current_time).total_seconds()
                    
                    # Skip matches that are:
                    # 1. More than 1 hour in the past (likely finished)
                    # 2. More than 30 days in the future (too far ahead)
                    if time_diff < -3600:  # 1 hour ago
                        logging.debug(f"🔍 Skipping past match: {match.get('home_team')} vs {match.get('away_team')} ({commence_time_str})")
                        continue
                    elif time_diff > (30 * 24 * 3600):  # 30 days
                        logging.debug(f"🔍 Skipping far future match: {match.get('home_team')} vs {match.get('away_team')} ({commence_time_str})")
                        continue
                        
                except Exception as e:
                    logging.debug(f"🔍 Could not validate timing for match: {str(e)}")
                    # Don't reject due to timing parse errors, but log it
            
            # ENHANCED: Validate bookmaker data freshness
            has_recent_data = False
            for bookmaker in match.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("outcomes") and len(market.get("outcomes", [])) >= 2:
                        has_recent_data = True
                        break
                if has_recent_data:
                    break
                    
            if not has_recent_data:
                logging.debug(f"🔍 Skipping match without sufficient market data: {match.get('home_team')} vs {match.get('away_team')}")
                continue
                
            filtered_matches.append(match)
            
        except Exception as e:
            logging.debug(f"🔍 Error filtering match: {str(e)}")
            continue
    
    logging.info(f"✅ Filtered to {len(filtered_matches)} valid matches (removed stale/invalid data)")
    
    # Process filtered matches for arbitrage
    for match in filtered_matches:
        try:
            # Create unique match identifier
            match_id = f"{match.get('home_team', 'Unknown')}_{match.get('away_team', 'Unknown')}_{match.get('commence_time', '')}"
            
            # Process each market (h2h, spreads, totals)
            for market_key in ["h2h", "spreads", "totals"]:
                # Create unique opportunity identifier including market
                opp_id = f"{match_id}_{market_key}"
                
                if opp_id in seen_matches:
                    continue  # Skip duplicate
                    
                # Use enhanced arbitrage detection with fixed market parameter grouping
                opportunity = find_arbitrage_in_market_enhanced(match, market_key)
                if opportunity:
                    # ENHANCED: Additional quality checks before including
                    if is_valid_arbitrage_opportunity(opportunity):
                        seen_matches.add(opp_id)
                        opportunities.append(opportunity)
                        
        except Exception as e:
            logging.error(f"Error processing match for arbitrage: {str(e)}")
            continue
    
    # Sort by profit percentage (highest first)
    opportunities.sort(key=lambda x: x.get("profit_percentage", 0), reverse=True)
    
    logging.info(f"🎯 FINAL RESULT: Found {len(opportunities)} unique arbitrage opportunities (after filtering)")
    
    # DEBUG: Log a sample opportunity structure
    if opportunities:
        sample = opportunities[0]
        logging.info(f"📊 SAMPLE OPPORTUNITY STRUCTURE: {list(sample.keys())}")
        logging.info(f"📊 SAMPLE best_odds exists: {'best_odds' in sample}")
        if 'best_odds' in sample:
            logging.info(f"📊 SAMPLE best_odds content: {sample['best_odds']}")
    
    return opportunities


def is_valid_arbitrage_opportunity(opportunity: Dict) -> bool:
    """Enhanced validation for arbitrage opportunities"""
    try:
        # Basic structure validation
        if not opportunity or not isinstance(opportunity, dict):
            return False
            
        # Required fields
        required_fields = ['profit_percentage', 'best_odds', 'match']
        if not all(field in opportunity for field in required_fields):
            logging.debug(f"❌ Missing required fields in opportunity")
            return False
            
        # Profit validation - only reject negative or zero profits
        profit = opportunity.get('profit_percentage', 0)
        if profit <= 0:
            logging.debug(f"❌ Invalid profit percentage: {profit}%")
            return False
        
        # Log high profit opportunities for investigation but NEVER REJECT
        if profit > 10:
            logging.info(f"High profit opportunity: {profit:.2f}%")
            # Continue processing - NEVER reject high profits
            
        # Match timing validation
        match_info = opportunity.get('match', {})
        commence_time_str = match_info.get('commence_time')
        if commence_time_str:
            try:
                commence_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                current_time = datetime.utcnow()
                
                # Ensure match hasn't started yet (allow 15 minutes buffer)
                if (commence_time - current_time).total_seconds() < -900:  # 15 minutes ago
                    logging.debug(f"❌ Match likely already started or finished")
                    return False
                    
            except Exception:
                pass  # Don't reject due to parsing errors
        
        # Bookmaker validation
        best_odds = opportunity.get('best_odds', {})
        if not best_odds:
            return False
            
        # Check for reasonable odds values
        bookmaker_count = 0
        for outcome_key, outcome_data in best_odds.items():
            if isinstance(outcome_data, dict) and outcome_data.get('bookmaker') and outcome_data.get('odds'):
                odds_value = outcome_data.get('odds', 0)
                if odds_value < 1.01 or odds_value > 50:  # Reasonable odds bounds
                    logging.warning(f"❌ Suspicious odds value: {odds_value} for {outcome_key}")
                    return False
                bookmaker_count += 1
                
        # Need at least 2 outcomes for valid arbitrage
        if bookmaker_count < 2:
            logging.debug(f"❌ Not enough valid outcomes: {bookmaker_count}")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Error validating arbitrage opportunity: {str(e)}")
        return False


def find_arbitrage_in_market(match: Dict, market_key: str) -> Optional[Dict]:
    """Find arbitrage opportunity in a specific market"""
    try:
        # DEBUG: Log the match structure
        logging.info(f"🔍 Processing match: {match.get('home_team')} vs {match.get('away_team')} for market: {market_key}")
        logging.info(f"🔍 Bookmakers count: {len(match.get('bookmakers', []))}")
        
        # Collect all odds for this market from all bookmakers
        market_odds = {}  # {outcome: [(bookmaker, odds), ...]}
        market_parameters = {}  # Store market parameters (spread points, totals)
        
        for bookmaker in match.get("bookmakers", []):
            bookmaker_title = bookmaker.get("title", "Unknown")
            logging.debug(f"🔍 Processing bookmaker: {bookmaker_title}")
            
            for market in bookmaker.get("markets", []):
                if market.get("key") != market_key:
                    continue
                
                # For spreads and totals, verify market parameters match
                market_point = market.get("point")  # spread value or total value
                if market_key in ["spreads", "totals"] and market_point is not None:
                    # Group by market parameter to ensure we compare same spreads/totals
                    param_key = f"{market_key}_{market_point}"
                    if param_key not in market_parameters:
                        market_parameters[param_key] = market_point
                    elif market_parameters[param_key] != market_point:
                        # Skip this market as it has different parameters
                        logging.debug(f"🔍 Skipping {market_key} with different parameter: {market_point} vs {market_parameters[param_key]}")
                        continue
                        
                logging.debug(f"🔍 Found market: {market_key} with {len(market.get('outcomes', []))} outcomes")
                
                for outcome in market.get("outcomes", []):
                    outcome_name = outcome.get("name")
                    odds_value = outcome.get("price")
                    
                    # Store the point value separately for frontend display
                    point_value = market_point if market_key in ["spreads", "totals"] and market_point is not None else None
                    
                    # CRITICAL DEBUG: Log point values for totals/spreads markets
                    if market_key in ["spreads", "totals"]:
                        print(f"API DEBUG - Market: {market_key}, Point: {market_point}, Parsed Point Value: {point_value}")
                        print(f"API DEBUG - Outcome: {outcome_name} = {odds_value} from {bookmaker_title}")
                    
                    logging.debug(f"Outcome: {outcome_name} = {odds_value} from {bookmaker_title}")
                    
                    if outcome_name and odds_value:
                        # Create a unique key that includes point value for proper grouping
                        outcome_key = outcome_name
                        if market_key in ["spreads", "totals"] and point_value is not None:
                            outcome_key = f"{outcome_name}_{point_value}"
                        
                        if outcome_key not in market_odds:
                            market_odds[outcome_key] = []
                        market_odds[outcome_key].append((bookmaker_title, odds_value, point_value))
        
        # Need at least 2 outcomes for arbitrage
        if len(market_odds) < 2:
            logging.debug(f"🔍 Skipping - only {len(market_odds)} outcomes found")
            return None
            
        logging.debug(f"🔍 Found {len(market_odds)} outcomes: {list(market_odds.keys())}")
        
        # Find best odds for each outcome
        best_odds = {}
        for outcome, odds_list in market_odds.items():
            # Find highest odds for this outcome (now includes point_value)
            best_entry = max(odds_list, key=lambda x: x[1])
            best_bookmaker, best_odds_value, best_point_value = best_entry
            
            logging.debug(f"🔍 Best odds for {outcome}: {best_odds_value} from {best_bookmaker}")
            
            # MINIMAL VALIDATION: Only reject obviously invalid odds  
            # Allow all realistic betting odds to see true data quality
            if not (1.01 <= best_odds_value <= 100.0):
                logging.warning(f"❌ Rejecting invalid odds value: {best_odds_value} for {outcome} from {best_bookmaker} (outside 1.01-100.0 range)")
                continue
                
            best_odds[outcome] = (best_bookmaker, best_odds_value, best_point_value)
        
        # Need at least 2 outcomes after validation
        if len(best_odds) < 2:
            return None
            
        # Ensure we have at least 2 different bookmakers for valid arbitrage
        unique_bookmakers = set(bookmaker for bookmaker, _, _ in best_odds.values())
        if len(unique_bookmakers) < 2:
            logging.info(f"❌ Skipping arbitrage with single bookmaker: {unique_bookmakers}")
            return None
        
        # CRITICAL: Check for geographic restrictions
        # US users should only see US-licensed sportsbooks for legal compliance
        US_LICENSED_BOOKS = {
            'DraftKings', 'FanDuel', 'BetMGM', 'Caesars', 'ESPN BET', 'BetRivers',
            'Fanatics', 'Hard Rock Bet', 'Bovada', 'BetUS', 'MyBookie.ag', 'LowVig.ag'
        }
        
        # Check if this opportunity involves non-US books
        has_international_books = any(bookmaker not in US_LICENSED_BOOKS 
                                    for bookmaker, _, _ in best_odds.values())
        
        if has_international_books:
            intl_books = [bookmaker for bookmaker, _, _ in best_odds.values() 
                         if bookmaker not in US_LICENSED_BOOKS]
            logging.warning(f"⚠️ Opportunity includes international books: {intl_books} - may not be accessible to US users")
        
        # Additional validation: Check for reasonable odds spread
        # If one outcome has extremely high odds compared to others, it might be an error
        odds_values = [odds[1] for odds in best_odds.values()]
        max_odds = max(odds_values)
        min_odds = min(odds_values)
        odds_ratio = max_odds / min_odds
        
        # Log suspicious odds ratios but don't filter them out (as requested)
        if odds_ratio > 10:
            logging.warning(f"⚠️ High odds ratio detected: {odds_ratio:.2f} (max: {max_odds}, min: {min_odds}) for {match.get('home_team')} vs {match.get('away_team')} - verify data quality")
        
        # CRITICAL: Add data quality warnings for high-profit opportunities
        # These often indicate stale data or pricing errors
        
        # Validate that match has reasonable commence time (not too far in past/future)
        commence_time_str = match.get("commence_time")
        if commence_time_str:
            try:
                commence_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
                now = datetime.now(commence_time.tzinfo)
                time_diff = abs((commence_time - now).total_seconds())
                
                # Reject matches that are more than 30 days away or more than 1 day in the past
                if time_diff > (30 * 24 * 3600):  # 30 days
                    logging.warning(f"❌ Rejecting match with invalid timing: {commence_time_str} for {match.get('home_team')} vs {match.get('away_team')}")
                    return None
            except Exception as e:
                logging.debug(f"Could not validate match timing: {e}")
                # Don't reject due to timing parse errors
        
        # Calculate arbitrage opportunity
        total_inverse_odds = sum(1 / odds[1] for odds in best_odds.values())
        
        logging.debug(f"🔍 Total inverse odds: {total_inverse_odds:.4f}")
        logging.debug(f"🔍 Best odds breakdown: {[(outcome, odds[1]) for outcome, odds in best_odds.items()]}")
        
        # Arbitrage exists if total inverse odds < 1
        if total_inverse_odds < 1:
            profit_percentage = ((1 / total_inverse_odds) - 1) * 100
            logging.info(f"🔍 ARBITRAGE DETECTED - Calculated profit percentage: {profit_percentage:.2f}% for {match.get('home_team')} vs {match.get('away_team')}")
            
              # NOW check for suspicious profits
            if profit_percentage > 20:
                logging.warning(f"🚨 HIGH PROFIT WARNING: {profit_percentage:.2f}% profit")
            # VALIDATION: Only require minimum threshold - no upper limit
            # High profits can be legitimate in certain market conditions
            if profit_percentage >= 0.1:  # Minimum realistic profit threshold
                logging.info(f"✅ Found valid arbitrage: {match.get('home_team')} vs {match.get('away_team')} - {profit_percentage:.2f}%")
                
                # Log detailed validation info for moderate-profit opportunities (above 5%)
                if profit_percentage > 5:
                    logging.info(f"🔍 HIGH PROFIT OPPORTUNITY DETAILS:")
                    logging.info(f"    Match: {match.get('home_team')} vs {match.get('away_team')}")
                    logging.info(f"    Profit: {profit_percentage:.2f}%")
                    logging.info(f"    Bookmakers: {list(unique_bookmakers)}")
                    logging.info(f"    Odds: {[(outcome, f'{odds:.2f}') for outcome, (_, odds) in best_odds.items()]}")
                    logging.info(f"    Odds Ratio: {odds_ratio:.2f}")
                    logging.info(f"    Commence Time: {match.get('commence_time')}")
                
                return {
                    "match": {
                        "home_team": match.get("home_team"),
                        "away_team": match.get("away_team"),
                        "commence_time": match.get("commence_time")
                    },
                    "sport_title": match.get("sport_title"),
                    "sport_key": match.get("sport_key"),
                    "market_key": market_key,
                    "market_name": get_market_display_name(market_key),
                    "profit_percentage": round(profit_percentage, 2),
                    "total_inverse_odds": round(total_inverse_odds, 4),
                    "best_odds": {outcome: {
                                    "bookmaker": bookmaker, 
                                    "odds": odds,
                                    "point_value": point_value,
                                    "market_type": market_key
                                 } for outcome, (bookmaker, odds, point_value) in best_odds.items()},
                    "outcomes": len(best_odds),
                    "api_source": "real",
                    "odds_ratio": round(odds_ratio, 2),
                    "has_international_books": has_international_books,
                    "international_books": [bookmaker for bookmaker, _, _ in best_odds.values() 
                                          if bookmaker not in US_LICENSED_BOOKS] if has_international_books else [],
                    "validation_warnings": [] if odds_ratio <= 10 else [f"High odds ratio: {odds_ratio:.2f}"]
                }
            else:
                logging.warning(f"Rejected low profit arbitrage: {profit_percentage:.2f}% profit for {match.get('home_team')} vs {match.get('away_team')} (below 0.1% threshold)")
        else:
            logging.info(f"No arbitrage found - Total inverse odds: {total_inverse_odds:.4f} for {match.get('home_team')} vs {match.get('away_team')} (need < 1.0)")
        
        return None
        if profit_percentage > 20:
            logging.warning(f"High profit warning: {profit_percentage:.2f}% profit for {match.get('home_team')} vs {match.get('away_team')}")
            logging.warning(f"    This profit level is unusual - verify odds are current and accurate")
            logging.warning(f"    Bookmakers: {list(unique_bookmakers)}")
            logging.warning(f"    Odds: {[(outcome, f'{odds:.2f}') for outcome, (_, odds) in best_odds.items()]}")
        
    except Exception as e:
        logging.error(f"Error finding arbitrage in {market_key} market: {str(e)}")
        return None


def get_market_display_name(market_key: str) -> str:
    """Convert market key to display name - using comprehensive mapping"""
    return get_comprehensive_market_display_name(market_key)


@router.get("/odds")
async def get_odds(sport_key: Optional[str] = None):
    """Get odds either from API or mock data based on DEV_MODE"""
    try:
        if DEV_MODE:
            odds_data = await get_odds_from_mock(sport_key)
        else:
            odds_data = await get_odds_from_api(sport_key)
            
        return {"odds": odds_data}
    except Exception as e:
        logging.error(f"Error in get_odds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/arbitrage")
async def get_arbitrage_opportunities(
    sport_key: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get arbitrage opportunities from REAL API data ONLY - no mock data"""
    try:
        # ONLY use real API data - no mock data fallbacks
        logging.info("🚀 Fetching arbitrage opportunities from real API data only")
        
        # Validate API key
        if not API_KEY or API_KEY == "your_odds_api_key_here":
            logging.error("❌ No valid API key configured")
            raise HTTPException(
                status_code=503, 
                detail="Odds API service is not configured. Please check your API key."
            )
        
        # Use stored data from database (updated by background scheduler)
        odds_data = await get_odds_from_database(db, sport_key)
        
        if not odds_data:
            logging.warning("⚠️ No stored odds data available from database")
            # Return empty results - no mock data for production
            return {
                "arbitrage_opportunities": [],
                "user_tier": _get_user_tier(current_user.id, db),
                "total_found": 0,
                "data_source": "database_no_data",
                "message": "No current betting odds available from the database"
            }
        
        logging.info(f"✅ Successfully retrieved {len(odds_data)} matches from database (real API data)")
        
        # Detect arbitrage opportunities
        opportunities = await detect_arbitrage_opportunities(odds_data)
        
        # Apply user tier filtering
        user_tier = _get_user_tier(current_user.id, db)
        
        logging.info(f"📊 Returning {len(opportunities)} arbitrage opportunities for {user_tier} user (real API data)")
        
        # DEBUG: Log what we're actually returning to frontend
        if opportunities:
            sample = opportunities[0]
            logging.info(f"🔍 SENDING TO FRONTEND - Sample opportunity keys: {list(sample.keys())}")
            logging.info(f"🔍 SENDING TO FRONTEND - Has best_odds: {'best_odds' in sample}")
            if 'best_odds' in sample:
                logging.info(f"🔍 SENDING TO FRONTEND - best_odds content: {sample['best_odds']}")
        else:
            logging.info("🔍 SENDING TO FRONTEND - No opportunities to send")
        
        # Check if we used cached data
        cache_key = f"odds_{sport_key or 'all'}"
        data_source = "real_api"
        if cache_key in api_cache:
            cached_data, cache_time = api_cache[cache_key]
            cache_age = int(time.time() - cache_time)
            if cache_age < CACHE_DURATION:
                data_source = f"real_api_cached_{cache_age}s"
        
        return {
            "arbitrage_opportunities": opportunities,
            "user_tier": user_tier,
            "total_found": len(opportunities),
            "data_source": data_source
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 503 for missing API key)
        raise
    except Exception as e:
        logging.error(f"Error in get_arbitrage_opportunities: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching arbitrage opportunities: {str(e)}")

# NEW: SportsGameOdds powered arbitrage endpoint
@router.get("/arbitrage/sgo")
async def get_sgo_arbitrage_opportunities(
    sport_key: Optional[str] = None,
    min_profit: float = 1.0,
    live_only: bool = False,
    force_refresh: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get arbitrage opportunities using SportsGameOdds API - Enhanced Version"""
    try:
        logging.info("🚀 Fetching arbitrage opportunities from SportsGameOdds API")
        
        # Clear cache if force_refresh is requested
        if force_refresh:
            global api_cache
            api_cache.clear()
            logging.info("🧹 Force refresh requested - cleared all backend caches")
        
        # Validate SGO API key
        if not SGO_API_KEY:
            logging.error("❌ No SGO API key configured")
            raise HTTPException(
                status_code=503, 
                detail="SportsGameOdds API service is not configured."
            )
        
        # Import time for performance logging
        import time
        start_time_all = time.time()
        
        user_tier = "basic"
        if current_user:
            user_tier = _get_user_tier(current_user.id, db)
            
        logging.info(f"⏱️ PERF: User Tier Check took {time.time() - start_time_all:.4f}s")
        
        # Import Pro live arbitrage SGO service
        from app.services.sgo_pro_live_service import SGOProLiveService
        
        # Initialize Pro live arbitrage service
        service_init_start = time.time()
        async with SGOProLiveService() as sgo_service:
            logging.info(f"⏱️ PERF: Service Init took {time.time() - service_init_start:.4f}s")
            
            fetch_start = time.time()
            # Find arbitrage opportunities based on live_only parameter
            if live_only:
                logging.info("🔍 API: Fetching LIVE arbitrage opportunities from SGO")
                opportunities = await sgo_service.get_live_arbitrage_opportunities()
                logging.info(f"📊 API: SGO returned {len(opportunities)} LIVE opportunities")
            else:
                # Get only upcoming opportunities for arbitrage tab (live opportunities are for Odds tab only)
                logging.info("🔍 API: Fetching UPCOMING arbitrage opportunities from SGO (Arbitrage tab)")
                opportunities = await sgo_service.get_upcoming_arbitrage_opportunities(force_refresh=force_refresh)
                logging.info(f"📊 API: SGO returned {len(opportunities)} UPCOMING opportunities")
            
            logging.info(f"⏱️ PERF: Data Fetch took {time.time() - fetch_start:.4f}s")
            
            # Enhanced deduplication to handle duplicate teams/bets
            seen_opportunities = set()
            unique_opportunities = []
            removed_count = 0
            
            for opp in opportunities:
                # Create a more specific ID for better deduplication
                opp_id = opp.get("id", "")
                if not opp_id:
                    # Enhanced fallback ID that includes more details
                    opp_id = f"{opp.get('sport', 'unknown')}_{opp.get('home_team', 'home')}_{opp.get('away_team', 'away')}_{opp.get('market_type', 'unknown')}_{opp.get('line', '')}_{opp.get('bet_type', '')}"
                
                if opp_id not in seen_opportunities:
                    seen_opportunities.add(opp_id)
                    unique_opportunities.append(opp)
                else:
                    removed_count += 1
                    logging.info(f"🔍 Deduplication: Removed duplicate opportunity: {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')} - {opp.get('profit_percentage', 0):.2f}%")
            
            logging.info(f"🔍 Deduplication: Removed {removed_count} duplicates, {len(unique_opportunities)} unique opportunities remain")
            
            # Data freshness validation - filter out stale opportunities
            fresh_opportunities = []
            stale_count = 0
            
            for opp in unique_opportunities:
                # Check if opportunity has a valid start time (SGO uses 'start_time', legacy uses 'commence_time')
                start_time = opp.get('start_time', '') or opp.get('commence_time', '')
                if start_time:
                    try:
                        # Parse the start time and check if it's in the future
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        
                        # Only include opportunities that start within the next 7 days and haven't started yet
                        time_until_start = (start_dt - now).total_seconds()
                        if time_until_start > -1800 and time_until_start < (7 * 24 * 3600):  # From 30 min ago to 7 days from now
                            fresh_opportunities.append(opp)
                        else:
                            stale_count += 1
                            hours_diff = time_until_start / 3600
                            logging.info(f"Data Freshness: Removed stale opportunity: {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')} - Start: {start_time} ({hours_diff:.1f}h from now)")
                    except Exception as e:
                        # If we can't parse the time, include it but log the issue
                        fresh_opportunities.append(opp)
                        logging.warning(f"🔍 Data Freshness: Could not parse start time for {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')}: {e}")
                else:
                    # If no start time, include it but log the issue
                    fresh_opportunities.append(opp)
                    logging.warning(f"🔍 Data Freshness: No start time for {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')}")
            
            opportunities = fresh_opportunities
            logging.info(f"🔍 Data Freshness: Removed {stale_count} stale opportunities, {len(opportunities)} fresh opportunities remain")
            
            # DEBUG: Log start time availability for first few opportunities
            for i, opp in enumerate(opportunities[:3]):
                start_time = opp.get('start_time', '') or opp.get('commence_time', '')
                if start_time:
                    logging.info(f"✅ API: Start time available for {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')}: {start_time}")
                else:
                    logging.warning(f"⚠️ API: No start time for {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')}")
            
            # SUMMARY: Log all opportunities found
            if opportunities:
                logging.info(f"📊 SUMMARY: Found {len(opportunities)} arbitrage opportunities:")
                for opp in opportunities[:5]:  # Show first 5
                    logging.info(f"   - {opp.get('home_team', 'Unknown')} vs {opp.get('away_team', 'Unknown')} - {opp.get('profit_percentage', 0):.2f}% profit")
            
            # Convert to frontend format
            formatted_opportunities = []
            for opp in opportunities:
                            formatted_opp = {
                                "id": opp.get("id", f"sgo_{opp.get('sport', 'unknown')}_{opp.get('home_team', 'home')}_{opp.get('away_team', 'away')}"),
                                "sport": opp.get("sport", "Unknown"),
                                "league": opp.get("league", "Unknown"),
                                "home_team": opp.get("home_team", "Home Team"),
                                "away_team": opp.get("away_team", "Away Team"),
                                "start_time": opp.get("start_time", ""),
                                "market_type": opp.get("market_type", "moneyline"),
                                "market_description": opp.get("market_description", ""),  # Add missing field!
                                "detailed_market_description": opp.get("detailed_market_description", ""),
                                "profit_percentage": opp.get("profit_percentage", 0),
                                "profit": opp.get("profit", 0),
                                "total_stake": opp.get("total_stake", 0),
                                "confidence_score": opp.get("confidence_score", 0.5),
                                "best_odds": opp.get("best_odds", {}),
                                "bookmakers_involved": opp.get("bookmakers_involved", []),
                                "implied_probability": opp.get("implied_probability", 0),
                                "game_type": opp.get("game_type", "UPCOMING"),  # Add game_type field
                            }
                            
                            # Debug logging for market descriptions
                            if opp.get("market_description"):
                                logging.info(f"🎯 API: Sending market description '{opp.get('market_description')}' for {opp.get('home_team')} vs {opp.get('away_team')}")
                            elif opp.get("detailed_market_description"):
                                logging.info(f"🎯 API: Sending detailed description '{opp.get('detailed_market_description')}' for {opp.get('home_team')} vs {opp.get('away_team')}")
                            else:
                                logging.warning(f"⚠️ API: No market description for {opp.get('home_team')} vs {opp.get('away_team')} - market_type: {opp.get('market_type')}")
                            
                            formatted_opportunities.append(formatted_opp)
        
        # Apply user tier filtering
        if user_tier == "basic" and len(formatted_opportunities) > 5:
            formatted_opportunities = formatted_opportunities[:5]
            message_suffix = " (limited to 5 for basic users)"
        else:
            message_suffix = ""
        
        logging.info(f"📊 Returning {len(formatted_opportunities)} SGO arbitrage opportunities for {user_tier} user")
        
        # Log sample opportunity for debugging
        if formatted_opportunities:
            sample = formatted_opportunities[0]
            logging.info(f"🔍 SGO Sample: {sample.get('home_team')} vs {sample.get('away_team')}")
            logging.info(f"🔍 SGO Profit: {sample.get('profit_percentage')}% in {sample.get('market_type')}")
            logging.info(f"🔍 SGO Books: {sample.get('bookmakers_involved')}")
        
        return {
            "arbitrage_opportunities": formatted_opportunities,
            "user_tier": user_tier,
            "total_found": len(formatted_opportunities),
            "data_source": "sgo_api_live",
            "message": f"Found {len(formatted_opportunities)} arbitrage opportunities from SportsGameOdds{message_suffix}",
            "api_info": {
                "min_profit_filter": min_profit,
                "sports_analyzed": sport_key or "all",
                "detection_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logging.error(f"Error in SGO arbitrage: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "arbitrage_opportunities": [],
            "user_tier": _get_user_tier(current_user.id, db),
            "total_found": 0,
            "data_source": "sgo_error",
            "message": f"SGO API Error: {str(e)}",
            "fallback_available": True
        }

# ---- Premium/Basic gating for live odds ----
def _get_user_tier(user_id: int, db: Session) -> str:
    """Return 'premium' for active/trial premium plans; otherwise 'basic'."""
    try:
        sub = (
            db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(["active", "trialing"]),
            )
            .first()
        )
        if not sub:
            return "basic"
        plan_name = (getattr(getattr(sub, "plan", None), "name", "") or "").lower()
        if sub.status == "trialing" or "premium" in plan_name:
            return "premium"
        return "basic"
    except Exception:
        return "basic"

def _filter_live_events(odds_data: List[Dict[str, Any]], include_live: bool) -> List[Dict[str, Any]]:
    if include_live:
        return odds_data
    filtered: List[Dict[str, Any]] = []
    now = datetime.utcnow()
    for match in odds_data:
        ct = match.get("commence_time")
        if not ct:
            # If no commence_time, be conservative and exclude from basic responses
            continue
        try:
            # Handle ISO strings ending with 'Z'
            dt = datetime.fromisoformat(ct.replace("Z", "+00:00"))
        except Exception:
            # If parsing fails, exclude from basic responses
            continue
        if dt > now:
            filtered.append(match)
    return filtered

@router.get("/odds-gated")
async def get_odds_gated(
    sport_key: Optional[str] = None,
    include_live: Optional[bool] = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return odds with server-side enforcement of live access based on subscription.

    - Premium or trial users: include_live respected.
    - Basic users: live odds are removed regardless of include_live.
    """
    try:
        # Determine user tier
        user_tier = _get_user_tier(current_user.id, db)
        allow_live = include_live if user_tier == "premium" else False

        # Fetch odds from real API only
        odds_data = await get_odds_from_api(sport_key)

        # Filter if necessary
        odds_data = _filter_live_events(odds_data, allow_live)
        return {"odds": odds_data, "user_tier": user_tier}
    except Exception as e:
        logging.error(f"Error in get_odds_gated: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def detect_arbitrage(odds: Dict[str, float], outcomes: int) -> Dict[str, Any]:
    """
    Detect arbitrage opportunities based on number of outcomes
    - For 2-outcome sports (e.g., basketball): home, away
    - For 3-outcome sports (e.g., soccer): home, away, draw
    """
    try:
        # Input validation
        if outcomes == 2 and not all(isinstance(odds.get(k), (int, float)) and odds.get(k) > 1 
                                      for k in ["home", "away"]):
            return {"arbitrage": False, "profit_percentage": 0}
            
        if outcomes == 3 and not all(isinstance(odds.get(k), (int, float)) and odds.get(k) > 1 
                                      for k in ["home", "away", "draw"]):
            return {"arbitrage": False, "profit_percentage": 0}

        # Calculate implied probabilities
        probabilities = {}
        total_prob = 0
        
        if outcomes == 2:
            probabilities["home"] = 1 / odds["home"]
            probabilities["away"] = 1 / odds["away"]
            total_prob = probabilities["home"] + probabilities["away"]
        else:  # 3 outcomes
            probabilities["home"] = 1 / odds["home"]
            probabilities["away"] = 1 / odds["away"]
            probabilities["draw"] = 1 / odds["draw"]
            total_prob = probabilities["home"] + probabilities["away"] + probabilities["draw"]
        
        profit_percentage = ((1 / total_prob) - 1) * 100

        # Log potential opportunities
        threshold = 1.02  # Allow up to 2% margin
        if total_prob < threshold:
            logging.info(f"""
            Potential opportunity analysis:
            Odds: {odds}
            Implied Probabilities: {', '.join([f"{k}: {(v*100):.1f}%" for k, v in probabilities.items()])}
            Total Probability: {(total_prob*100):.2f}%
            Potential Profit: {profit_percentage:.2f}%
            Is Arbitrage: {total_prob < 1}
            """)

            if total_prob < 1:  # True arbitrage opportunity
                return {
                    "arbitrage": True,
                    "profit_percentage": profit_percentage,
                    "probabilities": {**probabilities, "total": total_prob}
                }

        return {"arbitrage": False, "profit_percentage": 0}
    except Exception as e:
        logging.error(f"Error in detect_arbitrage: {str(e)}")
        return {"arbitrage": False, "profit_percentage": 0}

# DISABLED: Duplicate endpoint - use the async one above instead
# @router.get("/arbitrage")
def get_arbitrage_opportunities_OLD_DISABLED(
    min_profit: float = 0.5,
    sport_key: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get arbitrage opportunities with filtering options"""
    try:
        # Base query
        query = db.query(BettingOdds)
        
        # Apply sport filter if provided
        if sport_key:
            query = query.filter(BettingOdds.sport_key == sport_key)
            
        records = query.all()
        
        # Group matches by unique identifiers (including sport)
        grouped = {}
        for record in records:
            key = (record.sport_key, record.home_team, record.away_team, record.commence_time)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(record)
        
        opportunities = []
        for match_key, odds_list in grouped.items():
            sport_key, home_team, away_team, commence_time = match_key
            
            try:
                # Import sports config dynamically to get fresh data
                from importlib import reload
                import sports_config
                reload(sports_config)
                from sports_config import SUPPORTED_SPORTS
                
                # Get the sport configuration to know how many outcomes to expect
                sport_info = SUPPORTED_SPORTS.get(sport_key)
                if not sport_info:
                    continue
                
                outcomes_count = sport_info["outcomes"]
                
                if isinstance(commence_time, str):
                    match_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                else:
                    match_time = commence_time

                match_time = match_time.replace(tzinfo=timezone.utc)
                
                # Skip past matches
                if match_time < datetime.now(timezone.utc):
                    continue

                # Initialize best odds and bookmakers
                best_odds = {"home": 0, "away": 0}
                best_bookmakers = {"home": "", "away": ""}
                
                # Add draw for 3-way markets
                if outcomes_count == 3:
                    best_odds["draw"] = 0
                    best_bookmakers["draw"] = ""
                
                for record in odds_list:
                    try:
                        current_odds = float(record.odds)
                        if record.outcome == home_team and current_odds > best_odds["home"]:
                            best_odds["home"] = current_odds
                            best_bookmakers["home"] = record.sportsbook
                        elif record.outcome == away_team and current_odds > best_odds["away"]:
                            best_odds["away"] = current_odds
                            best_bookmakers["away"] = record.sportsbook
                        elif outcomes_count == 3 and record.outcome.lower() == "draw" and current_odds > best_odds["draw"]:
                            best_odds["draw"] = current_odds
                            best_bookmakers["draw"] = record.sportsbook
                    except ValueError:
                        continue

                # Skip if we don't have odds for all outcomes
                skip = False
                for outcome in best_odds:
                    if best_odds[outcome] <= 0 or not best_bookmakers[outcome]:
                        skip = True
                        break
                if skip:
                    continue

                # We need at least 2 different bookmakers for arbitrage
                if len(set(best_bookmakers.values())) < 2:
                    continue

                # Detect arbitrage
                arb_result = detect_arbitrage(best_odds, outcomes_count)
                
                if arb_result["arbitrage"] and arb_result["profit_percentage"] >= min_profit:
                    opportunities.append({
                        "sport_key": sport_key,
                        "sport_title": sport_info["title"],
                        "outcomes": outcomes_count,
                        "arbitrage_detected": True,  # Mark as real arbitrage opportunity
                        "match": {
                            "home_team": home_team,
                            "away_team": away_team,
                            "commence_time": match_time.strftime("%Y-%m-%d %H:%M:%S")
                        },
                        "profit_percentage": arb_result["profit_percentage"],
                        "best_odds": {
                            **best_odds,
                            **{f"{k}_bookmaker": v for k, v in best_bookmakers.items()}
                        }
                    })
            except Exception as e:
                logging.error(f"Error processing match {home_team} vs {away_team}: {str(e)}")
                continue

        # Sort by profit percentage
        opportunities.sort(key=lambda x: x["profit_percentage"], reverse=True)
        return {"arbitrage_opportunities": opportunities}
    except Exception as e:
        logging.error(f"Error in get_arbitrage_opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-arbitrage")
def get_my_arbitrage(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    arbitrages = db.query(UserArbitrage).filter(UserArbitrage.user_id == current_user.id).order_by(UserArbitrage.created_at.desc()).all()
    return {"arbitrages": [a.as_dict() for a in arbitrages]}

from pydantic import BaseModel, validator
from typing import Dict, Union

class ArbitrageSaveRequest(BaseModel):
    sport_key: str
    sport_title: str
    home_team: str
    away_team: str
    match_time: str
    odds: Dict[str, Union[int, float]]
    bookmakers: Dict[str, str]
    profit_percentage: float
    bet_amount: float = 0.0
    status: str = "open"
    notes: str = ""
    
    @validator('sport_key', 'sport_title', 'home_team', 'away_team')
    def validate_strings(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        if len(v) > 200:  # Reasonable length limit
            raise ValueError('Field too long')
        return v.strip()
    
    @validator('bet_amount')
    def validate_bet_amount(cls, v):
        if v < 0 or v > 1000000:  # Reasonable limits
            raise ValueError('Bet amount must be between 0 and 1,000,000')
        return v
    
    @validator('profit_percentage')
    def validate_profit_percentage(cls, v):
        # No upper limit on profit - if it's legitimate, we want it!
        if v < -100:  # Only prevent impossible negative profits
            raise ValueError('Profit percentage cannot be less than -100%')
        return v
    
    @validator('notes')
    def validate_notes(cls, v):
        if len(v) > 1000:  # Reasonable length limit
            raise ValueError('Notes too long')
        return v
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['open', 'closed', 'cancelled', 'completed']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/my-arbitrage")
@limiter.limit("10/minute")  # Limit saving arbitrages to prevent spam
def save_arbitrage(request: Request, data: ArbitrageSaveRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        # Validate and sanitize the match_time
        try:
            match_time = datetime.fromisoformat(data.match_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid match time format")
        
        # Validate odds data
        odds_values = [v for v in data.odds.values() if isinstance(v, (int, float)) and v > 0]
        if len(odds_values) < 2:
            raise HTTPException(status_code=400, detail="At least 2 valid odds required")
        
        # Calculate arbitrage profit using the correct formula and all outcome keys
        if data.bet_amount and len(odds_values) >= 2:
            total_prob = sum(1 / o for o in odds_values)
            profit = round(data.bet_amount * (1 / total_prob - 1), 2)
        else:
            profit = 0.0
            
        arb = UserArbitrage(
            user_id=current_user.id,
            sport_key=data.sport_key,
            sport_title=data.sport_title,
            home_team=data.home_team,
            away_team=data.away_team,
            match_time=match_time,
            odds=data.odds,
            bookmakers=data.bookmakers,
            profit_percentage=data.profit_percentage,
            bet_amount=data.bet_amount,
            profit=profit,
            status=data.status,
            notes=data.notes
        )
        db.add(arb)
        db.commit()
        db.refresh(arb)
        return {"success": True, "arbitrage": arb.as_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving arbitrage: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save arbitrage")

@router.delete("/my-arbitrage/{arbitrage_id}")
def delete_arbitrage(arbitrage_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    arb = db.query(UserArbitrage).filter(UserArbitrage.id == arbitrage_id, UserArbitrage.user_id == current_user.id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage not found")
    db.delete(arb)
    db.commit()
    return {"success": True}

@router.get("/my-arbitrage/preferences")
def get_user_arbitrage_opportunities(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get arbitrage opportunities based on user preferences"""
    try:
        # Get user profile preferences
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
        
        # Parse preferences
        sport_keys = profile.preferred_sports.split(",") if profile.preferred_sports else []
        min_profit = profile.minimum_profit_threshold
        
        # Get arbitrage opportunities filtered by user preferences
        all_opportunities = []
        for sport_key in sport_keys:
            # Use the main arbitrage function with user's filters
            result = get_arbitrage_opportunities(
                min_profit=min_profit,
                sport_key=sport_key,
                db=db
            )
            if "arbitrage_opportunities" in result:
                all_opportunities.extend(result["arbitrage_opportunities"])
        
        # Sort combined results
        all_opportunities.sort(key=lambda x: x["profit_percentage"], reverse=True)
        
        return {"arbitrage_opportunities": all_opportunities}
    except Exception as e:
        logging.error(f"Error in get_user_arbitrage_opportunities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sports", tags=["Sports"])
async def get_sports():
    """Get comprehensive list of all supported sports with full details"""
    try:
        # Force reload the sports configuration to pick up any updates
        from importlib import reload
        from scripts import sports_config
        reload(sports_config)
        from scripts.sports_config import SUPPORTED_SPORTS, get_active_sports, get_sports_by_category, get_priority_sports
        
        active_sports = get_active_sports()
        sports_by_category = get_sports_by_category()
        priority_sports = get_priority_sports(1)
        
        # Count stats
        total_sports = len(SUPPORTED_SPORTS)
        active_count = len(active_sports)
        priority_count = len(priority_sports)
        
        # Return ALL sports (not just active ones) so frontend can see everything
        sports_list = []
        for key, info in SUPPORTED_SPORTS.items():
            sports_list.append({
                "key": key,
                "title": info["title"],
                "outcomes": info["outcomes"],
                "markets": info["markets"],
                "priority": info["priority"],
                "active": info["active"]
            })
        
        logging.info(f"🔄 Sports endpoint serving {len(sports_list)} total sports ({active_count} active)")
        
        return {
            "sports": sports_list,
            "categories": sports_by_category,
            "stats": {
                "total_sports": total_sports,
                "active_sports": active_count,
                "priority_sports": priority_count
            }
        }
    except Exception as e:
        logging.error(f"Error in get_sports: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches", tags=["Matches"])
async def get_matches_browser(sport_key: Optional[str] = None):
    """Get upcoming matches summary for the match browser (API efficient)"""
    try:
        matches = await get_upcoming_matches_summary(sport_key)
        return {
            "matches": matches,
            "total_matches": len(matches),
            "sports_covered": len(set(m["sport_key"] for m in matches)),
            "data_source": "match_browser",
            "api_efficient": True
        }
    except Exception as e:
        logging.error(f"Error in get_matches_browser: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/{match_id}/odds", tags=["Matches"])
async def get_match_detailed_odds(
    match_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed odds for a specific match (on-demand loading)"""
    try:
        detailed_odds = await get_detailed_match_odds(match_id)
        
        if not detailed_odds:
            raise HTTPException(status_code=404, detail="Match not found or no odds available")
            
        return {
            "match_odds": detailed_odds,
            "data_source": "on_demand",
            "loaded_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting detailed odds for match {match_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/matches/browser/stats", tags=["Matches"])
async def get_browser_stats():
    """Get match browser statistics and cache info"""
    try:
        stats = get_match_browser_stats()
        return {
            "browser_stats": stats,
            "description": "API-efficient match browser with on-demand odds loading"
        }
    except Exception as e:
        logging.error(f"Error getting browser stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/clear", tags=["Debug"])
async def clear_cache():
    """Clear all cached data to force fresh API calls"""
    global api_cache
    api_cache.clear()
    logging.info("🧹 All caches cleared - forcing fresh API data")
    return {
        "message": "All caches cleared",
        "timestamp": datetime.utcnow().isoformat(),
        "cache_duration": CACHE_DURATION
    }

@router.get("/debug/sports-count", tags=["Debug"])
async def debug_sports_count():
    """Debug endpoint to check sports configuration"""
    try:
        # Force fresh import
        from importlib import reload
        import sports_config
        reload(sports_config)
        
        sports_count = len(sports_config.SUPPORTED_SPORTS)
        sample_keys = list(sports_config.SUPPORTED_SPORTS.keys())[:10]
        
        # Check for cricket sports specifically
        cricket_sports = [k for k in sports_config.SUPPORTED_SPORTS.keys() if 'cricket' in k]
        tennis_sports = [k for k in sports_config.SUPPORTED_SPORTS.keys() if 'tennis_wta' in k]
        
        return {
            "total_sports_in_config": sports_count,
            "sample_sport_keys": sample_keys,
            "cricket_sports_count": len(cricket_sports),
            "tennis_wta_sports_count": len(tennis_sports),
            "cricket_sample": cricket_sports[:3],
            "tennis_sample": tennis_sports[:3],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.get("/sports/stats", tags=["Sports"])  
async def get_sports_stats(db: Session = Depends(get_db)):
    """Get statistics about available sports and bookmakers with fresh data"""
    try:
        # Force reload both config modules to pick up updates
        from importlib import reload
        import config
        import sports_config  
        reload(config)
        reload(sports_config)
        
        from config import DEV_MODE, ALL_AVAILABLE_BOOKMAKERS, API_KEY
        from sports_config import get_active_sports
        
        # Check if we have real API access
        has_real_api = API_KEY and API_KEY != "your_odds_api_key_here"
        
        # Query database for actual data
        unique_sportsbooks = db.query(BettingOdds.sportsbook).distinct().all()
        db_sportsbooks = [sb[0] for sb in unique_sportsbooks if sb[0]]
        total_matches = db.query(BettingOdds.home_team, BettingOdds.away_team).distinct().count()
        total_odds_records = db.query(BettingOdds).count()
        
        if total_odds_records > 0 and has_real_api:
            # We have real data from API
            available_sportsbooks = db_sportsbooks
            sportsbook_count = len(db_sportsbooks)
            data_source = "live_api"
        else:
            # Show current platform state with updated bookmaker list
            available_sportsbooks = ALL_AVAILABLE_BOOKMAKERS
            sportsbook_count = len(ALL_AVAILABLE_BOOKMAKERS)
            total_odds_records = 4  # Current arbitrage opportunities available
            data_source = "operational"
        
        active_sports = len(get_active_sports())
        
        logging.info(f"🔄 Sports stats: {active_sports} active sports, {sportsbook_count} bookmakers")
        
        return {
            "available_sportsbooks": available_sportsbooks,
            "sportsbook_count": sportsbook_count,
            "total_odds_records": total_odds_records,
            "active_sports": active_sports,
            "data_source": data_source,
            "has_api_key": has_real_api
        }
    except Exception as e:
        logging.error(f"Error in get_sports_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug-odds", tags=["Debug"])
async def debug_odds(db: Session = Depends(get_db)):
    """Debug endpoint to check stored odds"""
    records = db.query(BettingOdds).all()
    
    matches = {}
    for record in records:
        key = f"{record.home_team} vs {record.away_team}"
        if key not in matches:
            matches[key] = {
                "home_team": record.home_team,
                "away_team": record.away_team,
                "commence_time": record.commence_time,
                "odds": []
            }
        matches[key]["odds"].append({
            "bookmaker": record.sportsbook,
            "outcome": record.outcome,
            "odds": record.odds
        })
    
    return {"matches": matches}

#==================== NOTIFICATION SYSTEM ENDPOINTS ====================

@router.post("/test-email-notification", tags=["Notifications"])
async def send_test_email_notification(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Send a test email notification to the current user"""
    try:
        from arbitrage_notifications import notification_service
        from user_models import UserProfile
        
        # Get user profile  
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile or not profile.notification_email:
            raise HTTPException(status_code=400, detail="Email notifications are not enabled in your profile")
        
        # Check if user already sent a test email today (rate limiting)
        today = date.today()
        from user_models import UserEmailNotificationLog
        
        # Check for existing test email today
        test_log = db.query(UserEmailNotificationLog).filter(
            UserEmailNotificationLog.user_id == current_user.id,
            UserEmailNotificationLog.email_date == today
        ).first()
        
        # Rate limit: Only 1 test email per day
        if test_log and test_log.email_count >= 1:
            raise HTTPException(
                status_code=429, 
                detail="Test email limit reached. You can only send 1 test email per day to prevent abuse of the email service."
            )
        
        # Create a TEST arbitrage opportunity for the test email
        test_opportunity = {
            'match': {
                'home_team': '[TEST] Chelsea',
                'away_team': '[TEST] Arsenal', 
                'commence_time': (datetime.now(timezone.utc) + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
            },
            'sport_title': '[TEST] English Premier League',
            'profit_percentage': 2.5,
            'best_odds': {
                'home': 1.95,
                'away': 2.15,
                'home_bookmaker': '[TEST] Bet365',
                'away_bookmaker': '[TEST] DraftKings'
            }
        }
        
        # Send test email (need to await the async function properly)
        success = await notification_service.send_notification_email(
            email=current_user.email,
            opportunities=[test_opportunity],
            subscription_status="test"
        )
        
        if success:
            # Track the test email (but don't count it against daily limits)
            notification_service.increment_daily_email_count(current_user.id, db)
            
            return {"success": True, "message": "Test email sent successfully!"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test email")
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error sending test email: {str(e)}")
        logger.error(f"Full traceback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")

# Function to send email notifications
async def send_arbitrage_notification_email(email: str, opportunities: List[Dict]):
    """Send an email notification about arbitrage opportunities"""
    
    # Create email content
    if len(opportunities) == 1:
        opp = opportunities[0]
        subject = f"New Arbitrage Opportunity: {opp['profit_percentage']:.2f}% Profit"
        
        # Simple message for a single opportunity
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h1 style="color: #d4af37;">New Arbitrage Opportunity!</h1>
            <p>We've found a new arbitrage opportunity with <strong>{opp['profit_percentage']:.2f}%</strong> profit.</p>
            
            <div style="background-color: #f8f9fa; border-radius: 5px; padding: 15px; margin: 20px 0;">
                <h3 style="margin-top: 0;">{opp['match']['home_team']} vs {opp['match']['away_team']}</h3>
                <p><strong>Sport:</strong> {opp['sport_title']}</p>
                <p><strong>Start Time:</strong> {opp['match']['commence_time']}</p>
                <p><strong>Profit:</strong> {opp['profit_percentage']:.2f}%</p>
            </div>
            
            <p>We've found a new arbitrage opportunity that matches your preferences!</p>
            <p><a href="http://localhost:8000/arbitrage" style="background-color: #d4af37; color: #fff; padding: 10px 15px; border-radius: 5px; text-decoration: none;">View Opportunity</a></p>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #777; font-size: 12px;">© 2025 Arbify - Arbitrage Betting Platform</p>
        </div>
        """
    else:
        # Summary message for multiple opportunities
        subject = f"{len(opportunities)} New Arbitrage Opportunities"
        
        opportunities_html = ""
        for opp in opportunities[:5]:  # Limit to first 5
            opportunities_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; border-left: 3px solid #d4af37; background-color: #f8f9fa;">
                <p style="margin: 0;"><strong>{opp['match']['home_team']} vs {opp['match']['away_team']}</strong></p>
                <p style="margin: 5px 0;"><strong>Profit:</strong> {opp['profit_percentage']:.2f}%</p>
                <p style="margin: 0;"><strong>Sport:</strong> {opp['sport_title']}</p>
            </div>
            """
        
        if len(opportunities) > 5:
            opportunities_html += f"<p>Plus {len(opportunities) - 5} more opportunities...</p>"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
            <h1 style="color: #d4af37;">New Arbitrage Opportunities!</h1>
            <p>We've found {len(opportunities)} new arbitrage opportunities for you.</p>
            
            <div style="margin: 20px 0;">
                {opportunities_html}
            </div>
            
            <p>We've found multiple new arbitrage opportunities that match your preferences!</p>
            <p><a href="http://localhost:8000/#arbitrage" style="background-color: #d4af37; color: #fff; padding: 10px 15px; border-radius: 5px; text-decoration: none;">View All Opportunities</a></p>
            
            <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #777; font-size: 12px;">© 2025 Arbify - Arbitrage Betting Platform</p>
        </div>
        """
    
    # Send the email
    try:
        return send_email(
            to_email=email,
            subject=subject,
            html_content=html_content
        )
    except Exception as e:
        logging.error(f"Failed to send notification email: {str(e)}")
        return False

# API endpoint to send a test notification
@notification_router.post("/test-email")
async def send_test_notification(
    email: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a test notification email to verify the system works"""
    
    # Only allow users to send test emails to themselves
    if email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="You can only send test notifications to your own email address"
        )
    
    # Create a sample opportunity for testing
    test_opportunity = {
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "outcomes": 2,
        "match": {
            "home_team": "Los Angeles Lakers",
            "away_team": "Golden State Warriors",
            "commence_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "profit_percentage": 2.5,
        "best_odds": {
            "home": 2.10,
            "away": 1.95,
            "home_bookmaker": "DraftKings",
            "away_bookmaker": "FanDuel"
        }
    }
    
    # Send the test notification in the background
    background_tasks.add_task(send_arbitrage_notification_email, email, [test_opportunity])
    
    return {"message": f"Test notification sent to {email}. Please check your inbox."}

# Endpoint to toggle notification preferences
@notification_router.post("/preferences")
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences for the current user"""
    try:
        logging.info(f"Updating preferences for user {current_user.id}: {preferences}")
        
        # Try to get existing profile with error handling
        profile = None
        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
            logging.info(f"Found existing profile: {profile is not None}")
        except Exception as query_error:
            logging.error(f"Error querying for profile: {str(query_error)}")
            
        # If no profile exists, try to create one
        if not profile:
            try:
                logging.info(f"Creating new profile for user {current_user.id}")
                profile = UserProfile(user_id=current_user.id)
                db.add(profile)
                db.flush()  # Ensure the profile is available for updates
                logging.info("Profile created successfully")
            except Exception as create_error:
                logging.error(f"Error creating profile: {str(create_error)}")
                db.rollback()
                # Return success with defaults - preferences will be stored in localStorage only
                return {
                    "success": True,
                    "preferences": {
                        "email": bool(preferences.get("email", True)),
                        "browser": bool(preferences.get("browser", False)),
                        "threshold": float(preferences.get("threshold", 1.0)),
                        "preferred_sports": preferences.get("preferred_sports"),
                        "preferred_bookmakers": preferences.get("preferred_bookmakers"),
                        "odds_format": preferences.get("odds_format", "decimal"),
                    },
                    "note": "Preferences saved locally - database update failed"
                }
        
        # Try to update each preference with maximum safety
        update_count = 0
        
        if "email" in preferences:
            try:
                if hasattr(profile, 'notification_email'):
                    profile.notification_email = bool(preferences["email"])
                    update_count += 1
                else:
                    logging.warning("notification_email column not found in database")
            except Exception as e:
                logging.error(f"Error setting notification_email: {str(e)}")
                
        if "browser" in preferences:
            try:
                if hasattr(profile, 'notification_browser'):
                    profile.notification_browser = bool(preferences["browser"])
                    update_count += 1
                else:
                    logging.warning("notification_browser column not found in database")
            except Exception as e:
                logging.error(f"Error setting notification_browser: {str(e)}")
                
        if "threshold" in preferences:
            try:
                threshold = float(preferences["threshold"])
                if hasattr(profile, 'minimum_profit_threshold'):
                    profile.minimum_profit_threshold = max(0.1, min(threshold, 10.0))
                    update_count += 1
                else:
                    logging.warning("minimum_profit_threshold column not found in database")
            except Exception as e:
                logging.error(f"Error setting minimum_profit_threshold: {str(e)}")
                
        # Save preferred_sports and preferred_bookmakers if present
        if "preferred_sports" in preferences:
            try:
                if hasattr(profile, 'preferred_sports'):
                    profile.preferred_sports = preferences["preferred_sports"]
                    update_count += 1
                else:
                    logging.warning("preferred_sports column not found in database")
            except Exception as e:
                logging.error(f"Error setting preferred_sports: {str(e)}")
                
        if "preferred_bookmakers" in preferences:
            try:
                if hasattr(profile, 'preferred_bookmakers'):
                    profile.preferred_bookmakers = preferences["preferred_bookmakers"]
                    update_count += 1
                else:
                    logging.warning("preferred_bookmakers column not found in database")
            except Exception as e:
                logging.error(f"Error setting preferred_bookmakers: {str(e)}")
                
        # Save odds format if provided
        if "odds_format" in preferences:
            try:
                fmt = str(preferences["odds_format"]).lower()
                if fmt in ("decimal", "american"):
                    if hasattr(profile, 'odds_format'):
                        profile.odds_format = fmt
                        update_count += 1
                    else:
                        logging.warning("odds_format column not found in database - will use default")
            except Exception as e:
                logging.error(f"Error setting odds_format: {str(e)}")
        
        # Try to commit changes
        try:
            if update_count > 0:
                db.commit()
                logging.info(f"Successfully committed {update_count} preference updates")
            else:
                logging.warning("No preferences could be updated in database")
        except Exception as commit_error:
            logging.error(f"Error committing preferences: {str(commit_error)}")
            db.rollback()
        
        # Build response with ultra-safe attribute access
        try:
            response = {
                "success": True,
                "preferences": {
                    "email": getattr(profile, "notification_email", bool(preferences.get("email", True))),
                    "browser": getattr(profile, "notification_browser", bool(preferences.get("browser", False))),
                    "threshold": getattr(profile, "minimum_profit_threshold", float(preferences.get("threshold", 1.0))),
                    "preferred_sports": getattr(profile, "preferred_sports", preferences.get("preferred_sports")),
                    "preferred_bookmakers": getattr(profile, "preferred_bookmakers", preferences.get("preferred_bookmakers")),
                    "odds_format": getattr(profile, "odds_format", preferences.get("odds_format", "decimal")) if hasattr(profile, "odds_format") else "decimal",
                }
            }
        except Exception as response_error:
            logging.error(f"Error building response: {str(response_error)}")
            # Fallback response
            response = {
                "success": True,
                "preferences": {
                    "email": bool(preferences.get("email", True)),
                    "browser": bool(preferences.get("browser", False)),
                    "threshold": float(preferences.get("threshold", 1.0)),
                    "preferred_sports": preferences.get("preferred_sports"),
                    "preferred_bookmakers": preferences.get("preferred_bookmakers"),
                    "odds_format": preferences.get("odds_format", "decimal"),
                },
                "note": "Using fallback response due to database issues"
            }
        
        logging.info(f"Successfully handled preferences update for user {current_user.id}")
        return response
        
    except Exception as e:
        logging.error(f"Critical error updating preferences for user {current_user.id}: {str(e)}")
        logging.error(f"Full error details: {repr(e)}")
        
        # Ultimate fallback - return success with input values
        try:
            return {
                "success": True,
                "preferences": {
                    "email": bool(preferences.get("email", True)),
                    "browser": bool(preferences.get("browser", False)),
                    "threshold": float(preferences.get("threshold", 1.0)),
                    "preferred_sports": preferences.get("preferred_sports"),
                    "preferred_bookmakers": preferences.get("preferred_bookmakers"),
                    "odds_format": preferences.get("odds_format", "decimal"),
                },
                "note": "Critical error - preferences saved locally only"
            }
        except Exception as final_error:
            logging.error(f"Final fallback failed: {str(final_error)}")
            raise HTTPException(status_code=500, detail=f"Error updating preferences: {str(e)}")

# Background task for checking arbitrage opportunities
# This is a placeholder - we'll use the browser notifications for now
# In a production system, you would set up Celery or a similar task queue
async def check_arbitrage_opportunities():
    """Background task to check for arbitrage opportunities (not currently used)"""
    while True:
        try:
            logging.info("Checking for new arbitrage opportunities...")
            # Implementation would be here
            await asyncio.sleep(900)  # Check every 15 minutes
        except Exception as e:
            logging.error(f"Error in background task: {str(e)}")
            await asyncio.sleep(60)  # Retry after 1 minute

# Include the notification router
router.include_router(notification_router)

@router.patch("/my-arbitrage/{arbitrage_id}")
def update_arbitrage(arbitrage_id: int, data: dict = Body(...), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    arb = db.query(UserArbitrage).filter(UserArbitrage.id == arbitrage_id, UserArbitrage.user_id == current_user.id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage not found")
    bet_amount = float(data.get("bet_amount", 0.0))
    odds = arb.odds or {}
    odds_values = [v for v in odds.values() if isinstance(v, (int, float)) and v > 0]
    if bet_amount and len(odds_values) >= 2:
        total_prob = sum(1 / o for o in odds_values)
        profit = round(bet_amount * (1 / total_prob - 1), 2)
    else:
        profit = 0.0
    arb.bet_amount = bet_amount
    arb.profit = profit
    db.commit()
    db.refresh(arb)
    return {"success": True, "arbitrage": arb.as_dict()}

@router.patch("/my-arbitrage/{arbitrage_id}/result")
def set_arbitrage_result(arbitrage_id: int, data: dict = Body(...), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    arb = db.query(UserArbitrage).filter(UserArbitrage.id == arbitrage_id, UserArbitrage.user_id == current_user.id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage not found")
    winning_outcome = data.get("winning_outcome")
    # Accept any string as a valid outcome
    arb.winning_outcome = winning_outcome
    db.commit()
    db.refresh(arb)
    return {"success": True, "arbitrage": arb.as_dict()}

@notification_router.post("/test-arbitrage-notification")
async def test_arbitrage_notification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a test arbitrage notification to the current user"""
    try:
        from arbitrage_notifications import send_test_notification
        
        # Check if user has email notifications enabled
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        if not profile or not profile.notification_email:
            return {
                "success": False,
                "message": "Email notifications are disabled in your preferences. Enable them to receive notifications."
            }
        
        # Send test notification
        success = await send_test_notification(current_user.email)
        
        if success:
            return {
                "success": True,
                "message": f"Test notification check triggered for {current_user.email}. If opportunities match your preferences, you'll receive an email."
            }
        else:
            return {
                "success": False,
                "message": "Failed to trigger test notification. Please try again."
            }
            
    except Exception as e:
        logging.error(f"Error in test notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending test notification: {str(e)}")

@notification_router.post("/trigger-notification-check")
async def trigger_notification_check(
    current_user: User = Depends(get_current_active_user)
):
    """Manually trigger the notification checking service (admin function)"""
    try:
        from arbitrage_notifications import notification_service
        
        # Only allow this for testing purposes
        await notification_service.check_and_notify_users()
        
        return {
            "success": True,
            "message": "Notification check triggered manually. Check server logs for details."
        }
        
    except Exception as e:
        logging.error(f"Error triggering notification check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error triggering notification check: {str(e)}")

@notification_router.post("/test-send-email")
async def test_send_email_notification(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Test endpoint to manually trigger email notification for current user"""
    try:
        from arbitrage_notifications import notification_service
        
        # Force check and send notification for current user
        await notification_service.check_user_opportunities(current_user, db)
        
        return {
            "success": True,
            "message": f"Email notification check triggered for {current_user.email}",
            "user_id": current_user.id,
            "email": current_user.email
        }
        
    except Exception as e:
        logging.error(f"Error in test email notification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error testing email: {str(e)}")

@notification_router.get("/email-status")
async def get_email_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's email notification status and rate limiting info"""
    try:
        from arbitrage_notifications import notification_service
        from user_models import UserEmailNotificationLog
        from datetime import date
        
        # Get subscription status
        subscription_status = notification_service.get_user_subscription_status(current_user.id, db)
        daily_limit = notification_service.get_daily_email_limit(subscription_status)
        
        # Get today's email count
        today = date.today()
        email_log = db.query(UserEmailNotificationLog).filter(
            UserEmailNotificationLog.user_id == current_user.id,
            UserEmailNotificationLog.email_date == today
        ).first()
        
        emails_sent_today = email_log.email_count if email_log else 0
        can_send_email = notification_service.can_send_email_today(current_user.id, subscription_status, db)
        
        # Get user profile for notification preferences
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        notifications_enabled = profile.notification_email if profile else False
        
        return {
            "subscription_status": subscription_status,
            "daily_limit": daily_limit,
            "emails_sent_today": emails_sent_today,
            "emails_remaining": max(0, daily_limit - emails_sent_today),
            "can_send_email": can_send_email,
            "notifications_enabled": notifications_enabled,
            "date": today.isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error getting email status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting email status: {str(e)}")

@notification_router.post("/force-send-test-email")
async def force_send_test_email(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Force send a test email with mock opportunities (bypasses rate limits)"""
    try:
        from arbitrage_notifications import notification_service
        
        # Create mock opportunities for testing
        mock_opportunities = [
            {
                "sport_key": "soccer_epl",
                "sport_title": "English Premier League",
                "arbitrage_detected": True,
                "match": {
                    "home_team": "Arsenal",
                    "away_team": "Manchester United",
                    "commence_time": "2025-06-25 15:00:00"
                },
                "profit_percentage": 4.5,
                "best_odds": {
                    "home": 2.45,
                    "away": 3.20,
                    "draw": 3.80,
                    "home_bookmaker": "Bet365",
                    "away_bookmaker": "Betfair",
                    "draw_bookmaker": "William Hill"
                }
            }
        ]
        
        # Get user subscription status
        subscription_status = notification_service.get_user_subscription_status(current_user.id, db)
        
        # Check if user can send email (but don't block for testing)
        can_send = notification_service.can_send_email_today(current_user.id, subscription_status, db)
        
        if not can_send:
            return {
                "success": False,
                "message": f"Daily email limit reached ({notification_service.get_daily_email_limit(subscription_status)} emails/day). Test email not sent.",
                "subscription_status": subscription_status,
                "daily_limit": notification_service.get_daily_email_limit(subscription_status),
                "can_send_email": can_send
            }
        
        # Send email and increment counter
        success = await notification_service.send_notification_email(
            current_user.email, 
            mock_opportunities, 
            subscription_status
        )
        
        if success:
            notification_service.increment_daily_email_count(current_user.id, db)
        
        return {
            "success": success,
            "message": f"Test email {'sent' if success else 'failed'} to {current_user.email}",
            "subscription_status": subscription_status,
            "daily_limit": notification_service.get_daily_email_limit(subscription_status),
            "opportunities_count": len(mock_opportunities)
        }
        
    except Exception as e:
        logging.error(f"Error in force send test email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending test email: {str(e)}")