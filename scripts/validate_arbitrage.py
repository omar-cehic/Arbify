#!/usr/bin/env python3
"""
Arbitrage Opportunity Validation Tool

This script helps validate the legitimacy of arbitrage opportunities
by cross-checking odds with multiple sources and applying realistic filters.
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArbitrageValidator:
    """Validates arbitrage opportunities for data quality and realism"""
    
    def __init__(self):
        self.suspicious_patterns = []
        self.validation_results = []
    
    def validate_opportunity(self, opportunity: Dict) -> Dict:
        """
        Comprehensive validation of an arbitrage opportunity
        Returns validation results with warnings and confidence score
        """
        validation = {
            "is_valid": True,
            "confidence_score": 1.0,
            "warnings": [],
            "red_flags": [],
            "recommendations": []
        }
        
        # Extract key data
        profit_pct = opportunity.get("profit_percentage", 0)
        home_team = opportunity.get("home_team", "")
        away_team = opportunity.get("away_team", "")
        best_odds = opportunity.get("best_odds", {})
        bookmakers = opportunity.get("bookmakers_involved", [])
        
        logger.info(f"🔍 Validating: {home_team} vs {away_team} - {profit_pct}% profit")
        
        # 1. PROFIT PERCENTAGE ANALYSIS
        if profit_pct > 20:
            validation["red_flags"].append(f"Extremely high profit: {profit_pct}%")
            validation["confidence_score"] *= 0.1
            validation["recommendations"].append("Verify odds are current and not from different time periods")
        elif profit_pct > 10:
            validation["warnings"].append(f"Very high profit: {profit_pct}%")
            validation["confidence_score"] *= 0.3
            validation["recommendations"].append("Double-check odds with bookmaker websites")
        elif profit_pct > 5:
            validation["warnings"].append(f"High profit: {profit_pct}%")
            validation["confidence_score"] *= 0.7
        
        # 2. BOOKMAKER ANALYSIS
        if len(bookmakers) < 2:
            validation["red_flags"].append("Insufficient bookmakers for arbitrage")
            validation["is_valid"] = False
        
        # Check for unrealistic bookmaker combinations
        known_good_bookmakers = {
            "fanduel", "draftkings", "betmgm", "caesars", "espnbet", 
            "pinnacle", "bet365", "pointsbet", "hardrockbet"
        }
        
        unknown_bookmakers = [bm for bm in bookmakers if bm.lower() not in known_good_bookmakers]
        if unknown_bookmakers:
            validation["warnings"].append(f"Unknown bookmakers: {unknown_bookmakers}")
            validation["confidence_score"] *= 0.8
        
        # 3. ODDS ANALYSIS
        if best_odds:
            odds_values = []
            for side_key, side_data in best_odds.items():
                if isinstance(side_data, dict) and "odds" in side_data:
                    odds_values.append(side_data["odds"])
            
            if len(odds_values) >= 2:
                # Check for identical odds (suspicious)
                if len(set(odds_values)) == 1:
                    validation["red_flags"].append(f"Identical odds across all sides: {odds_values[0]}")
                    validation["confidence_score"] *= 0.1
                
                # Check for unrealistic odds spreads
                min_odds, max_odds = min(odds_values), max(odds_values)
                odds_spread = max_odds - min_odds
                
                if odds_spread < 0.1:  # Very close odds
                    validation["warnings"].append(f"Very similar odds: {min_odds:.2f} to {max_odds:.2f}")
                    validation["confidence_score"] *= 0.5
                
                # Check for extreme odds values
                if any(odds < 1.01 or odds > 50 for odds in odds_values):
                    validation["red_flags"].append(f"Extreme odds values: {odds_values}")
                    validation["confidence_score"] *= 0.2
        
        # 4. TIMING ANALYSIS  
        start_time = opportunity.get("start_time") or opportunity.get("commence_time")
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                now = datetime.utcnow().replace(tzinfo=start_dt.tzinfo)
                time_diff_hours = (start_dt - now).total_seconds() / 3600
                
                if time_diff_hours < -1:  # Game started over 1 hour ago
                    validation["red_flags"].append("Game already started")
                    validation["confidence_score"] *= 0.3
                elif time_diff_hours > 168:  # More than 1 week away
                    validation["warnings"].append("Game is far in the future")
                    validation["confidence_score"] *= 0.8
                    
            except Exception as e:
                validation["warnings"].append(f"Could not parse start time: {start_time}")
        
        # 5. MARKET TYPE ANALYSIS
        market_type = opportunity.get("market_type", "")
        if market_type in ["totals", "team_totals"]:
            # Team totals are less common and harder to verify
            validation["warnings"].append("Team total markets are less liquid")
            validation["confidence_score"] *= 0.9
        
        # 6. CALCULATE FINAL VALIDATION
        if validation["confidence_score"] < 0.3:
            validation["is_valid"] = False
            validation["recommendations"].append("DO NOT BET - Too many red flags")
        elif validation["confidence_score"] < 0.5:
            validation["recommendations"].append("CAUTION - Verify manually before betting")
        elif validation["confidence_score"] < 0.7:
            validation["recommendations"].append("MODERATE CONFIDENCE - Double-check key odds")
        else:
            validation["recommendations"].append("GOOD OPPORTUNITY - Proceed with normal caution")
        
        return validation
    
    async def validate_with_external_check(self, opportunity: Dict) -> Dict:
        """
        Enhanced validation that attempts to verify odds with external sources
        """
        base_validation = self.validate_opportunity(opportunity)
        
        # TODO: Add external odds checking if needed
        # This could query other APIs or scrape bookmaker websites
        # For now, we'll just do the internal validation
        
        return base_validation

def print_validation_report(opportunity: Dict, validation: Dict):
    """Print a detailed validation report"""
    home = opportunity.get("home_team", "Team A")
    away = opportunity.get("away_team", "Team B") 
    profit = opportunity.get("profit_percentage", 0)
    
    print(f"\n{'='*60}")
    print(f"ARBITRAGE VALIDATION REPORT")
    print(f"{'='*60}")
    print(f"Match: {home} vs {away}")
    print(f"Profit: {profit:.2f}%")
    print(f"Valid: {'YES' if validation['is_valid'] else 'NO'}")
    print(f"Confidence: {validation['confidence_score']:.1%}")
    
    if validation['red_flags']:
        print(f"\nRED FLAGS:")
        for flag in validation['red_flags']:
            print(f"  - {flag}")
    
    if validation['warnings']:
        print(f"\nWARNINGS:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if validation['recommendations']:
        print(f"\nRECOMMENDATIONS:")
        for rec in validation['recommendations']:
            print(f"  - {rec}")
    
    print(f"{'='*60}\n")

async def main():
    """Test the validation system"""
    
    # Test with a high-profit opportunity (like your 17% one)
    suspicious_opportunity = {
        "home_team": "Mariners",
        "away_team": "Angels", 
        "profit_percentage": 17.01,
        "market_type": "moneyline",
        "bookmakers_involved": ["marathonbet", "pinnacle"],
        "best_odds": {
            "side1": {"odds": 2.41, "bookmaker": "marathonbet"},
            "side2": {"odds": 2.41, "bookmaker": "pinnacle"}
        },
        "start_time": "2025-09-12T01:40:00.000Z"
    }
    
    # Test with a more realistic opportunity
    realistic_opportunity = {
        "home_team": "Chiefs",
        "away_team": "Bills",
        "profit_percentage": 2.3,
        "market_type": "moneyline", 
        "bookmakers_involved": ["fanduel", "draftkings"],
        "best_odds": {
            "side1": {"odds": 1.95, "bookmaker": "fanduel"},
            "side2": {"odds": 2.05, "bookmaker": "draftkings"}
        },
        "start_time": "2025-09-15T20:00:00.000Z"
    }
    
    validator = ArbitrageValidator()
    
    print("Testing high-profit opportunity...")
    validation1 = await validator.validate_with_external_check(suspicious_opportunity)
    print_validation_report(suspicious_opportunity, validation1)
    
    print("Testing realistic opportunity...")
    validation2 = await validator.validate_with_external_check(realistic_opportunity)
    print_validation_report(realistic_opportunity, validation2)

if __name__ == "__main__":
    asyncio.run(main())