
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.services.sgo_pro_live_service import SGOProLiveService
from app.core.database import SessionLocal, BettingOdds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_db_persistence():
    logger.info("🧪 Testing Database Persistence...")
    
    # Create a mock event
    mock_event = {
        "sportID": "TEST_SPORT",
        "leagueID": "TEST_LEAGUE",
        "startsAt": datetime.utcnow().isoformat(),
        "participants": [
            {"name": "Test Home Team"},
            {"name": "Test Away Team"}
        ],
        "bookmakers": [
            {
                "title": "TestBookie",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Test Home Team", "price": 1.90},
                            {"name": "Test Away Team", "price": 2.00}
                        ]
                    }
                ]
            }
        ]
    }
    
    service = SGOProLiveService()
    
    # Save to DB
    logger.info("💾 Saving mock event to database...")
    service.save_odds_to_database([mock_event])
    
    # Verify in DB
    db = SessionLocal()
    try:
        odds = db.query(BettingOdds).filter(
            BettingOdds.sport_key == "test_sport",
            BettingOdds.home_team == "Test Home Team"
        ).all()
        
        logger.info(f"🔍 Found {len(odds)} records in database")
        
        if len(odds) >= 2:
            print("✅ PASS: Odds successfully saved to database")
            for odd in odds:
                print(f"   - {odd.outcome}: {odd.price} @ {odd.sportsbook}")
        else:
            print("❌ FAIL: Odds not found in database")
            
    finally:
        # Cleanup
        if odds:
            for odd in odds:
                db.delete(odd)
            db.commit()
            logger.info("🧹 Cleaned up test data")
        db.close()

if __name__ == "__main__":
    test_db_persistence()
