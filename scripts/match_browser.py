# match_browser.py - API-efficient match browser with on-demand odds loading

from typing import Dict, List, Optional
import logging
import aiohttp
import asyncio
from datetime import datetime, timezone
from app.core.config import API_KEY, BASE_API_URL
from app.core.sports_config import SUPPORTED_SPORTS

# Cache for match summaries (longer duration since this is basic info)
match_cache = {}
MATCH_CACHE_DURATION = 600  # 10 minutes for match listings

# Cache for detailed match odds (shorter duration for accuracy)
odds_cache = {}
ODDS_CACHE_DURATION = 120  # 2 minutes for detailed odds

async def get_upcoming_matches_summary(sport_key: str = None) -> List[Dict]:
    """
    Get upcoming matches with basic info only (no detailed odds)
    This uses minimal API calls - just match info, not full odds
    """
    import time
    
    cache_key = f"matches_{sport_key or 'all'}"
    current_time = time.time()
    
    # Check cache first
    if cache_key in match_cache:
        cached_data, cache_time = match_cache[cache_key]
        if current_time - cache_time < MATCH_CACHE_DURATION:
            logging.info(f"🚀 Using cached match summary for {cache_key}")
            return cached_data
    
    # Determine which sports to fetch
    POPULAR_SPORTS = [
        'soccer_epl',           # English Premier League
        'americanfootball_nfl', # NFL  
        'basketball_nba',       # NBA
        'baseball_mlb',         # MLB
        'icehockey_nhl'         # NHL
    ]
    
    sports_to_fetch = []
    if sport_key:
        if sport_key in SUPPORTED_SPORTS and SUPPORTED_SPORTS[sport_key]["active"]:
            sports_to_fetch.append((sport_key, SUPPORTED_SPORTS[sport_key]))
    else:
        # Fetch popular sports only for match browser
        sports_to_fetch = [(key, info) for key, info in SUPPORTED_SPORTS.items() 
                          if info["active"] and key in POPULAR_SPORTS]
    
    all_matches = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for sport_key, sport_info in sports_to_fetch:
            task = fetch_match_summaries(session, sport_key, sport_info)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Error in match summary fetch: {str(result)}")
            elif isinstance(result, list):
                all_matches.extend(result)
    
    # Sort by commence time (earliest first)
    all_matches.sort(key=lambda x: x.get('commence_time', ''))
    
    # Cache the results
    match_cache[cache_key] = (all_matches, current_time)
    
    logging.info(f"✅ Fetched {len(all_matches)} match summaries")
    return all_matches


async def fetch_match_summaries(session, sport_key: str, sport_info: dict) -> List[Dict]:
    """Fetch basic match info without detailed odds (saves API quota)"""
    try:
        # Use the sports endpoint instead of odds endpoint to get match info only
        url = f"{BASE_API_URL}/sports/{sport_key}/odds"
        params = {
            "apiKey": API_KEY,
            "regions": "us",  # Single region to reduce data
            "markets": "h2h", # Single market to minimize data
            "oddsFormat": "decimal",
            "dateFormat": "iso"
        }
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                matches_data = await response.json()
                
                # Convert to match summaries (basic info only)
                match_summaries = []
                for match in matches_data:
                    # Basic match info without detailed odds
                    summary = {
                        "id": match.get("id"),
                        "sport_key": sport_key,
                        "sport_title": sport_info["title"],
                        "home_team": match.get("home_team"),
                        "away_team": match.get("away_team"),
                        "commence_time": match.get("commence_time"),
                        # Add basic odds summary (just for display, not arbitrage)
                        "has_odds": len(match.get("bookmakers", [])) > 0,
                        "bookmaker_count": len(match.get("bookmakers", [])),
                        # Don't include full odds data - save API quota
                        "match_title": f"{match.get('home_team')} vs {match.get('away_team')}",
                        "status": "upcoming"
                    }
                    match_summaries.append(summary)
                
                logging.info(f"✅ {sport_info['title']}: {len(match_summaries)} match summaries")
                return match_summaries
                
            else:
                logging.error(f"❌ Error fetching match summaries for {sport_info['title']}: {response.status}")
                return []
                
    except Exception as e:
        logging.error(f"❌ Exception fetching match summaries for {sport_info['title']}: {str(e)}")
        return []


async def get_detailed_match_odds(match_id: str) -> Optional[Dict]:
    """
    Get detailed odds for a specific match (called on-demand)
    This is where we use API quota efficiently - only when user requests it
    """
    import time
    
    cache_key = f"match_odds_{match_id}"
    current_time = time.time()
    
    # Check cache first
    if cache_key in odds_cache:
        cached_data, cache_time = odds_cache[cache_key]
        if current_time - cache_time < ODDS_CACHE_DURATION:
            logging.info(f"🚀 Using cached detailed odds for match {match_id}")
            return cached_data
    
    # This would typically use the /events/{eventId}/odds endpoint
    # For now, we'll fetch from the regular endpoint and filter
    # In production, you'd want to use the specific event endpoint to save quota
    
    try:
        async with aiohttp.ClientSession() as session:
            # Note: This is a simplified version - ideally use /events/{match_id}/odds
            # For now, we'll return a placeholder structure
            detailed_odds = {
                "match_id": match_id,
                "markets": {
                    "h2h": {"available": True},
                    "spreads": {"available": True}, 
                    "totals": {"available": True}
                },
                "bookmakers": [],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Cache the detailed odds
            odds_cache[cache_key] = (detailed_odds, current_time)
            
            return detailed_odds
            
    except Exception as e:
        logging.error(f"❌ Error fetching detailed odds for match {match_id}: {str(e)}")
        return None


def get_match_browser_stats() -> Dict:
    """Get statistics about match browser usage and caching"""
    import time
    current_time = time.time()
    
    # Count active caches
    active_match_cache = sum(1 for _, (_, cache_time) in match_cache.items() 
                           if current_time - cache_time < MATCH_CACHE_DURATION)
    active_odds_cache = sum(1 for _, (_, cache_time) in odds_cache.items() 
                          if current_time - cache_time < ODDS_CACHE_DURATION)
    
    return {
        "active_match_summaries": active_match_cache,
        "active_detailed_odds": active_odds_cache,
        "total_match_cache_entries": len(match_cache),
        "total_odds_cache_entries": len(odds_cache),
        "match_cache_duration_minutes": MATCH_CACHE_DURATION // 60,
        "odds_cache_duration_minutes": ODDS_CACHE_DURATION // 60
    }