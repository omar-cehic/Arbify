# sgo_api_service.py - SportsGameOdds API Integration Service
import os
import time
import logging
import aiohttp
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SportsGameOdds API Configuration
SGO_API_KEY = os.getenv("SGO_API_KEY")  # Your API key
SGO_BASE_URL = "https://api.sportsgameodds.com/v2"

class SGOSport(Enum):
    """SportsGameOdds supported sports"""
    FOOTBALL = "FOOTBALL"
    BASKETBALL = "BASKETBALL" 
    BASEBALL = "BASEBALL"
    HOCKEY = "HOCKEY"
    SOCCER = "SOCCER"
    TENNIS = "TENNIS"
    MMA = "MMA"
    GOLF = "GOLF"

class SGOLeague(Enum):
    """Key leagues for arbitrage opportunities"""
    # Football
    NFL = "NFL"
    NCAAF = "NCAAF"
    
    # Basketball  
    NBA = "NBA"
    NCAAB = "NCAAB"
    WNBA = "WNBA"
    
    # Baseball
    MLB = "MLB"
    
    # Hockey
    NHL = "NHL"
    
    # Soccer
    EPL = "EPL"
    LA_LIGA = "LA_LIGA"
    BUNDESLIGA = "BUNDESLIGA"
    
    # Tennis
    ATP = "ATP"
    WTA = "WTA"
    
    # MMA
    UFC = "UFC"

@dataclass
class SGOMarket:
    """Represents a betting market structure"""
    stat_id: str
    bet_type_id: str
    period_id: str
    stat_entity_ids: List[str]
    odd_ids: List[str]
    description: str

# Priority markets for arbitrage detection
PRIORITY_MARKETS = {
    "moneyline_game": SGOMarket(
        stat_id="points",
        bet_type_id="ml", 
        period_id="game",
        stat_entity_ids=["home", "away"],
        odd_ids=["points-home-game-ml-home", "points-away-game-ml-away"],
        description="Moneyline (Full Game)"
    ),
    "spread_game": SGOMarket(
        stat_id="points",
        bet_type_id="sp",
        period_id="game", 
        stat_entity_ids=["home", "away"],
        odd_ids=["points-home-game-sp-home", "points-away-game-sp-away"],
        description="Spread (Full Game)"
    ),
    "totals_game": SGOMarket(
        stat_id="points",
        bet_type_id="ou",
        period_id="game",
        stat_entity_ids=["all"],
        odd_ids=["points-all-game-ou-over", "points-all-game-ou-under"], 
        description="Over/Under (Full Game)"
    ),
    "moneyline_3way": SGOMarket(
        stat_id="points", 
        bet_type_id="ml3way",
        period_id="game",
        stat_entity_ids=["home", "away", "all"],
        odd_ids=["points-home-game-ml3way-home", "points-away-game-ml3way-away", "points-all-game-ml3way-draw"],
        description="3-Way Moneyline (Soccer)"
    )
}

# US Licensed Bookmakers (for legal compliance)
US_LICENSED_BOOKMAKERS = {
    'draftkings', 'fanduel', 'betmgm', 'caesars', 'espnbet', 'betrivers',
    'fanatics', 'hardrockbet', 'bovada', 'betus', 'mybookie', 'lowvig'
}

class SGOApiService:
    """SportsGameOdds API service for arbitrage betting"""
    
    def __init__(self):
        self.api_key = SGO_API_KEY
        self.base_url = SGO_BASE_URL
        self.session = None
        self.rate_limit_delay = 0.1  # 0.1 second between requests (600 req/min)
        self.last_request_time = 0
        self.request_count = 0
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # Cache for static data
        self.sports_cache = {}
        self.leagues_cache = {}
        self.bookmakers_cache = {}
        self.cache_expiry = {}
        
        # Rookie plan limits
        self.requests_per_minute = 60
        self.objects_per_month = 5000000  # 5M objects
        self.update_frequency_minutes = 5
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"X-API-Key": self.api_key},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.info(f"⏱️ Rate limiting: sleeping {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        
        cached_time, _ = self.cache[cache_key]
        return time.time() - cached_time < self.cache_duration
    
    def _get_from_cache(self, cache_key: str):
        """Get data from cache"""
        if self._is_cache_valid(cache_key):
            _, data = self.cache[cache_key]
            logger.info(f"📦 Using cached data for {cache_key}")
            return data
        return None
    
    def _cache_data(self, cache_key: str, data: Any):
        """Cache API response data"""
        self.cache[cache_key] = (time.time(), data)
        logger.info(f"💾 Cached data for {cache_key}")
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated API request with rate limiting"""
        cache_key = f"{endpoint}_{str(params)}"
        
        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        await self._rate_limit()
        
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"🌐 SGO API Request #{self.request_count}: {endpoint}")
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self._cache_data(cache_key, data)
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"❌ SGO API Error {response.status}: {error_text}")
                    raise Exception(f"SGO API Error {response.status}: {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ SGO API Request failed: {str(e)}")
            raise
    
    async def get_sports(self) -> List[Dict]:
        """Get list of available sports"""
        return await self._make_request("sports")
    
    async def get_leagues(self, sport_id: str = None) -> List[Dict]:
        """Get leagues for a sport or all leagues"""
        endpoint = f"leagues/{sport_id}" if sport_id else "leagues"
        return await self._make_request(endpoint)
    
    async def get_events(self, 
                        sport_id: str = None,
                        league_id: str = None, 
                        limit: int = 50,
                        upcoming_only: bool = True) -> List[Dict]:
        """Get upcoming events/games"""
        params = {"limit": limit}
        
        if upcoming_only:
            # Only get events starting in the future
            params["start_time_after"] = datetime.utcnow().isoformat()
        
        # Use correct SGO v2 endpoints
        endpoint = "events"
        if sport_id:
            params["sportID"] = sport_id
        elif league_id:
            params["leagueID"] = league_id
            
        response_data = await self._make_request(endpoint, params)
        
        # Handle different response formats
        if isinstance(response_data, dict):
            # If response is a dict with a 'data' key containing the list
            if 'data' in response_data:
                return response_data['data']
            # If response is a dict with events data directly
            elif 'events' in response_data:
                return response_data['events']
            # If response is a dict but should be a list, wrap it
            else:
                return [response_data] if response_data else []
        elif isinstance(response_data, list):
            return response_data
        else:
            logger.warning(f"⚠️ Unexpected events response type: {type(response_data)}")
            return []
    
    async def get_upcoming_events(self, league_id: str = None, limit: int = 50) -> List[Dict]:
        """Get upcoming events with odds - convenience method"""
        return await self.get_events(league_id=league_id, limit=limit, upcoming_only=True)
    
    async def get_bookmakers(self) -> List[Dict]:
        """Get available bookmakers - SGO v2 doesn't have a bookmakers endpoint"""
        # SGO v2 doesn't have a dedicated bookmakers endpoint
        # Return the hardcoded list from the documentation
        return [
            {"bookmakerID": "draftkings", "name": "DraftKings"},
            {"bookmakerID": "fanduel", "name": "FanDuel"},
            {"bookmakerID": "betmgm", "name": "BetMGM"},
            {"bookmakerID": "caesars", "name": "Caesars"},
            {"bookmakerID": "espnbet", "name": "ESPN BET"},
            {"bookmakerID": "betrivers", "name": "BetRivers"},
            {"bookmakerID": "fanatics", "name": "Fanatics"},
            {"bookmakerID": "hardrockbet", "name": "Hard Rock Bet"},
            {"bookmakerID": "bovada", "name": "Bovada"},
            {"bookmakerID": "betus", "name": "BetUS"},
            {"bookmakerID": "mybookie", "name": "MyBookie"},
            {"bookmakerID": "lowvig", "name": "LowVig"}
        ]
    
    async def get_odds(self,
                      event_ids: List[str] = None,
                      sport_id: str = None,
                      league_id: str = None,
                      odd_ids: List[str] = None,
                      bookmaker_ids: List[str] = None,
                      limit: int = 100) -> List[Dict]:
        """Get odds data for events"""
        params = {"limit": limit}
        
        if event_ids:
            params["event_ids"] = ",".join(event_ids)
        if odd_ids:
            params["odd_ids"] = ",".join(odd_ids) 
        if bookmaker_ids:
            params["bookmaker_ids"] = ",".join(bookmaker_ids)
        
        endpoint = "odds"
        if sport_id:
            endpoint = f"sports/{sport_id}/odds"
        elif league_id:
            endpoint = f"leagues/{league_id}/odds"
            
        response_data = await self._make_request(endpoint, params)
        
        # Handle different response formats
        if isinstance(response_data, dict):
            # If response is a dict with a 'data' key containing the list
            if 'data' in response_data:
                return response_data['data']
            # If response is a dict with odds data directly
            elif 'odds' in response_data:
                return response_data['odds']
            # If response is a dict but should be a list, wrap it
            else:
                return [response_data] if response_data else []
        elif isinstance(response_data, list):
            return response_data
        else:
            logger.warning(f"⚠️ Unexpected odds response type: {type(response_data)}")
            return []
    
    async def get_arbitrage_opportunities(self,
                                        sports: List[str] = None,
                                        leagues: List[str] = None,
                                        max_events: int = 100,
                                        us_books_only: bool = True) -> List[Dict]:
        """
        Get arbitrage opportunities from SGO data
        
        Args:
            sports: List of sport IDs to check
            leagues: List of league IDs to check  
            max_events: Maximum events to analyze
            us_books_only: Only use US licensed bookmakers
            
        Returns:
            List of arbitrage opportunities
        """
        logger.info("🔍 Starting arbitrage opportunity search...")
        
        opportunities = []
        
        # Default to high-volume leagues if none specified (Rookie plan requires leagueID)
        if not sports and not leagues:
            leagues = ["NFL", "NBA", "MLB", "NHL"]  # Only leagues available in Rookie plan
        
        try:
            # Step 1: Get events for target sports/leagues
            all_events = []
            
            if leagues:
                for league in leagues:
                    events = await self.get_events(league_id=league, limit=max_events//len(leagues))
                    all_events.extend(events)
                    logger.info(f"📅 Found {len(events)} events for {league}")
            
            # Skip sports for now since Rookie plan requires leagueID
            if sports:
                logger.warning("⚠️ Skipping sports - Rookie plan requires leagueID parameter")
            
            logger.info(f"📊 Total events to analyze: {len(all_events)}")
            
            # Step 2: Get odds for these events
            if not all_events:
                logger.warning("⚠️ No events found")
                return []
            
            event_ids = [event.get("eventID", event.get("event_id", "")) for event in all_events[:max_events] if event.get("eventID") or event.get("event_id")]
            
            # Focus on key markets for arbitrage
            priority_odd_ids = []
            for market in PRIORITY_MARKETS.values():
                priority_odd_ids.extend(market.odd_ids)
            
            # Filter bookmakers if needed
            target_bookmakers = list(US_LICENSED_BOOKMAKERS) if us_books_only else None
            
            odds_data = await self.get_odds(
                event_ids=event_ids,
                odd_ids=priority_odd_ids,
                bookmaker_ids=target_bookmakers,
                limit=1000  # Higher limit for odds
            )
            
            logger.info(f"💰 Retrieved {len(odds_data)} odds records")
            
            # Step 3: Detect arbitrage opportunities
            opportunities = await self._detect_arbitrage_from_sgo_data(odds_data, all_events)
            
            logger.info(f"🎯 Found {len(opportunities)} arbitrage opportunities")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error getting arbitrage opportunities: {str(e)}")
            return []
    
    async def _detect_arbitrage_from_sgo_data(self, odds_data: List[Dict], events_data: List[Dict]) -> List[Dict]:
        """Detect arbitrage opportunities from SGO odds data"""
        opportunities = []
        
        # Group odds by event, market, and line
        event_odds = {}
        
        for odds_record in odds_data:
            # Ensure odds_record is a dict
            if not isinstance(odds_record, dict):
                continue
                
            event_id = odds_record.get("eventID", odds_record.get("event_id"))
            odd_id = odds_record.get("oddID", odds_record.get("odd_id"))
            
            if not event_id or not odd_id:
                continue
                
            if event_id not in event_odds:
                event_odds[event_id] = {}
            
            # Parse odd_id to determine market type
            market_type = self._parse_market_type(odd_id)
            if not market_type:
                continue
                
            if market_type not in event_odds[event_id]:
                event_odds[event_id][market_type] = {}
            
            # Get and normalize line
            line = odds_record.get("line")
            normalized_line = self._normalize_line(market_type, line)
            
            if normalized_line not in event_odds[event_id][market_type]:
                event_odds[event_id][market_type][normalized_line] = {}
            
            # Store odds by outcome
            outcome = self._parse_outcome(odd_id)
            if outcome:
                if outcome not in event_odds[event_id][market_type][normalized_line]:
                    event_odds[event_id][market_type][normalized_line][outcome] = []
                
                # Add this bookmaker's odds
                bookmaker_odds = {
                    "bookmaker": odds_record.get("bookmaker_id", "unknown"),
                    "odds": odds_record.get("odds_decimal", 0),
                    "line": line,
                    "updated": odds_record.get("updated_at")
                }
                
                event_odds[event_id][market_type][normalized_line][outcome].append(bookmaker_odds)
        
        # Create event lookup - ensure event is a dict
        events_lookup = {}
        for event in events_data:
            if isinstance(event, dict) and (event.get("eventID") or event.get("event_id")):
                event_id = event.get("eventID", event.get("event_id", ""))
                events_lookup[event_id] = event
        
        # Analyze each event for arbitrage
        for event_id, markets in event_odds.items():
            event_info = events_lookup.get(event_id, {})
            
            for market_type, lines in markets.items():
                for line_key, outcomes in lines.items():
                    # Use the actual line value from the first outcome if available, else the key
                    point = line_key if line_key != "default" else None
                    
                    arb_opp = self._calculate_arbitrage_opportunity(
                        event_info, market_type, outcomes, point
                    )
                    
                    if arb_opp:
                        opportunities.append(arb_opp)
        
        return opportunities
    
    def _parse_market_type(self, odd_id: str) -> str:
        """Parse market type from odd_id"""
        # Format: {statID}-{statEntityID}-{periodID}-{betTypeID}-{sideID}
        parts = odd_id.split("-")
        if len(parts) >= 4:
            bet_type = parts[3]
            period = parts[2]
            
            if bet_type == "ml" and period == "game":
                return "moneyline"
            elif bet_type == "sp" and period == "game":
                return "spread" 
            elif bet_type == "ou" and period == "game":
                return "totals"
            elif bet_type == "ml3way" and period == "game":
                return "moneyline_3way"
        
        return None
    
    def _parse_outcome(self, odd_id: str) -> str:
        """Parse outcome from odd_id"""
        parts = odd_id.split("-")
        if len(parts) >= 5:
            return parts[4]  # sideID
        return None

    def _normalize_line(self, market_type: str, line: Any) -> Any:
        """Normalize line value for grouping"""
        if line is None:
            return "default"
            
        try:
            val = float(line)
            if market_type == "spread":
                return abs(val)
            return val
        except (ValueError, TypeError):
            return "default"
    
    def _calculate_arbitrage_opportunity(self, event_info: Dict, market_type: str, outcomes: Dict, point: Optional[float] = None) -> Optional[Dict]:
        """Calculate if outcomes create an arbitrage opportunity"""
        try:
            # Need at least 2 outcomes
            if len(outcomes) < 2:
                return None
            
            # Find best odds for each outcome
            best_odds = {}
            for outcome, bookmaker_odds_list in outcomes.items():
                if not bookmaker_odds_list:
                    continue
                
                # Find highest odds for this outcome
                best = max(bookmaker_odds_list, key=lambda x: x["odds"])
                if best["odds"] > 1.0:  # Valid odds
                    best_odds[outcome] = best
            
            # Need at least 2 different bookmakers
            bookmakers = set(odds["bookmaker"] for odds in best_odds.values())
            if len(bookmakers) < 2:
                return None
            
            # Calculate arbitrage
            total_inverse_odds = sum(1/odds["odds"] for odds in best_odds.values())
            
            if total_inverse_odds < 1.0:  # Arbitrage opportunity!
                profit_percentage = ((1/total_inverse_odds) - 1) * 100
                
                # Calculate optimal bet amounts for $100 total stake
                total_stake = 100
                bet_amounts = {}
                
                for outcome, odds_info in best_odds.items():
                    bet_amounts[outcome] = (total_stake / total_inverse_odds) / odds_info["odds"]
                
                return {
                    "event_id": event_info.get("eventID", event_info.get("event_id")),
                    "sport": event_info.get("sportID", event_info.get("sport_id", "unknown")),
                    "league": event_info.get("leagueID", event_info.get("league_id", "unknown")),
                    "home_team": event_info.get("teams", {}).get("home", {}).get("names", {}).get("medium", "Home"),
                    "away_team": event_info.get("teams", {}).get("away", {}).get("names", {}).get("medium", "Away"),
                    "commence_time": event_info.get("status", {}).get("startsAt", event_info.get("start_time")),
                    "market_type": market_type,
                    "profit_percentage": round(profit_percentage, 3),
                    "best_odds": best_odds,
                    "bet_amounts": {k: round(v, 2) for k, v in bet_amounts.items()},
                    "total_stake": total_stake,
                    "guaranteed_profit": round(total_stake * profit_percentage / 100, 2),
                    "bookmakers_involved": list(bookmakers),
                    "updated_at": datetime.utcnow().isoformat(),
                    "data_source": "sgo_api",
                    "point": point
                }
        
        except Exception as e:
            logger.error(f"Error calculating arbitrage: {str(e)}")
            
        return None
    
    def get_rate_limit_status(self) -> Dict:
        """Get current rate limit status"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        recent_requests = len([t for t in self.request_times if t > minute_ago])
        
        return {
            'requests_this_minute': recent_requests,
            'max_requests_per_minute': self.requests_per_minute,
            'objects_this_month': self.object_count,
            'max_objects_per_month': self.objects_per_month,
            'remaining_requests': max(0, self.requests_per_minute - recent_requests),
            'remaining_objects': max(0, self.objects_per_month - self.object_count)
        }
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global service instance
sgo_service = SGOApiService()

# Efficient polling strategy for 5M objects/month (Rookie plan)
class SGOPollingStrategy:
    """Efficient polling strategy to maximize 5M objects/month"""
    
    def __init__(self):
        self.monthly_limit = 5000000  # 5M objects
        self.daily_budget = 166667  # ~5M/30 days
        self.hourly_budget = 6944  # ~166K/24 hours
        self.events_used_today = 0
        self.last_reset_date = datetime.now().date()
        
        # Priority leagues for arbitrage (highest volume/opportunity)
        self.priority_leagues = [
            "NFL", "NBA", "MLB", "NHL",  # Major US sports
            "EPL", "BUNDESLIGA", "LA_LIGA",  # Top soccer leagues
            "UFC"  # MMA has good arbitrage opportunities
        ]
        
        # Polling schedule (times per day to check) - More frequent with Rookie plan
        self.polling_times = [
            "08:00",  # Early morning
            "12:00",  # Midday
            "16:00",  # Afternoon
            "20:00",  # Evening
            "00:00"   # Midnight
        ]
    
    def should_poll_now(self) -> bool:
        """Check if we should poll based on budget and schedule"""
        now = datetime.now()
        
        # Reset daily counter if new day
        if now.date() > self.last_reset_date:
            self.events_used_today = 0
            self.last_reset_date = now.date()
        
        # Check daily budget
        if self.events_used_today >= self.daily_budget:
            logger.info(f"⏸️ Daily budget exhausted: {self.events_used_today}/{self.daily_budget}")
            return False
        
        # Check if it's a scheduled polling time (within 30 minutes)
        current_time = now.strftime("%H:%M")
        for poll_time in self.polling_times:
            poll_dt = datetime.strptime(poll_time, "%H:%M").time()
            current_dt = now.time()
            
            # Check if within 30 minutes of scheduled time
            time_diff = abs(datetime.combine(now.date(), current_dt) - 
                           datetime.combine(now.date(), poll_dt))
            
            if time_diff <= timedelta(minutes=30):
                return True
        
        return False
    
    def get_polling_params(self) -> Dict:
        """Get optimized parameters for current polling session"""
        remaining_budget = min(
            self.daily_budget - self.events_used_today,
            100  # Max per session with Rookie plan (much higher limit)
        )
        
        return {
            "max_events": remaining_budget,
            "sports": ["FOOTBALL", "BASKETBALL", "BASEBALL", "HOCKEY", "SOCCER"],
            "leagues": self.priority_leagues,  # All priority leagues
            "us_books_only": True
        }
    
    def record_usage(self, events_consumed: int):
        """Record API usage"""
        self.events_used_today += events_consumed
        logger.info(f"📊 API Usage: {self.events_used_today}/{self.daily_budget} events today")

# Global polling strategy
polling_strategy = SGOPollingStrategy()
