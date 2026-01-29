"""
Integration Script for Soccer/Football Enhancements
Patches existing SGO service with minimal changes to preserve baseball functionality
"""

import logging
import sys
import os

# Add the backend services to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from services.parser_integration_patch import ParserEnhancementMixin, diagnose_parser_issues
from services.soccer_football_enhancements import SoccerFootballEnhancer

logger = logging.getLogger(__name__)

def patch_sgo_service():
    """
    Apply minimal patches to existing SGO service
    This preserves your existing baseball functionality while enhancing soccer/football
    """
    
    # Import the existing service
    try:
        from services.sgo_pro_live_service import SGOProLiveService
    except ImportError as e:
        logger.error(f"Could not import SGO service: {e}")
        return False
    
    # Create a backup of original methods
    if not hasattr(SGOProLiveService, '_get_market_info_original'):
        SGOProLiveService._get_market_info_original = SGOProLiveService._get_market_info
    
    if not hasattr(SGOProLiveService, '_validate_arbitrage_opportunity_original'):
        SGOProLiveService._validate_arbitrage_opportunity_original = SGOProLiveService._validate_arbitrage_opportunity
    
    # Add the enhancement mixin
    class EnhancedSGOProLiveService(SGOProLiveService, ParserEnhancementMixin):
        def __init__(self):
            SGOProLiveService.__init__(self)
            ParserEnhancementMixin.__init__(self)
        
        def _get_market_info(self, odd_id: str, sport: str = "UNKNOWN") -> dict:
            """Enhanced market info with sport-specific improvements"""
            # Get original market info
            original_info = self._get_market_info_original(odd_id, sport)
            
            # Apply enhancements (preserves baseball functionality)
            enhanced_info = self.enhance_market_info(odd_id, sport, original_info)
            
            return enhanced_info
        
        def _validate_arbitrage_opportunity(self, opp: dict) -> dict:
            """Enhanced arbitrage validation with sport-specific rules"""
            # Get original validation
            original_validation = self._validate_arbitrage_opportunity_original(opp)
            
            # Apply sport-specific enhancements (preserves baseball functionality)
            enhanced_validation = self.validate_opportunity_enhanced(original_validation)
            
            return enhanced_validation
    
    # Replace the original class
    import services.sgo_pro_live_service
    services.sgo_pro_live_service.SGOProLiveService = EnhancedSGOProLiveService
    
    logger.info("✅ Successfully patched SGO service with soccer/football enhancements")
    return True

def test_enhancements():
    """Test the enhancements with sample data"""
    enhancer = SoccerFootballEnhancer()
    
    # Test soccer market recognition
    soccer_tests = [
        {
            'odd_id': 'points-home-game-ml3way-home',
            'sport': 'SOCCER',
            'existing_info': {'market_type': 'unknown'}
        },
        {
            'odd_id': 'points-all-game-ou-over',
            'sport': 'SOCCER',
            'existing_info': {'market_type': 'unknown'}
        }
    ]
    
    print("\n🔧 Testing Soccer Market Recognition:")
    for test in soccer_tests:
        enhanced = enhancer.enhance_market_recognition(
            test['odd_id'], test['sport'], test['existing_info']
        )
        print(f"  {test['odd_id']} -> {enhanced.get('market_type', 'unknown')}")
    
    # Test football market recognition
    football_tests = [
        {
            'odd_id': 'points-home-game-ml-home',
            'sport': 'FOOTBALL',
            'existing_info': {'market_type': 'unknown'}
        },
        {
            'odd_id': 'points-home-game-sp-home',
            'sport': 'FOOTBALL',
            'existing_info': {'market_type': 'unknown'}
        }
    ]
    
    print("\n🔧 Testing Football Market Recognition:")
    for test in football_tests:
        enhanced = enhancer.enhance_market_recognition(
            test['odd_id'], test['sport'], test['existing_info']
        )
        print(f"  {test['odd_id']} -> {enhanced.get('market_type', 'unknown')}")
    
    # Test validation
    sample_opportunities = [
        {
            'sport': 'SOCCER',
            'market_description': 'Soccer 3-Way Moneyline',
            'line': None,
            'profit_percentage': 3.5,
            'best_odds': {
                'home': {'bookmaker': 'bet365', 'american_odds': '+180'},
                'away': {'bookmaker': 'pinnacle', 'american_odds': '+220'},
                'draw': {'bookmaker': 'unibet', 'american_odds': '+240'}
            }
        },
        {
            'sport': 'FOOTBALL',
            'market_description': 'Football Point Spread',
            'line': -3.5,
            'profit_percentage': 2.1,
            'best_odds': {
                'home': {'bookmaker': 'fanduel', 'american_odds': '-110'},
                'away': {'bookmaker': 'draftkings', 'american_odds': '-105'}
            }
        }
    ]
    
    print("\n🔧 Testing Opportunity Validation:")
    for opp in sample_opportunities:
        validation = enhancer.validate_arbitrage_opportunity(opp, opp['sport'])
        print(f"  {opp['sport']} {opp['market_description']}: Valid={validation.is_valid}, Confidence={validation.confidence_score:.2f}")
        if validation.issues:
            for issue in validation.issues:
                print(f"    - {issue}")

def main():
    """Main integration function"""
    print("🚀 Integrating Soccer/Football Enhancements into Existing Parser")
    print("=" * 70)
    
    # Test enhancements first
    print("\n1. Testing Enhancements...")
    test_enhancements()
    
    # Apply patches
    print("\n2. Applying Patches to SGO Service...")
    success = patch_sgo_service()
    
    if success:
        print("✅ Integration completed successfully!")
        print("\nNext Steps:")
        print("1. The existing SGO service now has enhanced soccer/football recognition")
        print("2. Baseball functionality is preserved unchanged")
        print("3. Monitor logs for enhanced market recognition (🔧 ENHANCED messages)")
        print("4. Check validation results for improved confidence scores")
        print("5. Review opportunities for sport-specific validation feedback")
        
        print("\nEnhancement Features Added:")
        print("- Soccer 3-way moneyline recognition")
        print("- Football point spread validation")
        print("- Sport-specific line value validation")
        print("- Bookmaker reliability scoring")
        print("- Confidence score improvements")
        print("- Detailed validation feedback")
        
    else:
        print("❌ Integration failed - check logs for details")
        return False
    
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = main()
    sys.exit(0 if success else 1)
