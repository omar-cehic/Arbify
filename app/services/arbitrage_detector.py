# arbitrage_detector.py - Real-time arbitrage detection using SGO API
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .sgo_pro_live_service import SGOProLiveService

logger = logging.getLogger(__name__)

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage betting opportunity"""
    event_id: str
    sport: str
    league: str
    home_team: str
    away_team: str
    commence_time: str
    market_type: str
    profit_percentage: float
    best_odds: Dict[str, Dict]
    bet_amounts: Dict[str, float]
    total_stake: float
    guaranteed_profit: float
    bookmakers_involved: List[str]
    updated_at: str
    data_source: str
    point: Optional[float] = None

class ArbitrageDetector:
    """Real-time arbitrage opportunity detector using SGO API"""
    
    def __init__(self):
        self.opportunities = []
        self.last_update = None
        self.is_running = False
        
    async def start_detection(self):
        """Start the arbitrage detection process"""
        logger.info("🚀 Starting arbitrage detection with SGO API...")
        self.is_running = True
        
        while self.is_running:
            try:
                await self._detect_opportunities()
                
                # Wait 5 minutes before next check
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Error in arbitrage detection: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop_detection(self):
        """Stop the arbitrage detection process"""
        logger.info("🛑 Stopping arbitrage detection...")
        self.is_running = False
    
    async def _detect_opportunities(self):
        """Detect arbitrage opportunities from SGO data"""
        logger.info("🔍 Detecting arbitrage opportunities...")
        
        try:
            async with SGOProLiveService() as service:
                # Get arbitrage opportunities from SGO (this also saves to DB)
                opportunities = await service.get_upcoming_arbitrage_opportunities()
            
            # Convert to ArbitrageOpportunity objects
            self.opportunities = []
            for opp in opportunities:
                # Map dictionary to dataclass
                self.opportunities.append(ArbitrageOpportunity(
                    event_id=opp.get("id", ""),
                    sport=opp.get("sport", ""),
                    league=opp.get("league", ""),
                    home_team=opp.get("home_team", ""),
                    away_team=opp.get("away_team", ""),
                    commence_time=opp.get("start_time", ""),
                    market_type=opp.get("market_type", ""),
                    profit_percentage=opp.get("profit_percentage", 0.0),
                    best_odds=opp.get("best_odds", {}),
                    bet_amounts=opp.get("bet_amounts", {}),
                    total_stake=opp.get("total_stake", 0.0),
                    guaranteed_profit=opp.get("profit", 0.0),
                    bookmakers_involved=opp.get("bookmakers_involved", []),
                    updated_at=datetime.utcnow().isoformat(),
                    data_source="sgo_pro",
                    point=None
                ))
            
            self.last_update = datetime.now()
            
            logger.info(f"✅ Found {len(self.opportunities)} arbitrage opportunities")
            
            # Log top opportunities
            if self.opportunities:
                top_opportunities = sorted(
                    self.opportunities, 
                    key=lambda x: x.profit_percentage, 
                    reverse=True
                )[:5]
                
                for i, opp in enumerate(top_opportunities, 1):
                    logger.info(
                        f"🎯 #{i}: {opp.home_team} vs {opp.away_team} "
                        f"({opp.market_type}) - {opp.profit_percentage:.2f}% profit"
                    )
            
        except Exception as e:
            logger.error(f"❌ Error detecting opportunities: {e}")
    
    def get_opportunities(self, 
                         min_profit: float = 0.0,
                         max_opportunities: int = 50) -> List[Dict]:
        """Get current arbitrage opportunities"""
        filtered_opps = [
            opp for opp in self.opportunities 
            if opp.profit_percentage >= min_profit
        ]
        
        # Sort by profit percentage (highest first)
        filtered_opps.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        # Convert to dict format for API response
        return [
            {
                "event_id": opp.event_id,
                "sport": opp.sport,
                "league": opp.league,
                "home_team": opp.home_team,
                "away_team": opp.away_team,
                "commence_time": opp.commence_time,
                "market_type": opp.market_type,
                "profit_percentage": opp.profit_percentage,
                "best_odds": opp.best_odds,
                "bet_amounts": opp.bet_amounts,
                "total_stake": opp.total_stake,
                "guaranteed_profit": opp.guaranteed_profit,
                "bookmakers_involved": opp.bookmakers_involved,
                "updated_at": opp.updated_at,
                "data_source": opp.data_source
            }
            for opp in filtered_opps[:max_opportunities]
        ]
    
    def get_status(self) -> Dict:
        """Get detector status"""
        return {
            "is_running": self.is_running,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "total_opportunities": len(self.opportunities)
        }

# Global detector instance
arbitrage_detector = ArbitrageDetector()

# Background task management
detection_task = None

async def start_arbitrage_detection():
    """Start arbitrage detection in background"""
    global detection_task
    if detection_task is None or detection_task.done():
        detection_task = asyncio.create_task(arbitrage_detector.start_detection())
        logger.info("🎯 Arbitrage detection started in background")
    return detection_task

async def stop_arbitrage_detection():
    """Stop arbitrage detection"""
    global detection_task
    if detection_task and not detection_task.done():
        await arbitrage_detector.stop_detection()
        detection_task.cancel()
        logger.info("🛑 Arbitrage detection stopped")
    detection_task = None

def get_arbitrage_opportunities(min_profit: float = 0.0, max_opportunities: int = 50) -> List[Dict]:
    """Get current arbitrage opportunities (synchronous wrapper)"""
    return arbitrage_detector.get_opportunities(min_profit, max_opportunities)

def get_detector_status() -> Dict:
    """Get detector status (synchronous wrapper)"""
    return arbitrage_detector.get_status()
