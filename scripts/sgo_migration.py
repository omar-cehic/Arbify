# sgo_migration.py - Migration script to integrate SportsGameOdds API
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.database import get_db_session
from sgo_api_service import sgo_service, polling_strategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SGODataMigrator:
    """Migrate existing arbitrage system to use SportsGameOdds API"""
    
    def __init__(self):
        self.service = sgo_service
        self.polling = polling_strategy
        
    async def migrate_odds_data_structure(self, legacy_odds: List[Dict]) -> List[Dict]:
        """Convert legacy odds format to SGO format"""
        migrated_data = []
        
        for match in legacy_odds:
            try:
                # Convert legacy match format to SGO event format
                sgo_event = {
                    "event_id": f"legacy_{match.get('id', 'unknown')}",
                    "sport_id": self._map_sport_to_sgo(match.get('sport_key', '')),
                    "league_id": self._map_league_to_sgo(match.get('sport_key', '')),
                    "home_team_name": match.get('home_team', 'Home'),
                    "away_team_name": match.get('away_team', 'Away'),
                    "start_time": match.get('commence_time'),
                    "bookmakers": self._convert_bookmakers(match.get('bookmakers', [])),
                    "markets": self._convert_markets(match.get('bookmakers', [])),
                    "updated_at": datetime.utcnow().isoformat(),
                    "data_source": "legacy_migration"
                }
                
                migrated_data.append(sgo_event)
                
            except Exception as e:
                logger.error(f"Error migrating match {match.get('id')}: {str(e)}")
                continue
        
        logger.info(f"✅ Migrated {len(migrated_data)} events from legacy format")
        return migrated_data
    
    def _map_sport_to_sgo(self, sport_key: str) -> str:
        """Map legacy sport keys to SGO sport IDs"""
        mapping = {
            'americanfootball_nfl': 'FOOTBALL',
            'americanfootball_ncaaf': 'FOOTBALL',
            'basketball_nba': 'BASKETBALL',
            'basketball_ncaab': 'BASKETBALL',
            'basketball_wnba': 'BASKETBALL',
            'baseball_mlb': 'BASEBALL',
            'icehockey_nhl': 'HOCKEY',
            'soccer_epl': 'SOCCER',
            'soccer_spain_la_liga': 'SOCCER',
            'soccer_germany_bundesliga': 'SOCCER',
            'soccer_italy_serie_a': 'SOCCER',
            'soccer_france_ligue_one': 'SOCCER',
            'tennis_atp': 'TENNIS',
            'tennis_wta': 'TENNIS',
            'mma_mixed_martial_arts': 'MMA'
        }
        
        return mapping.get(sport_key, 'UNKNOWN')
    
    def _map_league_to_sgo(self, sport_key: str) -> str:
        """Map legacy sport keys to SGO league IDs"""
        mapping = {
            'americanfootball_nfl': 'NFL',
            'americanfootball_ncaaf': 'NCAAF',
            'basketball_nba': 'NBA', 
            'basketball_ncaab': 'NCAAB',
            'basketball_wnba': 'WNBA',
            'baseball_mlb': 'MLB',
            'icehockey_nhl': 'NHL',
            'soccer_epl': 'EPL',
            'soccer_spain_la_liga': 'LA_LIGA',
            'soccer_germany_bundesliga': 'BUNDESLIGA',
            'soccer_italy_serie_a': 'IT_SERIE_A',
            'soccer_france_ligue_one': 'FR_LIGUE_1',
            'tennis_atp': 'ATP',
            'tennis_wta': 'WTA',
            'mma_mixed_martial_arts': 'UFC'
        }
        
        return mapping.get(sport_key, 'UNKNOWN')
    
    def _convert_bookmakers(self, legacy_bookmakers: List[Dict]) -> List[Dict]:
        """Convert legacy bookmaker format to SGO format"""
        converted = []
        
        for bookmaker in legacy_bookmakers:
            sgo_bookmaker = {
                "bookmaker_id": self._map_bookmaker_to_sgo(bookmaker.get('key', '')),
                "bookmaker_name": bookmaker.get('title', ''),
                "markets": self._convert_bookmaker_markets(bookmaker.get('markets', []))
            }
            converted.append(sgo_bookmaker)
        
        return converted
    
    def _map_bookmaker_to_sgo(self, legacy_key: str) -> str:
        """Map legacy bookmaker keys to SGO bookmaker IDs"""
        mapping = {
            'fanduel': 'fanduel',
            'draftkings': 'draftkings', 
            'betmgm': 'betmgm',
            'caesars': 'caesars',
            'pointsbet_us': 'pointsbet',
            'betrivers': 'betrivers',
            'foxbet': 'foxbet',
            'espnbet': 'espnbet',
            'bovada': 'bovada',
            'betus': 'betus',
            'mybookie_ag': 'mybookie'
        }
        
        return mapping.get(legacy_key, legacy_key)
    
    def _convert_bookmaker_markets(self, legacy_markets: List[Dict]) -> List[Dict]:
        """Convert legacy market format to SGO format"""
        converted = []
        
        for market in legacy_markets:
            market_key = market.get('key', '')
            outcomes = market.get('outcomes', [])
            
            if market_key == 'h2h':  # Moneyline
                for outcome in outcomes:
                    sgo_outcome = {
                        "odd_id": f"points-{outcome.get('name', '').lower()}-game-ml-{outcome.get('name', '').lower()}",
                        "odds_decimal": outcome.get('price', 0),
                        "line": None,
                        "outcome": outcome.get('name', ''),
                        "market_type": "moneyline"
                    }
                    converted.append(sgo_outcome)
                    
            elif market_key == 'spreads':  # Point spread
                for outcome in outcomes:
                    sgo_outcome = {
                        "odd_id": f"points-{outcome.get('name', '').lower()}-game-sp-{outcome.get('name', '').lower()}",
                        "odds_decimal": outcome.get('price', 0),
                        "line": outcome.get('point', 0),
                        "outcome": outcome.get('name', ''),
                        "market_type": "spread"
                    }
                    converted.append(sgo_outcome)
                    
            elif market_key == 'totals':  # Over/Under
                for outcome in outcomes:
                    side = "over" if outcome.get('name', '').lower() == 'over' else "under"
                    sgo_outcome = {
                        "odd_id": f"points-all-game-ou-{side}",
                        "odds_decimal": outcome.get('price', 0),
                        "line": outcome.get('point', 0),
                        "outcome": outcome.get('name', ''),
                        "market_type": "totals"
                    }
                    converted.append(sgo_outcome)
        
        return converted
    
    def _convert_markets(self, legacy_bookmakers: List[Dict]) -> Dict[str, List[Dict]]:
        """Organize markets by type from all bookmakers"""
        markets = {
            "moneyline": [],
            "spread": [], 
            "totals": []
        }
        
        for bookmaker in legacy_bookmakers:
            bookmaker_id = self._map_bookmaker_to_sgo(bookmaker.get('key', ''))
            
            for market in bookmaker.get('markets', []):
                market_key = market.get('key', '')
                
                for outcome in market.get('outcomes', []):
                    market_data = {
                        "bookmaker_id": bookmaker_id,
                        "odds_decimal": outcome.get('price', 0),
                        "line": outcome.get('point'),
                        "outcome": outcome.get('name', ''),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    
                    if market_key == 'h2h':
                        markets["moneyline"].append(market_data)
                    elif market_key == 'spreads':
                        markets["spread"].append(market_data)
                    elif market_key == 'totals':
                        markets["totals"].append(market_data)
        
        return markets
    
    async def test_sgo_connection(self) -> bool:
        """Test connection to SportsGameOdds API"""
        try:
            logger.info("🔌 Testing SGO API connection...")
            
            sports = await self.service.get_sports()
            logger.info(f"✅ SGO API connected! Found {len(sports)} sports")
            
            # Test getting a few events
            events = await self.service.get_events(sport_id="FOOTBALL", limit=5)
            logger.info(f"📅 Retrieved {len(events)} football events")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ SGO API connection failed: {str(e)}")
            return False
    
    async def run_initial_arbitrage_scan(self) -> List[Dict]:
        """Run initial arbitrage scan with SGO API"""
        try:
            logger.info("🚀 Running initial arbitrage scan with SGO...")
            
            # Check if we should poll now
            if not self.polling.should_poll_now():
                logger.info("⏸️ Not time to poll yet or budget exhausted")
                return []
            
            # Get polling parameters
            params = self.polling.get_polling_params()
            logger.info(f"📊 Polling with params: {params}")
            
            # Get arbitrage opportunities
            opportunities = await self.service.get_arbitrage_opportunities(**params)
            
            # Record usage
            events_used = sum(len(await self.service.get_events(sport_id=sport, limit=5)) 
                            for sport in params.get("sports", []))
            self.polling.record_usage(events_used)
            
            logger.info(f"🎯 Found {len(opportunities)} arbitrage opportunities")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Error in arbitrage scan: {str(e)}")
            return []
    
    async def close(self):
        """Close connections"""
        await self.service.close()

async def main():
    """Main migration function"""
    migrator = SGODataMigrator()
    
    try:
        # Test connection
        if not await migrator.test_sgo_connection():
            logger.error("❌ Cannot connect to SGO API. Aborting migration.")
            return
        
        # Run initial scan
        opportunities = await migrator.run_initial_arbitrage_scan()
        
        if opportunities:
            logger.info(f"🎉 Migration successful! Found {len(opportunities)} opportunities")
            
            # Display sample opportunity
            if opportunities:
                sample = opportunities[0]
                logger.info(f"📋 Sample opportunity:")
                logger.info(f"   Match: {sample.get('home_team')} vs {sample.get('away_team')}")
                logger.info(f"   Sport: {sample.get('sport')} ({sample.get('league')})")
                logger.info(f"   Market: {sample.get('market_type')}")
                logger.info(f"   Profit: {sample.get('profit_percentage')}%")
                logger.info(f"   Bookmakers: {sample.get('bookmakers_involved')}")
        else:
            logger.info("ℹ️ Migration successful but no arbitrage opportunities found at this time")
    
    finally:
        await migrator.close()

if __name__ == "__main__":
    asyncio.run(main())
