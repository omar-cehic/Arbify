
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.services.market_grouper import MarketGrouper

def test_market_grouper():
    print("🧪 Testing MarketGrouper...")
    
    # Test Case 1: Fuzzy Line Matching (2.5 vs 2.50)
    odds_fuzzy = [
        {
            'odd_id': '1', 'event_id': 'e1', 'market_type': 'ou', 'period_id': 'game', 
            'stat_id': 'points', 'stat_entity_id': 'all', 'line': '2.5', 'bookmaker': 'book1'
        },
        {
            'odd_id': '2', 'event_id': 'e1', 'market_type': 'ou', 'period_id': 'game', 
            'stat_id': 'points', 'stat_entity_id': 'all', 'line': '2.50', 'bookmaker': 'book2'
        }
    ]
    
    grouped = MarketGrouper.group_markets(odds_fuzzy)
    print(f"Test 1 (Fuzzy): Expected 1 group, Got {len(grouped)}")
    if len(grouped) == 1:
        print("✅ PASS: 2.5 and 2.50 grouped together")
    else:
        print("❌ FAIL: 2.5 and 2.50 NOT grouped together")
        
    # Test Case 2: Strict Line Separation (2.5 vs 3.5)
    odds_strict = [
        {
            'odd_id': '3', 'event_id': 'e1', 'market_type': 'ou', 'period_id': 'game', 
            'stat_id': 'points', 'stat_entity_id': 'all', 'line': '2.5', 'bookmaker': 'book1'
        },
        {
            'odd_id': '4', 'event_id': 'e1', 'market_type': 'ou', 'period_id': 'game', 
            'stat_id': 'points', 'stat_entity_id': 'all', 'line': '3.5', 'bookmaker': 'book2'
        }
    ]
    
    grouped_strict = MarketGrouper.group_markets(odds_strict)
    print(f"Test 2 (Strict): Expected 2 groups, Got {len(grouped_strict)}")
    if len(grouped_strict) == 2:
        print("✅ PASS: 2.5 and 3.5 separated")
    else:
        print("❌ FAIL: 2.5 and 3.5 improperly grouped")

if __name__ == "__main__":
    test_market_grouper()
