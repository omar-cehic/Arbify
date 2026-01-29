# SGO Production Service - Proper Implementation for Public Launch
import os
import logging
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SportsGameOdds API Configuration
SGO_API_KEY = os.getenv("SGO_API_KEY")
SGO_BASE_URL = "https://api.sportsgameodds.com/v2"

@dataclass
class ArbitrageOpportunity:
    """Structured arbitrage opportunity"""
    event_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    start_time: str
    market_type: str
    profit_percentage: float
    total_stake: float
    guaranteed_profit: float
    best_odds: Dict[str, Any]
    bookmakers_involved: List[str]
    odd_ids: List[str]

class SGOProductionService:
    """Production-ready SGO API service using proper oddID format"""
    
    def __init__(self):
        self.api_key = SGO_API_KEY
        self.base_url = SGO_BASE_URL
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make authenticated request to SGO API"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                
                if response.status == 200 and data.get('success'):
                    return data.get('data', [])
                elif response.status == 429:
                    logger.warning(f"⚠️ Rate limited on {endpoint}")
                    return {'error': 'rate_limited', 'message': 'API rate limit exceeded'}
                else:
                    logger.error(f"❌ API Error {response.status}: {data}")
                    return {'error': 'api_error', 'message': data.get('error', 'Unknown error')}
                    
        except Exception as e:
            logger.error(f"❌ Request failed for {endpoint}: {str(e)}")
            return {'error': 'request_failed', 'message': str(e)}
    
    async def get_events_with_odds(self, league_ids: List[str] = None, limit: int = 50) -> List[Dict]:
        """
        Get events with comprehensive odds data using /odds endpoint
        This is the key endpoint that returns byBookmaker data needed for arbitrage
        """
        logger.info("🔍 Fetching events with comprehensive odds data...")
        
        # Default to major leagues if none specified
        if not league_ids:
            league_ids = ['NFL', 'NBA', 'MLB', 'NHL', 'EPL', 'MLS']
        
        all_events = []
        
        for league_id in league_ids:
            try:
                logger.info(f"📊 Fetching odds for {league_id}...")
                
                # Use /odds endpoint with league filter for comprehensive data
                params = {
                    'league_id': league_id,
                    'limit': limit,
                    'upcoming_only': True
                }
                
                odds_data = await self._make_request('odds', params)
                
                if isinstance(odds_data, dict) and 'error' in odds_data:
                    if odds_data['error'] == 'rate_limited':
                        logger.warning(f"⚠️ Rate limited for {league_id}")
                        continue
                    else:
                        logger.error(f"❌ Error fetching {league_id}: {odds_data['message']}")
                        continue
                
                if isinstance(odds_data, list) and odds_data:
                    logger.info(f"✅ Found {len(odds_data)} events with odds for {league_id}")
                    all_events.extend(odds_data)
                else:
                    logger.info(f"📭 No events found for {league_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {league_id}: {str(e)}")
                continue
        
        logger.info(f"📊 Total events with odds collected: {len(all_events)}")
        return all_events
    
    def parse_odd_id(self, odd_id: str) -> Dict[str, str]:
        """
        Parse oddID format: {statID}-{statEntityID}-{periodID}-{betTypeID}-{sideID}
        """
        try:
            parts = odd_id.split('-')
            if len(parts) == 5:
                return {
                    'stat_id': parts[0],
                    'stat_entity_id': parts[1], 
                    'period_id': parts[2],
                    'bet_type_id': parts[3],
                    'side_id': parts[4]
                }
        except:
            pass
        return {}
    
    def detect_arbitrage_from_sgo_data(self, event_data: Dict) -> Optional[ArbitrageOpportunity]:
        """
        Detect arbitrage opportunities from SGO event data with byBookmaker information
        """
        try:
            event_id = event_data.get('eventID')
            odds_data = event_data.get('odds', {})
            
            if not odds_data:
                return None
            
            # Group odds by market type (using oddID parsing)
            markets = {}
            
            for odd_id, odd_info in odds_data.items():
                parsed = self.parse_odd_id(odd_id)
                bet_type = parsed.get('bet_type_id', 'unknown')
                side_id = parsed.get('side_id', 'unknown')
                
                if bet_type not in markets:
                    markets[bet_type] = {}
                
                # Get byBookmaker data for this odd
                by_bookmaker = odd_info.get('byBookmaker', {})
                
                for bookmaker_id, bookmaker_data in by_bookmaker.items():
                    odds_value = bookmaker_data.get('odds')
                    if odds_value:
                        if side_id not in markets[bet_type]:
                            markets[bet_type][side_id] = []
                        
                        markets[bet_type][side_id].append({
                            'bookmaker': bookmaker_id,
                            'odds': float(odds_value),
                            'odd_id': odd_id
                        })
            
            # Check each market for arbitrage opportunities
            for bet_type, sides in markets.items():
                if len(sides) >= 2:  # Need at least 2 outcomes
                    arbitrage_result = self._calculate_arbitrage(sides)
                    
                    if arbitrage_result and arbitrage_result['profit_percentage'] > 0.5:
                        return ArbitrageOpportunity(
                            event_id=event_id,
                            sport=event_data.get('sportID', 'Unknown'),
                            league=event_data.get('leagueID', 'Unknown'),
                            home_team=event_data.get('homeTeamName', 'Home'),
                            away_team=event_data.get('awayTeamName', 'Away'),
                            start_time=event_data.get('startDate', ''),
                            market_type=bet_type,
                            profit_percentage=arbitrage_result['profit_percentage'],
                            total_stake=arbitrage_result['total_stake'],
                            guaranteed_profit=arbitrage_result['guaranteed_profit'],
                            best_odds=arbitrage_result['best_odds'],
                            bookmakers_involved=arbitrage_result['bookmakers'],
                            odd_ids=arbitrage_result['odd_ids']
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error detecting arbitrage for event {event_data.get('eventID')}: {str(e)}")
            return None
    
    def _calculate_arbitrage(self, sides: Dict[str, List[Dict]]) -> Optional[Dict]:
        """Calculate arbitrage opportunity from odds data"""
        try:
            # Find best odds for each side
            best_odds = {}
            
            for side, odds_list in sides.items():
                if odds_list:
                    best_odd = max(odds_list, key=lambda x: x['odds'])
                    best_odds[side] = best_odd
            
            if len(best_odds) < 2:
                return None
            
            # Calculate arbitrage
            total_implied_probability = sum(1 / odd['odds'] for odd in best_odds.values())
            
            if total_implied_probability < 1.0:  # Arbitrage exists
                profit_percentage = ((1 / total_implied_probability) - 1) * 100
                total_stake = 1000  # Standard stake
                
                # Calculate stakes for each bet
                stakes = {}
                for side, odd_data in best_odds.items():
                    stake = (total_stake / total_implied_probability) / odd_data['odds']
                    stakes[side] = {
                        'odds': odd_data['odds'],
                        'bookmaker': odd_data['bookmaker'],
                        'stake': round(stake, 2)
                    }
                
                guaranteed_profit = total_stake * (profit_percentage / 100)
                
                return {
                    'profit_percentage': round(profit_percentage, 2),
                    'total_stake': total_stake,
                    'guaranteed_profit': round(guaranteed_profit, 2),
                    'best_odds': stakes,
                    'bookmakers': list(set(odd['bookmaker'] for odd in best_odds.values())),
                    'odd_ids': [odd['odd_id'] for odd in best_odds.values()]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error calculating arbitrage: {str(e)}")
            return None
    
    async def find_arbitrage_opportunities(self, max_events: int = 100) -> List[Dict]:
        """
        Main method to find arbitrage opportunities using proper SGO data
        """
        logger.info("🚀 Starting production arbitrage search with SGO API...")
        
        try:
            # Get events with comprehensive odds data
            events_with_odds = await self.get_events_with_odds(limit=max_events)
            
            if not events_with_odds:
                logger.warning("⚠️ No events with odds data found")
                return []
            
            opportunities = []
            
            for event_data in events_with_odds:
                arbitrage_opp = self.detect_arbitrage_from_sgo_data(event_data)
                
                if arbitrage_opp:
                    # Convert to dict format for API response
                    opp_dict = {
                        'event_id': arbitrage_opp.event_id,
                        'sport_key': arbitrage_opp.sport.lower(),
                        'sport_title': arbitrage_opp.sport,
                        'league': arbitrage_opp.league,
                        'home_team': arbitrage_opp.home_team,
                        'away_team': arbitrage_opp.away_team,
                        'commence_time': arbitrage_opp.start_time,
                        'market_type': arbitrage_opp.market_type,
                        'profit_percentage': arbitrage_opp.profit_percentage,
                        'total_stake': arbitrage_opp.total_stake,
                        'guaranteed_profit': arbitrage_opp.guaranteed_profit,
                        'best_odds': arbitrage_opp.best_odds,
                        'bookmakers_involved': arbitrage_opp.bookmakers_involved,
                        'odd_ids': arbitrage_opp.odd_ids
                    }
                    opportunities.append(opp_dict)
            
            # Sort by profit percentage
            opportunities.sort(key=lambda x: x['profit_percentage'], reverse=True)
            
            logger.info(f"✅ Found {len(opportunities)} arbitrage opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error in find_arbitrage_opportunities: {str(e)}")
            return []

# Global service instance
sgo_production_service = SGOProductionService()

async def get_production_arbitrage_opportunities(max_events: int = 50) -> List[Dict]:
    """
    Wrapper function for getting production arbitrage opportunities
    """
    async with SGOProductionService() as service:
        return await service.find_arbitrage_opportunities(max_events)

if __name__ == "__main__":
    # Test the production service
    async def test_production_service():
        opportunities = await get_production_arbitrage_opportunities(10)
        print(f"Found {len(opportunities)} arbitrage opportunities")
        for opp in opportunities[:3]:  # Show first 3
            print(f"- {opp['home_team']} vs {opp['away_team']}: {opp['profit_percentage']:.2f}% profit")
    
    asyncio.run(test_production_service())
