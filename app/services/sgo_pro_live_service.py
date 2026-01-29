"""
SGO Pro Live Service - Optimized for Pro plan with live odds detection
"""

import os
import asyncio
import aiohttp
import logging
import random
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import dateutil.parser
from app.core.config import SGO_API_KEY, STALE_DATA_THRESHOLD_MINUTES
from app.services.market_grouper import MarketGrouper
from app.core.database import SessionLocal, BettingOdds

logger = logging.getLogger(__name__)

class SGOProLiveService:
    """SGO service optimized for Pro plan with live odds and arbitrage detection
    Enhanced with sport-specific validation for soccer and football
    """
    
    # Rate Limiting State (Shared Access across instances)
    _rate_limit_lock = asyncio.Lock()
    _window_start_time = datetime.now()
    _request_count = 0
    _max_requests_per_minute = 290
    
    def __init__(self):
        # Get API key from environment variable (production) or use Pro plan key
        self.api_key = os.getenv("SGO_API_KEY")
        self.base_url = "https://api.sportsgameodds.com/v2"
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = None
        
        # MASTER NHL TOGGLE - Easy to control
        self.PROCESS_NHL = True  # Set to True when you want NHL back
        
        # ENABLED SPORTS - Block NHL at source
        self.ENABLED_SPORTS = {'SOCCER', 'BASKETBALL', 'HOCKEY', 'BASEBALL', 'MMA', 'FOOTBALL', 'TENNIS'}
        self.ENABLED_LEAGUES = ["NFL", "NBA", "MLB", "EPL", "BUNDESLIGA", "LA_LIGA", "IT_SERIE_A", "MLS"]
        
        # Hardcoded NHL team list for blocking
        self.NHL_TEAMS = [
            'maple leafs', 'rangers', 'sharks', 'wild', 'stars', 
            'ducks', 'penguins', 'hurricanes', 'predators', 'oilers',
            'canadiens', 'kraken', 'flames', 'golden knights', 'bruins',
            'blackhawks', 'red wings', 'sabres', 'senators', 'lightning',
            'panthers', 'islanders', 'devils', 'flyers', 'capitals',
            'blue jackets', 'avalanche', 'jets', 'blues', 'kings'
        ]
        
        # Structure logging flag
        self._logged_structure = False
        
        # US-accessible bookmakers (exclude international exchanges that US users cannot access)
        self.us_bookmakers = {
            'fanduel', 'draftkings', 'betmgm', 'caesars', 'espnbet', 'bovada',
            'unibet', 'pointsbet', 'williamhill', 'hardrockbet', 'fliff', 
            'ballybet', 'wynnbet', 'betrivers', 'sugarhouse', 'barstool',
            'superbook', 'foxbet', 'twinspires', 'betfred', 'betparx',
            'si_sportsbook', 'resorts_world', 'golden_nugget'
        }
        
        # International/Exchange bookmakers (not accessible to US users)  
        self.international_bookmakers = {
            'betfairexchange', 'prophetexchange', '1xbet', 'lowvig', 
            'bookmakereu', '888sport', 'coral', 'bet365', 'pinnacle',
            'tipico'  # Tipico is EU-based, not accessible to most US users
        }
        
        # Sport-specific validation rules (builds on existing algorithm)
        self._init_sport_validation_rules()
        
    def save_odds_to_database(self, events: List[Dict[str, Any]]):
        """
        Save fetched odds to the database for debugging and 'View Odds' feature.
        Uses batch inserts for efficiency.
        """
        if not events:
            return

        try:
            db = SessionLocal()
            try:
                # Prepare batch of objects to save
                odds_objects = []
                current_time = datetime.utcnow()
                
                # Track what we're saving to avoid duplicates in this batch
                seen_keys = set()
                
                for event in events:
                    # Extract basic info
                    home_team, away_team = self._extract_team_names(event)
                    sport_id = event.get('sportID', event.get('sport', 'UNKNOWN'))
                    league_id = event.get('leagueID', 'UNKNOWN')
                    commence_time = event.get('startsAt')
                    
                    # Skip if no odds
                    if not event.get('odds') and not event.get('bookmakers'):
                        continue
                        
                    # Handle SGO's nested structure (bookmakers -> markets -> outcomes)
                    # Note: SGO structure varies, sometimes it's flat odds, sometimes nested
                    
                    # Strategy: Flatten everything into BettingOdds objects
                    # We'll use a simplified mapping for now to get data IN
                    
                    # 1. Check for 'bookmakers' list (standard SGO format)
                    bookmakers = event.get('bookmakers', [])
                    if not bookmakers and event.get('odds'):
                        # Fallback: sometimes 'odds' is the list of bookmakers or markets
                        # This depends on the specific SGO endpoint version
                        pass 
                        
                    for bookmaker in bookmakers:
                        bm_name = bookmaker.get('title', bookmaker.get('name', 'Unknown'))
                        
                        for market in bookmaker.get('markets', []):
                            market_key = market.get('key', 'unknown')
                            
                            for outcome in market.get('outcomes', []):
                                outcome_name = outcome.get('name', 'Unknown')
                                price = outcome.get('price', 0)
                                
                                # Create unique key for deduplication
                                key = f"{sport_id}_{home_team}_{away_team}_{bm_name}_{market_key}_{outcome_name}"
                                if key in seen_keys:
                                    continue
                                seen_keys.add(key)
                                
                                odds_obj = BettingOdds(
                                    sport_key=sport_id.lower(),
                                    sport_title=league_id,
                                    commence_time=commence_time,
                                    home_team=home_team,
                                    away_team=away_team,
                                    sportsbook=bm_name,
                                    price=price, # Schema might use 'price' or 'odds' - check model
                                    odds=price,  # Map to 'odds' field as well just in case
                                    outcome=outcome_name,
                                    market_key=market_key,
                                    last_update=current_time
                                )
                                odds_objects.append(odds_obj)
                
                if odds_objects:
                    # Bulk save (or add_all)
                    # Note: For true upsert, we'd need more complex logic. 
                    # For now, we'll just append. A cleanup job should handle old data.
                    # Ideally, we delete old records for these events first.
                    
                    # Simple cleanup: Delete records for these sports updated > 5 mins ago?
                    # Or just insert. Let's insert for now to see data.
                    
                    db.add_all(odds_objects)
                    db.commit()
                    logger.info(f"💾 SAVED {len(odds_objects)} odds records to database")
                else:
                    logger.debug("💾 No odds objects created to save")
                    
            except Exception as e:
                logger.error(f"Error saving odds to database: {str(e)}")
                db.rollback()
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in save_odds_to_database: {str(e)}")

    def _init_sport_validation_rules(self):
        """Initialize sport-specific validation rules (enhances existing algorithm)"""
        # Soccer validation rules
        self.soccer_valid_lines = {0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0}
        self.soccer_reliable_books = {'bet365', 'pinnacle', 'unibet', 'williamhill', 'fanduel', 'draftkings'}
        
        # Football validation rules  
        self.football_valid_spreads = {x * 0.5 for x in range(-56, 57)}  # -28.0 to +28.0
        self.football_valid_totals = {x * 0.5 for x in range(60, 140)}   # 30.0 to 69.5
        self.football_reliable_books = {'fanduel', 'draftkings', 'betmgm', 'caesars', 'espnbet'}
    
    def _categorize_opportunity_accessibility(self, opp: Dict[str, Any]) -> str:
        """Categorize arbitrage opportunity by bookmaker accessibility"""
        best_odds = opp.get('best_odds', {})
        
        has_international = False
        has_us = False
        
        for side, odds_info in best_odds.items():
            bookmaker = odds_info.get('bookmaker', '').lower()
            
            if bookmaker in self.international_bookmakers:
                has_international = True
            else:
                has_us = True
        
        if has_international and has_us:
            return "mixed"  # Mix of US and international bookmakers
        elif has_international:
            return "international"  # Only international bookmakers
        else:
            return "us"  # Only US bookmakers
    
    def _validate_arbitrage_opportunity(self, opp: Dict[str, Any]) -> Dict[str, Any]:
        """Validate arbitrage opportunity for data quality issues (enhanced with sport-specific rules)"""
        best_odds = opp.get('best_odds', {})
        issues = []
        confidence = 1.0
        sport = opp.get('sport', 'UNKNOWN').upper()
        
        # Check 1: Both teams can't be underdogs (American odds both positive) - BUT ONLY FOR MONEYLINE BETS
        market_description = opp.get('market_description', '').lower()
        is_moneyline = 'moneyline' in market_description or ('away' in best_odds and 'home' in best_odds and len(best_odds) == 2)
        
        if is_moneyline:  # Only apply this check to moneyline bets, not over/under
            american_odds = []
            for side, odds_info in best_odds.items():
                american_odds_str = odds_info.get('american_odds', '')
                if american_odds_str.startswith('+'):
                    american_odds.append('positive')
                elif american_odds_str.startswith('-'):
                    american_odds.append('negative')
            
            if len(american_odds) == 2 and all(odds == 'positive' for odds in american_odds):
                issues.append("Both teams shown as underdogs in moneyline (impossible)")
                confidence = 0.1  # Very low confidence
        
        # Check 2: Log high profits but NEVER reject them
        profit = opp.get('profit_percentage', 0)
        sport = opp.get('league', '').upper()
        
        if sport in ['MLB', 'NBA', 'NFL', 'NHL'] and profit > 15:
            logging.info(f"High profit opportunity detected: {profit:.1f}% for {sport}")
            # No confidence reduction - high profits can be legitimate
        
        # Check 3: Bookmaker accessibility and sport-specific validation
        international_bookmakers = {'betfairexchange', 'prophetexchange', '1xbet', 'tipico'}
        bookmakers_used = set()
        
        for side, odds_info in best_odds.items():
            bookmaker = odds_info.get('bookmaker', '').lower()
            bookmakers_used.add(bookmaker)
        
        if bookmakers_used.intersection(international_bookmakers):
            issues.append("Uses international bookmakers (limited US access)")
            confidence *= 0.8
        
        # Sport-specific validation (builds on existing algorithm)
        confidence = self._apply_sport_specific_validation(opp, confidence, issues, sport)  # Still show these, just with lower confidence
        
        # Check 4: Odds format consistency
        decimal_odds = []
        
        # Check 5: Stale Data Filtering (Ghost Lines)
        current_time = datetime.utcnow()
        for side, odds_info in best_odds.items():
            last_update_str = odds_info.get("last_update")
            if last_update_str:
                try:
                    # Parse timestamp (SGO Format usually ISO)
                    # Handle both Z-terminated and naive strings appropriately
                    if last_update_str.endswith('Z'):
                        last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))
                        # Make current time aware for comparison
                        now_aware = current_time.replace(microsecond=0).astimezone() if last_update.tzinfo else current_time
                    else:
                        last_update = datetime.fromisoformat(last_update_str)
                        now_aware = current_time
                    
                    # Calculate Age
                    # Handling timezone awareness mismatch simply by stripping if needed or ensuring comparison works
                    if last_update.tzinfo and not now_aware.tzinfo:
                         now_aware = now_aware.replace(tzinfo=last_update.tzinfo)
                    
                    # Rough check using offset-naive if complexity is high, but prefer robust parsing
                    age_minutes = (now_aware - last_update).total_seconds() / 60
                    
                    if age_minutes > STALE_DATA_THRESHOLD_MINUTES:
                        logger.warning(f"🚫 STALE DATA: {odds_info.get('bookmaker')} odds are {age_minutes:.1f} min old. Filtered.")
                        issues.append(f"Stale odds ({age_minutes:.0f}m old)")
                        confidence = 0.0 # Kill it
                except Exception as e:
                    # If we can't parse time, be cautious but don't hard reject unless confident
                    logger.debug(f"Time parse error for {last_update_str}: {e}")
            else:
                 # If no timestamp, it's risky. Downgrade slightly or pass? 
                 # SGO usually provides it. If missing, assume it might be okay but warn.
                 pass

        for side, odds_info in best_odds.items():
            odds = odds_info.get('odds', 0)
            if isinstance(odds, (int, float)) and odds > 0:
                decimal_odds.append(odds)
        
        if len(decimal_odds) == 2:
            implied_prob_total = sum(1/odds for odds in decimal_odds)
            if implied_prob_total >= 1.0:
                issues.append("Implied probabilities > 100% (not arbitrage)")
                confidence = 0.0
        
        # Add enhanced validation info to opportunity
        opp['validation'] = {
            'issues': issues,
            'confidence_score': confidence,
            'data_quality': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low',
            'last_checked': datetime.now().isoformat(),
            'verification_needed': confidence < 0.8
        }
        
        # Add verification instructions for manual checking
        opp['verification_instructions'] = self._create_verification_instructions(opp)
        
        return opp
    
    def _apply_sport_specific_validation(self, opp: Dict[str, Any], confidence: float, issues: List[str], sport: str) -> float:
        """Apply sport-specific validation rules (enhances existing algorithm without breaking baseball)"""
        # Preserve baseball functionality - no changes to existing baseball logic
        if sport in ['MLB', 'BASEBALL']:
            return confidence
        
        market_description = opp.get('market_description', '').lower()
        line_value = opp.get('line')
        profit_percentage = opp.get('profit_percentage', 0)
        best_odds = opp.get('best_odds', {})
        bookmakers_used = {odds_info.get('bookmaker', '').lower() for odds_info in best_odds.values()}
        
        # Soccer-specific validation
        if sport in ['SOCCER'] or 'soccer' in sport.lower():
            # Validate soccer total lines
            if line_value is not None and ('total' in market_description or 'over' in market_description):
                if line_value not in self.soccer_valid_lines:
                    issues.append(f"Invalid soccer total line: {line_value}")
                    confidence *= 0.7
            
            # Soccer profit margin validation (typically lower than other sports)
            if profit_percentage > 8.0:
                issues.append(f"High profit margin for soccer: {profit_percentage}%")
                confidence *= 0.8
            
            # Soccer bookmaker reliability
            reliable_count = len(bookmakers_used.intersection(self.soccer_reliable_books))
            if reliable_count == 0:
                issues.append("No reliable soccer bookmakers")
                confidence *= 0.7
            
            # 3-way moneyline validation
            if '3way' in market_description or 'draw' in market_description:
                if len(best_odds) != 3:
                    issues.append("3-way market should have exactly 3 sides")
                    confidence *= 0.6
        
        # Football-specific validation  
        elif sport in ['NFL', 'NCAAF', 'FOOTBALL']:
            # Validate football spreads
            if line_value is not None and ('spread' in market_description or 'point' in market_description):
                if line_value not in self.football_valid_spreads:
                    issues.append(f"Invalid football spread: {line_value}")
                    confidence *= 0.8
            
            # Validate football totals
            if line_value is not None and 'total' in market_description:
                if line_value not in self.football_valid_totals:
                    issues.append(f"Invalid football total: {line_value}")
                    confidence *= 0.8
            
            # Football profit margin validation
            if profit_percentage > 12.0:
                issues.append(f"High profit margin for football: {profit_percentage}%")
                confidence *= 0.8
            
            # Football bookmaker reliability
            reliable_count = len(bookmakers_used.intersection(self.football_reliable_books))
            if reliable_count == 0:
                issues.append("No reliable football bookmakers")
                confidence *= 0.8
        
        return confidence
    
    def _create_verification_instructions(self, opp: Dict[str, Any]) -> Dict[str, Any]:
        """Create step-by-step instructions for manually verifying an opportunity"""
        best_odds = opp.get('best_odds', {})
        market_description = opp.get('market_description', '')
        home_team = opp.get('home_team', '')
        away_team = opp.get('away_team', '')
        
        instructions = {
            "game": f"{home_team} vs {away_team}",
            "market": market_description,
            "steps": [],
            "warning": "⚠️ Always verify odds on bookmaker sites before betting. Lines change frequently."
        }
        
        for side, odds_info in best_odds.items():
            bookmaker = odds_info.get('bookmaker', 'unknown')
            american_odds = odds_info.get('american_odds', 'N/A')
            line = odds_info.get('line', 'N/A')
            
            if 'total' in market_description.lower() and line != 'N/A':
                if side == 'over':
                    instructions["steps"].append(f"Go to {bookmaker.title()} → Find {home_team} vs {away_team} → Look for 'Over/Under' or 'Totals' → Verify 'Over {line}' shows {american_odds}")
                elif side == 'under':
                    instructions["steps"].append(f"Same game → Verify 'Under {line}' shows {american_odds}")
            elif 'moneyline' in market_description.lower():
                team_name = home_team if side == 'home' else away_team if side == 'away' else 'Team'
                instructions["steps"].append(f"Go to {bookmaker.title()} → Find {home_team} vs {away_team} → Verify '{team_name} to Win' shows {american_odds}")
        
        return instructions
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def _ensure_session(self):
        """Ensure HTTP session is available"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _rate_limit(self):
        """Rate limiting for Pro plan (300 requests/minute) - Window Based with Locking"""
        async with self.__class__._rate_limit_lock:
            now = datetime.now()
            time_passed = (now - self.__class__._window_start_time).total_seconds()
            
            # Reset window if 60 seconds have passed
            if time_passed > 60:
                self.__class__._window_start_time = now
                self.__class__._request_count = 0
                logger.debug("🔄 Rate limit window reset")
                
            # Check if limit reached
            if self.__class__._request_count >= self.__class__._max_requests_per_minute:
                wait_time = 61 - time_passed
                if wait_time < 0: wait_time = 0
                
                logger.warning(f"⏳ Rate limit reached ({self.__class__._request_count}/{self.__class__._max_requests_per_minute}), waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                
                # Reset after wait
                self.__class__._window_start_time = datetime.now()
                self.__class__._request_count = 0
                
            self.__class__._request_count += 1
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a single SGO API request with Pro plan rate limiting"""
        await self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"X-Api-Key": self.api_key}
        
        if params is None:
            params = {}
            
        # Pro plan parameters
        params.update({
            "limit": 100,  # API Max Limit per request
            "oddsAvailable": "true"
        })
        
        logger.info(f"Making SGO Pro request to {endpoint} (request #{self.__class__._request_count})")
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Log SGO structure ONCE only
                    if data.get("data") and not self._logged_structure:
                        events = data["data"]
                        if events:
                            import json
                            logger.debug(f"🔴 SGO STRUCTURE: {json.dumps(events[0], indent=2)}")
                            self._logged_structure = True
                    
                    logger.info(f"SGO Pro request successful: {endpoint}")
                    return data
                elif response.status == 429:
                    logger.warning(f"Rate limited on {endpoint}, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    return {"success": False, "error": "Rate limited"}
                else:
                    error_text = await response.text()
                    msg = f"SGO Pro API error {response.status} on {endpoint}: {error_text}"
                    if response.status == 429 or "rate limit" in error_text.lower():
                         logger.warning(msg)
                         return {"success": False, "error": "Rate limited"}
                    
                    # Downgrade 5xx errors to warning if they are transient
                    if 500 <= response.status < 600:
                        logger.warning(msg)
                    else:
                        logger.error(msg)
                        
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            # Downgrade common networking errors to warning
            error_str = str(e).lower()
            if "rate limit" in error_str or "429" in error_str or "timeout" in error_str or "connection" in error_str:
                logger.warning(f"SGO Pro request issue on {endpoint}: {str(e)}")
            else:
                logger.error(f"SGO Pro request failed on {endpoint}: {str(e)}")
                
            return {"success": False, "error": str(e)}
    
    # Live Caching State
    _live_cache = []
    _live_cache_time = None
    _live_fetch_lock = asyncio.Lock()
    _LIVE_CACHE_TTL = 15  # Seconds for live data

    async def get_live_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """Get live arbitrage opportunities with Request Coalescing"""
        # 1. Check Cache
        now = datetime.now()
        if self.__class__._live_cache and self.__class__._live_cache_time:
            age = (now - self.__class__._live_cache_time).total_seconds()
            if age < self.__class__._LIVE_CACHE_TTL:
                return self.__class__._live_cache

        # 2. Coalescing
        async with self.__class__._live_fetch_lock:
            # 3. Double Check
            now = datetime.now()
            if self.__class__._live_cache and self.__class__._live_cache_time:
                age = (now - self.__class__._live_cache_time).total_seconds()
                if age < self.__class__._LIVE_CACHE_TTL:
                    return self.__class__._live_cache

            # 4. Fetch
            opportunities = []
            try:
                logger.info(f"🚀 SGO Pro Live Service starting fetch...")
            
                # Check live games first (these have the most arbitrage opportunities)
                logger.info("🔍 Searching for LIVE games with arbitrage opportunities...")
                
                # Get live games - add comprehensive filters to exclude stale data
                from datetime import datetime, timedelta
                today = datetime.now()
                start_date = (today - timedelta(hours=6)).strftime("%Y-%m-%d")  # Allow games from 6 hours ago
                end_date = today.strftime("%Y-%m-%d")
                
                live_data = await self._make_request("/events", {
                    "live": "true",
                    "limit": 20,
                    "status": "active",  # Only active events
                    "startDate": start_date,  # From 6 hours ago
                    "endDate": end_date,  # Until today
                    "oddsAvailable": "true"  # Only events with odds
                })
                
                logger.debug(f"🔍 LIVE GAMES DEBUG: SGO API response status: {live_data.get('success', 'unknown')}")
                if live_data.get("data"):
                    logger.debug(f"🔍 LIVE GAMES DEBUG: Found {len(live_data['data'])} live events in response")
                else:
                    logger.debug("🔍 LIVE GAMES DEBUG: No live events data in response")
                
                if live_data.get("success", True) and live_data.get("data"):
                    live_events = live_data["data"]
                    
                    # Save raw odds to database for debugging and 'View Odds' feature
                    # PERF: Run DB save in background thread to avoid blocking response
                    try:
                        loop = asyncio.get_running_loop()
                        loop.run_in_executor(None, self.save_odds_to_database, live_events)
                    except Exception as e:
                        logger.error(f"Error triggering background DB save: {e}")
                    
                    # Dense logging - pack multiple pieces of info per line
                    active_events = [e for e in live_events if not e.get("cancelled", False) and not e.get("ended", False)]
                    stale_events = [e for e in live_events if e.get("startsAt", "") < "2025-10-01"]
                    logger.debug(f"📊 SGO LIVE: {len(live_events)} total, {len(active_events)} active, {len(stale_events)} stale (July 2025)")
                    
                    for event in live_events:
                        # HARD STOP: Skip any events before October 2025
                        start_time = event.get("startsAt", "")
                        if start_time and start_time < "2025-10-01":
                            continue  # Silent skip - these are definitely stale
                        
                        # CRITICAL: Skip cancelled, ended, or old events
                        if (event.get("cancelled", False) or 
                            event.get("ended", False) or
                            event.get("started", False) or 
                            not event.get("oddsAvailable", True)):
                            continue
                        
                        # HARDCODED NHL BLOCKING - Extract team names properly
                        home_team, away_team = self._extract_team_names(event)
                        
                        # HARDCODED NHL BLOCKING - Second check
                        if self._is_nhl_event(home_team, away_team):
                            logger.debug(f"🔴 CRITICAL: NHL BLOCKED (LIVE) - {home_team} vs {away_team}")
                            continue
                        
                        # CRITICAL: Block NHL at source before processing
                        if not self._is_sport_enabled(event):
                            continue
                            
                        opp = await self._analyze_live_event_for_arbitrage(event)
                        if opp:
                            # Validate data quality before adding
                            validated_opp = self._validate_arbitrage_opportunity(opp)
                            validation = validated_opp.get('validation', {})
                            
                            confidence_score = validation.get('confidence_score', 0)
                            # logger.debug(f"🔴 CRITICAL: OPPORTUNITY VALIDATION - Confidence: {confidence_score:.2f}")
                            
                            if confidence_score > 0.1:  # TEMPORARILY LOWERED to see what's being rejected
                                # Categorize by accessibility instead of filtering out
                                accessibility = self._categorize_opportunity_accessibility(validated_opp)
                                validated_opp['accessibility'] = accessibility
                                
                                opportunities.append(validated_opp)
                                confidence = validation.get('data_quality', 'unknown')
                                logger.info(f"🎯 LIVE ARBITRAGE FOUND ({confidence}, {accessibility}): {validated_opp['home_team']} vs {validated_opp['away_team']} - {validated_opp['profit_percentage']}% profit")
                                if validation.get('issues'):
                                    logger.debug(f"⚠️  Data issues: {', '.join(validation['issues'])}")
                            else:
                                logger.debug(f"🚫 DATA QUALITY: Rejected {opp['home_team']} vs {opp['away_team']} - Low confidence ({validation.get('confidence_score', 0):.1f})")
                                for issue in validation.get('issues', []):
                                    logger.debug(f"   📋 Issue: {issue}")
                else:
                    logger.warning(f"⚠️ Live games request failed: {live_data}")
                
                # Redundant sequential polling removed for performance
                # Upcoming games are already handled by tiered parallel polling in get_upcoming_arbitrage_opportunities
                logger.info("🔍 Live opportunity check complete (Upcoming handled by background tier polling)")
                            

                
                logger.info(f"🏁 Live arbitrage search complete: Found {len(opportunities)} opportunities")
                
                # 5. Update Cache
                self.__class__._live_cache = opportunities
                self.__class__._live_cache_time = datetime.now()
                return opportunities
            
            except Exception as e:
                logger.error(f"Error in get_live_arbitrage_opportunities: {str(e)}")
                import traceback
                logger.error(f"Stack trace: {traceback.format_exc()}")
                return []
    
    # Caching and Coalescing State
    _cache = []
    _cache_time = None
    _fetch_lock = asyncio.Lock()
    _CACHE_TTL = 30  # Seconds
    
    async def get_upcoming_arbitrage_opportunities(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Public wrapper for upcoming arbitrage opportunities with Request Coalescing and CACHING.
        """
        # 1. Check Cache (Fast path)
        now = datetime.now()
        if not force_refresh and self.__class__._cache and self.__class__._cache_time:
            age = (now - self.__class__._cache_time).total_seconds()
            if age < self.__class__._CACHE_TTL:
                logger.debug(f"⚡ CACHE HIT: Serving {len(self.__class__._cache)} opportunities ({age:.1f}s old)")
                return self.__class__._cache

        # 2. Coalescing (Wait for existing fetch if one is running)
        async with self.__class__._fetch_lock:
            # 3. Double-Check Cache (after acquiring lock)
            now = datetime.now()
            if self.__class__._cache and self.__class__._cache_time:
                age = (now - self.__class__._cache_time).total_seconds()
                # If cache is fresh enough (even if force_refresh was requested, if it's < 5s old, reuse it)
                min_ttl = 5 if force_refresh else self.__class__._CACHE_TTL
                if age < min_ttl:
                    logger.info(f"⚡ CACHE HIT (Coalesced): Serving {len(self.__class__._cache)} opportunities ({age:.1f}s old)")
                    return self.__class__._cache

            # 4. Perform Actual Fetch
            logger.info("🔄 REFRESHING: Cache stale or forced, fetching new data...")
            result = await self._fetch_upcoming_internal()
            
            # 5. Update Cache
            self.__class__._cache = result
            self.__class__._cache_time = datetime.now()
            return result

    async def _fetch_upcoming_internal(self) -> List[Dict[str, Any]]:
        """Internal method to fetch data from API (Original Logic)"""
        try:
            logger.info("🔍 Searching for UPCOMING games with arbitrage opportunities (Tiered Polling)...")
            
            # TIERED POLLING: Fetch events for each sport separately to bypass 100-item limit
            all_upcoming_events = []
            import time
            polling_start = time.time()
            
            # Prioritize major sports
            tiered_sports = ['BASKETBALL', 'FOOTBALL', 'HOCKEY', 'BASEBALL', 'SOCCER', 'TENNIS', 'MMA']
            # Add any other enabled sports that aren't in the priority list
            for sport in self.ENABLED_SPORTS:
                if sport not in tiered_sports:
                    tiered_sports.append(sport)
            
            # Create tasks for all tiered sports except the ones we want to skip or specialized logic
            tasks = []
            for sport in tiered_sports:
                logger.debug(f"  > Queueing poll for sport: {sport}")
                tasks.append(self._get_upcoming_events(sport_id=sport))
            
            # PARALLEL EXECUTION: Run all sports requests concurrently
            # This is critical to prevent timeouts (total time = slowest request, not sum of all)
            logger.info(f"⏱️ PERF: Starting parallel poll for {len(tasks)} sports...")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                sport = tiered_sports[i]
                if isinstance(result, Exception):
                    logger.error(f"    - Error polling {sport}: {result}")
                elif result:
                    all_upcoming_events.extend(result)
                    logger.info(f"    + Found {len(result)} events for {sport}")
                else:
                    logger.debug(f"    - No events for {sport}")
            
            polling_time = time.time() - polling_start
            logger.info(f"⏱️ PERF: SGO Polling Complete | Total Time: {polling_time:.4f}s | Events: {len(all_upcoming_events)}")
            
            # Save raw odds to database for debugging and 'View Odds' feature
            if all_upcoming_events:
                # PERF: Run DB save in background thread to avoid blocking response
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, self.save_odds_to_database, all_upcoming_events)
                logger.info("💾 Triggered background DB save for upcoming events")
            
            if not all_upcoming_events:
                logger.info("📊 No upcoming events found across all sports")
                return []
            
            polling_time = time.time() - polling_start
            logger.info(f"⏱️ POLLING TIME: {polling_time:.2f}s | Found {len(all_upcoming_events)} events")
            
            opportunities = []
            analysis_start = time.time()
            # PARALLEL PROCESSING: Analyze all events concurrently to prevent timeout
            # (Previously was sequential: 500 events x 0.1s = 50s delay -> Timeout)
            logging.info(f"⚡ FAST MODE: Analyzing {len(all_upcoming_events)} events in parallel...")
            
            analysis_tasks = []
            for event in all_upcoming_events:
                 # Check blocked sports/teams BEFORE parsing to save CPU
                if not self._is_sport_enabled(event):
                    continue
                    
                analysis_tasks.append(self._analyze_upcoming_event_for_arbitrage(event))
            
            # Execute all checks at once
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            for result in analysis_results:
                if isinstance(result, Exception):
                     # Log but don't crash
                    logger.debug(f"Analysis error: {str(result)}")
                    continue
                    
                if result: # If opportunity found
                    opp = result
                    try:
                        # Validate data quality before adding
                        validated_opp = self._validate_arbitrage_opportunity(opp)
                        validation = validated_opp.get('validation', {})
                        confidence_score = validation.get('confidence_score', 0)
                        
                        if confidence_score > 0.1:
                            accessibility = self._categorize_opportunity_accessibility(validated_opp)
                            validated_opp['accessibility'] = accessibility
                            
                            opportunities.append(validated_opp)
                            confidence = validation.get('data_quality', 'unknown')
                            logger.info(f"🎯 UPCOMING ARBITRAGE FOUND ({confidence}): {validated_opp['home_team']} vs {validated_opp['away_team']} - {validated_opp['profit_percentage']}% profit")
                    except Exception as e:
                        logger.error(f"Error validating opportunity: {e}")
            
            analysis_time = time.time() - analysis_start
            logger.info(f"⏱️ ANALYSIS TIME: {analysis_time:.2f}s | {len(opportunities)} opportunities")
            
            logger.info(f"✅ Found {len(opportunities)} upcoming arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error in get_upcoming_arbitrage_opportunities: {str(e)}")
            return []
    
    async def _analyze_live_event_for_arbitrage(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a LIVE event for arbitrage opportunities"""
        try:
            event_id = event.get("eventID", "")
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("medium", "Home")
            away_team = teams.get("away", {}).get("names", {}).get("medium", "Away")
            # IMPROVED: Better start time extraction with fallbacks
            start_time = (event.get("status", {}).get("startsAt", "") or 
                         event.get("startsAt", "") or 
                         event.get("startTime", "") or 
                         event.get("commence_time", ""))
            current_status = event.get("status", {}).get("currentStatus", "")
            odds = event.get("odds", {})
            
            # Get actual sport and league from event data
            sport = event.get("sportID", "Unknown")
            league = event.get("leagueID", "Unknown")
            
            # logger.info(f"🔍 Analyzing LIVE game: {home_team} vs {away_team} ({sport} - {league}) Status: {current_status}")  # DISABLED to prevent rate limiting
            
            if not odds:
                return None
            
            # Look for arbitrage in live games - mark as LIVE
            opportunity = await self._find_arbitrage_in_odds(odds, event_id, home_team, away_team, start_time, "LIVE", sport, league)
            if opportunity:
                # Ensure the opportunity is properly marked as LIVE
                opportunity['game_type'] = 'LIVE'
                opportunity['is_live'] = True
                opportunity['status'] = 'LIVE'
                logger.info(f"🔴 LIVE OPPORTUNITY CREATED: {home_team} vs {away_team} - {opportunity.get('profit_percentage', 0):.2f}% profit")
            return opportunity
            
        except Exception as e:
            logger.error(f"Error analyzing live event: {str(e)}")
            return None
    
    async def _get_upcoming_events(self, sport_id: str = None) -> List[Dict[str, Any]]:
        """Get upcoming events from SGO API (supports sport filtering)"""
        try:
            params = {
                "days": 7,
                "status": "upcoming"
            }
            
            start_time_req = time.time()
            if sport_id:
                # SGO API parameter for sport is 'sportID' (Case Sensitive, verified via debug script)
                params["sportID"] = sport_id
            
            # Get events for the next 7 days
            response = await self._make_request("events", params)
            
            if response.get("success") is False:
                logger.error(f"SGO API error: {response.get('error')}")
                return []
            
            events = response.get("data", [])
            
            # CRITICAL FIX: SGO API sometimes ignores sportId param, so filter manually
            if sport_id:
                filtered_events = []
                for event in events:
                    event_sport = event.get("sportID", event.get("sport", "")).upper()
                    if event_sport == sport_id.upper() or (sport_id.upper() == "SOCCER" and "SOCCER" in event_sport):
                        filtered_events.append(event)
                
                if len(filtered_events) < len(events):
                    logger.warning(f"⚠️ API returned mixed sports. Filtered {len(events)} -> {len(filtered_events)} for {sport_id}")
                events = filtered_events
                
            elapsed = time.time() - start_time_req
            logger.info(f"⏱️ PERF: Fetched {sport_id} | {elapsed:.4f}s | {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Error getting upcoming events: {str(e)}")
            return []
    
    async def _analyze_upcoming_event_for_arbitrage(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze an UPCOMING event for arbitrage opportunities"""
        try:
            event_id = event.get("eventID", "")
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("medium", "Home")
            away_team = teams.get("away", {}).get("names", {}).get("medium", "Away")
            # IMPROVED: Better start time extraction with fallbacks
            start_time = (event.get("status", {}).get("startsAt", "") or 
                         event.get("startsAt", "") or 
                         event.get("startTime", "") or 
                         event.get("commence_time", ""))
            odds = event.get("odds", {})
            
            # Get actual sport and league from event data
            sport = event.get("sportID", "Unknown")
            league = event.get("leagueID", "Unknown")
            
            # DEBUG: Log start time extraction for debugging
            if not start_time:
                logger.warning(f"⚠️ MISSING START TIME: {home_team} vs {away_team} - Event keys: {list(event.keys())}")
                if "status" in event:
                    logger.warning(f"   Status keys: {list(event['status'].keys())}")
            else:
                logger.debug(f"✅ START TIME FOUND: {home_team} vs {away_team} - {start_time}")
            
            if not odds:
                return None
            
            # Look for arbitrage in upcoming games
            # CRITICAL FIX: Check if game has actually started based on timestamp
            game_type = "UPCOMING"
            try:
                if start_time:
                    # Parse start time (handling ISO format with 'Z' or offset)
                    start_dt = dateutil.parser.parse(start_time)
                    now = datetime.now(timezone.utc)
                    
                    # If start time is in the past, mark as LIVE
                    if start_dt < now:
                        game_type = "LIVE"
                        logger.debug(f"⏱️ EVENT STARTED: {home_team} vs {away_team} started at {start_time} (Now: {now}) -> Marked LIVE")
            except Exception as e:
                logger.warning(f"Failed to parse start time {start_time}: {e}")

            return await self._find_arbitrage_in_odds(odds, event_id, home_team, away_team, start_time, game_type, sport, league)
            
        except Exception as e:
            logger.error(f"Error analyzing upcoming event: {str(e)}")
            return None
    
    async def _analyze_event_for_arbitrage(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze an upcoming event for arbitrage opportunities"""
        try:
            event_id = event.get("eventID", "")
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("medium", "Home")
            away_team = teams.get("away", {}).get("names", {}).get("medium", "Away")
            start_time = event.get("status", {}).get("startsAt", "")
            odds = event.get("odds", {})
            
            # Get actual sport and league from event data
            sport = event.get("sportID", "Unknown")
            league = event.get("leagueID", "Unknown")
            
            if not odds:
                return None
            
            # Look for moneyline arbitrage in upcoming games
            # CRITICAL FIX: Check if game has actually started
            game_type = "UPCOMING"
            try:
                if start_time:
                    start_dt = dateutil.parser.parse(start_time)
                    now = datetime.now(timezone.utc)
                    if start_dt < now:
                        game_type = "LIVE"
            except Exception:
                pass

            return await self._find_arbitrage_in_odds(odds, event_id, home_team, away_team, start_time, game_type, sport, league)
            
        except Exception as e:
            logger.error(f"Error analyzing event: {str(e)}")
            return None
    
    def _get_market_info(self, odd_id: str, sport: str = "UNKNOWN") -> Dict[str, Any]:
        """Extract market information from SGO oddID format: statID-statEntityID-periodID-betTypeID-sideID"""
        
        # Parse SGO oddID structure
        parts = odd_id.split("-")
        
        # CRITICAL FIX: Handle compound side IDs (e.g., away+draw, home+draw, not_draw)
        side_parts = parts[4:] if len(parts) > 4 else ["unknown"]
        side_id = "-".join(side_parts)
        
        market_info = {
            "stat_id": parts[0] if len(parts) > 0 else "unknown",
            "stat_entity_id": parts[1] if len(parts) > 1 else "unknown", 
            "period_id": parts[2] if len(parts) > 2 else "game",
            "bet_type_id": parts[3] if len(parts) > 3 else "ml",
            "side_id": side_id,
            "market_type": "unknown",
            "market_description": "Unknown Market",
            "line": None
        }
        
        stat_id = market_info["stat_id"]
        stat_entity_id = market_info["stat_entity_id"]
        period_id = market_info["period_id"]
        bet_type_id = market_info["bet_type_id"]
        
        # Determine market type based on stat_id and stat_entity_id
        # CRITICAL FIX: Handle soccer markets FIRST before general points logic
        if stat_id == "points" and stat_entity_id in ["home", "away", "all"] and self._is_soccer_sport(sport):
            # Soccer goals markets (moneyline, spread, totals, even/odd, yes/no) with period support
            terminology = self._get_sport_terminology(sport)
            unit = terminology['unit']  # "Goals" for soccer
            
            # DEBUG: Log when soccer-specific logic is used
            if sport == "SOCCER" or "soccer" in sport.lower():
                logger.debug(f"⚽ SOCCER MARKET RECOGNIZED: {odd_id} -> market_type will be soccer-specific")
                # Log basic markets at INFO level for visibility
                if bet_type_id in ["ml", "ou"] and stat_entity_id in ["home", "away", "all"]:
                    logger.debug(f"⚽ BASIC SOCCER MARKET: {odd_id} -> {bet_type_id} for {stat_entity_id}")
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                
                if bet_type_id == "ml":
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_moneyline"
                        market_info["market_description"] = f"{period_name} Home Moneyline"
                        market_info["detailed_market_description"] = f"{period_name} Home Team Moneyline"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_moneyline"
                        market_info["market_description"] = f"{period_name} Away Moneyline"
                        market_info["detailed_market_description"] = f"{period_name} Away Team Moneyline"
                elif bet_type_id == "ml3way":
                    # Handle compound side IDs for 3-way moneylines
                    if side_id == "home+draw":
                        market_info["market_type"] = f"soccer_{period_id}_home_draw_3way"
                        market_info["market_description"] = f"{period_name} Home/Draw (3-Way)"
                        market_info["detailed_market_description"] = f"{period_name} Home or Draw 3-Way Moneyline"
                    elif side_id == "away+draw":
                        market_info["market_type"] = f"soccer_{period_id}_away_draw_3way"
                        market_info["market_description"] = f"{period_name} Away/Draw (3-Way)"
                        market_info["detailed_market_description"] = f"{period_name} Away or Draw 3-Way Moneyline"
                    elif side_id == "not_draw":
                        market_info["market_type"] = f"soccer_{period_id}_3way_not_draw"
                        market_info["market_description"] = f"{period_name} Home/Away (3-Way)"
                        market_info["detailed_market_description"] = f"{period_name} Home or Away 3-Way Moneyline"
                    elif stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_3way_moneyline"
                        market_info["market_description"] = f"{period_name} Home (3-Way)"
                        market_info["detailed_market_description"] = f"{period_name} Home Team 3-Way Moneyline"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_3way_moneyline"
                        market_info["market_description"] = f"{period_name} Away (3-Way)"
                        market_info["detailed_market_description"] = f"{period_name} Away Team 3-Way Moneyline"
                    else:  # all
                        market_info["market_type"] = f"soccer_{period_id}_draw_3way_moneyline"
                        market_info["market_description"] = f"{period_name} Draw (3-Way)"
                        market_info["detailed_market_description"] = f"{period_name} Draw 3-Way Moneyline"
                elif bet_type_id == "sp":
                    # Spread (Goal difference)
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_spread"
                        market_info["market_description"] = f"{period_name} Home Goal Spread"
                        market_info["detailed_market_description"] = f"{period_name} Home Team Goal Spread"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_spread"
                        market_info["market_description"] = f"{period_name} Away Goal Spread"
                        market_info["detailed_market_description"] = f"{period_name} Away Team Goal Spread"
                elif bet_type_id == "ou":
                    # Over/Under goals
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_total"
                        market_info["market_description"] = f"{period_name} Home Team Total {unit}"
                        market_info["detailed_market_description"] = f"{period_name} Home Team Total {unit} Over/Under"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_total"
                        market_info["market_description"] = f"{period_name} Away Team Total {unit}"
                        market_info["detailed_market_description"] = f"{period_name} Away Team Total {unit} Over/Under"
                    else:  # all
                        market_info["market_type"] = f"soccer_{period_id}_total_goals"
                        market_info["market_description"] = f"{period_name} Total {unit}"
                        market_info["detailed_market_description"] = f"{period_name} Total {unit} Over/Under"
                elif bet_type_id == "eo":
                    # Even/Odd goals
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_even_odd"
                        market_info["market_description"] = f"{period_name} Home Team {unit} Even/Odd"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_even_odd"
                        market_info["market_description"] = f"{period_name} Away Team {unit} Even/Odd"
                    else:  # all
                        market_info["market_type"] = f"soccer_{period_id}_total_even_odd"
                        market_info["market_description"] = f"{period_name} Total {unit} Even/Odd"
                elif bet_type_id == "yn":
                    # Yes/No anytime goals
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_anytime"
                        market_info["market_description"] = f"{period_name} Home Team Anytime {unit} Yes/No"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_anytime"
                        market_info["market_description"] = f"{period_name} Away Team Anytime {unit} Yes/No"
                    else:  # all
                        market_info["market_type"] = f"soccer_{period_id}_anytime_goals"
                        market_info["market_description"] = f"{period_name} Anytime {unit} Yes/No"
            else:
                # Full match soccer markets
                if bet_type_id == "ml":
                    if stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_moneyline"
                        market_info["market_description"] = "Home Moneyline"
                        market_info["detailed_market_description"] = "Home Team Moneyline"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_moneyline"
                        market_info["market_description"] = "Away Moneyline"
                        market_info["detailed_market_description"] = "Away Team Moneyline"
                elif bet_type_id == "ml3way":
                    # Handle compound side IDs for 3-way moneylines
                    if side_id == "home+draw":
                        market_info["market_type"] = "soccer_home_draw_3way"
                        market_info["market_description"] = "Home/Draw (3-Way)"
                        market_info["detailed_market_description"] = "Home or Draw 3-Way Moneyline"
                    elif side_id == "away+draw":
                        market_info["market_type"] = "soccer_away_draw_3way"
                        market_info["market_description"] = "Away/Draw (3-Way)"
                        market_info["detailed_market_description"] = "Away or Draw 3-Way Moneyline"
                    elif side_id == "not_draw":
                        market_info["market_type"] = "soccer_3way_not_draw"
                        market_info["market_description"] = "Home/Away (3-Way)"
                        market_info["detailed_market_description"] = "Home or Away 3-Way Moneyline"
                    elif stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_3way_moneyline"
                        market_info["market_description"] = "Home (3-Way)"
                        market_info["detailed_market_description"] = "Home Team 3-Way Moneyline"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_3way_moneyline"
                        market_info["market_description"] = "Away (3-Way)"
                        market_info["detailed_market_description"] = "Away Team 3-Way Moneyline"
                    else:  # all
                        market_info["market_type"] = "soccer_draw_3way_moneyline"
                        market_info["market_description"] = "Draw (3-Way)"
                        market_info["detailed_market_description"] = "Draw 3-Way Moneyline"
                elif bet_type_id == "sp":
                    # Spread (Goal difference)
                    if stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_spread"
                        market_info["market_description"] = "Home Goal Spread"
                        market_info["detailed_market_description"] = "Home Team Goal Spread"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_spread"
                        market_info["market_description"] = "Away Goal Spread"
                        market_info["detailed_market_description"] = "Away Team Goal Spread"
                elif bet_type_id == "ou":
                    # Over/Under goals
                    if stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_total"
                        market_info["market_description"] = f"Home Team Total {unit}"
                        market_info["detailed_market_description"] = f"Home Team Total {unit} Over/Under"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_total"
                        market_info["market_description"] = f"Away Team Total {unit}"
                        market_info["detailed_market_description"] = f"Away Team Total {unit} Over/Under"
                    else:  # all
                        market_info["market_type"] = "soccer_total_goals"
                        market_info["market_description"] = f"Total {unit}"
                        market_info["detailed_market_description"] = f"Total {unit} Over/Under"
                elif bet_type_id == "eo":
                    # Even/Odd goals
                    if stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_even_odd"
                        market_info["market_description"] = f"Home Team {unit} Even/Odd"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_even_odd"
                        market_info["market_description"] = f"Away Team {unit} Even/Odd"
                    else:  # all
                        market_info["market_type"] = "soccer_total_even_odd"
                        market_info["market_description"] = f"Total {unit} Even/Odd"
                elif bet_type_id == "yn":
                    # Yes/No anytime goals
                    if stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_anytime"
                        market_info["market_description"] = f"Home Team Anytime {unit} Yes/No"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_anytime"
                        market_info["market_description"] = f"Away Team Anytime {unit} Yes/No"
                    else:  # all
                        market_info["market_type"] = "soccer_anytime_goals"
                        market_info["market_description"] = f"Anytime {unit} Yes/No"
        
        elif stat_id == "points":
            # Sport-specific terminology (per SGO documentation)
            sport_terminology = self._get_sport_terminology(sport)
            
            if stat_entity_id == "home":
                if bet_type_id == "ml":
                    market_info["market_type"] = "home_moneyline"
                    market_info["market_description"] = "Home Moneyline"
                    market_info["detailed_market_description"] = "Home Team Moneyline"
                elif bet_type_id == "sp":
                    market_info["market_type"] = "home_spread"
                    market_info["market_description"] = f"Home {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"Home Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ml3way":
                    # Handle compound side IDs for 3-way moneylines
                    if side_id == "home+draw":
                        market_info["market_type"] = "home_draw_3way"
                        market_info["market_description"] = "Home/Draw (3-Way)"
                        market_info["detailed_market_description"] = "Home or Draw 3-Way Moneyline"
                    else:
                        market_info["market_type"] = "home_3way_moneyline"
                        market_info["market_description"] = "Home (3-Way)"
                        market_info["detailed_market_description"] = "Home Team 3-Way Moneyline"
                elif bet_type_id == "ou":
                    market_info["market_type"] = "team_total_home"
                    market_info["market_description"] = f"Home Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = "team_total_home_even_odd"
                    market_info["market_description"] = f"Home Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = "team_anytime_home"
                    market_info["market_description"] = f"Home Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "away":
                if bet_type_id == "ml":
                    market_info["market_type"] = "away_moneyline"
                    market_info["market_description"] = "Away Moneyline"
                    market_info["detailed_market_description"] = "Away Team Moneyline"
                elif bet_type_id == "sp":
                    market_info["market_type"] = "away_spread"
                    market_info["market_description"] = f"Away {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"Away Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ml3way":
                    # Handle compound side IDs for 3-way moneylines
                    if side_id == "away+draw":
                        market_info["market_type"] = "away_draw_3way"
                        market_info["market_description"] = "Away/Draw (3-Way)"
                        market_info["detailed_market_description"] = "Away or Draw 3-Way Moneyline"
                    else:
                        market_info["market_type"] = "away_3way_moneyline"
                        market_info["market_description"] = "Away (3-Way)"
                        market_info["detailed_market_description"] = "Away Team 3-Way Moneyline"
                elif bet_type_id == "ou":
                    market_info["market_type"] = "team_total_away"
                    market_info["market_description"] = f"Away Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = "team_total_away_even_odd"
                    market_info["market_description"] = f"Away Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = "team_anytime_away"
                    market_info["market_description"] = f"Away Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "all":
                if bet_type_id == "ml3way":
                    # Handle compound side IDs for 3-way moneylines
                    if side_id == "not_draw":
                        market_info["market_type"] = "3way_not_draw"
                        market_info["market_description"] = "Home/Away (3-Way)"
                        market_info["detailed_market_description"] = "Home or Away 3-Way Moneyline"
                    else:
                        market_info["market_type"] = "draw_3way_moneyline"
                        market_info["market_description"] = "Draw (3-Way)"
                        market_info["detailed_market_description"] = "Draw 3-Way Moneyline"
                elif bet_type_id == "ou":
                    market_info["market_type"] = "game_total"
                    market_info["market_description"] = f"Game Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = "game_total_even_odd"
                    market_info["market_description"] = f"Total {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = "anytime_scoring"
                    market_info["market_description"] = f"Anytime {sport_terminology['unit']} Yes/No"
            else:
                # Player prop - extract player name for better description
                player_name = self._extract_player_name(stat_entity_id)
                
                if bet_type_id == "ou":
                    market_info["market_type"] = f"player_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {sport_terminology['unit']}"
                    market_info["detailed_market_description"] = f"{player_name} {sport_terminology['unit']} Over/Under"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"player_{sport_terminology['unit'].lower()}_even_odd"
                    market_info["market_description"] = f"{player_name} {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"player_anytime_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} Anytime {sport_terminology['unit']} Yes/No"
        
        # FOOTBALL PERIOD MARKETS (per SGO docs: halves, quarters, regulation)
        elif stat_id == "points" and (self._is_football_period(period_id) or period_id == "reg"):
            sport_terminology = self._get_sport_terminology(sport)
            period_name = self._get_football_period_name(period_id)
            
            if stat_entity_id == "home":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"football_{period_id}_moneyline_home"
                    market_info["market_description"] = f"{period_name} Moneyline - Home"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"football_{period_id}_spread_home"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"{period_name} Home Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"football_{period_id}_team_total_home"
                    market_info["market_description"] = f"{period_name} Home Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"football_{period_id}_team_total_home_even_odd"
                    market_info["market_description"] = f"{period_name} Home Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"football_{period_id}_team_anytime_home"
                    market_info["market_description"] = f"{period_name} Home Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "away":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"football_{period_id}_moneyline_away"
                    market_info["market_description"] = f"{period_name} Moneyline - Away"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"football_{period_id}_spread_away"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"{period_name} Away Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"football_{period_id}_team_total_away"
                    market_info["market_description"] = f"{period_name} Away Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"football_{period_id}_team_total_away_even_odd"
                    market_info["market_description"] = f"{period_name} Away Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"football_{period_id}_team_anytime_away"
                    market_info["market_description"] = f"{period_name} Away Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "all":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"football_{period_id}_moneyline"
                    market_info["market_description"] = f"{period_name} Moneyline"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"football_{period_id}_spread"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"football_{period_id}_total"
                    market_info["market_description"] = f"{period_name} Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"football_{period_id}_total_even_odd"
                    market_info["market_description"] = f"{period_name} Total {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"football_{period_id}_anytime_scoring"
                    market_info["market_description"] = f"{period_name} Anytime {sport_terminology['unit']} Yes/No"
            else:
                # Player period props for football
                player_name = self._extract_player_name(stat_entity_id)
                if bet_type_id == "ou":
                    market_info["market_type"] = f"football_{period_id}_player_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {period_name} {sport_terminology['unit']}"
                    market_info["detailed_market_description"] = f"{player_name} {period_name} {sport_terminology['unit']} Over/Under"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"football_{period_id}_player_{sport_terminology['unit'].lower()}_even_odd"
                    market_info["market_description"] = f"{player_name} {period_name} {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"football_{period_id}_player_anytime_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {period_name} Anytime {sport_terminology['unit']} Yes/No"
        
        # BASKETBALL PERIOD MARKETS (per SGO docs: halves, quarters, regulation)
        elif stat_id == "points" and self._is_basketball_period(period_id):
            sport_terminology = self._get_sport_terminology(sport)
            period_name = self._get_basketball_period_name(period_id)
            
            if stat_entity_id == "home":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"basketball_{period_id}_moneyline_home"
                    market_info["market_description"] = f"{period_name} Moneyline - Home"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"basketball_{period_id}_spread_home"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"{period_name} Home Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"basketball_{period_id}_team_total_home"
                    market_info["market_description"] = f"{period_name} Home Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"basketball_{period_id}_team_total_home_even_odd"
                    market_info["market_description"] = f"{period_name} Home Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"basketball_{period_id}_team_anytime_home"
                    market_info["market_description"] = f"{period_name} Home Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "away":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"basketball_{period_id}_moneyline_away"
                    market_info["market_description"] = f"{period_name} Moneyline - Away"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"basketball_{period_id}_spread_away"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"{period_name} Away Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"basketball_{period_id}_team_total_away"
                    market_info["market_description"] = f"{period_name} Away Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"basketball_{period_id}_team_total_away_even_odd"
                    market_info["market_description"] = f"{period_name} Away Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"basketball_{period_id}_team_anytime_away"
                    market_info["market_description"] = f"{period_name} Away Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "all":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"basketball_{period_id}_moneyline"
                    market_info["market_description"] = f"{period_name} Moneyline"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"basketball_{period_id}_spread"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"basketball_{period_id}_total"
                    market_info["market_description"] = f"{period_name} Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"basketball_{period_id}_total_even_odd"
                    market_info["market_description"] = f"{period_name} Total {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"basketball_{period_id}_anytime_scoring"
                    market_info["market_description"] = f"{period_name} Anytime {sport_terminology['unit']} Yes/No"
                elif bet_type_id == "ml3way":
                    market_info["market_type"] = f"basketball_{period_id}_3way_moneyline"
                    market_info["market_description"] = f"{period_name} 3-Way Moneyline"
            else:
                # Player period props for basketball
                player_name = self._extract_player_name(stat_entity_id)
                if bet_type_id == "ou":
                    market_info["market_type"] = f"basketball_{period_id}_player_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {period_name} {sport_terminology['unit']}"
                    market_info["detailed_market_description"] = f"{player_name} {period_name} {sport_terminology['unit']} Over/Under"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"basketball_{period_id}_player_{sport_terminology['unit'].lower()}_even_odd"
                    market_info["market_description"] = f"{player_name} {period_name} {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"basketball_{period_id}_player_anytime_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {period_name} Anytime {sport_terminology['unit']} Yes/No"
        
        # BASEBALL PERIOD MARKETS (per SGO docs: ALL period patterns)
        elif stat_id == "points" and self._is_baseball_period(period_id):
            sport_terminology = self._get_sport_terminology(sport)
            period_name = self._get_period_name(period_id)
            
            if stat_entity_id == "home":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"baseball_{period_id}_moneyline_home"
                    market_info["market_description"] = f"{period_name} Moneyline - Home"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"baseball_{period_id}_spread_home"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"{period_name} Home Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"baseball_{period_id}_team_total_home"
                    market_info["market_description"] = f"{period_name} Home Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"baseball_{period_id}_team_total_home_even_odd"
                    market_info["market_description"] = f"{period_name} Home Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"baseball_{period_id}_team_anytime_home"
                    market_info["market_description"] = f"{period_name} Home Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "away":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"baseball_{period_id}_moneyline_away"
                    market_info["market_description"] = f"{period_name} Moneyline - Away"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"baseball_{period_id}_spread_away"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                    market_info["detailed_market_description"] = f"{period_name} Away Team {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"baseball_{period_id}_team_total_away"
                    market_info["market_description"] = f"{period_name} Away Team Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"baseball_{period_id}_team_total_away_even_odd"
                    market_info["market_description"] = f"{period_name} Away Team {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"baseball_{period_id}_team_anytime_away"
                    market_info["market_description"] = f"{period_name} Away Team Anytime {sport_terminology['unit']} Yes/No"
            elif stat_entity_id == "all":
                if bet_type_id == "ml":
                    market_info["market_type"] = f"baseball_{period_id}_moneyline"
                    market_info["market_description"] = f"{period_name} Moneyline"
                elif bet_type_id == "ml3way":
                    market_info["market_type"] = f"baseball_{period_id}_3way_moneyline"
                    market_info["market_description"] = f"{period_name} 3-Way Moneyline"
                elif bet_type_id == "sp":
                    market_info["market_type"] = f"baseball_{period_id}_spread"
                    market_info["market_description"] = f"{period_name} {sport_terminology['spread_name']}"
                elif bet_type_id == "ou":
                    market_info["market_type"] = f"baseball_{period_id}_total"
                    market_info["market_description"] = f"{period_name} Total {sport_terminology['unit']}"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"baseball_{period_id}_total_even_odd"
                    market_info["market_description"] = f"{period_name} Total {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"baseball_{period_id}_anytime_scoring"
                    market_info["market_description"] = f"{period_name} Anytime {sport_terminology['unit']} Yes/No"
            else:
                # Player period props
                player_name = self._extract_player_name(stat_entity_id)
                if bet_type_id == "ou":
                    market_info["market_type"] = f"baseball_{period_id}_player_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {period_name} {sport_terminology['unit']}"
                    market_info["detailed_market_description"] = f"{player_name} {period_name} {sport_terminology['unit']} Over/Under"
                elif bet_type_id == "eo":
                    market_info["market_type"] = f"baseball_{period_id}_player_{sport_terminology['unit'].lower()}_even_odd"
                    market_info["market_description"] = f"{player_name} {period_name} {sport_terminology['unit']} Even/Odd"
                elif bet_type_id == "yn":
                    market_info["market_type"] = f"baseball_{period_id}_player_anytime_{sport_terminology['unit'].lower()}"
                    market_info["market_description"] = f"{player_name} {period_name} Anytime {sport_terminology['unit']} Yes/No"
                
        elif stat_id.startswith("batting_"):
            # Baseball batting props (from SGO baseball docs)
            batting_markets = {
                "batting_hits": "Hits",
                "batting_homeRuns": "Home Runs", 
                "batting_RBI": "RBI",
                "batting_strikeouts": "Strikeouts",
                "batting_basesOnBalls": "Walks",
                "batting_firstHomeRun": "First Home Run",
                "batting_singles": "Singles",
                "batting_doubles": "Doubles", 
                "batting_triples": "Triples",
                "batting_totalBases": "Total Bases",
                "batting_stolenBases": "Stolen Bases",
                "batting_hits+runs+rbi": "Hits + Runs + RBI"
            }
            stat_name = batting_markets.get(stat_id, stat_id.replace("batting_", "").replace("_", " ").title())
            # Extract player name from stat_entity_id (format: PLAYER_NAME_1_MLB)
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = f"player_{stat_id}"
            market_info["market_description"] = f"{player_name} {stat_name}"
            market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        elif stat_id.startswith("pitching_"):
            # Baseball pitching props (from SGO baseball docs)
            pitching_markets = {
                "pitching_strikeouts": "Strikeouts",
                "pitching_basesOnBalls": "Walks Allowed", 
                "pitching_win": "Pitching Win",
                "pitching_runsAllowed": "Runs Allowed",
                "pitching_pitchesThrown": "Pitches Thrown",
                "pitching_homeRunsAllowed": "Home Runs Allowed",
                "pitching_outs": "Outs Recorded",
                "pitching_hits": "Hits Allowed"
            }
            stat_name = pitching_markets.get(stat_id, stat_id.replace("pitching_", "").replace("_", " ").title())
            # Extract player name from stat_entity_id (format: PLAYER_NAME_1_MLB)
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = f"player_{stat_id}"
            market_info["market_description"] = f"{player_name} {stat_name}"
            market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        # ADDITIONAL PITCHING STATS (per SGO docs)
        elif stat_id == "pitching_earnedRuns":
            # Pitching earned runs (team/game/player + all periods)
            if stat_entity_id in ["home", "away"]:
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"team_pitching_earned_runs_{period_id}"
                market_info["market_description"] = f"{stat_entity_id.title()} Team {period_name} Earned Runs".strip()
            elif stat_entity_id == "all":
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"game_pitching_earned_runs_{period_id}"
                market_info["market_description"] = f"{period_name} Total Earned Runs".strip()
            else:
                # Player earned runs
                player_name = self._extract_player_name(stat_entity_id)
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"player_pitching_earned_runs_{period_id}"
                market_info["market_description"] = f"{player_name} {period_name} Earned Runs".strip()
                if bet_type_id == "ou":
                    market_info["detailed_market_description"] = f"{player_name} {period_name} Earned Runs Over/Under".strip()
                    
        elif stat_id == "pitching_outs":
            # Pitching outs (team/game/player + all periods)
            if stat_entity_id in ["home", "away"]:
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"team_pitching_outs_{period_id}"
                market_info["market_description"] = f"{stat_entity_id.title()} Team {period_name} Outs".strip()
            elif stat_entity_id == "all":
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"game_pitching_outs_{period_id}"
                market_info["market_description"] = f"{period_name} Total Outs".strip()
            else:
                # Player outs
                player_name = self._extract_player_name(stat_entity_id)
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"player_pitching_outs_{period_id}"
                market_info["market_description"] = f"{player_name} {period_name} Outs".strip()
                if bet_type_id == "ou":
                    market_info["detailed_market_description"] = f"{player_name} {period_name} Outs Over/Under".strip()
                    
        elif stat_id == "pitching_hits":
            # Pitching hits allowed (all periods supported)
            if stat_entity_id in ["home", "away"]:
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"team_pitching_hits_{period_id}"
                market_info["market_description"] = f"{stat_entity_id.title()} Team {period_name} Hits Allowed".strip()
            elif stat_entity_id == "all":
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"game_pitching_hits_{period_id}"
                market_info["market_description"] = f"{period_name} Total Hits Allowed".strip()
            else:
                # Player hits allowed
                player_name = self._extract_player_name(stat_entity_id)
                period_name = self._get_period_name(period_id) if period_id != "game" else ""
                market_info["market_type"] = f"player_pitching_hits_{period_id}"
                market_info["market_description"] = f"{player_name} {period_name} Hits Allowed".strip()
                if bet_type_id == "ou":
                    market_info["detailed_market_description"] = f"{player_name} {period_name} Hits Allowed Over/Under".strip()
        
        # COMPREHENSIVE BASEBALL STAT HANDLER (for any remaining stats from SGO docs)
        elif self._is_baseball_stat(stat_id):
            # Handle any baseball stat using dynamic approach
            market_info.update(self._parse_baseball_stat(stat_id, stat_entity_id, period_id, bet_type_id))
            
        elif stat_id == "fantasyScore":
            # Fantasy score props (per SGO baseball docs)
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = "player_fantasy_score"
            market_info["market_description"] = f"{player_name} Fantasy Score"
            market_info["detailed_market_description"] = f"{player_name} Fantasy Score Over/Under"
            
        elif stat_id in ["firstToScore", "lastToScore"]:
            # Special scoring markets (per SGO baseball docs) 
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = f"player_{stat_id}"
            if stat_id == "firstToScore":
                market_info["market_description"] = f"{player_name} First Run"
            else:  # lastToScore
                market_info["market_description"] = f"{player_name} Last Run"
            
        # FOOTBALL/AMERICAN FOOTBALL MARKETS (NFL, NCAAF, CFL)
        elif stat_id.startswith("passing_"):
            # Football passing props (with period support)
            stat_name = stat_id.replace("passing_", "").replace("_", " ").title()
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_passing"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        elif stat_id.startswith("rushing_"):
            # Football rushing props (with period support)
            stat_name = stat_id.replace("rushing_", "").replace("_", " ").title()
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_rushing"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        elif stat_id.startswith("receiving_"):
            # Football receiving props (with period support)
            stat_name = stat_id.replace("receiving_", "").replace("_", " ").title()
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_receiving"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        elif stat_id.startswith("fieldGoals_") or stat_id.startswith("extraPoints_"):
            # Football kicking props (field goals, extra points)
            if stat_id.startswith("fieldGoals_"):
                stat_name = stat_id.replace("fieldGoals_", "Field Goals ").replace("_", " ").title()
            else:
                stat_name = stat_id.replace("extraPoints_", "Extra Points ").replace("_", " ").title()
                
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_kicking"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        # ADDITIONAL FOOTBALL STATS (Defense, Special Teams, etc.)
        elif stat_id.startswith("defense_"):
            # Football defensive props (tackles, sacks, interceptions, etc.)
            stat_name = stat_id.replace("defense_", "").replace("_", " ").title()
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_defense"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
                
        elif stat_id in ["anytimeTouchdown", "anytime_touchdown", "firstTouchdown", "first_touchdown", "lastTouchdown", "last_touchdown"]:
            # Football touchdown props
            player_name = self._extract_player_name(stat_entity_id)
            
            if "anytime" in stat_id.lower():
                touchdown_type = "Anytime Touchdown"
            elif "first" in stat_id.lower():
                touchdown_type = "First Touchdown"
            else:
                touchdown_type = "Last Touchdown"
                
            market_info["market_type"] = f"player_touchdown_{touchdown_type.lower().replace(' ', '_')}"
            market_info["market_description"] = f"{player_name} {touchdown_type}"
            market_info["detailed_market_description"] = f"{player_name} {touchdown_type} Yes/No"
            
        elif stat_id.startswith("punting_") or stat_id.startswith("kickReturns_") or stat_id.startswith("puntReturns_"):
            # Football special teams props
            if stat_id.startswith("punting_"):
                stat_name = stat_id.replace("punting_", "Punting ").replace("_", " ").title()
            elif stat_id.startswith("kickReturns_"):
                stat_name = stat_id.replace("kickReturns_", "Kick Return ").replace("_", " ").title()
            else:
                stat_name = stat_id.replace("puntReturns_", "Punt Return ").replace("_", " ").title()
                
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_special_teams"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        # COMPREHENSIVE FOOTBALL STATS (from complete SGO football docs verification)
        elif stat_id in ["turnovers", "passing_touchdowns", "rushing_touchdowns", "receiving_touchdowns", 
                         "defense_interceptions", "defense_sacks", "defense_tackles", "fumbles",
                         "fieldGoals_made", "extraPoints_kicksMade", "kicking_totalPoints", "fantasyScore",
                         "passing_completions", "passing_attempts", "passing_interceptions", "rushing_attempts",
                         "rushing_longestRush", "receiving_longestReception", "receiving_targets",
                         "anytimeTouchdown", "firstTouchdown", "lastTouchdown", "punting_yards", 
                         "punting_attempts", "kickReturns_yards", "kickReturns_attempts", "puntReturns_yards",
                         "puntReturns_attempts", "fumbles_lost", "fumbles_recovered", "combinedTackles", 
                         "combined_tackles", "totalTackles", "total_tackles", "assistedTackles", "soloTackles",
                         # Additional football stats from SGO documentation verification
                         "passing_longest", "passing_rating", "passing_sacked", "rushing_longest", 
                         "receiving_longest", "defense_forcedFumbles", "defense_fumbleRecoveries",
                         "defense_passDeflections", "defense_qbHits", "defense_safeties", "defense_tfl",
                         "kicking_fieldGoalAttempts", "kicking_extraPointAttempts", "kicking_longest",
                         # MISSING FROM SGO FOOTBALL DOCS - Adding these critical stats:
                         "fieldGoals_attempted", "fieldGoals_longest", "extraPoints_attempted",
                         "punting_longest", "punting_average", "kickReturns_longest", "kickReturns_touchdowns",
                         "puntReturns_longest", "puntReturns_touchdowns", "defense_tackles_for_loss",
                         "defense_quarterback_hits", "defense_passes_defended", "defense_fumbles_forced",
                         "defense_fumbles_recovered", "kicking_points", "fumbles_forced", "fumbles_recoveries",
                         # Combined stats that are commonly found in SGO data
                         "passing+rushing_yards", "rushing+receiving_yards", "touchdowns"]:
            # Football individual stats (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            # Clean up stat name
            if stat_id == "passing_touchdowns":
                stat_name = "Passing Touchdowns"
            elif stat_id == "rushing_touchdowns":
                stat_name = "Rushing Touchdowns"
            elif stat_id == "receiving_touchdowns":
                stat_name = "Receiving Touchdowns"
            elif stat_id == "defense_interceptions":
                stat_name = "Interceptions"
            elif stat_id == "defense_sacks":
                stat_name = "Sacks"
            elif stat_id == "defense_tackles":
                stat_name = "Tackles"
            elif stat_id == "fieldGoals_made":
                stat_name = "Field Goals Made"
            elif stat_id == "extraPoints_kicksMade":
                stat_name = "Extra Points Made"
            elif stat_id == "kicking_totalPoints":
                stat_name = "Kicking Total Points"
            elif stat_id == "fantasyScore":
                stat_name = "Fantasy Score"
            elif stat_id == "passing_completions":
                stat_name = "Passing Completions"
            elif stat_id == "passing_attempts":
                stat_name = "Passing Attempts"
            elif stat_id == "passing_interceptions":
                stat_name = "Passing Interceptions"
            elif stat_id == "rushing_attempts":
                stat_name = "Rushing Attempts"
            elif stat_id == "rushing_longestRush":
                stat_name = "Longest Rush"
            elif stat_id == "receiving_longestReception":
                stat_name = "Longest Reception"
            elif stat_id == "receiving_targets":
                stat_name = "Targets"
            elif stat_id == "anytimeTouchdown":
                stat_name = "Anytime Touchdown"
            elif stat_id == "firstTouchdown":
                stat_name = "First Touchdown"
            elif stat_id == "lastTouchdown":
                stat_name = "Last Touchdown"
            elif stat_id == "punting_yards":
                stat_name = "Punting Yards"
            elif stat_id == "punting_attempts":
                stat_name = "Punting Attempts"
            elif stat_id == "kickReturns_yards":
                stat_name = "Kick Return Yards"
            elif stat_id == "kickReturns_attempts":
                stat_name = "Kick Return Attempts"
            elif stat_id == "puntReturns_yards":
                stat_name = "Punt Return Yards"
            elif stat_id == "puntReturns_attempts":
                stat_name = "Punt Return Attempts"
            elif stat_id == "fumbles_lost":
                stat_name = "Fumbles Lost"
            elif stat_id == "fumbles_recovered":
                stat_name = "Fumbles Recovered"
            elif stat_id in ["combinedTackles", "combined_tackles"]:
                stat_name = "Combined Tackles"
            elif stat_id in ["totalTackles", "total_tackles"]:
                stat_name = "Total Tackles"
            elif stat_id == "assistedTackles":
                stat_name = "Assisted Tackles"
            elif stat_id == "soloTackles":
                stat_name = "Solo Tackles"
            elif stat_id == "passing_longest":
                stat_name = "Longest Pass"
            elif stat_id == "passing_rating":
                stat_name = "Passer Rating"
            elif stat_id == "passing_sacked":
                stat_name = "Times Sacked"
            elif stat_id == "rushing_longest":
                stat_name = "Longest Rush"
            elif stat_id == "receiving_longest":
                stat_name = "Longest Reception"
            elif stat_id == "defense_forcedFumbles":
                stat_name = "Forced Fumbles"
            elif stat_id == "defense_fumbleRecoveries":
                stat_name = "Fumble Recoveries"
            elif stat_id == "defense_passDeflections":
                stat_name = "Pass Deflections"
            elif stat_id == "defense_qbHits":
                stat_name = "QB Hits"
            elif stat_id == "defense_safeties":
                stat_name = "Safeties"
            elif stat_id == "defense_tfl":
                stat_name = "Tackles for Loss"
            elif stat_id == "kicking_fieldGoalAttempts":
                stat_name = "Field Goal Attempts"
            elif stat_id == "kicking_extraPointAttempts":
                stat_name = "Extra Point Attempts"
            elif stat_id == "kicking_longest":
                stat_name = "Longest Field Goal"
            elif stat_id == "passing+rushing_yards":
                stat_name = "Passing + Rushing Yards"
            elif stat_id == "rushing+receiving_yards":
                stat_name = "Rushing + Receiving Yards"
            elif stat_id == "touchdowns":
                stat_name = "Total Touchdowns"
            elif stat_id == "fieldGoals_attempted":
                stat_name = "Field Goal Attempts"
            elif stat_id == "fieldGoals_longest":
                stat_name = "Longest Field Goal"
            elif stat_id == "extraPoints_attempted":
                stat_name = "Extra Point Attempts"
            elif stat_id == "punting_longest":
                stat_name = "Longest Punt"
            elif stat_id == "punting_average":
                stat_name = "Punting Average"
            elif stat_id == "kickReturns_longest":
                stat_name = "Longest Kick Return"
            elif stat_id == "kickReturns_touchdowns":
                stat_name = "Kick Return Touchdowns"
            elif stat_id == "puntReturns_longest":
                stat_name = "Longest Punt Return"
            elif stat_id == "puntReturns_touchdowns":
                stat_name = "Punt Return Touchdowns"
            elif stat_id == "defense_tackles_for_loss":
                stat_name = "Tackles for Loss"
            elif stat_id == "defense_quarterback_hits":
                stat_name = "QB Hits"
            elif stat_id == "defense_passes_defended":
                stat_name = "Passes Defended"
            elif stat_id == "defense_fumbles_forced":
                stat_name = "Fumbles Forced"
            elif stat_id == "defense_fumbles_recovered":
                stat_name = "Fumbles Recovered"
            elif stat_id == "kicking_points":
                stat_name = "Kicking Points"
            elif stat_id == "fumbles_forced":
                stat_name = "Fumbles Forced"
            elif stat_id == "fumbles_recoveries":
                stat_name = "Fumble Recoveries"
            else:
                stat_name = stat_id.replace("_", " ").title()
            
            if self._is_football_period(period_id):
                period_name = self._get_football_period_name(period_id)
                market_info["market_type"] = f"football_{period_id}_player_{stat_id.replace('_', '')}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        # BASKETBALL MARKETS
        elif stat_id in ["assists", "rebounds", "steals", "blocks"]:
            # Basketball basic stats
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = f"team_{stat_id}"
                market_info["market_description"] = f"{stat_entity_id.title()} Team {stat_id.title()}" if stat_entity_id != "all" else f"Game {stat_id.title()}"
            else:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"Player {stat_id.title()}"
                
        elif stat_id.startswith("threePointers"):
            # Basketball 3-pointer props
            stat_name = stat_id.replace("threePointers", "Three Pointers ").replace("Made", "Made").replace("Attempted", "Attempted")
            market_info["market_type"] = f"player_{stat_id}"
            market_info["market_description"] = f"Player {stat_name}"
            
        elif stat_id.startswith("freeThrows"):
            # Basketball free throw props
            stat_name = stat_id.replace("freeThrows", "Free Throws ").replace("Made", "Made").replace("Attempted", "Attempted")
            market_info["market_type"] = f"player_{stat_id}"
            market_info["market_description"] = f"Player {stat_name}"

        # BASKETBALL COMBINATION STATS (from SGO Basketball docs)
        elif stat_id == "points+assists":
            market_info["market_type"] = "player_points_assists"
            market_info["market_description"] = f"Player Points + Assists - {stat_entity_id}"

        elif stat_id == "points+rebounds":
            market_info["market_type"] = "player_points_rebounds"
            market_info["market_description"] = f"Player Points + Rebounds - {stat_entity_id}"

        elif stat_id == "rebounds+assists":
            market_info["market_type"] = "player_rebounds_assists"
            market_info["market_description"] = f"Player Rebounds + Assists - {stat_entity_id}"

        elif stat_id == "points+rebounds+assists":
            market_info["market_type"] = "player_triple_double_stats"
            market_info["market_description"] = f"Player Points + Rebounds + Assists - {stat_entity_id}"

        elif stat_id == "blocks+steals":
            market_info["market_type"] = "player_blocks_steals"
            market_info["market_description"] = f"Player Blocks + Steals - {stat_entity_id}"

        # BASKETBALL SPECIAL MARKETS
        elif stat_id == "doubleDouble":
            market_info["market_type"] = "player_double_double"
            market_info["market_description"] = f"Player Double-Double - {stat_entity_id}"

        elif stat_id == "tripleDouble":
            market_info["market_type"] = "player_triple_double"
            market_info["market_description"] = f"Player Triple-Double - {stat_entity_id}"

        elif stat_id == "firstBasket":
            market_info["market_type"] = "player_first_basket"
            market_info["market_description"] = f"Player First Basket - {stat_entity_id}"

        elif stat_id == "minutesPlayed":
            market_info["market_type"] = "player_minutes"
            market_info["market_description"] = f"Player Minutes Played - {stat_entity_id}"

        # FOOTBALL MARKETS (NFL/NCAAF from SGO Football docs)
        elif stat_id in ["passing_yards", "passingYards"]:
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = "team_passing_yards"
                market_info["market_description"] = f"{stat_entity_id.title()} Team Passing Yards" if stat_entity_id != "all" else "Game Passing Yards"
            else:
                market_info["market_type"] = "player_passing_yards"
                market_info["market_description"] = f"Player Passing Yards - {stat_entity_id}"

        elif stat_id in ["rushing_yards", "rushingYards"]:
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = "team_rushing_yards"
                market_info["market_description"] = f"{stat_entity_id.title()} Team Rushing Yards" if stat_entity_id != "all" else "Game Rushing Yards"
            else:
                market_info["market_type"] = "player_rushing_yards"
                market_info["market_description"] = f"Player Rushing Yards - {stat_entity_id}"

        elif stat_id in ["receiving_yards", "receivingYards"]:
            market_info["market_type"] = "player_receiving_yards"
            market_info["market_description"] = f"Player Receiving Yards - {stat_entity_id}"

        elif stat_id in ["passing_touchdowns", "passingTouchdowns", "passing_tds"]:
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = "team_passing_touchdowns"
                market_info["market_description"] = f"{stat_entity_id.title()} Team Passing TDs" if stat_entity_id != "all" else "Game Passing TDs"
            else:
                market_info["market_type"] = "player_passing_touchdowns"
                market_info["market_description"] = f"Player Passing TDs - {stat_entity_id}"

        elif stat_id in ["rushing_touchdowns", "rushingTouchdowns", "rushing_tds"]:
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = "team_rushing_touchdowns"
                market_info["market_description"] = f"{stat_entity_id.title()} Team Rushing TDs" if stat_entity_id != "all" else "Game Rushing TDs"
            else:
                market_info["market_type"] = "player_rushing_touchdowns"
                market_info["market_description"] = f"Player Rushing TDs - {stat_entity_id}"

        elif stat_id in ["receiving_touchdowns", "receivingTouchdowns", "receiving_tds"]:
            market_info["market_type"] = "player_receiving_touchdowns"
            market_info["market_description"] = f"Player Receiving TDs - {stat_entity_id}"

        elif stat_id in ["receptions", "receiving_receptions"]:
            market_info["market_type"] = "player_receptions"
            market_info["market_description"] = f"Player Receptions - {stat_entity_id}"

        elif stat_id in ["passing_completions", "passingCompletions"]:
            market_info["market_type"] = "player_passing_completions"
            market_info["market_description"] = f"Player Passing Completions - {stat_entity_id}"

        elif stat_id in ["passing_attempts", "passingAttempts"]:
            market_info["market_type"] = "player_passing_attempts"
            market_info["market_description"] = f"Player Passing Attempts - {stat_entity_id}"

        elif stat_id in ["rushing_attempts", "rushingAttempts"]:
            market_info["market_type"] = "player_rushing_attempts"
            market_info["market_description"] = f"Player Rushing Attempts - {stat_entity_id}"

        elif stat_id in ["interceptions", "passing_interceptions"]:
            market_info["market_type"] = "player_interceptions"
            market_info["market_description"] = f"Player Interceptions - {stat_entity_id}"

        # FOOTBALL COMBINATION STATS
        elif stat_id in ["passing_yards+touchdowns", "passing_yards+rushing_yards"]:
            stat_parts = stat_id.split('+')
            market_info["market_type"] = f"player_{'_'.join(stat_parts)}"
            readable_parts = [part.replace('_', ' ').title() for part in stat_parts]
            market_info["market_description"] = f"Player {' + '.join(readable_parts)} - {stat_entity_id}"

        elif stat_id in ["rushing_yards+touchdowns", "receiving_yards+touchdowns"]:
            stat_parts = stat_id.split('+')
            market_info["market_type"] = f"player_{'_'.join(stat_parts)}"
            readable_parts = [part.replace('_', ' ').title() for part in stat_parts]
            market_info["market_description"] = f"Player {' + '.join(readable_parts)} - {stat_entity_id}"

        # FOOTBALL SPECIAL MARKETS
        elif stat_id in ["anytime_touchdown", "anytimeTouchdown", "first_touchdown", "firstTouchdown"]:
            market_type = stat_id.replace("anytime", "anytime").replace("first", "first").replace("Touchdown", "_touchdown")
            market_info["market_type"] = f"player_{market_type}"
            market_info["market_description"] = f"Player {stat_id.replace('_', ' ').replace('Touchdown', ' TD').title()} - {stat_entity_id}"

        elif stat_id in ["field_goals", "fieldGoals", "field_goals_made", "fieldGoals_made"]:
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = "team_field_goals"
                market_info["market_description"] = f"{stat_entity_id.title()} Team Field Goals" if stat_entity_id != "all" else "Game Field Goals"
            else:
                market_info["market_type"] = "player_field_goals"
                market_info["market_description"] = f"Player Field Goals - {stat_entity_id}"

        # FOOTBALL ADVANCED MARKETS (from SGO Football docs)
        elif stat_id in ["defense_interceptions", "defenseInterceptions"]:
            # Extract player name from stat_entity_id (format: PLAYER_NAME_1_NFL)
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = "player_defense_interceptions"
            market_info["market_description"] = f"{player_name} Defensive Interceptions"
            market_info["detailed_market_description"] = f"{player_name} Defensive Interceptions Over/Under"
            
        elif stat_id in ["defense_sacks", "defenseSacks"]:
            # Extract player name from stat_entity_id (format: PLAYER_NAME_1_NFL)
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = "defense_sacks"
            market_info["market_description"] = f"{player_name} Sacks"
            market_info["detailed_market_description"] = f"{player_name} Sacks Over/Under"

        elif stat_id in ["extraPoints_kicksMade", "extraPointsKicksMade", "extra_points"]:
            # Extract player name from stat_entity_id (format: PLAYER_NAME_1_NFL)
            player_name = self._extract_player_name(stat_entity_id)
            market_info["market_type"] = "player_extra_points"
            market_info["market_description"] = f"{player_name} Extra Points Made"
            market_info["detailed_market_description"] = f"{player_name} Extra Points Made Over/Under"

        elif stat_id in ["kicking_totalPoints", "kickingTotalPoints"]:
            market_info["market_type"] = "player_kicking_points"
            market_info["market_description"] = f"Player Kicking Total Points - {stat_entity_id}"

        elif stat_id in ["turnovers"]:
            if stat_entity_id in ["home", "away", "all"]:
                market_info["market_type"] = "team_turnovers"
                market_info["market_description"] = f"{stat_entity_id.title()} Team Turnovers" if stat_entity_id != "all" else "Game Turnovers"
            else:
                market_info["market_type"] = "player_turnovers"
                market_info["market_description"] = f"Player Turnovers - {stat_entity_id}"

        # HANDBALL MARKETS (from SGO Handball docs)
        # Handball uses "points" statID but represents goals in the sport
        elif sport == "HANDBALL" and stat_id == "points":
            if bet_type_id == "ml":
                # Moneyline
                if stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = "handball_moneyline"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Moneyline"
            elif bet_type_id == "sp":
                # Spread (Goal difference)
                if stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = "handball_spread"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Spread"
            elif bet_type_id == "ou":
                # Over/Under Goals
                if stat_entity_id == "all":
                    market_info["market_type"] = "handball_total_goals"
                    market_info["market_description"] = "Total Goals Over/Under"
                elif stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = "handball_team_goals"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Goals Over/Under"
            elif bet_type_id == "eo":
                # Even/Odd Goals
                if stat_entity_id == "all":
                    market_info["market_type"] = "handball_total_goals_even_odd"
                    market_info["market_description"] = "Total Goals Even/Odd"
                elif stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = "handball_team_goals_even_odd"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Goals Even/Odd"
            elif bet_type_id == "yn":
                # Yes/No Anytime Goals
                if stat_entity_id == "all":
                    market_info["market_type"] = "handball_anytime_goals"
                    market_info["market_description"] = "Anytime Goals Yes/No"
                elif stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = "handball_team_anytime_goals"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Anytime Goals Yes/No"

        # HANDBALL PERIOD MARKETS (1st Half, 2nd Half)
        elif sport == "HANDBALL" and stat_id == "points" and period_id in ["1h", "2h"]:
            period_name = "1st Half" if period_id == "1h" else "2nd Half"
            if bet_type_id == "ml":
                market_info["market_type"] = f"handball_{period_id}_moneyline"
                market_info["market_description"] = f"{period_name} Moneyline"
            elif bet_type_id == "sp":
                market_info["market_type"] = f"handball_{period_id}_spread"
                market_info["market_description"] = f"{period_name} Spread"
            elif bet_type_id == "ou":
                if stat_entity_id == "all":
                    market_info["market_type"] = f"handball_{period_id}_total_goals"
                    market_info["market_description"] = f"{period_name} Total Goals Over/Under"
                elif stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = f"handball_{period_id}_team_goals"
                    market_info["market_description"] = f"{period_name} {stat_entity_id.title()} Team Goals Over/Under"

        # HOCKEY MARKETS (from SGO Hockey docs)
        # Hockey uses "points" statID but represents goals in the sport
        elif sport == "HOCKEY" and stat_id == "points":
            if bet_type_id == "ml":
                # Moneyline (includes regulation and full game)
                if period_id == "reg":
                    market_info["market_type"] = "hockey_regulation_moneyline"
                    market_info["market_description"] = f"Regulation Moneyline - {stat_entity_id.title()}"
                else:
                    market_info["market_type"] = "hockey_moneyline"
                    market_info["market_description"] = f"Moneyline - {stat_entity_id.title()}"
            elif bet_type_id == "sp":
                # Spread (Puck line)
                if period_id == "reg":
                    market_info["market_type"] = "hockey_regulation_spread"
                    market_info["market_description"] = f"Regulation Puck Line - {stat_entity_id.title()}"
                else:
                    market_info["market_type"] = "hockey_spread"
                    market_info["market_description"] = f"Puck Line - {stat_entity_id.title()}"
            elif bet_type_id == "ou":
                # Over/Under Goals
                if period_id == "reg":
                    if stat_entity_id == "all":
                        market_info["market_type"] = "hockey_regulation_total_goals"
                        market_info["market_description"] = "Regulation Total Goals Over/Under"
                    elif stat_entity_id in ["home", "away"]:
                        market_info["market_type"] = "hockey_regulation_team_goals"
                        market_info["market_description"] = f"Regulation {stat_entity_id.title()} Team Goals Over/Under"
                    else:
                        # Player regulation goals
                        market_info["market_type"] = "hockey_player_regulation_goals"
                        market_info["market_description"] = f"Player Regulation Goals - {stat_entity_id}"
                else:
                    if stat_entity_id == "all":
                        market_info["market_type"] = "hockey_total_goals"
                        market_info["market_description"] = "Total Goals Over/Under"
                    elif stat_entity_id in ["home", "away"]:
                        market_info["market_type"] = "hockey_team_goals"
                        market_info["market_description"] = f"{stat_entity_id.title()} Team Goals Over/Under"
                    else:
                        # Player goals
                        market_info["market_type"] = "hockey_player_goals"
                        market_info["market_description"] = f"Player Goals - {stat_entity_id}"

        # HOCKEY PLAYER PROPS (from SGO Hockey docs)
        elif sport == "HOCKEY" and stat_id in ["shots", "hits", "blocks", "faceOffs_won", "goalie_goalsAgainst", "minutesPlayed"]:
            if stat_id == "shots":
                market_info["market_type"] = "hockey_player_shots"
                market_info["market_description"] = f"Player Shots - {stat_entity_id}"
            elif stat_id == "hits":
                market_info["market_type"] = "hockey_player_hits"
                market_info["market_description"] = f"Player Hits - {stat_entity_id}"
            elif stat_id == "blocks":
                market_info["market_type"] = "hockey_player_blocked_shots"
                market_info["market_description"] = f"Player Blocked Shots - {stat_entity_id}"
            elif stat_id == "faceOffs_won":
                market_info["market_type"] = "hockey_player_faceoffs_won"
                market_info["market_description"] = f"Player Faceoffs Won - {stat_entity_id}"
            elif stat_id == "goalie_goalsAgainst":
                market_info["market_type"] = "hockey_goalie_goals_against"
                market_info["market_description"] = f"Goalie Goals Against - {stat_entity_id}"
            elif stat_id == "minutesPlayed":
                market_info["market_type"] = "hockey_player_minutes"
                market_info["market_description"] = f"Player Minutes Played - {stat_entity_id}"

        # HOCKEY SPECIAL MARKETS
        elif sport == "HOCKEY" and stat_id in ["firstToScore", "lastToScore", "powerPlay_goals+assists"]:
            if stat_id == "firstToScore":
                market_info["market_type"] = "hockey_player_first_goal"
                market_info["market_description"] = f"Player First Goal - {stat_entity_id}"
            elif stat_id == "lastToScore":
                market_info["market_type"] = "hockey_player_last_goal"
                market_info["market_description"] = f"Player Last Goal - {stat_entity_id}"
            elif stat_id == "powerPlay_goals+assists":
                market_info["market_type"] = "hockey_player_powerplay_points"
                market_info["market_description"] = f"Player Power-Play Points - {stat_entity_id}"

        # HOCKEY PERIOD MARKETS (1st, 2nd, 3rd periods)
        elif sport == "HOCKEY" and stat_id == "points" and period_id in ["1p", "2p", "3p"]:
            period_name = f"{period_id[0]}{'st' if period_id[0] == '1' else 'nd' if period_id[0] == '2' else 'rd'} Period"
            if bet_type_id == "ml":
                market_info["market_type"] = f"hockey_{period_id}_moneyline"
                market_info["market_description"] = f"{period_name} Moneyline"
            elif bet_type_id == "sp":
                market_info["market_type"] = f"hockey_{period_id}_spread"
                market_info["market_description"] = f"{period_name} Puck Line"
            elif bet_type_id == "ou":
                if stat_entity_id == "all":
                    market_info["market_type"] = f"hockey_{period_id}_total_goals"
                    market_info["market_description"] = f"{period_name} Total Goals Over/Under"
                elif stat_entity_id in ["home", "away"]:
                    market_info["market_type"] = f"hockey_{period_id}_team_goals"
                    market_info["market_description"] = f"{period_name} {stat_entity_id.title()} Team Goals Over/Under"
            
        # COMPREHENSIVE SOCCER MARKETS (per SGO soccer docs)
        # Handle soccer "points" markets (which are actually "goals" in soccer)
        # Player goals markets vs Game totals with player references
        elif stat_id == "points" and stat_entity_id not in ["home", "away", "all"] and self._is_soccer_sport(sport):
            # CRITICAL FIX: Some SGO soccer markets use player-like entity IDs for game totals
            # Need to differentiate between actual player props and game totals with player references
            
            # Check if this looks like a total goals market with a player reference (common in soccer)
            if "_LA_LIGA" in stat_entity_id or "_" in stat_entity_id and len(stat_entity_id.split("_")) >= 3:
                # This appears to be a game total with a player/league reference, not an actual player prop
                terminology = self._get_sport_terminology(sport)
                unit = terminology['unit']  # "Goals" for soccer
                
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    market_info["market_type"] = f"soccer_{period_id}_game_total"
                    market_info["market_description"] = f"{period_name} Total {unit} Over/Under"
                else:
                    market_info["market_type"] = "soccer_game_total"
                    market_info["market_description"] = f"Game Total {unit}"
                    market_info["detailed_market_description"] = f"Game Total {unit} Over/Under"
                    
                logger.info(f"🔍 SOCCER FIX: Corrected market classification from player to game total for {stat_entity_id}")
            else:
                # This is likely an actual player goals market
                player_name = self._extract_player_name(stat_entity_id)
                
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    market_info["market_type"] = f"soccer_{period_id}_player_goals"
                    market_info["market_description"] = f"{player_name} {period_name} Goals"
                    market_info["detailed_market_description"] = f"{player_name} {period_name} Goals Over/Under"
                else:
                    market_info["market_type"] = "soccer_player_goals"
                    market_info["market_description"] = f"{player_name} Goals"
                    market_info["detailed_market_description"] = f"{player_name} Goals Over/Under"
        
        # SOCCER PLAYER PROPS (comprehensive from SGO soccer docs)
        elif stat_id == "assists" and self._is_soccer_sport(sport):
            # Soccer assists (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_assists"
                market_info["market_description"] = f"{player_name} {period_name} Assists"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Assists Over/Under"
            else:
                market_info["market_type"] = "soccer_player_assists"
                market_info["market_description"] = f"{player_name} Assists"
                market_info["detailed_market_description"] = f"{player_name} Assists Over/Under"
        
        elif stat_id in ["shots", "shotsOnTarget", "shotsOffTarget", "shots_onGoal", "shots_onTarget", "attempts"] and self._is_soccer_sport(sport):
            # Soccer shots props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            if stat_id == "shots":
                stat_name = "Shots"
            elif stat_id in ["shotsOnTarget", "shots_onTarget", "shots_onGoal"]:
                stat_name = "Shots on Target"
            elif stat_id == "attempts":
                stat_name = "Shot Attempts"
            else:
                stat_name = "Shots off Target"
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"soccer_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        elif stat_id in ["corners", "cornerKicks"] and self._is_soccer_sport(sport):
            # Soccer corners/corner kicks (with period support) - handles both team and player
            
            if stat_entity_id in ["home", "away", "all"]:
                # TEAM-LEVEL CORNER MARKETS (per SGO soccer docs)
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_corners"
                        market_info["market_description"] = f"{period_name} Home Team Corners Over/Under"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_corners"
                        market_info["market_description"] = f"{period_name} Away Team Corners Over/Under"
                    else:  # all
                        market_info["market_type"] = f"soccer_{period_id}_total_corners"
                        market_info["market_description"] = f"{period_name} Total Corners Over/Under"
                else:
                    # Full match team corner markets
                    if stat_entity_id == "home":
                        market_info["market_type"] = "soccer_home_corners"
                        market_info["market_description"] = "Home Team Corners Over/Under"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = "soccer_away_corners"
                        market_info["market_description"] = "Away Team Corners Over/Under"
                    else:  # all
                        market_info["market_type"] = "soccer_total_corners"
                        market_info["market_description"] = "Total Corners Over/Under"
            else:
                # PLAYER-LEVEL CORNER MARKETS
                player_name = self._extract_player_name(stat_entity_id)
                
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    market_info["market_type"] = f"soccer_{period_id}_player_corners"
                    market_info["market_description"] = f"{player_name} {period_name} Corners"
                    market_info["detailed_market_description"] = f"{player_name} {period_name} Corners Over/Under"
                else:
                    market_info["market_type"] = "soccer_player_corners"
                    market_info["market_description"] = f"{player_name} Corners"
                    market_info["detailed_market_description"] = f"{player_name} Corners Over/Under"
        
        elif stat_id in ["passes", "passes_attempted", "passes_successful", "crosses", "dribbles", "dribbles_attempted", "passes_completed", 
                         "crosses_completed", "dribbles_completed", "clearances", "shots_assisted", "passes_accurate"] and self._is_soccer_sport(sport):
            # Soccer passing/crossing/dribbling/clearances props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            if stat_id == "dribbles_attempted":
                stat_name = "Dribbles Attempted"
            elif stat_id == "passes_attempted":
                stat_name = "Passes Attempted"
            elif stat_id == "passes_successful":
                stat_name = "Successful Passes"
            elif stat_id == "passes_accurate":
                stat_name = "Accurate Passes"
            elif stat_id == "passes_completed":
                stat_name = "Passes Completed"
            elif stat_id == "crosses_completed":
                stat_name = "Crosses Completed"
            elif stat_id == "dribbles_completed":
                stat_name = "Dribbles Completed"
            elif stat_id == "clearances":
                stat_name = "Clearances"
            elif stat_id == "shots_assisted":
                stat_name = "Shots Assisted"
            else:
                stat_name = stat_id.title()
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
                logger.debug(f"⚽ BASIC SOCCER MARKET: {odd_id} -> {market_info['market_type']}")
            else:
                market_info["market_type"] = f"soccer_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
                logger.debug(f"⚽ BASIC SOCCER MARKET: {odd_id} -> {market_info['market_type']}")
        
        elif stat_id in ["tackles", "interceptions", "blocks"] and self._is_soccer_sport(sport):
            # Soccer defensive props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            stat_name = stat_id.title()
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"soccer_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        elif stat_id in ["fouls", "foulsDrawn", "foulsCommitted"] and self._is_soccer_sport(sport):
            # Soccer fouls props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            if stat_id == "fouls":
                stat_name = "Fouls"
            elif stat_id == "foulsDrawn":
                stat_name = "Fouls Drawn"
            else:
                stat_name = "Fouls Committed"
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"soccer_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        elif stat_id in ["yellowCards", "redCards", "combinedCards", "weightedCards"] and self._is_soccer_sport(sport):
            # Soccer cards props (with period support) - handles BOTH team and player cards
            
            if stat_entity_id in ["home", "away", "all"]:
                # TEAM-LEVEL CARD MARKETS (per SGO soccer docs)
                if stat_id == "yellowCards":
                    stat_name = "Yellow Cards"
                elif stat_id == "redCards":
                    stat_name = "Red Cards"
                elif stat_id == "combinedCards":
                    stat_name = "Total Cards"
                else:
                    stat_name = "Weighted Cards"
                
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_{period_id}_home_{stat_id}"
                        market_info["market_description"] = f"{period_name} Home Team {stat_name} Over/Under"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_{period_id}_away_{stat_id}"
                        market_info["market_description"] = f"{period_name} Away Team {stat_name} Over/Under"
                    else:  # all
                        market_info["market_type"] = f"soccer_{period_id}_total_{stat_id}"
                        market_info["market_description"] = f"{period_name} Total {stat_name} Over/Under"
                else:
                    # Full match team card markets
                    if stat_entity_id == "home":
                        market_info["market_type"] = f"soccer_home_{stat_id}"
                        market_info["market_description"] = f"Home Team {stat_name} Over/Under"
                    elif stat_entity_id == "away":
                        market_info["market_type"] = f"soccer_away_{stat_id}"
                        market_info["market_description"] = f"Away Team {stat_name} Over/Under"
                    else:  # all
                        market_info["market_type"] = f"soccer_total_{stat_id}"
                        market_info["market_description"] = f"Total {stat_name} Over/Under"
            else:
                # PLAYER-LEVEL CARD MARKETS
                player_name = self._extract_player_name(stat_entity_id)
                
                if stat_id == "yellowCards":
                    stat_name = "Yellow Cards"
                elif stat_id == "redCards":
                    stat_name = "Red Cards"
                elif stat_id == "combinedCards":
                    stat_name = "Total Cards"
                else:
                    stat_name = "Weighted Cards"
                
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    market_info["market_type"] = f"soccer_{period_id}_player_{stat_id}"
                    market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                    market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
                else:
                    market_info["market_type"] = f"soccer_player_{stat_id}"
                    market_info["market_description"] = f"{player_name} {stat_name}"
                    market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        elif stat_id in ["goalie_goalsAgainst", "goalie_saves"] and self._is_soccer_sport(sport):
            # Soccer goalkeeper props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            if stat_id == "goalie_goalsAgainst":
                stat_name = "Goals Against"
            else:
                stat_name = "Saves"
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_goalkeeper_{stat_id.split('_')[1]}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"soccer_goalkeeper_{stat_id.split('_')[1]}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
        
        elif stat_id == "minutesPlayed" and self._is_soccer_sport(sport):
            # Soccer minutes played (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_minutes"
                market_info["market_description"] = f"{player_name} {period_name} Minutes Played"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Minutes Played Over/Under"
            else:
                market_info["market_type"] = "soccer_player_minutes"
                market_info["market_description"] = f"{player_name} Minutes Played"
                market_info["detailed_market_description"] = f"{player_name} Minutes Played Over/Under"
        
        elif stat_id == "bothTeamsScored":
            # Both teams to score special market
            market_info["market_type"] = "soccer_both_teams_score"
            market_info["market_description"] = "Both Teams to Score Yes/No"
            market_info["market_type"] = "soccer_both_teams_score"
            market_info["market_description"] = "Both Teams to Score Yes/No"
            market_info["detailed_market_description"] = "Both Teams to Score Yes/No"
            
        # DYNAMIC COMBINED STATS (e.g. goals+assists)
        elif "+" in stat_id and self._is_soccer_sport(sport):
            # Handle combined stats dynamically
            player_name = self._extract_player_name(stat_entity_id)
            stat_name = stat_id.replace("+", " + ").title()
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id.replace('+', '_')}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"soccer_player_{stat_id.replace('+', '_')}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        # BOTH TEAMS TO SCORE (BTTS) - Critical soccer market
        # SGO uses "bothTeamsScored" as the statID per their documentation
        elif stat_id in ["bothTeamsScored", "bothTeamsToScore"] and self._is_soccer_sport(sport):
            # Both Teams To Score market (Yes/No)
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_btts"
                market_info["market_description"] = f"{period_name} Both Teams To Score"
                market_info["detailed_market_description"] = f"{period_name} Both Teams To Score Yes/No"
            else:
                market_info["market_type"] = "soccer_btts"
                market_info["market_description"] = "Both Teams To Score"
                market_info["detailed_market_description"] = "Both Teams To Score Yes/No"
        
        # CLEAN SHEET markets
        elif stat_id in ["cleanSheet", "clean_sheet", "clean_sheets"] and self._is_soccer_sport(sport):
            # Clean Sheet market (team keeps zero goals)
            if stat_entity_id in ["home", "away"]:
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    market_info["market_type"] = f"soccer_{period_id}_{stat_entity_id}_clean_sheet"
                    market_info["market_description"] = f"{period_name} {stat_entity_id.title()} Team Clean Sheet"
                    market_info["detailed_market_description"] = f"{period_name} {stat_entity_id.title()} Team Clean Sheet Yes/No"
                else:
                    market_info["market_type"] = f"soccer_{stat_entity_id}_clean_sheet"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Clean Sheet"
                    market_info["detailed_market_description"] = f"{stat_entity_id.title()} Team Clean Sheet Yes/No"
        
        # TEAM TO WIN TO NIL (soccer-specific market from SGO docs)
        elif stat_id == "teamToWinToNil" and self._is_soccer_sport(sport):
            # Team wins and opponent scores zero goals
            if stat_entity_id in ["home", "away"]:
                if self._is_soccer_period(period_id):
                    period_name = self._get_soccer_period_name(period_id)
                    market_info["market_type"] = f"soccer_{period_id}_{stat_entity_id}_win_to_nil"
                    market_info["market_description"] = f"{period_name} {stat_entity_id.title()} Team Win To Nil"
                    market_info["detailed_market_description"] = f"{period_name} {stat_entity_id.title()} Team Win To Nil Yes/No"
                else:
                    market_info["market_type"] = f"soccer_{stat_entity_id}_win_to_nil"
                    market_info["market_description"] = f"{stat_entity_id.title()} Team Win To Nil"
                    market_info["detailed_market_description"] = f"{stat_entity_id.title()} Team Win To Nil Yes/No"
        
        # FIRST/LAST GOAL SCORER (soccer-specific from SGO docs)
        elif stat_id in ["firstGoalScorer", "lastGoalScorer", "anytimeGoalScorer"] and self._is_soccer_sport(sport):
            # Goal scorer props
            player_name = self._extract_player_name(stat_entity_id)
            
            if "first" in stat_id.lower():
                goal_type = "First Goal"
            elif "last" in stat_id.lower():
                goal_type = "Last Goal"
            else:
                goal_type = "Anytime Goal"
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id.lower()}"
                market_info["market_description"] = f"{player_name} {period_name} {goal_type}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {goal_type} Scorer"
            else:
                market_info["market_type"] = f"soccer_player_{stat_id.lower()}"
                market_info["market_description"] = f"{player_name} {goal_type}"
                market_info["detailed_market_description"] = f"{player_name} {goal_type} Scorer"
            
        # MISSING CRITICAL SOCCER STATS FROM SGO DOCS
        elif stat_id in ["offsides", "duels_won", "duels_lost", "aerial_duels_won", "ground_duels_won", 
                         "possession_lost", "dispossessed", "errors", "big_chances_created", "key_passes",
                         "saves", "punches", "catches", "clean_sheets", "possession", "touches", 
                         "accurate_passes", "long_balls", "through_balls"] and self._is_soccer_sport(sport):
            # Additional critical soccer player props from SGO documentation
            player_name = self._extract_player_name(stat_entity_id)
            
            if stat_id == "offsides":
                stat_name = "Offsides"
            elif stat_id == "duels_won":
                stat_name = "Duels Won"
            elif stat_id == "duels_lost":
                stat_name = "Duels Lost"
            elif stat_id == "aerial_duels_won":
                stat_name = "Aerial Duels Won"
            elif stat_id == "ground_duels_won":
                stat_name = "Ground Duels Won"
            elif stat_id == "possession_lost":
                stat_name = "Possession Lost"
            elif stat_id == "dispossessed":
                stat_name = "Dispossessed"
            elif stat_id == "errors":
                stat_name = "Errors"
            elif stat_id == "big_chances_created":
                stat_name = "Big Chances Created"
            elif stat_id == "key_passes":
                stat_name = "Key Passes"
            elif stat_id == "saves":
                stat_name = "Saves"
            elif stat_id == "punches":
                stat_name = "Punches"
            elif stat_id == "catches":
                stat_name = "Catches"
            elif stat_id == "clean_sheets":
                stat_name = "Clean Sheets"
            elif stat_id == "possession":
                stat_name = "Possession"
            elif stat_id == "touches":
                stat_name = "Touches"
            elif stat_id == "accurate_passes":
                stat_name = "Accurate Passes"
            elif stat_id == "long_balls":
                stat_name = "Long Balls"
            elif stat_id == "through_balls":
                stat_name = "Through Balls"
            else:
                stat_name = stat_id.replace("_", " ").title()
            
            if self._is_soccer_period(period_id):
                period_name = self._get_soccer_period_name(period_id)
                market_info["market_type"] = f"soccer_{period_id}_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"soccer_player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        # BASKETBALL MARKETS (NBA, NCAAB, WNBA)
        elif stat_id == "rebounds":
            # Basketball rebounds props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_rebounds"
                market_info["market_description"] = f"{player_name} {period_name} Rebounds"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Rebounds Over/Under"
            else:
                market_info["market_type"] = f"player_rebounds"
                market_info["market_description"] = f"{player_name} Rebounds"
                market_info["detailed_market_description"] = f"{player_name} Rebounds Over/Under"
            
        elif stat_id == "assists":
            # Basketball assists props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_assists"
                market_info["market_description"] = f"{player_name} {period_name} Assists"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Assists Over/Under"
            else:
                market_info["market_type"] = f"player_assists"
                market_info["market_description"] = f"{player_name} Assists"
                market_info["detailed_market_description"] = f"{player_name} Assists Over/Under"
            
        elif stat_id == "steals":
            # Basketball steals props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_steals"
                market_info["market_description"] = f"{player_name} {period_name} Steals"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Steals Over/Under"
            else:
                market_info["market_type"] = f"player_steals"
                market_info["market_description"] = f"{player_name} Steals"
                market_info["detailed_market_description"] = f"{player_name} Steals Over/Under"
            
        elif stat_id == "blocks":
            # Basketball blocks props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_blocks"
                market_info["market_description"] = f"{player_name} {period_name} Blocks"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Blocks Over/Under"
            else:
                market_info["market_type"] = f"player_blocks"
                market_info["market_description"] = f"{player_name} Blocks"
                market_info["detailed_market_description"] = f"{player_name} Blocks Over/Under"
            
        elif stat_id == "minutesPlayed":
            # Basketball minutes played props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_minutes"
                market_info["market_description"] = f"{player_name} {period_name} Minutes Played"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Minutes Played Over/Under"
            else:
                market_info["market_type"] = "soccer_player_minutes"
                market_info["market_description"] = f"{player_name} Minutes Played"
                market_info["detailed_market_description"] = f"{player_name} Minutes Played Over/Under"
            
        elif stat_id == "fantasyScore":
            # Basketball fantasy score props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_fantasy_score"
                market_info["market_description"] = f"{player_name} {period_name} Fantasy Score"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Fantasy Score Over/Under"
            else:
                market_info["market_type"] = f"player_fantasy_score"
                market_info["market_description"] = f"{player_name} Fantasy Score"
                market_info["detailed_market_description"] = f"{player_name} Fantasy Score Over/Under"
            
        elif stat_id == "points+assists":
            # Basketball points + assists combination props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_points_assists"
                market_info["market_description"] = f"{player_name} {period_name} Points + Assists"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Points + Assists Over/Under"
            else:
                market_info["market_type"] = f"player_points_assists"
                market_info["market_description"] = f"{player_name} Points + Assists"
                market_info["detailed_market_description"] = f"{player_name} Points + Assists Over/Under"
            
        elif stat_id == "rebounds+assists":
            # Basketball rebounds + assists combination props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_rebounds_assists"
                market_info["market_description"] = f"{player_name} {period_name} Rebounds + Assists"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Rebounds + Assists Over/Under"
            else:
                market_info["market_type"] = f"player_rebounds_assists"
                market_info["market_description"] = f"{player_name} Rebounds + Assists"
                market_info["detailed_market_description"] = f"{player_name} Rebounds + Assists Over/Under"
            
        elif stat_id == "blocks+steals":
            # Basketball blocks + steals combination props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_blocks_steals"
                market_info["market_description"] = f"{player_name} {period_name} Blocks + Steals"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Blocks + Steals Over/Under"
            else:
                market_info["market_type"] = f"player_blocks_steals"
                market_info["market_description"] = f"{player_name} Blocks + Steals"
                market_info["detailed_market_description"] = f"{player_name} Blocks + Steals Over/Under"
            
        elif stat_id in ["threePointersMade", "threePointersAttempted", "freeThrowsMade", "freeThrowsAttempted", 
                         "fieldGoalsMade", "fieldGoalsAttempted", "personalFouls", "turnovers"]:
            # Basketball additional individual stats (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            
            # Clean up stat name
            if stat_id == "threePointersMade":
                stat_name = "Three Pointers Made"
            elif stat_id == "threePointersAttempted":
                stat_name = "Three Pointers Attempted"
            elif stat_id == "freeThrowsMade":
                stat_name = "Free Throws Made"
            elif stat_id == "freeThrowsAttempted":
                stat_name = "Free Throws Attempted"
            elif stat_id == "fieldGoalsMade":
                stat_name = "Field Goals Made"
            elif stat_id == "fieldGoalsAttempted":
                stat_name = "Field Goals Attempted"
            elif stat_id == "personalFouls":
                stat_name = "Personal Fouls"
            elif stat_id == "turnovers":
                stat_name = "Turnovers"
            else:
                stat_name = stat_id.replace("_", " ").title()
            
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_{stat_id.lower()}"
                market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = f"player_{stat_id.lower()}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        elif stat_id == "doubleDouble":
            # Basketball double-double props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_double_double"
                market_info["market_description"] = f"{player_name} {period_name} Double-Double"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Double-Double Yes/No"
            else:
                market_info["market_type"] = f"player_double_double"
                market_info["market_description"] = f"{player_name} Double-Double"
                market_info["detailed_market_description"] = f"{player_name} Double-Double Yes/No"
            
        elif stat_id == "tripleDouble":
            # Basketball triple-double props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_triple_double"
                market_info["market_description"] = f"{player_name} {period_name} Triple-Double"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Triple-Double Yes/No"
            else:
                market_info["market_type"] = f"player_triple_double"
                market_info["market_description"] = f"{player_name} Triple-Double"
                market_info["detailed_market_description"] = f"{player_name} Triple-Double Yes/No"
            
        elif stat_id == "firstBasket":
            # Basketball first basket props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_first_basket"
                market_info["market_description"] = f"{player_name} {period_name} First Basket"
                market_info["detailed_market_description"] = f"{player_name} {period_name} First Basket Yes/No"
            else:
                market_info["market_type"] = f"player_first_basket"
                market_info["market_description"] = f"{player_name} First Basket"
                market_info["detailed_market_description"] = f"{player_name} First Basket Yes/No"
            
        elif stat_id == "firstToScore":
            # Basketball first to score props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_first_to_score"
                market_info["market_description"] = f"{player_name} {period_name} First To Score"
                market_info["detailed_market_description"] = f"{player_name} {period_name} First To Score Yes/No"
            else:
                market_info["market_type"] = f"player_first_score"
                market_info["market_description"] = f"{player_name} First Score"
                market_info["detailed_market_description"] = f"{player_name} First Score Yes/No"
            
        # ADDITIONAL BASKETBALL STATS (from comprehensive SGO docs review)
        elif stat_id == "turnovers":
            # Basketball turnovers props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_turnovers"
                market_info["market_description"] = f"{player_name} {period_name} Turnovers"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Turnovers Over/Under"
            else:
                market_info["market_type"] = f"player_turnovers"
                market_info["market_description"] = f"{player_name} Turnovers"
                market_info["detailed_market_description"] = f"{player_name} Turnovers Over/Under"
                
        # HOCKEY MARKETS
        elif stat_id in ["goals", "assists", "points", "shotsOnGoal", "blockedShots", "powerPlayPoints", "timeOnIce"] and self._is_hockey_period(period_id) or self._is_hockey_period(period_id):
            # Hockey player props (goals, assists, points, etc.)
            player_name = self._extract_player_name(stat_entity_id)
            period_name = self._get_hockey_period_name(period_id) if period_id != "game" else ""
            
            if stat_id == "shotsOnGoal":
                stat_name = "Shots on Goal"
            elif stat_id == "blockedShots":
                stat_name = "Blocked Shots"
            elif stat_id == "powerPlayPoints":
                stat_name = "Power Play Points"
            elif stat_id == "timeOnIce":
                stat_name = "Time on Ice"
            else:
                stat_name = stat_id.title()
                
            market_info["market_type"] = f"hockey_{period_id}_player_{stat_id}"
            market_info["market_description"] = f"{player_name} {period_name} {stat_name}".strip()
            market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under".strip()
            
        elif stat_id in ["goalie_saves", "goalie_goalsAgainst", "goalie_shutouts"] and (self._is_hockey_period(period_id) or period_id == "game"):
            # Hockey goalie props
            player_name = self._extract_player_name(stat_entity_id)
            period_name = self._get_hockey_period_name(period_id) if period_id != "game" else ""
            
            if stat_id == "goalie_saves":
                stat_name = "Saves"
            elif stat_id == "goalie_goalsAgainst":
                stat_name = "Goals Against"
            else:
                stat_name = "Shutouts"
                
            market_info["market_type"] = f"hockey_{period_id}_goalie_{stat_id.split('_')[1]}"
            market_info["market_description"] = f"{player_name} {period_name} {stat_name}".strip()
            market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under".strip()
            
        # MMA MARKETS
        elif stat_id == "methodOfVictory":
            # Method of Victory
            market_info["market_type"] = "mma_method_of_victory"
            
            if stat_entity_id == "ko_tko":
                method = "KO/TKO"
            elif stat_entity_id == "submission":
                method = "Submission"
            elif stat_entity_id == "decision":
                method = "Decision"
            elif stat_entity_id == "draw":
                method = "Draw"
            else:
                method = stat_entity_id.replace("_", " ").title()
                
            market_info["market_description"] = f"Win by {method}"
            market_info["detailed_market_description"] = f"Method of Victory: {method}"
            
        elif stat_id == "rounds":
            # Total Rounds
            market_info["market_type"] = "mma_total_rounds"
            market_info["market_description"] = "Total Rounds"
            market_info["detailed_market_description"] = "Total Rounds Over/Under"
            
        elif stat_id == "fight_to_go_the_distance":
            # Fight to Go the Distance
            market_info["market_type"] = "mma_go_distance"
            market_info["market_description"] = "Fight to Go the Distance"
            market_info["detailed_market_description"] = "Fight to Go the Distance Yes/No"
            
        elif stat_id in ["significant_strikes", "takedowns_landed", "knockdowns", "submission_attempts"]:
            # MMA Fighter Props
            player_name = self._extract_player_name(stat_entity_id)
            stat_name = stat_id.replace("_", " ").title()
            
            market_info["market_type"] = f"mma_fighter_{stat_id}"
            market_info["market_description"] = f"{player_name} {stat_name}"
            market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            
        # SOCCER COMPLEX MARKETS
        elif stat_id == "points" and self._is_soccer_sport(sport):
            # Handle 3-Way Moneyline, Double Chance, Correct Score, HT/FT
            
            if "ml3way" in market_id:
                # 3-Way Moneyline (1X2)
                market_info["market_type"] = f"soccer_{period_id}_ml_3way"
                if stat_entity_id == "draw":
                    market_info["market_description"] = f"{period_name} Draw"
                    market_info["detailed_market_description"] = f"{period_name} 3-Way Moneyline: Draw"
                else:
                    market_info["market_description"] = f"{period_name} {stat_entity_id.title()} Win (3-Way)"
                    market_info["detailed_market_description"] = f"{period_name} 3-Way Moneyline: {stat_entity_id.title()}"
                    
            elif "dc" in market_id:
                # Double Chance
                market_info["market_type"] = f"soccer_{period_id}_double_chance"
                dc_map = {"1x": "Home or Draw", "x2": "Draw or Away", "12": "Home or Away"}
                outcome = dc_map.get(stat_entity_id.lower(), stat_entity_id)
                market_info["market_description"] = f"{period_name} Double Chance: {outcome}"
                market_info["detailed_market_description"] = f"{period_name} Double Chance: {outcome}"
                
            elif "cs" in market_id:
                # Correct Score
                market_info["market_type"] = f"soccer_{period_id}_correct_score"
                score = stat_entity_id.replace("-", ":")
                market_info["market_description"] = f"{period_name} Correct Score {score}"
                market_info["detailed_market_description"] = f"{period_name} Correct Score: {score}"
                
            elif "htft" in market_id:
                # Half Time / Full Time
                market_info["market_type"] = "soccer_ht_ft"
                # Format: "1/1", "X/2", etc. SGO might send "home-home" or similar
                outcome = stat_entity_id.replace("-", "/").replace("home", "1").replace("away", "2").replace("draw", "X")
                market_info["market_description"] = f"HT/FT: {outcome}"
                market_info["detailed_market_description"] = f"Half Time / Full Time: {outcome}"
                
            # Fallback to standard points logic for ML (2-way), Spread, Total
            else:
                 pass # Continue to standard logic below
                 
        # TENNIS MARKETS
        elif stat_id == "games" and self._is_tennis_sport(sport):
            # Game Handicap or Total Games
            if market_info["market_type"] == "spread":
                market_info["market_type"] = f"tennis_{period_id}_game_handicap"
                market_info["market_description"] = f"{period_name} Game Handicap"
                market_info["detailed_market_description"] = f"{period_name} Game Handicap"
            elif market_info["market_type"] == "total":
                market_info["market_type"] = f"tennis_{period_id}_total_games"
                market_info["market_description"] = f"{period_name} Total Games"
                market_info["detailed_market_description"] = f"{period_name} Total Games Over/Under"
                
        elif stat_id == "sets" and self._is_tennis_sport(sport):
            # Set Handicap or Total Sets
            if market_info["market_type"] == "spread":
                market_info["market_type"] = f"tennis_{period_id}_set_handicap"
                market_info["market_description"] = f"{period_name} Set Handicap"
                market_info["detailed_market_description"] = f"{period_name} Set Handicap"
            elif "cs" in market_id:
                # Set Betting (Correct Score)
                market_info["market_type"] = f"tennis_{period_id}_set_betting"
                score = stat_entity_id.replace("-", ":")
                market_info["market_description"] = f"Set Betting {score}"
                market_info["detailed_market_description"] = f"Set Betting: {score}"
                
        elif stat_id == "tiebreak" and self._is_tennis_sport(sport):
            # Tie-break Yes/No
            market_info["market_type"] = f"tennis_{period_id}_tiebreak"
            market_info["market_description"] = f"{period_name} Tie-break"
            market_info["detailed_market_description"] = f"{period_name} Tie-break Yes/No"
            
        elif stat_id in ["aces", "doubleFaults", "firstServePercentage", "breakPointsConverted"] and self._is_tennis_sport(sport):
            # Tennis Player Props
            player_name = self._extract_player_name(stat_entity_id)
            stat_name = stat_id.replace("Percentage", " %").replace("Points", " Points").title()
            
            market_info["market_type"] = f"tennis_{period_id}_player_{stat_id}"
            market_info["market_description"] = f"{player_name} {period_name} {stat_name}"
            market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_name} Over/Under"
                
        elif stat_id == "personalFouls":
            # Basketball personal fouls props (with period support)
            player_name = self._extract_player_name(stat_entity_id)
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_fouls"
                market_info["market_description"] = f"{player_name} {period_name} Personal Fouls"
                market_info["detailed_market_description"] = f"{player_name} {period_name} Personal Fouls Over/Under"
            else:
                market_info["market_type"] = f"player_fouls"
                market_info["market_description"] = f"{player_name} Personal Fouls"
                market_info["detailed_market_description"] = f"{player_name} Personal Fouls Over/Under"
                
        elif stat_id.startswith("threePointers"):
            # Basketball 3-pointer props (made, attempted)
            player_name = self._extract_player_name(stat_entity_id)
            stat_suffix = stat_id.replace("threePointers_", "").replace("threePointers", "")
            
            if "made" in stat_suffix.lower():
                stat_desc = "3-Pointers Made"
            elif "attempted" in stat_suffix.lower():
                stat_desc = "3-Point Attempts"
            else:
                stat_desc = "3-Pointers"
                
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_three_pointers"
                market_info["market_description"] = f"{player_name} {period_name} {stat_desc}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_desc} Over/Under"
            else:
                market_info["market_type"] = f"player_three_pointers"
                market_info["market_description"] = f"{player_name} {stat_desc}"
                market_info["detailed_market_description"] = f"{player_name} {stat_desc} Over/Under"
                
        elif stat_id.startswith("freeThrows"):
            # Basketball free throw props (made, attempted)
            player_name = self._extract_player_name(stat_entity_id)
            stat_suffix = stat_id.replace("freeThrows_", "").replace("freeThrows", "")
            
            if "made" in stat_suffix.lower():
                stat_desc = "Free Throws Made"
            elif "attempted" in stat_suffix.lower():
                stat_desc = "Free Throw Attempts"
            else:
                stat_desc = "Free Throws"
                
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_free_throws"
                market_info["market_description"] = f"{player_name} {period_name} {stat_desc}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_desc} Over/Under"
            else:
                market_info["market_type"] = f"player_free_throws"
                market_info["market_description"] = f"{player_name} {stat_desc}"
                market_info["detailed_market_description"] = f"{player_name} {stat_desc} Over/Under"
                
        elif stat_id.startswith("fieldGoals"):
            # Basketball field goal props (made, attempted)
            player_name = self._extract_player_name(stat_entity_id)
            stat_suffix = stat_id.replace("fieldGoals_", "").replace("fieldGoals", "")
            
            if "made" in stat_suffix.lower():
                stat_desc = "Field Goals Made"
            elif "attempted" in stat_suffix.lower():
                stat_desc = "Field Goal Attempts"
            else:
                stat_desc = "Field Goals"
                
            if self._is_basketball_period(period_id):
                period_name = self._get_basketball_period_name(period_id)
                market_info["market_type"] = f"basketball_{period_id}_player_field_goals"
                market_info["market_description"] = f"{player_name} {period_name} {stat_desc}"
                market_info["detailed_market_description"] = f"{player_name} {period_name} {stat_desc} Over/Under"
            else:
                market_info["market_type"] = f"player_field_goals"
                market_info["market_description"] = f"{player_name} {stat_desc}"
                market_info["detailed_market_description"] = f"{player_name} {stat_desc} Over/Under"
            
        # TENNIS MARKETS
        elif stat_id in ["games", "sets", "aces", "doubleFaults", "breakPoints"]:
            # Tennis markets
            if stat_entity_id in ["home", "away"]:
                # Player-specific tennis stats
                if stat_id == "breakPoints":
                    stat_name = "Break Points"
                elif stat_id == "doubleFaults":
                    stat_name = "Double Faults"
                else:
                    stat_name = stat_id.title()
                
                market_info["market_type"] = f"tennis_{stat_entity_id}_{stat_id}"
                market_info["market_description"] = f"{stat_entity_id.title()} Player {stat_name}"
                market_info["detailed_market_description"] = f"{stat_entity_id.title()} Player {stat_name} Over/Under"
            else:
                # General tennis markets
                if stat_id == "breakPoints":
                    stat_name = "Break Points"
                elif stat_id == "doubleFaults":
                    stat_name = "Double Faults"
                else:
                    stat_name = stat_id.title()
                    
                market_info["market_type"] = f"tennis_{stat_id}"
                market_info["market_description"] = f"Tennis {stat_name}"
            
        # GENERIC STAT HANDLER (Catch-all for known stats to prevent fallback warning)
        elif stat_id in ["goals+assists", "plusMinus", "shots_onGoal", "shotsOnGoal", "faceoffsWon", "blockedShots", "timeOnIce", 
                        "firstTo10", "firstTo15", "firstTo20", "firstTo25", "firstTo75", 
                        "twoPointersMade", "twoPointersAttempted", "threePointersMade", "threePointersAttempted",
                        "freeThrowsMade", "freeThrowsAttempted"]:
             # Extract player name if present
            player_name = self._extract_player_name(stat_entity_id)
            stat_name = stat_id.replace("_", " ").replace("+", " + ").title()
            
            # Fix specific naming conventions
            if "Two Pointers" in stat_name: stat_name = stat_name.replace("Two Pointers", "2-Pointers")
            if "Three Pointers" in stat_name: stat_name = stat_name.replace("Three Pointers", "3-Pointers")
            
            if player_name:
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_name}"
                market_info["detailed_market_description"] = f"{player_name} {stat_name} Over/Under"
            else:
                market_info["market_type"] = stat_id
                market_info["market_description"] = f"{stat_name}"
                market_info["detailed_market_description"] = f"{stat_name} Over/Under"
            
        else:
            # Other specialty markets - use fallback
            # DEBUG: Log unrecognized stats to identify missing handlers (rate limited)
            import random
            if random.random() < 0.1:  # Only log 10% of unrecognized stats to avoid spam
                logger.warning(f"🚨 UNRECOGNIZED STAT: {stat_id} for {stat_entity_id} in {sport}")
                logger.warning(f"🚨 FALLBACK USED: This may cause incorrect market descriptions!")
            
            # CRITICAL FIX: Include player name for player stats in fallback
            if stat_entity_id not in ["home", "away", "all"] and not any(keyword in stat_entity_id for keyword in ["_LA_LIGA", "_NFL", "_NBA", "_MLB"]):
                # This appears to be a player stat that we missed
                player_name = self._extract_player_name(stat_entity_id)
                market_info["market_type"] = f"player_{stat_id}"
                market_info["market_description"] = f"{player_name} {stat_id.replace('_', ' ').title()}"
                market_info["detailed_market_description"] = f"{player_name} {stat_id.replace('_', ' ').title()} Over/Under"
            else:
                # Team or game level stat
                market_info["market_type"] = stat_id
                market_info["market_description"] = f"{stat_id.replace('_', ' ').title()}"
        
        return market_info

    def _get_detailed_market_description(self, odd_id: str, market_type: str, line: Optional[float] = None) -> str:
        """Get detailed market description from SGO odd_id patterns"""
        try:
            # Reduced logging to prevent Railway rate limits
            # logger.info(f"🔍 DEBUG: Processing odd_id '{odd_id}' for market_type '{market_type}' with line {line}")
            
            # Stat type mapping (excluding 'points' - we'll handle it specially)
            stat_type_map = {
                'receiving_receptions': 'Receptions',
                'receiving_yards': 'Receiving Yards',
                'rushing_yards': 'Rushing Yards',
                'rushing_attempts': 'Rushing Attempts',
                'rushing_longestRush': 'Longest Rush',
                'touchdowns': 'Touchdowns',
                'passing_yards': 'Passing Yards',
                'passing_touchdowns': 'Passing TDs',
                'interceptions': 'Interceptions',
                'fumbles': 'Fumbles',
                'turnovers': 'Turnovers',
                'firstBasket': 'First Basket',
                'doubleDouble': 'Double-Double',
                'tripleDouble': 'Triple-Double',
                'assists': 'Assists',
                'rebounds': 'Rebounds',
                'steals': 'Steals',
                'blocks': 'Blocks',
                'twoPointersMade': '2-Pointers Made',
                'twoPointersAttempted': '2-Pointers Attempted',
                'threePointersMade': '3-Pointers Made',
                'threePointersAttempted': '3-Pointers Attempted',
                'freeThrowsMade': 'Free Throws Made',
                'freeThrowsAttempted': 'Free Throws Attempted',
                'firstTo10': 'First to 10 Points',
                'firstTo15': 'First to 15 Points',
                'firstTo20': 'First to 20 Points',
                'firstTo25': 'First to 25 Points',
                'firstTo75': 'First to 75 Points',
                'batting_hits': 'Hits',
                'batting_homeRuns': 'Home Runs',
                'batting_RBI': 'RBI',
                'batting_stolenBases': 'Stolen Bases',
                'batting_strikeouts': 'Strikeouts',
                'batting_basesOnBalls': 'Walks',
                'batting_singles': 'Singles',
                'batting_doubles': 'Doubles',
                'batting_triples': 'Triples',
                'batting_totalBases': 'Total Bases',
                'batting_hits+runs+rbi': 'Hits + Runs + RBI',
                'extraPoints_kicksMade': 'Extra Points Made',
                'kicking_totalPoints': 'Kicking Total Points',
                'games': 'Games',
                'rushing+receiving_yards': 'Rushing + Receiving Yards',
                'pitching_strikeouts': 'Pitching Strikeouts',
                'pitching_walks': 'Pitching Walks',
                'pitching_hits': 'Pitching Hits',
                'pitching_earnedRuns': 'Earned Runs',
                'pitching_innings': 'Innings Pitched',
                'pitching_wins': 'Pitching Wins',
                'pitching_losses': 'Pitching Losses',
                'pitching_saves': 'Saves',
                'pitching_holds': 'Holds',
                'pitching_blownSaves': 'Blown Saves',
                'pitching_qualityStarts': 'Quality Starts',
                'pitching_completeGames': 'Complete Games',
                'pitching_shutouts': 'Shutouts',
                'pitching_noHitters': 'No Hitters',
                'pitching_perfectGames': 'Perfect Games',
                # Football specific additions
                'defense_interceptions': 'Interceptions',
                'defense_tackles': 'Tackles',
                'defense_sacks': 'Sacks',
                'defense_tackles+assists': 'Tackles + Assists',
                'fieldGoals_made': 'Field Goals Made',
                'fieldGoals_attempted': 'Field Goals Attempted',
                'kicking_points': 'Kicking Points',
                'punting_yards': 'Punting Yards',
                'punting_punts': 'Punts',
                # Hockey specific additions
                'goals': 'Goals',
                'assists': 'Assists',
                'points': 'Points',
                'shotsOnGoal': 'Shots on Goal',
                'shots_onGoal': 'Shots on Goal',
                'blockedShots': 'Blocked Shots',
                'powerPlayPoints': 'Power Play Points',
                'goalie_saves': 'Saves',
                'goalie_goalsAgainst': 'Goals Against',
                'goalie_shutouts': 'Shutouts',
                'faceoffsWon': 'Faceoffs Won',
                'timeOnIce': 'Time on Ice',
                'goals+assists': 'Goals + Assists',
                # MMA specific additions
                'methodOfVictory': 'Method of Victory',
                'rounds': 'Total Rounds',
                'fight_to_go_the_distance': 'Fight to Go the Distance',
                'significant_strikes': 'Significant Strikes',
                'takedowns_landed': 'Takedowns Landed',
                'knockdowns': 'Knockdowns',
                'submission_attempts': 'Submission Attempts',
                # Soccer specific additions
                'corners': 'Corners',
                'cards': 'Cards',
                'shots': 'Shots',
                'shotsOnTarget': 'Shots on Target',
                'tackles': 'Tackles',
                'passes': 'Passes',
                'fouls': 'Fouls',
                'offsides': 'Offsides',
                'crosses': 'Crosses',
                'interceptions': 'Interceptions',
                'clearances': 'Clearances',
                'saves': 'Saves',
                'minutesPlayed': 'Minutes Played',
                'fantasyScore': 'Fantasy Score',
                'bothTeamsScored': 'Both Teams to Score',
                'cleanSheet': 'Clean Sheet',
                'teamToWinToNil': 'Win to Nil',
                'firstGoalScorer': 'First Goal Scorer',
                'lastGoalScorer': 'Last Goal Scorer',
                'anytimeGoalScorer': 'Anytime Goal Scorer',
                # Tennis specific additions
                'games': 'Games',
                'sets': 'Sets',
                'aces': 'Aces',
                'doubleFaults': 'Double Faults',
                'firstServePercentage': '1st Serve %',
                'firstServePointsWon': '1st Serve Points Won',
                'secondServePointsWon': '2nd Serve Points Won',
                'breakPointsSaved': 'Break Points Saved',
                'breakPointsConverted': 'Break Points Converted',
                'serviceGamesWon': 'Service Games Won',
                'returnGamesWon': 'Return Games Won',
                'totalPointsWon': 'Total Points Won',
                'tiebreak': 'Tie-break'
            }
            
            # Period mapping
            period_map = {
                'game': 'Full Match',
                '1h': '1st Half',
                '2h': '2nd Half',
                'ot': 'Extra Time',
                'pen': 'Penalties',
                'reg': 'Regulation',
                '1q': '1st Quarter',
                '2q': '2nd Quarter',
                '3q': '3rd Quarter',
                '4q': '4th Quarter',
                '1p': '1st Period',
                '2p': '2nd Period',
                '3p': '3rd Period',
                '1s': '1st Set',
                '2s': '2nd Set',
                '3s': '3rd Set',
                '4s': '4th Set',
                '5s': '5th Set',
                '1i': '1st Inning',
                '2i': '2nd Inning',
                '3i': '3rd Inning',
                '4i': '4th Inning',
                '5i': '5th Inning',
                '6i': '6th Inning',
                '7i': '7th Inning',
                '8i': '8th Inning',
                '9i': '9th Inning',
                '1ix7': '1st 7 Innings',
                'reg': 'Regulation',
                # Global / Other Periods
                'so': 'Shootout',
                'ot': 'Extra Time',
                '1m': '1st Minute',
                '1mx5': '1st 5 Minutes',
                '1mx10': '1st 10 Minutes',
                '1mx15': '1st 15 Minutes',
                '9r': 'Round 9',
                '10r': 'Round 10',
                '11r': 'Round 11',
                '12r': 'Round 12'
            }
            
            # Extract stat type and period from odd_id
            stat_type = None
            period = 'Game'
            player_name = None
            
            # Extract player name if present (format: STAT-PLAYER_NAME_1_LEAGUE-...)
            import re
            player_match = re.search(r'-([A-Z_]+_\d+_[A-Z]+)-', odd_id)
            if player_match:
                player_name = player_match.group(1).replace('_', ' ')
            
            # Special handling for 'points' - determine context based on odd_id structure and sport
            if 'points-' in odd_id:
                # Determine sport context from odd_id (look for league indicators)
                is_soccer = any(league in odd_id.upper() for league in ['SOCC', 'SERIE', 'LIGA', 'PREMIER', 'BUNDESLIGA', 'CHAMPIONS'])
                is_basketball = any(league in odd_id.upper() for league in ['NBA', 'WNBA', 'NCAA'])
                is_football = any(league in odd_id.upper() for league in ['NFL', 'NCAA'])
                is_baseball = any(league in odd_id.upper() for league in ['MLB', 'NPB', 'KBO'])
                
                if player_name:
                    # Player prop: points-PLAYER_NAME_1_LEAGUE-...
                    if is_soccer:
                        stat_type = 'Goals'
                    elif is_basketball:
                        stat_type = 'Points'
                    elif is_football:
                        stat_type = 'Points'
                    elif is_baseball:
                        stat_type = 'Runs'
                    else:
                        stat_type = 'Points'
                elif 'home-' in odd_id:
                    # Team total: points-home-game-ou-over
                    if is_soccer:
                        stat_type = 'Home Team Total Goals'
                    elif is_basketball:
                        stat_type = 'Home Team Total Points'
                    elif is_football:
                        stat_type = 'Home Team Total Points'
                    elif is_baseball:
                        stat_type = 'Home Team Total Runs'
                    else:
                        stat_type = 'Home Team Total Points'
                elif 'away-' in odd_id:
                    # Team total: points-away-game-ou-over
                    if is_soccer:
                        stat_type = 'Away Team Total Goals'
                    elif is_basketball:
                        stat_type = 'Away Team Total Points'
                    elif is_football:
                        stat_type = 'Away Team Total Points'
                    elif is_baseball:
                        stat_type = 'Away Team Total Runs'
                    else:
                        stat_type = 'Away Team Total Points'
                elif 'all-' in odd_id:
                    # Game total: points-all-game-ou-over
                    if is_soccer:
                        stat_type = 'Game Total Goals'
                    elif is_basketball:
                        stat_type = 'Game Total Points'
                    elif is_football:
                        stat_type = 'Game Total Points'
                    elif is_baseball:
                        stat_type = 'Game Total Runs'
                    else:
                        stat_type = 'Game Total Points'
                else:
                    # Default based on sport
                    if is_soccer:
                        stat_type = 'Game Total Goals'
                    elif is_basketball:
                        stat_type = 'Game Total Points'
                    elif is_football:
                        stat_type = 'Game Total Points'
                    elif is_baseball:
                        stat_type = 'Game Total Runs'
                    else:
                        stat_type = 'Game Total Points'
                
                # logger.info(f"🔍 DEBUG: Points market detected - stat_type: '{stat_type}' for odd_id '{odd_id}'")
            else:
                # Look for other stat type patterns
                for key, value in stat_type_map.items():
                    if key in odd_id:
                        stat_type = value
                        # logger.info(f"🔍 DEBUG: Matched stat type '{key}' -> '{value}' for odd_id '{odd_id}'")
                        break
            
            # Look for period patterns
            for key, value in period_map.items():
                if f'-{key}-' in odd_id or f'_{key}_' in odd_id:
                    period = value
                    break
            
            # Build detailed description
            if stat_type:
                # Add player name if available
                if player_name:
                    stat_display = f"{player_name} {stat_type}"
                else:
                    stat_display = stat_type
                
                if market_type == 'totals':
                    if line is not None:
                        # Add helpful context for different market types
                        if "Team Total" in stat_display:
                            if "Goals" in stat_display:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Team Total Goals' or 'Alternative Lines' section*"
                            elif "Points" in stat_display:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Team Total Points' section*"
                            elif "Runs" in stat_display:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Team Total Runs' section*"
                            else:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Team Totals' section*"
                        elif "Game Total" in stat_display:
                            if "Goals" in stat_display:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Over/Under Goals' section*"
                            elif "Points" in stat_display:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Over/Under Points' section*"
                            elif "Runs" in stat_display:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Over/Under Runs' section*"
                            else:
                                description = f"{stat_display} Over/Under {line} ({period}) - *Check 'Over/Under' section*"
                        else:
                            description = f"{stat_display} Over/Under {line} ({period})"
                    else:
                        description = f"{stat_display} Over/Under ({period})"
                elif market_type == 'spread':
                    if line is not None:
                        description = f"{stat_display} Spread {line:+.1f} ({period})"
                    else:
                        description = f"{stat_display} Spread ({period})"
                elif market_type == 'moneyline':
                    # For moneyline, don't use stat_type - just show moneyline
                    if 'ml3way' in odd_id or '3way' in odd_id:
                        if 'home' in odd_id:
                            description = f"Home Team 3-Way Moneyline ({period})"
                        elif 'away' in odd_id:
                            description = f"Away Team 3-Way Moneyline ({period})"
                        elif 'draw' in odd_id:
                            description = f"Draw 3-Way Moneyline ({period})"
                        else:
                            description = f"3-Way Moneyline ({period})"
                    else:
                        if 'home' in odd_id:
                            description = f"Home Team Moneyline ({period})"
                        elif 'away' in odd_id:
                            description = f"Away Team Moneyline ({period})"
                        else:
                            description = f"Moneyline ({period})"
                elif market_type in ['yn', 'yes_no']:
                    description = f"{stat_display} Yes/No ({period})"
                else:
                    description = f"{stat_display} ({period})"
                
                # logger.info(f"🎯 Generated detailed description: '{description}' from odd_id: {odd_id}")
                return description
            
            logger.debug(f"⚠️ No stat_type found for odd_id: {odd_id}, using fallback")
            # For fallback, just return the market type without stat info
            if market_type == 'totals':
                return f"Over/Under ({period})"
            elif market_type == 'spread':
                return f"Spread ({period})"
            elif market_type == 'moneyline':
                if 'ml3way' in odd_id or '3way' in odd_id:
                    return f"3-Way Moneyline ({period})"
                else:
                    return f"Moneyline ({period})"
            else:
                return f"{market_type.title()} ({period})"
            
        except Exception as e:
            logger.error(f"Error in _get_detailed_market_description: {str(e)}")
            return market_type.title()

    def _get_team_name(self, side: str, home_team: str, away_team: str) -> str:
        """Get team name based on side"""
        if side == "home":
            return home_team
        elif side == "away":
            return away_team
        elif side == "over":
            return "Over"
        elif side == "under":
            return "Under"
        else:
            return side.title()
    
    def _calculate_confidence_score(self, market_description: str, best_odds: dict, sport: str, league: str) -> float:
        """Calculate confidence score based on market type and bookmaker availability"""
        base_score = 0.5  # Start with 50% confidence
        
        # Major bookmakers that are widely available
        major_bookmakers = ["fanduel", "draftkings", "betmgm", "caesars", "espnbet", "pinnacle", "bet365"]
        bookmaker_count = len([bm for bm in best_odds.values() if bm["bookmaker"].lower() in major_bookmakers])
        
        # Boost confidence for major bookmakers
        if bookmaker_count >= 2:
            base_score += 0.3
        elif bookmaker_count >= 1:
            base_score += 0.2
        
        # Market type confidence adjustments
        if "Game Total" in market_description:
            base_score += 0.2  # Game totals are widely available
        elif "Moneyline" in market_description:
            base_score += 0.2  # Moneylines are universally available
        elif "Team Total" in market_description:
            base_score -= 0.1  # Team totals are less common
        elif "Spread" in market_description:
            base_score += 0.1  # Spreads are common but not universal
        
        # Sport-specific adjustments
        if sport == "FOOTBALL" and "Points" in market_description:
            base_score += 0.1  # NFL/NBA points are very common
        elif sport == "BASEBALL" and "Runs" in market_description:
            base_score += 0.1  # MLB runs are very common
        elif sport == "SOCCER" and "Goals" in market_description:
            if "Team Total" in market_description:
                base_score -= 0.2  # Soccer team totals are rare
            else:
                base_score += 0.1  # Soccer game totals are common
        
        # Ensure score is between 0.1 and 0.95
        return max(0.1, min(0.95, base_score))
    
    def _get_verification_tips(self, market_description: str, sport: str) -> str:
        """Get helpful tips for verifying the market on bookmaker websites"""
        tips = []
        
        if "Team Total" in market_description:
            if sport == "SOCCER":
                tips.append("Look for 'Team Total Goals' in Alternative Lines or Player Props sections")
                tips.append("May be under 'Team Goals' or 'Individual Team Totals'")
            elif sport == "FOOTBALL":
                tips.append("Check 'Team Total Points' in the main betting menu")
                tips.append("Often under 'Alternative Lines' or 'Team Totals'")
            elif sport == "BASEBALL":
                tips.append("Look for 'Team Total Runs' in the main menu")
                tips.append("May be under 'Team Totals' or 'Alternative Lines'")
        elif "Game Total" in market_description:
            tips.append("This is the main Over/Under market - should be prominently displayed")
            tips.append("Look for 'Total Goals/Points/Runs' in the main betting menu")
        elif "Moneyline" in market_description:
            tips.append("This is the main win/lose market - should be the first option")
            tips.append("Look for team names with odds next to them")
        elif "Spread" in market_description:
            tips.append("Look for 'Point Spread' or 'Handicap' section")
            tips.append("May be under 'Alternative Lines' or 'Spreads'")
        
        if not tips:
            tips.append("Check the main betting menu for this market type")
            tips.append("Look in 'Alternative Lines' or 'Player Props' if not in main menu")
        
        return " | ".join(tips)
    
    def _validate_sgo_data_quality(self, odds_data: dict, bookmaker: str, odd_id: str) -> dict:
        """Validate the quality and freshness of SGO data"""
        validation = {
            "is_valid": True,
            "issues": [],
            "data_age_hours": 0,
            "bookmaker_confidence": "unknown"
        }
        
        # Check data age
        if "lastUpdatedAt" in odds_data:
            try:
                last_updated = datetime.fromisoformat(odds_data["lastUpdatedAt"].replace('Z', '+00:00'))
                age_hours = (datetime.now() - last_updated.replace(tzinfo=None)).total_seconds() / 3600
                validation["data_age_hours"] = age_hours
                
                if age_hours > 4:
                    validation["issues"].append(f"Data is {age_hours:.1f} hours old")
                if age_hours > 24:
                    validation["is_valid"] = False
                    validation["issues"].append("Data is over 24 hours old - likely stale")
            except:
                validation["issues"].append("Could not parse lastUpdatedAt timestamp")
        
        # Check bookmaker confidence
        major_bookmakers = ["fanduel", "draftkings", "betmgm", "caesars", "espnbet", "pinnacle", "bet365"]
        if bookmaker.lower() in major_bookmakers:
            validation["bookmaker_confidence"] = "high"
        elif bookmaker.lower() in ["unknown", "test", "demo"]:
            validation["bookmaker_confidence"] = "low"
            validation["issues"].append(f"Bookmaker '{bookmaker}' is not a real bookmaker")
        else:
            validation["bookmaker_confidence"] = "medium"
        
        # Check for suspicious patterns
        if "points-away-game-ou" in odd_id and "SOCC" in odd_id.upper():
            validation["issues"].append("Soccer team totals are rarely offered by major bookmakers")
        
        return validation
    
    def _track_opportunity_persistence(self, opportunity_id: str, home_team: str, away_team: str, profit_percentage: float) -> None:
        """Track which opportunities persist vs disappear"""
        # This would ideally be stored in a database, but for now we'll log it
        logger.info(f"📊 OPPORTUNITY FOUND: {home_team} vs {away_team} - {profit_percentage:.2f}% profit - ID: {opportunity_id}")
    
    # _trace_data_flow REMOVED for performance optimization

    async def _find_arbitrage_in_odds(self, odds: Dict[str, Any], event_id: str, home_team: str, away_team: str, start_time: str, game_type: str, sport: str = "FOOTBALL", league: str = "NFL") -> Optional[Dict[str, Any]]:
        
        # CRITICAL: Block stale data at odds level (events before October 2025)
        if start_time and start_time < "2025-10-01":
            logger.debug(f"🔴 STALE DATA BLOCKED: {home_team} vs {away_team} - {start_time}")
            return None
        
        # HARDCODED NHL BLOCKING - REMOVED TO ENABLE HOCKEY
        # if self._is_nhl_event(home_team, away_team):
        #     logger.error(f"🔴 NHL BLOCKED (ALGORITHM): {home_team} vs {away_team}")
        #     return None
        
        """Find arbitrage opportunities in odds data using Pro plan byBookmaker structure"""
        
        # CRITICAL: Filter out TENNIS block removed
        # if sport == "TENNIS" or "tennis" in sport.lower():
        #     logger.warning(f"🚫 FILTERED: Tennis sport not implemented - {home_team} vs {away_team}")
        #     return None
        
        # CRITICAL: Filter out generic/placeholder team names
        generic_team_names = ["home", "away", "team a", "team b", "team 1", "team 2", "tbd", "tba"]
        if (home_team.lower() in generic_team_names or 
            away_team.lower() in generic_team_names or
            home_team.lower() == away_team.lower() or
            len(home_team) < 2 or len(away_team) < 2):
            # logger.warning(f"🚫 FILTERED: Generic team names detected - {home_team} vs {away_team}")
            return None
            
        try:
            if self.__class__._request_count > 5: # Only log first 5 to avoid spam
                logger.debug(f"🔍 _find_arbitrage_in_odds: Starting analysis for {home_team} vs {away_team}") 
            else:
                logger.info(f"🔍 _find_arbitrage_in_odds: Starting analysis for {home_team} vs {away_team}")
            
            # Reduced logging to prevent Railway rate limiting
            logger.debug(f"🔍 Analysis: {home_team} vs {away_team} ({sport}/{league})")
            # DEBUG: Enhanced logging for specific games that should have opportunities
            football_games = ["virginia", "florida", "arizona", "tcu", "oregon", "houston"]
            soccer_games = ["juarez", "leon", "puebla", "guadalajara", "chivas"]
            
            # Yield control periodically to avoid blocking event loop
            if len(odds) > 100:
                await asyncio.sleep(0)
            
            # Initialize market grouping by unique identifiers
            markets_by_identifier = {}
            opportunities = []
            
            for i, (odd_id, odd_data) in enumerate(odds.items()):
                # Yield control every 50 markets to let other tasks run
                if i > 0 and i % 50 == 0:
                    await asyncio.sleep(0)
                # CRITICAL: Skip cancelled or ended odds
                if odd_data.get("cancelled", False) or odd_data.get("ended", False):
                    logger.debug(f"⏭️ SKIPPING: Odd cancelled/ended - {odd_id}")
                    continue
                
                # Extract market information for proper grouping
                market_info = self._get_market_info(odd_id, sport)
                
                # DEBUG: Reduced logging to prevent Railway rate limits
                # DEBUG: Enhanced market recognition logging
                # DEBUG LOGGING REMOVED FOR PERFORMANCE
                
                # Create standardized market identifier using FULL SGO structure to prevent incorrect grouping
                line_value = market_info.get("line")
                stat_id = market_info.get("stat_id", "unknown")
                stat_entity_id = market_info.get("stat_entity_id", "unknown") 
                period_id = market_info.get("period_id", "game")
                bet_type_id = market_info.get("bet_type_id", "ml")
                
                # Debug suspicious market identifiers - Reduced logging to prevent rate limits
                if "batting_totalBases" in odd_id:
                    logger.debug(f"🔍 MARKET ID DEBUG: {odd_id}")
                    logger.debug(f"🔍 Components: stat_id={stat_id}, entity={stat_entity_id}, period={period_id}, bet_type={bet_type_id}")
                    # Only show first 3 bookmakers to reduce log spam
                    by_bookmaker = odd_data.get("byBookmaker", {})
                    sample_bookmakers = list(by_bookmaker.items())[:3]
                    for bm_id, bm_data in sample_bookmakers:
                        line_val = bm_data.get("overUnder", "N/A")
                        logger.debug(f"   - {bm_id}: line={line_val}, odds={bm_data.get('odds', 'N/A')}")
                
                # Process ALL markets (no filtering)
                # Pro plan has odds in byBookmaker nested structure
                by_bookmaker = odd_data.get("byBookmaker", {})
                
                # DEBUG: Check if we have bookmaker data for target games
                target_games = ["arizona", "tcu", "oregon", "houston", "juarez", "leon", "puebla", "guadalajara", "chivas"]
                if any(team in home_team.lower() or team in away_team.lower() for team in target_games):
                    if not by_bookmaker:
                        # Only log moneyline/basic markets missing data
                        if "game-ml-" in odd_id or "game-sp-" in odd_id or "game-ou-" in odd_id:
                            # logger.info(f"🚨 NO BASIC DATA: {odd_id}")
                            pass
                    elif len(by_bookmaker) == 0:
                        if "game-ml-" in odd_id or "game-sp-" in odd_id:
                            logger.info(f"🚨 EMPTY BASIC DATA: {odd_id}")
                    else:
                        basic_markets = ["points-home-game-ml", "points-away-game-ml"]
                        if any(market in odd_id for market in basic_markets):
                            logger.info(f"🔍 BASIC ML: {odd_id} has {len(by_bookmaker)} bookmakers")
                
                if by_bookmaker:
                    # CRITICAL FIX: Process each bookmaker individually with their specific line values
                    # This prevents false arbitrage from comparing different line values
                    
                    for bookmaker_id, bookmaker_data in by_bookmaker.items():
                        # CRITICAL: Skip unavailable bookmakers, invalid odds, and stale data
                        if (not bookmaker_data.get("available", True) or
                            not bookmaker_data.get("odds") or
                            bookmaker_data.get("odds") in ["+100", "-100", "0"]):  # Skip placeholder odds
                            continue
                        
                        # CRITICAL: Skip extremely stale bookmaker data (before 2025)
                        last_updated_str = bookmaker_data.get("lastUpdatedAt", "")
                        if last_updated_str:
                            try:
                                last_updated = dateutil.parser.parse(last_updated_str)
                                
                                # Check for ancient data (pre-2025)
                                if last_updated.year < 2025:
                                    logger.debug(f"⚠️ STALE BOOKMAKER: {bookmaker_id} - {last_updated_str} (Ancient)")
                                    continue
                                
                                # Check for recent stale data (threshold)
                                now = datetime.now(timezone.utc)
                                if (now - last_updated).total_seconds() > (STALE_DATA_THRESHOLD_MINUTES * 60):
                                    if bookmaker_id.lower() in ["pinnacle", "bet365"]: # Log major bookmakers as warning
                                        logger.debug(f"⚠️ STALE ODDS BLOCKED: {bookmaker_id} - Age: {(now - last_updated).total_seconds()/60:.1f}m > {STALE_DATA_THRESHOLD_MINUTES}m")
                                    continue
                            except Exception:
                                pass # Ignore parse errors, rely on other checks
                        
                        # BOVADA FILTER: Skip Bovada for ALL soccer markets (consistently provides wrong/delayed data)
                        if (bookmaker_id.lower() == "bovada" and (sport == "SOCCER" or "soccer" in sport.lower())):
                            logger.debug(f"⚠️ BOVADA FILTERED: {odd_id} - blocking all Bovada soccer data due to inaccuracy")
                            continue
                        
                        # Extract bookmaker-specific line value (overUnder for totals, spread for spreads, None for moneylines)
                        bookmaker_line = bookmaker_data.get("overUnder") or bookmaker_data.get("spread")
                        # Don't skip if no line - moneylines don't have line values
                        
                        # DEBUG: Log bookmaker diversity for key markets
                        if "points-all-game-ou-over" in odd_id or "points-home-game-ml-home" in odd_id:
                            logger.debug(f"📊 BOOKMAKER: {odd_id} @ {bookmaker_id} - Line: {bookmaker_line} | Odds: {bookmaker_data.get('odds')} | Available: {bookmaker_data.get('available', True)}")
                        
                        # Convert line to float if it exists, otherwise keep as None for moneylines
                        if bookmaker_line is not None:
                            try:
                                bookmaker_line = float(bookmaker_line)
                            except (ValueError, TypeError):
                                continue  # Skip bookmakers with invalid line values
                        
                        # CRITICAL: Validate bookmaker data quality
                        american_odds = bookmaker_data.get("odds", "+100")
                        
                        # DEBUG: Log Bovada odds specifically to track data quality issues
                        if bookmaker_id.lower() == "bovada":
                            if self._is_soccer_sport(sport) and bet_type_id == "ou" and stat_entity_id == "all":
                                logger.debug(f"🎲 BOVADA SOCCER: {odd_id} -> {american_odds} @ line {bookmaker_line}")
                            elif sport == "BASEBALL" and bet_type_id == "ou" and stat_entity_id == "all":
                                # Reduced logging - removed Bovada baseball debug spam
                                pass
                        # Skip suspicious data
                        if self._is_suspicious_bookmaker_data(bookmaker_id, american_odds, bookmaker_line, sport):
                            if "batting_" in odd_id or bookmaker_id.lower() == "unknown":
                                logger.debug(f"⚠️ SKIPPING SUSPICIOUS: {bookmaker_id} with odds {american_odds} (likely placeholder/test data)")
                                continue
                                
                        # DEBUG: Log basic markets for target games (REDUCED to prevent rate limits)
                        target_games = ["arizona", "tcu", "oregon", "houston", "juarez", "leon", "puebla", "guadalajara", "chivas"]
                        if any(team in home_team.lower() or team in away_team.lower() for team in target_games):
                            basic_markets = ["points-home-game-ml", "points-away-game-ml"]  # Focus on moneylines only
                            if any(market in odd_id for market in basic_markets):
                                if bookmaker_line:
                                    logger.debug(f"📊 ML LINE: {odd_id} -> {bookmaker_line} @ {bookmaker_id}")
                                else:
                                    logger.debug(f"📊 ML NO LINE: {odd_id} @ {bookmaker_id}")
                        
                        # Create unique market identifier using MarketGrouper logic
                        # This replaces the manual string concatenation that caused strict matching issues
                        
                        # Construct a temporary odd object for the grouper
                        temp_odd = {
                            'event_id': event_id,
                            'market_type': market_info.get("market_type"),
                            'period_id': period_id,
                            'stat_id': stat_id,
                            'stat_entity_id': stat_entity_id,
                            'line': bookmaker_line
                        }
                        
                        unique_market_id = MarketGrouper._generate_group_key(temp_odd)
                        
                        if not unique_market_id:
                            continue
                            unique_market_id = f"{stat_id}_{stat_entity_id}_{period_id}_{bet_type_id}"
                        
                        # DENSE DEBUG: Log market grouping for soccer totals (pack info into one line)
                        if sport == "SOCCER" and bet_type_id == "ou" and "palmeiras" in home_team.lower():
                            logger.error(f"🔍 SOCCER MARKET: {odd_id} → {unique_market_id} | {bookmaker_id}@{bookmaker_line} | odds:{bookmaker_data.get('odds')}")
                        
                        # Debug for batting_totalBases - Show actual line values being used
                        if "batting_totalBases" in unique_market_id:
                            logger.debug(f"🔍 CREATING MARKET: {unique_market_id} @ {bookmaker_id}")
                            logger.debug(f"   - Line Value: {bookmaker_line}")
                            logger.debug(f"🔴 PROCESSING EVENT: {event.get('name', event.get('eventID', 'Unknown'))}")
                            logger.debug(f"   - Odds: {bookmaker_data.get('odds', 'N/A')}")
                        
                        # Initialize market grouping if not exists
                        if unique_market_id not in markets_by_identifier:
                            markets_by_identifier[unique_market_id] = {
                                "market_info": {
                                    **market_info,
                                    "line": bookmaker_line if bookmaker_line is not None else 0
                                },
                                "odds_data": {}
                            }
                        
                        # Add this bookmaker's odds to the market group
                        side = market_info.get("side_id", "unknown")
                        
                        # DEBUG: Check for side_id issues in target games
                        target_games = ["arizona", "tcu", "oregon", "houston", "juarez", "leon", "puebla", "guadalajara", "chivas"]
                        if any(team in home_team.lower() or team in away_team.lower() for team in target_games):
                            basic_markets = ["points-home-game-ml", "points-away-game-ml", "points-all-game-ou"]
                            if any(market in odd_id for market in basic_markets):
                                if side == "unknown":
                                    logger.info(f"🚨 UNKNOWN SIDE: {odd_id} -> side={side}")
                                else:
                                    logger.debug(f"✅ GOOD SIDE: {odd_id} -> side={side}")
                        
                        if side not in markets_by_identifier[unique_market_id]["odds_data"]:
                            markets_by_identifier[unique_market_id]["odds_data"][side] = {}
                            
                        # Convert odds to decimal
                        american_odds = bookmaker_data.get("odds", "+100")
                        try:
                            decimal_odds = self._american_to_decimal(american_odds)
                        except:
                            continue
                            
                        markets_by_identifier[unique_market_id]["odds_data"][side][bookmaker_id] = {
                            "odds": decimal_odds,
                            "american_odds": american_odds,
                            "bookmaker": bookmaker_id,
                            "line": bookmaker_line if bookmaker_line is not None else 0,
                            "validation": {
                                "is_valid": True,
                                "issues": [],
                                "data_age_hours": 0,
                                "bookmaker_confidence": self._get_bookmaker_confidence(bookmaker_id)
                            }
                        }
                    else:
                        # If no byBookmaker data, skip this odd_id
                        continue
            
            # Process all grouped markets for arbitrage opportunities (dense logging)
            if len(markets_by_identifier) > 0:
                market_types = list(set([data["market_info"]["market_type"] for data in markets_by_identifier.values()]))
                logger.debug(f"📊 MARKETS: {home_team} vs {away_team} | {len(markets_by_identifier)} markets | types: {market_types[:5]}")
            
            for market_id, market_data in markets_by_identifier.items():
                market_info = market_data["market_info"]
                odds_data = market_data["odds_data"]
                
                # Debug batting_totalBases markets
                if "batting_totalBases" in market_id:
                    logger.debug(f"🔍 ANALYZING MARKET: {market_id}")
                    logger.debug(f"   - Line: {market_info.get('line')}")
                    logger.debug(f"   - Sides available: {list(odds_data.keys())}")
                    for side, bookmakers in odds_data.items():
                        logger.debug(f"🔴 BOOKMAKERS FOUND: {len(bookmakers)} bookmakers")
                
                # Need at least 2 sides for arbitrage
                if len(odds_data) < 2:
                    logger.debug(f"⏭️ SKIPPING: Market {market_id} - only {len(odds_data)} sides")
                    continue
                    
                # Find best odds for each side
                best_odds = {}
                for side, bookmaker_odds in odds_data.items():
                    if not bookmaker_odds:
                        # DEBUG: Log why we have no bookmaker odds for this side
                        if any(team in home_team.lower() or team in away_team.lower() for team in ["arizona", "tcu", "oregon", "houston", "juarez", "leon", "puebla", "guadalajara", "chivas"]):
                            logger.info(f"🚨 NO BOOKMAKERS FOR SIDE: {market_id} - {side}")
                        continue
                        
                    # Find bookmaker with best odds for this side
                    best_bookmaker = max(bookmaker_odds.items(), key=lambda x: x[1]["odds"])
                    best_odds[side] = best_bookmaker[1]
                
                # Check if we have at least 2 sides with valid odds
                if len(best_odds) >= 2:
                    # CRITICAL VALIDATION: Skip opportunities with None/invalid line values
                    line_value = market_info.get("line")
                    if line_value is None:
                        logger.info(f"⚠️ SKIPPING: Market {market_id} has None line value - preventing false arbitrage")
                        continue
                    
                    # ADDITIONAL VALIDATION: Ensure all best odds have the same line value
                    line_values = set()
                    for side, odds_info in best_odds.items():
                        line_val = odds_info.get("line")
                        if line_val is not None:
                            line_values.add(line_val)
                    
                    if len(line_values) > 1:
                        logger.info(f"⚠️ SKIPPING: Market {market_id} has mismatched line values {line_values} - preventing false arbitrage")
                        continue
                    
                    if len(line_values) == 0:
                        logger.info(f"⚠️ SKIPPING: Market {market_id} has no valid line values - preventing false arbitrage")
                        continue
                    
                # CRITICAL VALIDATION: Prevent false positives
                bookmakers_used = [odds_info["bookmaker"] for odds_info in best_odds.values()]
                unique_bookmakers_count = len(set(bookmakers_used))
                
                # Reduced logging - only log successful arbitrage

                # STRICT RULE 1: Reject if same bookmaker on both sides (critical false positive prevention)
                if unique_bookmakers_count < 2:
                    # Reduced logging to prevent rate limiting
                    continue

                # STRICT RULE 2: Check for suspicious patterns before calculating profit
                if self._has_suspicious_arbitrage_pattern(best_odds, market_id, sport):
                    logger.debug(f"⚠️ SUSPICIOUS PATTERN: {market_id}")
                    continue
                                
                # Calculate arbitrage (reduced logging)
                total_implied_prob = sum(1/odds_data["odds"] for odds_data in best_odds.values())
                
                if total_implied_prob < 1.0:
                    profit_percentage = ((1/total_implied_prob - 1) * 100)
                    
                    # CRITICAL: Filter out 0% or near-0% arbitrage (not real opportunities)
                    if profit_percentage < 0.01:
                        continue
                    
                    # PROFIT HANDLING: Show ALL opportunities with confidence warnings
                    confidence = "high"
                    note = ""
                    
                    if profit_percentage > 10.0:
                        confidence = "low"
                        note = "Very high profit - verify odds quickly, may be stale data"
                        logger.debug(f"⚠️ HIGH PROFIT OPPORTUNITY: {profit_percentage:.2f}% - {market_id}")
                    elif profit_percentage > 5.0:
                        confidence = "medium" 
                        note = "High profit - verify odds before betting"
                        logger.debug(f"📈 MEDIUM PROFIT OPPORTUNITY: {profit_percentage:.2f}% - {market_id}")
                    else:
                        logger.debug(f"✅ NORMAL PROFIT OPPORTUNITY: {profit_percentage:.2f}% - {market_id}")
                    
                    # FINAL NHL BLOCKING - REMOVED TO ENABLE HOCKEY
                    # nhl_teams = ['MAPLE LEAFS', 'RANGERS', 'SHARKS', 'WILD', 'STARS', 'DUCKS', 'PENGUINS', 'HURRICANES', 'PREDATORS']
                    # event_name = f"{home_team} {away_team}".upper()
                    # 
                    # if any(team in event_name for team in nhl_teams):
                    #     logger.error(f"🔴 FINAL NHL BLOCK: {home_team} vs {away_team} - NHL team detected at opportunity creation")
                    #     continue
                    
                    # Create opportunity object
                    opportunity = {
                        "id": f"sgo_pro_{game_type.lower()}_{event_id}_{market_info['market_type']}",
                        "sport": sport,
                        "league": league,
                        "home_team": home_team,
                        "away_team": away_team,
                        "start_time": start_time,
                        "market_type": market_info["market_type"],
                        "market_description": market_info.get("detailed_market_description", market_info["market_description"]),
                        "profit_percentage": round(profit_percentage, 2),
                        "best_odds": best_odds,
                        "line": line_value,
                        "confidence_score": 0.8,
                        "confidence": confidence,
                        "note": note,
                        "last_updated": datetime.now(timezone.utc).isoformat(), # Mark as fresh if validated
                        "bookmakers": [odds_data["bookmaker"] for odds_data in best_odds.values()]
                    }
                    
                    # Log arbitrage opportunities with sport-specific emojis and detailed odds info
                    if sport in ["NFL", "NCAAF", "FOOTBALL"] or "football" in sport.lower():
                        logger.info(f"🏈 FOOTBALL ARBITRAGE CREATED: {home_team} vs {away_team} - {profit_percentage:.2f}% profit")
                    elif self._is_soccer_sport(sport) or "soccer" in sport.lower():
                        logger.info(f"⚽ SOCCER ARBITRAGE CREATED: {home_team} vs {away_team} - {profit_percentage:.2f}% profit")
                        # Log detailed odds for soccer to help debug Bovada issues - CHANGED TO DEBUG
                        logger.debug(f"⚽ SOCCER ARB DETAILS: {market_info['market_description']} @ line {market_info.get('line')}")
                        for side, odds_info in best_odds.items():
                             logger.debug(f"  └─ {side}: {odds_info['bookmaker']} @ {odds_info['american_odds']}")
                    elif sport == "BASEBALL":
                         logger.info(f"⚾ BASEBALL ARBITRAGE CREATED: {home_team} vs {away_team} - {profit_percentage:.2f}% profit")
                         # Log detailed odds for baseball to help debug phantom line issues - CHANGED TO DEBUG
                         logger.debug(f"⚾ BASEBALL ARB DETAILS: {market_info['market_description']} @ line {market_info.get('line')}")
                         for side, odds_info in best_odds.items():
                             logger.debug(f"  └─ {side}: {odds_info['bookmaker']} @ {odds_info['american_odds']}")
                    else:
                        logger.info(f"🚨 ARBITRAGE CREATED: {home_team} vs {away_team} - {profit_percentage:.2f}% profit")
                    
                    logger.debug(f"🔍 Market ID: {market_id}")
                    logger.debug(f"🔍 Market Description: {market_info['market_description']}")
                    logger.debug(f"🔍 Detailed Description: {market_info.get('detailed_market_description', 'N/A')}")
                    logger.debug(f"🔍 Market Type: {market_info['market_type']}")
                    logger.debug(f"🔍 Line: {market_info.get('line')}")
                    logger.debug(f"🔍 Best Odds: {best_odds}")
                    logger.debug(f"🔍 Bookmakers: {[odds_info['bookmaker'] for odds_info in best_odds.values()]}")
                    logger.debug(f"🔍 Stat Entity ID: {market_info.get('stat_entity_id', 'N/A')}")
                    logger.info(f"✅ ARBITRAGE OPPORTUNITY VALIDATED AND CREATED")
                    
                    # SUCCESS: Dense logging when opportunity is created (pack all critical info)
                    bookmaker_list = [f"{side}:{info['bookmaker']}@{info['american_odds']}" for side, info in best_odds.items()]
                    logger.debug(f"🎉 ARBITRAGE: {home_team} vs {away_team} | {market_id} | {profit_percentage:.2f}% | {' | '.join(bookmaker_list)}")
                    opportunities.append(opportunity)
        
            # CRITICAL: Always log opportunity results with detailed breakdown
            if len(opportunities) > 0:
                logger.debug(f"🎉 SUCCESS: {home_team} vs {away_team} - {len(opportunities)} opportunities found")
            else:
                # Log why no opportunities were found
                total_markets = len(markets_by_identifier)
                logger.debug(f"🔴 NO ARBITRAGE: {home_team} vs {away_team} - {total_markets} markets processed, 0 opportunities (check: same bookmaker, line mismatch, low profit)")
                
                if any(team in home_team.lower() or team in away_team.lower() for team in football_games + soccer_games):
                    # Reduce noise: changed from info to debug
                    logger.debug(f"❌ NO ARBITRAGE: {home_team} vs {away_team} - {len(markets_by_identifier)} markets processed")
                    
                    # Show basic game markets and their line values for debugging
                    basic_markets = {k: v for k, v in markets_by_identifier.items() if "game" in k and ("ml" in k or "sp" in k or "ou" in k)}
                    if basic_markets:
                        logger.debug(f"🔴 MARKETS FOUND: {len(basic_markets)} markets")
                        for market_id, data in list(basic_markets.items())[:3]:
                            # Count total bookmakers across all sides
                            total_bookmakers = sum(len(side_data) for side_data in data.get('odds_data', {}).values())
                            logger.debug(f"   📊 {market_id}: {total_bookmakers} bookmakers")
                        
                            # CRITICAL DEBUG: For soccer total goals, show detailed breakdown
                            if "points_all_game_ou_2.5" in market_id:
                                sides_data = data.get('odds_data', {})
                                logger.debug(f"   🔍 SOCCER TOTAL BREAKDOWN:")
                                for side, bookmaker_data in sides_data.items():
                                    logger.debug(f"     {side}: {len(bookmaker_data)} bookmakers")
                                    if len(bookmaker_data) > 0:
                                        sample_books = list(bookmaker_data.keys())[:3]
                                        logger.debug(f"     Sample books: {sample_books}")
                                        for book in sample_books:
                                            odds = bookmaker_data[book].get('odds', 'N/A')
                                            logger.debug(f"       {book}: {odds}")
                    else:
                        logger.debug(f"🚨 NO BASIC GAME MARKETS FOUND")
            
            if len(opportunities) > 0:
                logger.debug(f"✅ Found {len(opportunities)} arbitrage opportunities for {home_team} vs {away_team}")
            else:
                logger.debug(f"✅ Found 0 arbitrage opportunities for {home_team} vs {away_team}")
            
            # Return the first opportunity if any were found
            if opportunities:
                return opportunities[0]
            
            # No arbitrage opportunities found
            logger.debug(f"🔍 _find_arbitrage_in_odds: Completed analysis for {home_team} vs {away_team} - no arbitrage found")
            return None
        
        except Exception as e:
            logger.error(f"Error finding arbitrage in odds: {str(e)}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            return None

    def _is_suspicious_bookmaker_data(self, bookmaker_id: str, american_odds: str, line_value: float, sport: str = "UNKNOWN") -> bool:
        """
        Detect suspicious bookmaker data that could create false arbitrage opportunities.
        
        Based on analysis of real data patterns:
        - Underdog consistently returns +100 odds regardless of actual market
        - This creates false arbitrage when compared to legitimate bookmaker odds
        - Bovada and some bookmakers show phantom lines (e.g., 6.5 when only 6.0/7.0 exist)
        """
        
        # Convert odds for analysis
        try:
            odds_value = american_odds.replace('+', '').replace('-', '')
            odds_numeric = int(odds_value)
        except (ValueError, AttributeError):
            return True  # Invalid odds format is suspicious
        
        # Pattern 1: DFS/Fantasy platform filtering - these create fake arbitrage opportunities
        fantasy_platforms = ["underdog", "prizepicks", "superpicks", "parlayplay"]
        if bookmaker_id.lower() in fantasy_platforms:
            # DFS/Fantasy platforms consistently create fake arbitrage - always filter
            return True
        
        # Pattern 2: "Unknown" bookmaker - always suspicious regardless of odds
        if bookmaker_id.lower() == "unknown":
            return True
        
        # Pattern 3: Any bookmaker consistently using +100 (even odds) which is suspicious for player props
        if american_odds == "+100" and bookmaker_id.lower() in ["unknown", "generic", "placeholder"]:
            return True
        
        # Pattern 4: Extremely suspicious odds patterns
        if odds_numeric == 100 and american_odds.startswith('+'):
            # +100 odds are statistically unlikely for most player props
            # Real player props typically have odds like -110, +120, -150, etc.
            suspicious_bookmakers = ["underdog", "unknown", "generic", "test", "demo"]
            if any(suspicious in bookmaker_id.lower() for suspicious in suspicious_bookmakers):
                return True
        
        # Pattern 5: Phantom half-point lines for baseball totals from Bovada
        # Bovada typically offers: 5.0, 5.5, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5
        # They do NOT offer: 6.5, 10.5, 11.5 etc. (these are phantom SGO interpolations)
        if bookmaker_id.lower() == "bovada" and line_value is not None:
            # Check if this is a baseball total (typically in range 5-12)
            # Only apply strict phantom line checks to Baseball
            is_baseball = sport == "BASEBALL" or "baseball" in str(line_value).lower() # Context check as fallback
            
            if is_baseball and 5 <= line_value <= 12:
                # Check for suspicious half-point lines
                if line_value in [6.5, 10.5, 11.5]:
                    logger.warning(f"⚠️ PHANTOM LINE: Bovada showing {line_value} (line doesn't exist on their site)")
                return True
        
        return False

    def _has_suspicious_arbitrage_pattern(self, best_odds: dict, market_id: str, sport: str = "UNKNOWN") -> bool:
        """
        Detect suspicious arbitrage patterns that indicate fake opportunities.
        
        Common patterns:
        1. One bookmaker with suspiciously good odds (+100) vs others with normal odds (-180, etc.)
        2. Profit margins that are unrealistically high (>20%)
        3. Known problematic bookmaker combinations
        """
        
        if len(best_odds) < 2:
            return False
        
        # Extract odds and bookmakers
        odds_info = list(best_odds.values())
        bookmakers = [info["bookmaker"] for info in odds_info]
        american_odds = [info["american_odds"] for info in odds_info]
        decimal_odds = [info["odds"] for info in odds_info]
        
        # Pattern 1: Check for +100 odds combined with heavily negative odds (classic fake arbitrage)
        has_plus_100 = any(odds == "+100" for odds in american_odds)
        has_heavy_negative = any(odds.startswith("-") and int(odds[1:]) > 150 for odds in american_odds if odds.startswith("-"))
        
        if has_plus_100 and has_heavy_negative:
            logger.info(f"🚫 REJECTED: Suspicious +100/-150+ pattern in {market_id}")
            return True
        
        # Pattern 2: Check for unrealistic profit margins (>8% is very suspicious for real arbitrage)
        total_implied_prob = sum(1/odds for odds in decimal_odds)
        if total_implied_prob < 1.0:
            profit_percentage = ((1/total_implied_prob - 1) * 100)
            if profit_percentage > 8.0:  # Real arbitrage rarely exceeds 5%, >8% is almost always false positive
                # Reduced logging - silent rejection of suspicious profits
                logger.info(f"🚫 REJECTED: Unrealistic profit {profit_percentage:.2f}% in {market_id}")
                return True
        
        # Pattern 3: CRITICAL - Same bookmaker arbitrage (mathematically impossible)
        unique_bookmakers = set(bookmakers)
        if len(unique_bookmakers) < 2:
            logger.info(f"🚫 REJECTED: Single bookmaker {unique_bookmakers} in {market_id} (Need at least 2)")
            return True  # Cannot have arbitrage with the same bookmaker
        
        # Pattern 4: Known problematic bookmaker combinations (DFS/Fantasy platforms)
        suspicious_bookmakers = ["underdog", "prizepicks", "superpicks", "parlayplay", "unknown", "generic", "test", "demo"]
        if any(bm.lower() in suspicious_bookmakers for bm in bookmakers):
            # DFS/Fantasy platforms create fake arbitrage opportunities - always reject
                return True
        
        # Pattern 5: Check for phantom lines that don't exist on bookmaker sites
        for side, odds_data in best_odds.items():
            line_value = odds_data.get("line")
            bookmaker = odds_data.get("bookmaker", "")
            
            if self._is_phantom_line(bookmaker, line_value, market_id, sport):
                logger.info(f"🚫 PHANTOM LINE: {bookmaker} @ {line_value} in {market_id}")
                return True
        
        return False

    def _is_phantom_line(self, bookmaker: str, line_value: float, market_id: str, sport: str = "UNKNOWN") -> bool:
        """
        Detect phantom lines that don't exist on actual bookmaker sites.
        These are often SGO interpolations or stale data.
        """
        if line_value is None:
            return False
            
        bookmaker_lower = bookmaker.lower()
        
        # Bovada phantom lines (from logs warning)
        if bookmaker_lower == "bovada":
            # Baseball totals: Bovada typically offers 5.0, 5.5, 6.0, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5
            # They do NOT offer: 6.5, 10.5, 11.5 (these are phantom)
            is_baseball = sport == "BASEBALL" or "baseball" in market_id.lower() or "mlb" in market_id.lower()
            if is_baseball:
                if 5 <= line_value <= 12:
                    phantom_lines = {6.5, 10.5, 11.5, 12.5}
                    if line_value in phantom_lines:
                        logger.warning(f"⚠️ PHANTOM LINE DETECTED: {bookmaker} @ {line_value} (doesn't exist on site)")
                        return True
        
        # Add other known phantom line patterns here
        # Example: DraftKings doesn't offer certain quarter lines
        # Example: FanDuel doesn't offer certain player prop lines
        
        return False

    def _is_nhl_event(self, team1: str, team2: str) -> bool:
        """Hardcoded NHL blocking - check team names against NHL list"""
        team1_lower = team1.lower() if team1 else ''
        team2_lower = team2.lower() if team2 else ''
        
        for nhl_team in self.NHL_TEAMS:
            if nhl_team in team1_lower or nhl_team in team2_lower:
                return True
        return False

    def _extract_team_names(self, event: Dict[str, Any]) -> tuple:
        """Extract team names from SGO event - comprehensive extraction"""
        # Try multiple paths for team names based on actual SGO structure
        home_team = 'Unknown'
        away_team = 'Unknown'
        
        # Method 1: Direct homeTeam/awayTeam fields
        if event.get('homeTeam'):
            home_team = event['homeTeam']
        if event.get('awayTeam'):
            away_team = event['awayTeam']
            
        # Method 2: teams.home/away.name structure
        if home_team == 'Unknown' and event.get('teams'):
            teams = event['teams']
            if teams.get('home', {}).get('name'):
                home_team = teams['home']['name']
            if teams.get('away', {}).get('name'):
                away_team = teams['away']['name']
                
        # Method 3: teams.home/away.names.medium structure  
        if home_team == 'Unknown' and event.get('teams'):
            teams = event['teams']
            if teams.get('home', {}).get('names', {}).get('medium'):
                home_team = teams['home']['names']['medium']
            if teams.get('away', {}).get('names', {}).get('medium'):
                away_team = teams['away']['names']['medium']
                
        # Method 4: participants array
        participants = event.get('participants', [])
        if home_team == 'Unknown' and len(participants) >= 2:
            if participants[0].get('name'):
                home_team = participants[0]['name']
            if participants[1].get('name'):
                away_team = participants[1]['name']
                
        # Method 5: Extract from eventName if available (e.g., "Team A vs Team B")
        if home_team == 'Unknown' and event.get('eventName'):
            event_name = event['eventName']
            if ' vs ' in event_name:
                parts = event_name.split(' vs ')
                if len(parts) == 2:
                    home_team = parts[0].strip()
                    away_team = parts[1].strip()
            elif ' @ ' in event_name:
                parts = event_name.split(' @ ')
                if len(parts) == 2:
                    away_team = parts[0].strip()
                    home_team = parts[1].strip()
        
        return home_team, away_team

    def _is_sport_enabled(self, event: Dict[str, Any]) -> bool:
        """Check if event sport is in our enabled sports list - COMPREHENSIVE HOCKEY BLOCKING"""
        # Extract team names using improved extraction
        home_team, away_team = self._extract_team_names(event)
        
        # COMPREHENSIVE HOCKEY BLOCKING - REMOVED TO ENABLE HOCKEY
        # if self._is_nhl_event(home_team, away_team):
        #     logger.error(f"🔴 CRITICAL: NHL BLOCKED - {home_team} vs {away_team}")
        #     return False
        
        # Extract sport from event (check both 'sport' and 'sportID' fields)
        sport = event.get('sportID', event.get('sport', '')).upper()
        league = event.get('leagueID', '').upper()
        
        # BLOCK ALL HOCKEY SPORTS (not just NHL) - REMOVED TO ENABLE HOCKEY
        # hockey_indicators = ['HOCKEY', 'NHL', 'SHL', 'KHL', 'AHL', 'IIHF', 'ICE_HOCKEY', 'ICEHOCKEY']
        # if any(indicator in sport for indicator in hockey_indicators) or any(indicator in league for indicator in hockey_indicators):
        #     logger.error(f"🔴 HOCKEY BLOCKED: {sport}/{league} - {home_team} vs {away_team}")
        #     return False
        
        # Debug: Log what sports are being processed
        if sport in self.ENABLED_SPORTS:
            logger.debug(f"✅ SPORT ENABLED: {sport} - {home_team} vs {away_team}")
        
        # Block non-enabled sports
        if sport not in self.ENABLED_SPORTS and sport not in ['UNKNOWN', '']:
            # Tennis block removed
            logger.error(f"🔴 SPORT NOT ENABLED: {sport} - {home_team} vs {away_team}")
            return False
            
        return True

    def _get_sport_terminology(self, sport: str) -> Dict[str, str]:
        """
        Get sport-specific terminology for points/goals/runs per SGO documentation.
        
        Args:
            sport: Sport identifier (e.g., "BASEBALL", "BASKETBALL", "SOCCER", etc.)
            
        Returns:
            Dict with 'unit' and 'spread_name' for the sport
        """
        sport_upper = sport.upper()
        
        # Baseball leagues use "runs" (per SGO baseball docs)
        if any(baseball_indicator in sport_upper for baseball_indicator in ['BASEBALL', 'MLB', 'KBO', 'NPB', 'CPBL']):
            return {
                'unit': 'Runs',
                'spread_name': 'Run Line'
            }
        
        # American Football leagues use "points" (NFL, NCAAF, CFL, USFL, XFL)
        elif any(football_indicator in sport_upper for football_indicator in ['NFL', 'NCAAF', 'CFL', 'USFL', 'XFL', 'AMERICAN_FOOTBALL']):
            return {
                'unit': 'Points',
                'spread_name': 'Spread'
            }
        
        # Soccer leagues use "goals" (excluding American football)
        elif any(soccer_indicator in sport_upper for soccer_indicator in ['SOCCER', 'EPL', 'BUNDESLIGA', 'LA_LIGA', 'SERIE_A', 'CHAMPIONS', 'UEFA']) and not any(football_indicator in sport_upper for football_indicator in ['NFL', 'NCAAF', 'CFL', 'USFL', 'XFL']):
            return {
                'unit': 'Goals',
                'spread_name': 'Goal Spread'
            }
        
        # Hockey leagues use "goals"
        elif any(hockey_indicator in sport_upper for hockey_indicator in ['HOCKEY', 'NHL', 'KHL']):
            return {
                'unit': 'Goals', 
                'spread_name': 'Puck Line'
            }
        
        # Handball leagues use "goals"
        elif 'HANDBALL' in sport_upper:
            return {
                'unit': 'Goals',
                'spread_name': 'Goal Spread'
            }
        
        # MMA leagues use "points" (for winner) but have specific terminology
        elif any(mma_indicator in sport_upper for mma_indicator in ['MMA', 'UFC', 'BELLATOR', 'PFL']):
            return {
                'unit': 'Points',
                'spread_name': 'Point Spread'
            }
            
        # Tennis leagues use "games" and "sets"
        elif any(tennis_indicator in sport_upper for tennis_indicator in ['TENNIS', 'ATP', 'WTA', 'ITF']):
            return {
                'unit': 'Games',
                'spread_name': 'Game Handicap'
            }
        
        # Basketball, Football (American), and others use "points"
        else:
            return {
                'unit': 'Points',
                'spread_name': 'Point Spread'
            }
    
    def _get_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name from SGO period ID.
        
        Args:
            period_id: Period identifier (e.g., "1h", "1ix3", "1i", "game")
            
        Returns:
            Human-readable period name
        """
        period_mapping = {
            "game": "Full Game",
            "1h": "1st Half", 
            "2h": "2nd Half",
            # Individual innings
            "1i": "1st Inning",
            "2i": "2nd Inning", 
            "3i": "3rd Inning",
            "4i": "4th Inning",
            "5i": "5th Inning",
            "6i": "6th Inning", 
            "7i": "7th Inning",
            "8i": "8th Inning",
            "9i": "9th Inning",
            # Multi-inning periods
            "1ix3": "1st 3 Innings",
            "1ix4": "1st 4 Innings", 
            "1ix5": "1st 5 Innings",
            "1ix6": "1st 6 Innings",
            "1ix7": "1st 7 Innings",
            "1ix8": "1st 8 Innings", 
            "1ix9": "1st 9 Innings",
            "1p": "1st Period",
            "2p": "2nd Period", 
            "3p": "3rd Period",
            "ot": "Overtime",
            "reg": "Regulation"
        }
        
        # If not in mapping, generate dynamically for baseball periods
        if period_id not in period_mapping:
            import re
            
            # Individual innings: 1i -> "1st Inning", 2i -> "2nd Inning", etc.
            inning_match = re.match(r'^(\d+)i$', period_id)
            if inning_match:
                inning_num = int(inning_match.group(1))
                ordinal = self._get_ordinal(inning_num)
                return f"{ordinal} Inning"
                
            # Multi-inning periods: 1ix4 -> "1st 4 Innings", 1ix7 -> "1st 7 Innings"
            multi_inning_match = re.match(r'^1ix(\d+)$', period_id)
            if multi_inning_match:
                num_innings = multi_inning_match.group(1)
                return f"1st {num_innings} Innings"
        
        return period_mapping.get(period_id, period_id.upper())
    
    def _is_baseball_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a baseball period (excluding 'game').
        
        Handles patterns like:
        - Halves: 1h, 2h
        - Individual innings: 1i, 2i, 3i, 4i, 5i, 6i, 7i, 8i, 9i
        - Multi-inning periods: 1ix3, 1ix4, 1ix5, 1ix6, 1ix7, 1ix8, 1ix9
        - And potentially more complex patterns from SGO
        """
        if not period_id or period_id == "game":
            return False
            
        # Pattern matching for baseball periods
        import re
        
        # Half periods: 1h, 2h
        if re.match(r'^[12]h$', period_id):
            return True
            
        # Individual innings: 1i, 2i, ..., 9i (and beyond for extra innings)
        if re.match(r'^\d+i$', period_id):
            return True
            
        # Multi-inning periods: 1ix3, 1ix4, 1ix5, etc.
        if re.match(r'^1ix\d+$', period_id):
            return True
            
        # Other potential baseball period patterns can be added here
        return False
    
    def _get_ordinal(self, number: int) -> str:
        """Convert number to ordinal (1 -> '1st', 2 -> '2nd', etc.)"""
        if 10 <= number % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
        return f"{number}{suffix}"
    
    def _normalize_line_value(self, line_value, stat_id, bet_type_id):
        """Normalize line values to group similar lines for arbitrage detection"""
        if line_value is None:
            return None
            
        try:
            line_float = float(line_value)
            
            # For totals (over/under), group half-point differences
            if bet_type_id == "ou":
                # Round to nearest 0.5 for football/soccer totals
                if stat_id == "points":
                    return round(line_float * 2) / 2  # Groups 47.0 and 47.5 -> 47.5
                # Keep exact for baseball (already well-standardized)
                else:
                    return line_float
                    
            # For spreads, group quarter-point differences  
            elif bet_type_id == "sp":
                return round(line_float * 4) / 4  # Groups to nearest 0.25
                
            # For all other bet types, keep exact
            else:
                return line_float
                
        except (ValueError, TypeError):
            return line_value
    
    def _is_baseball_stat(self, stat_id: str) -> bool:
        """Check if stat_id is a baseball-specific stat from SGO docs"""
        baseball_stat_prefixes = [
            'batting_', 'pitching_', 'fielding_', 'baserunning_', 
            'catching_', 'hitting_', 'offensive_', 'defensive_'
        ]
        
        baseball_stats = [
            'runs', 'hits', 'errors', 'assists', 'putouts', 'doublePlays',
            'triplePlays', 'leftOnBase', 'timeOfGame', 'attendance'
        ]
        
        return (any(stat_id.startswith(prefix) for prefix in baseball_stat_prefixes) or 
                stat_id in baseball_stats)
    
    def _parse_baseball_stat(self, stat_id: str, stat_entity_id: str, period_id: str, bet_type_id: str) -> Dict[str, str]:
        """
        Parse any baseball stat from SGO docs dynamically.
        
        This handles all the baseball stats that aren't explicitly coded above,
        providing consistent naming and period support for ANY stat from SGO docs.
        """
        result = {}
        
        # Clean up stat name for display
        if stat_id.startswith('batting_'):
            clean_stat = stat_id.replace('batting_', '').replace('_', ' ').title()
            stat_category = 'batting'
        elif stat_id.startswith('pitching_'):
            clean_stat = stat_id.replace('pitching_', '').replace('_', ' ').title()
            stat_category = 'pitching'
        elif stat_id.startswith('fielding_'):
            clean_stat = stat_id.replace('fielding_', '').replace('_', ' ').title()
            stat_category = 'fielding'
        else:
            clean_stat = stat_id.replace('_', ' ').title()
            stat_category = 'game'
        
        # Get period name for description
        period_name = self._get_period_name(period_id) if period_id != "game" else ""
        
        # Determine entity type and build market info
        if stat_entity_id in ["home", "away"]:
            # Team stat
            result["market_type"] = f"team_{stat_id}_{period_id}"
            result["market_description"] = f"{stat_entity_id.title()} Team {period_name} {clean_stat}".strip()
        elif stat_entity_id == "all":
            # Game total stat
            result["market_type"] = f"game_{stat_id}_{period_id}" 
            result["market_description"] = f"{period_name} Total {clean_stat}".strip()
        else:
            # Player stat
            player_name = self._extract_player_name(stat_entity_id)
            result["market_type"] = f"player_{stat_id}_{period_id}"
            result["market_description"] = f"{player_name} {period_name} {clean_stat}".strip()
            
            if bet_type_id == "ou":
                result["detailed_market_description"] = f"{player_name} {period_name} {clean_stat} Over/Under".strip()
        
        return result

    def _extract_player_name(self, stat_entity_id: str) -> str:
        """Extract and format player name from SGO stat_entity_id format (PLAYER_NAME_1_LEAGUE)"""
        try:
            # Remove the trailing _1_LEAGUE part (e.g., _1_MLB, _1_NFL, _1_NBA)
            # Split by underscore and take all parts except the last two
            parts = stat_entity_id.split("_")
            if len(parts) >= 3:
                # Take all parts except the last two (which are number and league)
                name_parts = parts[:-2]
                # Join with space and title case each word
                player_name = " ".join(part.title() for part in name_parts)
                return player_name
            else:
                # Fallback: just title case the whole thing
                return stat_entity_id.replace("_", " ").title()
        except Exception:
            # Fallback: return original with underscores replaced by spaces
            return stat_entity_id.replace("_", " ").title()

    def _american_to_decimal(self, american_odds: str) -> float:
        """Convert American odds to decimal odds"""
        try:
            odds = float(american_odds)
            if odds > 0:
                # Positive American odds
                return (odds / 100) + 1
            else:
                # Negative American odds
                return (100 / abs(odds)) + 1
        except (ValueError, TypeError):
            return 0.0
    
    def _is_basketball_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a basketball period (excluding 'game').
        
        Handles patterns like:
        - Halves: 1h, 2h
        - Quarters: 1q, 2q, 3q, 4q
        - Regulation: reg
        """
        if not period_id or period_id == "game":
            return False
            
        # Basketball period patterns (per SGO basketball docs)
        basketball_periods = ["1h", "2h", "1q", "2q", "3q", "4q", "reg"]
        return period_id in basketball_periods
    
    def _get_basketball_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for basketball periods.
        
        Args:
            period_id: Period identifier (e.g., "1h", "2q", "reg")
            
        Returns:
            Human-readable period name (e.g., "1st Half", "2nd Quarter", "Regulation")
        """
        period_names = {
            "1h": "1st Half",
            "2h": "2nd Half", 
            "1q": "1st Quarter",
            "2q": "2nd Quarter",
            "3q": "3rd Quarter",
            "4q": "4th Quarter",
            "reg": "Regulation"
        }
        return period_names.get(period_id, period_id.upper())
    
    def _is_football_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a football period (excluding 'game').
        
        Handles patterns like:
        - Halves: 1h, 2h
        - Quarters: 1q, 2q, 3q, 4q
        """
        if not period_id or period_id == "game":
            return False
            
        # Football period patterns (per SGO football docs)
        football_periods = ["1h", "2h", "1q", "2q", "3q", "4q", "reg"]
        return period_id in football_periods
    
    def _get_football_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for football periods.
        
        Args:
            period_id: Period identifier (e.g., "1h", "2q")
            
        Returns:
            Human-readable period name (e.g., "1st Half", "2nd Quarter")
        """
        period_names = {
            "1h": "1st Half",
            "2h": "2nd Half", 
            "1q": "1st Quarter",
            "2q": "2nd Quarter",
            "3q": "3rd Quarter",
            "4q": "4th Quarter",
            "reg": "Regulation"
        }
        return period_names.get(period_id, period_id.upper())
    
    def _is_soccer_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a soccer period (excluding 'game').
        
        Handles patterns like:
        - Halves: 1h, 2h
        - Regulation: reg
        """
        if not period_id or period_id == "game":
            return False
            
        # Soccer period patterns (per SGO soccer docs)
        soccer_periods = ["1h", "2h", "reg"]
        return period_id in soccer_periods
    
    def _get_soccer_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for soccer periods.
        
        Args:
            period_id: Period identifier (e.g., "1h", "2h", "reg")
            
        Returns:
            Human-readable period name (e.g., "1st Half", "2nd Half", "Regulation")
        """
        period_names = {
            "1h": "1st Half",
            "2h": "2nd Half", 
            "reg": "Regulation"
        }
        return period_names.get(period_id, period_id.upper())
    
    def _is_handball_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a handball period (excluding 'game').
        
        Handles patterns like:
        - Halves: 1h, 2h
        """
        if not period_id or period_id == "game":
            return False
            
        # Handball period patterns
        handball_periods = ["1h", "2h"]
        return period_id in handball_periods
    
    def _get_handball_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for handball periods.
        
        Args:
            period_id: Period identifier (e.g., "1h", "2h")
            
        Returns:
            Human-readable period name (e.g., "1st Half", "2nd Half")
        """
        period_names = {
            "1h": "1st Half",
            "2h": "2nd Half"
        }
        return period_names.get(period_id, period_id.upper())

    def _is_tennis_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a tennis period (excluding 'game').
        
        Handles patterns like:
        - Sets: 1s, 2s, 3s, 4s, 5s
        """
        if not period_id or period_id == "game":
            return False
            
        # Tennis period patterns
        tennis_periods = ["1s", "2s", "3s", "4s", "5s"]
        return period_id in tennis_periods
    
    def _get_tennis_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for tennis periods.
        
        Args:
            period_id: Period identifier (e.g., "1s", "2s")
            
        Returns:
            Human-readable period name (e.g., "1st Set", "2nd Set")
        """
        period_names = {
            "1s": "1st Set",
            "2s": "2nd Set",
            "3s": "3rd Set",
            "4s": "4th Set",
            "5s": "5th Set"
        }
        return period_names.get(period_id, period_id.upper())

    def _is_tennis_sport(self, sport: str) -> bool:
        """
        Check if the sport is tennis.
        
        Args:
            sport: Sport identifier
            
        Returns:
            True if tennis sport, False otherwise
        """
        sport_upper = sport.upper()
        tennis_indicators = ['TENNIS', 'ATP', 'WTA', 'ITF', 'CHALLENGER']
        return any(indicator in sport_upper for indicator in tennis_indicators)

    def _is_mma_period(self, period_id: str) -> bool:
        """
        Check if period_id represents an MMA period (excluding 'game').
        
        Handles patterns like:
        - Rounds: 1r, 2r, 3r, 4r, 5r
        """
        if not period_id or period_id == "game":
            return False
            
        # MMA period patterns
        import re
        return bool(re.match(r'^\d+r$', period_id))
    
    def _get_mma_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for MMA periods.
        
        Args:
            period_id: Period identifier (e.g., "1r")
            
        Returns:
            Human-readable period name (e.g., "Round 1")
        """
        if period_id == "game":
            return "Full Fight"
            
        import re
        match = re.match(r'^(\d+)r$', period_id)
        if match:
            return f"Round {match.group(1)}"
            
        return period_id.upper()

    def _is_soccer_sport(self, sport: str) -> bool:
        """
        Check if the sport is soccer/football (not American football).
        
        Args:
            sport: Sport identifier
            
        Returns:
            True if soccer sport, False otherwise
        """
        sport_upper = sport.upper()
        
        # CRITICAL FIX: American football must be checked FIRST to prevent misclassification
        american_football_indicators = ['NFL', 'NCAAF', 'CFL', 'USFL', 'XFL', 'FOOTBALL']
        
        # If it's American football, it's definitely NOT soccer
        if any(indicator in sport_upper for indicator in american_football_indicators):
            return False
            
        # Soccer-specific indicators (excluding ambiguous "FOOTBALL")
        soccer_indicators = [
            'SOCCER', 'EPL', 'BUNDESLIGA', 'LA_LIGA', 'LALIGA', 'LA LIGA', 
            'SERIE_A', 'SERIE A', 'CHAMPIONS', 'UEFA', 'MLS', 'LIGUE_1', 
            'LIGUE 1', 'BR_SERIE_A', 'BRAZILIAN', 'PRIMEIRA', 'LIGA_MX',
            'LIGA MX', 'INTERNATIONAL_SOCCER', 'EUROPA_LEAGUE', 'EUROPA LEAGUE',
            'CHAMPIONS_LEAGUE', 'CHAMPIONS LEAGUE'
        ]
        
        return any(indicator in sport_upper for indicator in soccer_indicators)
    
    def _get_bookmaker_confidence(self, bookmaker: str) -> str:
        """Get confidence level for bookmaker"""
        major_bookmakers = ["fanduel", "draftkings", "betmgm", "caesars", "espnbet", "pinnacle", "bet365"]
        if bookmaker.lower() in major_bookmakers:
            return "high"
        elif bookmaker.lower() in ["unknown", "test", "demo"]:
            return "low"
        else:
            return "medium"
    
    def _convert_american_to_decimal(self, american_odds: str) -> float:
        """Convert American odds to decimal odds"""
        try:
            odds = float(american_odds)
            if odds > 0:
                # Positive American odds
                return (odds / 100) + 1
            else:
                # Negative American odds
                return (100 / abs(odds)) + 1
        except (ValueError, TypeError):
            return 0.0

    def _is_hockey_period(self, period_id: str) -> bool:
        """
        Check if period_id represents a hockey period (excluding 'game').
        
        Handles patterns like:
        - Periods: 1p, 2p, 3p
        - Overtime: ot
        - Regulation: reg
        """
        if not period_id or period_id == "game":
            return False
            
        # Hockey period patterns
        hockey_periods = ["1p", "2p", "3p", "ot", "reg"]
        return period_id in hockey_periods
    
    def _get_hockey_period_name(self, period_id: str) -> str:
        """
        Get human-readable period name for hockey periods.
        
        Args:
            period_id: Period identifier (e.g., "1p", "ot")
            
        Returns:
            Human-readable period name (e.g., "1st Period", "Overtime")
        """
        period_names = {
            "1p": "1st Period",
            "2p": "2nd Period", 
            "3p": "3rd Period",
            "ot": "Overtime",
            "reg": "Regulation"
        }
        return period_names.get(period_id, period_id.upper())
