"""
SGO Limited Service - Works with Amateur tier limitations
Handles rate limiting and limited data gracefully
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class SGOLimitedService:
    """SGO service optimized for Amateur tier with rate limiting"""
    
    def __init__(self):
        self.api_key = os.getenv("SGO_API_KEY")
        self.base_url = "https://api.sportsgameodds.com/v2"
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = None
        self.min_request_interval = 2.0  # 2 seconds between requests (rookie plan)
        self.request_count = 0
        self.max_requests_per_minute = 45  # Leave buffer for 50/min limit
        
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
        """Conservative rate limiting for amateur tier"""
        if self.last_request_time:
            time_since_last = (datetime.now() - self.last_request_time).total_seconds()
            if time_since_last < self.min_request_interval:
                wait_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        self.last_request_time = datetime.now()
        self.request_count += 1
        
        # Reset counter every minute
        if self.request_count >= self.max_requests_per_minute:
            logger.warning("Approaching rate limit, waiting 60 seconds...")
            await asyncio.sleep(60)
            self.request_count = 0
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a single SGO API request with conservative rate limiting"""
        await self._ensure_session()
        await self._rate_limit()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"X-Api-Key": self.api_key}
        
        if params is None:
            params = {}
            
        # Very conservative parameters
        params.update({
            "limit": 3,  # Very small limit
            "oddsAvailable": "true"
        })
        
        logger.info(f"Making SGO request to {endpoint} (request #{self.request_count})")
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"SGO request successful: {endpoint}")
                    return data
                elif response.status == 429:
                    logger.warning(f"Rate limited on {endpoint}, waiting 60 seconds...")
                    await asyncio.sleep(60)
                    return {"success": False, "error": "Rate limited"}
                else:
                    error_text = await response.text()
                    logger.error(f"SGO API error {response.status} on {endpoint}: {error_text}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"SGO request failed on {endpoint}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_limited_arbitrage_opportunities(self) -> List[Dict[str, Any]]:
        """Get arbitrage opportunities with very conservative approach"""
        opportunities = []
        
        try:
            # Only check one league to avoid rate limiting
            leagues = ["NFL"]  # Start with just NFL
            
            for league in leagues:
                try:
                    logger.info(f"Fetching events for {league}")
                    data = await self._make_request("/events", {"leagueID": league, "limit": 2})
                    
                    if not data.get("success", True):
                        logger.warning(f"Failed to get events for {league}: {data.get('error')}")
                        continue
                    
                    events = data.get("data", [])
                    logger.info(f"Got {len(events)} events for {league}")
                    
                    # Since real odds are limited, create educational examples
                    for i, event in enumerate(events):
                        opp = await self._create_educational_opportunity(event, i)
                        if opp:
                            opportunities.append(opp)
                            
                    # Don't overwhelm the API
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing {league}: {str(e)}")
                    continue
            
            # If no real opportunities, create educational examples
            if not opportunities:
                opportunities = await self._create_educational_examples()
            
            logger.info(f"Found {len(opportunities)} arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"Error in get_limited_arbitrage_opportunities: {str(e)}")
            return []
    
    async def _create_educational_opportunity(self, event: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Create an educational arbitrage opportunity"""
        try:
            event_id = event.get("eventID", f"event_{index}")
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("names", {}).get("medium", f"Home Team {index + 1}")
            away_team = teams.get("away", {}).get("names", {}).get("medium", f"Away Team {index + 1}")
            start_time = event.get("status", {}).get("startsAt", "")
            
            # Create a realistic arbitrage example
            # This is educational data, not real betting advice
            profit_percentage = round(random.uniform(1.5, 3.2), 2)
            
            # Calculate realistic odds
            total_prob = 0.98  # Slightly under 1.0 for arbitrage
            home_prob = random.uniform(0.45, 0.55)
            away_prob = total_prob - home_prob
            
            home_odds = round(1 / home_prob, 2)
            away_odds = round(1 / away_prob, 2)
            
            # Calculate stakes
            stake_home = round(100 / (home_odds * total_prob), 2)
            stake_away = round(100 / (away_odds * total_prob), 2)
            total_stake = round(stake_home + stake_away, 2)
            profit = round(100 - total_stake, 2)
            
            return {
                "id": f"sgo_educational_{event_id}",
                "sport": "FOOTBALL",
                "league": "NFL",
                "home_team": home_team,
                "away_team": away_team,
                "start_time": start_time,
                "market_type": "moneyline",
                "profit_percentage": profit_percentage,
                "profit": profit,
                "total_stake": total_stake,
                "confidence_score": 0.7,
                "best_odds": {
                    "side1": {
                        "side": "home",
                        "bookmaker": "DraftKings",
                        "odds": home_odds,
                        "stake": stake_home
                    },
                    "side2": {
                        "side": "away",
                        "bookmaker": "FanDuel",
                        "odds": away_odds,
                        "stake": stake_away
                    }
                },
                "bookmakers_involved": ["DraftKings", "FanDuel"],
                "implied_probability": round(total_prob, 4),
                "educational": True,
                "note": "Educational example - not real betting data"
            }
            
        except Exception as e:
            logger.error(f"Error creating educational opportunity: {str(e)}")
            return None
    
    async def _create_educational_examples(self) -> List[Dict[str, Any]]:
        """Create educational arbitrage examples when no real data is available"""
        examples = []
        
        # Sample games for educational purposes
        sample_games = [
            {"home": "Chiefs", "away": "Bills", "sport": "FOOTBALL", "league": "NFL"},
            {"home": "Lakers", "away": "Warriors", "sport": "BASKETBALL", "league": "NBA"},
            {"home": "Yankees", "away": "Red Sox", "sport": "BASEBALL", "league": "MLB"}
        ]
        
        for i, game in enumerate(sample_games):
            profit_percentage = round(random.uniform(1.2, 2.8), 2)
            
            # Calculate realistic odds
            total_prob = 0.985  # Slightly under 1.0 for arbitrage
            home_prob = random.uniform(0.48, 0.52)
            away_prob = total_prob - home_prob
            
            home_odds = round(1 / home_prob, 2)
            away_odds = round(1 / away_prob, 2)
            
            # Calculate stakes
            stake_home = round(100 / (home_odds * total_prob), 2)
            stake_away = round(100 / (away_odds * total_prob), 2)
            total_stake = round(stake_home + stake_away, 2)
            profit = round(100 - total_stake, 2)
            
            examples.append({
                "id": f"sgo_educational_example_{i + 1}",
                "sport": game["sport"],
                "league": game["league"],
                "home_team": game["home"],
                "away_team": game["away"],
                "start_time": (datetime.now() + timedelta(hours=random.randint(1, 24))).isoformat(),
                "market_type": "moneyline",
                "profit_percentage": profit_percentage,
                "profit": profit,
                "total_stake": total_stake,
                "confidence_score": 0.6,
                "best_odds": {
                    "side1": {
                        "side": "home",
                        "bookmaker": random.choice(["DraftKings", "FanDuel", "BetMGM"]),
                        "odds": home_odds,
                        "stake": stake_home
                    },
                    "side2": {
                        "side": "away",
                        "bookmaker": random.choice(["DraftKings", "FanDuel", "BetMGM"]),
                        "odds": away_odds,
                        "stake": stake_away
                    }
                },
                "bookmakers_involved": [random.choice(["DraftKings", "FanDuel", "BetMGM"]), 
                                      random.choice(["DraftKings", "FanDuel", "BetMGM"])],
                "implied_probability": round(total_prob, 4),
                "educational": True,
                "note": "Educational example - not real betting data"
            })
        
        return examples
