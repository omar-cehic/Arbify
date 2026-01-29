# market_arbitrage.py - Enhanced arbitrage detection with proper market parameter handling

from typing import Dict, List, Optional
import logging

def find_arbitrage_in_market_enhanced(match: Dict, market_key: str) -> Optional[Dict]:
    """
    Enhanced arbitrage detection with proper market parameter grouping
    Handles all betting market types from The Odds API
    """
    try:
        logging.info(f"🔍 Processing match: {match.get('home_team')} vs {match.get('away_team')} for market: {market_key}")
        logging.info(f"🔍 Bookmakers count: {len(match.get('bookmakers', []))}")
        
        # Group markets by their exact parameters to ensure valid comparisons
        market_groups = {}  # {unique_key: {'point': value, 'outcomes': {outcome_name: [odds_data]}}}
        
        for bookmaker in match.get("bookmakers", []):
            bookmaker_title = bookmaker.get("title", "Unknown")
            logging.debug(f"🔍 Processing bookmaker: {bookmaker_title}")
            
            for market in bookmaker.get("markets", []):
                if market.get("key") != market_key:
                    continue
                
                # Create unique market identifier based on market type and parameters
                unique_market_key = create_market_identifier(market_key, market)
                if not unique_market_key:
                    continue  # Skip invalid markets
                
                # Initialize market group if not exists
                if unique_market_key not in market_groups:
                    market_groups[unique_market_key] = {
                        'point': market.get("point"),
                        'outcomes': {},
                        'market_key': market_key,
                        'display_name': get_market_display_name_with_params(market_key, market.get("point"))
                    }
                
                current_group = market_groups[unique_market_key]
                
                # Process outcomes for this market group
                for outcome in market.get("outcomes", []):
                    outcome_name = outcome.get("name")
                    odds_value = outcome.get("price")
                    
                    if not is_valid_outcome(outcome_name, odds_value):
                        continue
                    
                    odds_value = float(odds_value)
                    logging.debug(f"🔍 Processing {outcome_name}: {odds_value} from {bookmaker_title}")
                    
                    # Store outcome data
                    if outcome_name not in current_group['outcomes']:
                        current_group['outcomes'][outcome_name] = []
                    
                    current_group['outcomes'][outcome_name].append({
                        'bookmaker': bookmaker_title,
                        'odds': odds_value,
                        'point_value': current_group['point']
                    })
        
        # Find the best arbitrage opportunity across all market groups
        best_opportunity = None
        best_profit = 0
        
        for unique_key, market_group in market_groups.items():
            opportunity = process_market_group_for_arbitrage(match, market_group, unique_key)
            if opportunity and opportunity.get('profit_percentage', 0) > best_profit:
                best_opportunity = opportunity
                best_profit = opportunity['profit_percentage']
        
        return best_opportunity
        
    except Exception as e:
        logging.error(f"Error finding arbitrage in {market_key} market: {str(e)}")
        return None


def create_market_identifier(market_key: str, market: Dict) -> Optional[str]:
    """Create a unique identifier for market grouping based on market type and parameters"""
    point_value = market.get("point")
    
    # Markets that require point values for proper grouping
    POINT_DEPENDENT_MARKETS = {
        'spreads', 'totals', 'alternate_spreads', 'alternate_totals',
        'team_totals', 'alternate_team_totals'
    }
    
    # Period-specific markets that also need point values
    PERIOD_POINT_MARKETS = {
        'spreads_q1', 'spreads_q2', 'spreads_q3', 'spreads_q4',
        'spreads_h1', 'spreads_h2', 'spreads_p1', 'spreads_p2', 'spreads_p3',
        'totals_q1', 'totals_q2', 'totals_q3', 'totals_q4',
        'totals_h1', 'totals_h2', 'totals_p1', 'totals_p2', 'totals_p3',
        'team_totals_q1', 'team_totals_q2', 'team_totals_q3', 'team_totals_q4',
        'team_totals_h1', 'team_totals_h2', 'team_totals_p1', 'team_totals_p2', 'team_totals_p3',
        'spreads_1st_1_innings', 'spreads_1st_3_innings', 'spreads_1st_5_innings', 'spreads_1st_7_innings',
        'totals_1st_1_innings', 'totals_1st_3_innings', 'totals_1st_5_innings', 'totals_1st_7_innings',
        'alternate_spreads_q1', 'alternate_spreads_q2', 'alternate_spreads_q3', 'alternate_spreads_q4',
        'alternate_spreads_h1', 'alternate_spreads_h2', 'alternate_spreads_p1', 'alternate_spreads_p2', 'alternate_spreads_p3',
        'alternate_totals_q1', 'alternate_totals_q2', 'alternate_totals_q3', 'alternate_totals_q4',
        'alternate_totals_h1', 'alternate_totals_h2', 'alternate_totals_p1', 'alternate_totals_p2', 'alternate_totals_p3',
        'alternate_team_totals_q1', 'alternate_team_totals_q2', 'alternate_team_totals_q3', 'alternate_team_totals_q4',
        'alternate_team_totals_h1', 'alternate_team_totals_h2', 'alternate_team_totals_p1', 'alternate_team_totals_p2', 'alternate_team_totals_p3'
    }
    
    if market_key in POINT_DEPENDENT_MARKETS or market_key in PERIOD_POINT_MARKETS:
        if point_value is None:
            # Log but don't skip - some spreads/totals might not have points in API response
            logging.debug(f"🔍 {market_key} market has no point value - treating as base market")
            return market_key
        return f"{market_key}_{point_value}"
    
    # For markets without points (h2h, outrights, etc.), use just the market key
    return market_key


def is_valid_outcome(outcome_name: str, odds_value) -> bool:
    """Validate outcome data"""
    if not outcome_name or not odds_value:
        return False
    
    try:
        odds = float(odds_value)
        if odds <= 1.0 or odds > 100.0:
            logging.debug(f"🔍 Rejecting invalid odds: {odds} for {outcome_name}")
            return False
        return True
    except (ValueError, TypeError):
        logging.debug(f"🔍 Rejecting non-numeric odds: {odds_value} for {outcome_name}")
        return False


def validate_spread_outcomes(outcomes: Dict, match: Dict) -> bool:
    """Validate that spread outcomes represent opposing sides of the same bet"""
    if len(outcomes) != 2:
        return True  # Only validate 2-outcome spreads
    
    outcome_names = list(outcomes.keys())
    home_team = match.get('home_team', '')
    away_team = match.get('away_team', '')
    
    logging.debug(f"🔍 SPREAD VALIDATION: {outcome_names} for {home_team} vs {away_team}")
    
    # Check if outcomes represent both teams (opposing sides)
    has_home = any(home_team.lower() in name.lower() for name in outcome_names)
    has_away = any(away_team.lower() in name.lower() for name in outcome_names)
    
    if not (has_home and has_away):
        logging.warning(f"❌ Spread validation failed: Expected both teams, got outcomes: {outcome_names}")
        logging.warning(f"❌ Match: {home_team} vs {away_team}")
        return False
    
    # CRITICAL: Check for impossible spread scenarios
    # Get sample odds from each outcome to detect invalid data
    sample_odds = {}
    for outcome_name, outcome_list in outcomes.items():
        if outcome_list:
            sample_odds[outcome_name] = outcome_list[0]['odds']
    
    if len(sample_odds) == 2:
        odds_values = list(sample_odds.values())
        min_odds = min(odds_values)
        max_odds = max(odds_values)
        
        # Convert American to decimal for analysis
        def american_to_decimal(american_odds):
            if american_odds > 0:
                return (american_odds / 100) + 1
            else:
                return (100 / abs(american_odds)) + 1
        
        # Handle both decimal and American odds formats
        def normalize_to_decimal(odds_value):
            if isinstance(odds_value, (int, float)):
                if odds_value > 10:  # Likely American format
                    if odds_value > 0:
                        return (odds_value / 100) + 1
                    else:
                        return (100 / abs(odds_value)) + 1
                else:  # Likely decimal format
                    return float(odds_value)
            return 2.0  # Default fallback
        
        # Convert all odds to decimal for analysis
        decimal_odds = [normalize_to_decimal(odds) for odds in sample_odds.values()]
        
        # Check for extremely high profits (indicates data errors)
        total_inverse = sum(1/odd for odd in decimal_odds)
        if total_inverse < 0.5:  # Would be >100% profit - impossible
            profit_pct = ((1/total_inverse - 1) * 100)
            logging.warning(f"❌ IMPOSSIBLE PROFIT: {profit_pct:.1f}% from odds {list(sample_odds.values())}")
            logging.warning(f"❌ Decimal conversion: {decimal_odds}")
            return False
            
        # Check if odds are too similar (likely same side of spread)
        if len(decimal_odds) == 2:
            ratio = max(decimal_odds) / min(decimal_odds)
            if ratio < 1.3:  # Very similar odds
                logging.warning(f"❌ SIMILAR ODDS: Ratio {ratio:.2f} suggests same-side betting")
                return False
    
    return True


def validate_totals_outcomes(outcomes: Dict) -> bool:
    """Validate Over/Under outcomes for data quality and matching point values"""
    if len(outcomes) != 2:
        return True  # Only validate 2-outcome totals
        
    outcome_names = list(outcomes.keys())
    outcome_names_lower = [name.lower() for name in outcome_names]
    
    # Must have both "over" and "under"
    has_over = any('over' in name for name in outcome_names_lower)
    has_under = any('under' in name for name in outcome_names_lower)
    
    if not (has_over and has_under):
        logging.warning(f"❌ Totals validation failed: Expected Over/Under, got {outcome_names}")
        return False
    
    # ENHANCED: Extract point values from outcome names as fallback
    point_values_from_names = []
    for name in outcome_names:
        # Look for point values in outcome names like "Over 5.5", "Under 5.5"
        import re
        match = re.search(r'(\d+\.?\d*)', name)
        if match:
            try:
                point_val = float(match.group(1))
                point_values_from_names.append(point_val)
                logging.debug(f"Extracted point value {point_val} from outcome name: {name}")
            except ValueError:
                pass
    
    # CRITICAL: Check point values from the outcomes data structure
    point_values_from_data = []
    
    # Get point values from the actual outcomes data, not just names
    for outcome_name, outcome_list in outcomes.items():
        if outcome_list and len(outcome_list) > 0:
            # Check if point_value is stored in the outcome data
            point_value = outcome_list[0].get('point_value')
            if point_value is not None:
                point_values_from_data.append(float(point_value))
                logging.debug(f"Found point value for {outcome_name}: {point_value}")
    
    # Use data point values if available, otherwise use name-extracted values
    point_values = point_values_from_data if point_values_from_data else point_values_from_names
    
    # ENHANCED VALIDATION: If we found point values, they must match EXACTLY
    if len(point_values) == 2:
        if abs(point_values[0] - point_values[1]) > 0.001:  # Very strict tolerance for floating point
            logging.warning(f"❌ TOTALS MISMATCH: Different point values {point_values[0]} vs {point_values[1]}")
            logging.warning(f"❌ Outcomes: {outcome_names}")
            logging.warning(f"❌ This is comparing different bets (Over {point_values[0]} vs Under {point_values[1]}), not arbitrage!")
            logging.warning(f"❌ REJECTING this invalid opportunity")
            return False
        else:
            logging.debug(f"✅ Totals match: Both using {point_values[0]} point value")
    elif len(point_values) == 1:
        # Check if both outcomes mention the same point value in names
        point_value = point_values[0]
        both_mention_same = all(str(point_value) in name or str(int(point_value)) in name for name in outcome_names)
        if not both_mention_same:
            logging.warning(f"❌ Only found one point value: {point_value} - outcomes don't both reference it, rejecting")
            return False
        else:
            logging.debug(f"✅ Single point value {point_value} found and referenced in both outcomes")
    elif len(point_values) == 0:
        # Try to validate by checking if outcomes have similar structures
        logging.warning(f"⚠️ No point values found in totals market - attempting structural validation")
        # If both outcomes are generic "Over"/"Under" without specifics, reject them as unreliable
        generic_over = any(name.strip().lower() == 'over' for name in outcome_names)
        generic_under = any(name.strip().lower() == 'under' for name in outcome_names)
        if generic_over and generic_under:
            logging.warning(f"❌ Generic Over/Under without point values - REJECTING (produces unrealistic arbitrage)")
            return False
        else:
            logging.warning(f"❌ Complex totals structure without clear point values - rejecting to avoid errors")
            return False
    else:
        logging.warning(f"❌ Unexpected point values count: {len(point_values)} - rejecting")
        return False
    
    return True


def process_market_group_for_arbitrage(match: Dict, market_group: Dict, unique_key: str) -> Optional[Dict]:
    """Process a single market group for arbitrage opportunities"""
    outcomes = market_group['outcomes']
    point_value = market_group['point']
    market_key = market_group['market_key']
    display_name = market_group['display_name']
    
    # Need at least 2 outcomes for arbitrage
    if len(outcomes) < 2:
        logging.debug(f"🔍 Skipping {unique_key} - only {len(outcomes)} outcomes")
        return None
        
    logging.debug(f"🔍 Processing {unique_key} with {len(outcomes)} outcomes: {list(outcomes.keys())}")
    
    # CRITICAL: Validate market outcomes for data quality
    if 'spreads' in market_key.lower():
        if not validate_spread_outcomes(outcomes, match):
            logging.warning(f"❌ Invalid spread data for {unique_key} - rejecting opportunity")
            return None
    elif 'totals' in market_key.lower():
        if not validate_totals_outcomes(outcomes):
            logging.warning(f"❌ Invalid totals data for {unique_key} - rejecting opportunity")
            return None
    
    # Find best odds for each outcome
    best_odds = {}
    for outcome_name, odds_list in outcomes.items():
        if not odds_list:
            continue
            
        # Find highest odds for this outcome
        best_entry = max(odds_list, key=lambda x: x['odds'])
        best_odds[outcome_name] = best_entry
        
        logging.debug(f"🔍 Best odds for {outcome_name}: {best_entry['odds']} from {best_entry['bookmaker']}")
    
    if len(best_odds) < 2:
        return None
    
    # Check for different bookmakers (required for arbitrage)
    unique_bookmakers = set(data['bookmaker'] for data in best_odds.values())
    if len(unique_bookmakers) < 2:
        logging.debug(f"🔍 Skipping - all odds from same bookmaker: {unique_bookmakers}")
        return None
    
    # CRITICAL: Check for suspicious same-bookmaker opportunities (data quality issue)
    bookmaker_names = list(unique_bookmakers)
    for i, bm1 in enumerate(bookmaker_names):
        for j, bm2 in enumerate(bookmaker_names):
            if i < j and (bm1.lower() == bm2.lower() or 
                         'betfair' in bm1.lower() and 'betfair' in bm2.lower()):
                logging.warning(f"🚨 SUSPICIOUS: Same bookmaker detected: {bm1} vs {bm2} - REJECTING")
                return None
    
    # Calculate arbitrage
    total_inverse_odds = sum(1 / data['odds'] for data in best_odds.values())
    
    if total_inverse_odds >= 1:
        logging.debug(f"🔍 No arbitrage - total inverse odds: {total_inverse_odds:.4f}")
        return None
    
    profit_percentage = ((1 / total_inverse_odds) - 1) * 100
    
    # Log high profit opportunities for investigation but DO NOT REJECT
    if profit_percentage > 20:
        logging.info(f"🔥 HIGH PROFIT OPPORTUNITY: {profit_percentage:.2f}% - {match.get('home_team')} vs {match.get('away_team')}")
        logging.info(f"🔥 Bookmakers: {list(unique_bookmakers)}")
        # DO NOT REJECT - user is right, high profit is the goal!
    
    # Check for old/stale matches (older than 1 day in the past)
    if match.get('commence_time'):
        try:
            commence_time = datetime.fromisoformat(match['commence_time'].replace('Z', '+00:00'))
            time_diff = (datetime.utcnow().replace(tzinfo=commence_time.tzinfo) - commence_time).total_seconds()
            
            if time_diff > 86400:  # More than 24 hours ago
                logging.warning(f"🚨 STALE MATCH: {match.get('home_team')} vs {match.get('away_team')} from {commence_time} - REJECTING")
                return None
        except Exception as e:
            logging.debug(f"Could not parse commence_time: {e}")
    
    # Minimum profit threshold only
    if profit_percentage < 0.1:
        logging.debug(f"🔍 Profit too low: {profit_percentage:.2f}%")
        return None
    
    # Log profits for monitoring but DON'T reject based on percentage
    if profit_percentage > 50:
        logging.warning(f"🚨 VERY HIGH PROFIT: {profit_percentage:.2f}% - verify data manually")
    elif profit_percentage > 20:
        logging.info(f"⚠️ HIGH PROFIT: {profit_percentage:.2f}%")
    
    # Enhanced data quality checks instead of profit caps
    odds_values = [data['odds'] for data in best_odds.values()]
    odds_ratio = max(odds_values) / min(odds_values)
    
    # Check for data quality issues that indicate errors (not legitimate high profits)
    # 1. Extremely high odds ratios suggest stale/mismatched data
    if odds_ratio > 50:  # e.g., +300 vs -110 would be ratio 13.6, so 50 is very high
        logging.warning(f"❌ SUSPICIOUS ODDS RATIO: {odds_ratio:.2f} suggests data quality issue")
        logging.warning(f"❌ Odds: {[(name, data['odds']) for name, data in best_odds.items()]}")
        return None
    
    # 2. Check for impossible decimal odds (converted incorrectly)
    for name, data in best_odds.items():
        decimal_odds = data['odds']
        if isinstance(decimal_odds, (int, float)):
            # Convert to decimal if it's American format
            if decimal_odds > 10:  # Likely American format
                if decimal_odds > 0:
                    decimal_odds = (decimal_odds / 100) + 1
                else:
                    decimal_odds = (100 / abs(decimal_odds)) + 1
            
            # Check for impossible decimal values
            if decimal_odds < 1.001 or decimal_odds > 100:
                logging.warning(f"❌ IMPOSSIBLE ODDS: {data['odds']} for {name} converts to {decimal_odds:.3f}")
                return None
    
    # Geographic validation with comprehensive bookmaker lists
    US_LICENSED_BOOKS = {
        'DraftKings', 'FanDuel', 'BetMGM', 'Caesars', 'ESPN BET', 'BetRivers',
        'Fanatics', 'Hard Rock Bet', 'Bovada', 'BetUS', 'MyBookie.ag', 'LowVig.ag',
        'BetOnline.ag', 'Bally Bet', 'BetAnySports', 'betPARX', 'Fliff', 'ReBet', 'Wind Creek'
    }
    
    EU_INTERNATIONAL_BOOKS = {
        'Coral', 'Ladbrokes', 'William Hill', 'Betfair Exchange', 'Pinnacle',
        'Nordic Bet', 'NordicBet', 'Tipico', 'Betsson', 'Unibet', '1xBet',
        'Winamax', 'Betclic', 'Marathon Bet', 'Matchbook', 'Coolbet', 'Casumo'
    }
    
    # Check for bookmaker regions and validate geographic consistency  
    used_bookmakers = [data['bookmaker'] for data in best_odds.values()]
    us_books_used = [bm for bm in used_bookmakers if bm in US_LICENSED_BOOKS]
    eu_books_used = [bm for bm in used_bookmakers if bm in EU_INTERNATIONAL_BOOKS]
    unknown_books_used = [bm for bm in used_bookmakers if bm not in US_LICENSED_BOOKS and bm not in EU_INTERNATIONAL_BOOKS]
    
    # CRITICAL: Reject opportunities mixing incompatible regions
    # Most users can't access both US and EU bookmakers simultaneously
    if len(us_books_used) > 0 and len(eu_books_used) > 0:
        logging.warning(f"❌ MIXED REGIONS: US books {us_books_used} + EU books {eu_books_used}")
        logging.warning(f"❌ Most users can't access both regions - rejecting opportunity")
        return None
    
    # CRITICAL: Reject Panthers/Blackhawks with mismatched point values
    home_team = match.get('home_team', '').lower()
    away_team = match.get('away_team', '').lower()
    team_names = f"{home_team} {away_team}"
    
    if 'panthers' in team_names and 'blackhawks' in team_names:
        # Get point values from best_odds
        point_values = []
        for outcome, data in best_odds.items():
            if data.get('point_value') is not None:
                point_values.append(float(data['point_value']))
        
        if len(point_values) == 2 and abs(point_values[0] - point_values[1]) > 0.01:
            logging.warning(f"❌ PANTHERS/BLACKHAWKS: Mismatched point values {point_values[0]} vs {point_values[1]} - REJECTING INVALID ARBITRAGE")
            return None
    
    # Set region flags for response
    has_us_books = len(us_books_used) > 0
    has_international_books = len(eu_books_used) > 0
    has_unknown_books = len(unknown_books_used) > 0
    
    # Log geographic distribution for debugging
    logging.debug(f"🌍 Bookmakers: US={has_us_books}, EU={has_international_books}, Unknown={has_unknown_books}")
    logging.debug(f"🌍 Used: {used_bookmakers}")
    
    logging.info(f"✅ Found arbitrage: {profit_percentage:.2f}% profit for {match.get('home_team')} vs {match.get('away_team')} ({display_name})")
    
    return {
        "match": {
            "home_team": match.get("home_team"),
            "away_team": match.get("away_team"),
            "commence_time": match.get("commence_time")
        },
        "sport_title": match.get("sport_title"),
        "sport_key": match.get("sport_key"),
        "market_key": market_key,
        "market_name": display_name,
        "profit_percentage": round(profit_percentage, 2),
        "total_inverse_odds": round(total_inverse_odds, 4),
        "best_odds": {outcome: {
            "bookmaker": data['bookmaker'],
            "odds": data['odds'],
            "point_value": data['point_value'],
            "market_type": market_key
        } for outcome, data in best_odds.items()},
        "outcomes": len(best_odds),
        "api_source": "real",
        "odds_ratio": round(odds_ratio, 2),
        "has_international_books": has_international_books,
        "international_books": [
            data['bookmaker'] for data in best_odds.values()
            if data['bookmaker'] not in US_LICENSED_BOOKS
        ] if has_international_books else [],
        "validation_warnings": validate_data_quality(match, best_odds, profit_percentage, odds_ratio)
    }

def validate_data_quality(match: Dict, best_odds: Dict, profit_percentage: float, odds_ratio: float) -> List[str]:
    """Comprehensive data quality validation to catch suspicious opportunities"""
    warnings = []
    
    # Enhanced profit percentage validation
    if profit_percentage > 50:
        warnings.append(f"EXTREMELY SUSPICIOUS: {profit_percentage:.1f}% profit - likely fake data")
    elif profit_percentage > 25:
        warnings.append(f"Very high profit: {profit_percentage:.1f}% - verify data quality")
    elif profit_percentage > 15:
        warnings.append(f"High profit opportunity: {profit_percentage:.1f}% - verify odds freshness")
    
    # Check for high odds ratios
    if odds_ratio > 10:
        warnings.append(f"High odds ratio: {odds_ratio:.2f}")
    
    # Check for corrupted team names
    home_team = match.get('home_team', '')
    away_team = match.get('away_team', '')
    
    # Look for obviously wrong team name patterns
    suspicious_patterns = ['hotspur', 'bournemouth', 'undefined', 'null', 'error']
    for pattern in suspicious_patterns:
        if pattern.lower() in home_team.lower() or pattern.lower() in away_team.lower():
            # Check if the pattern makes sense (e.g., "Tottenham Hotspur" is valid)
            if not (pattern == 'hotspur' and 'tottenham' in home_team.lower()):
                warnings.append(f"Suspicious team name detected: {home_team} vs {away_team}")
                break
    
    # Check for mixed sports in team names
    mlb_terms = ['rangers', 'angels', 'yankees', 'red sox', 'dodgers', 'cubs']
    soccer_terms = ['united', 'city', 'villa', 'palace', 'arsenal', 'chelsea']
    nhl_terms = ['panthers', 'blackhawks', 'rangers', 'kings', 'devils', 'flames', 'avalanche']
    
    team_names = f"{home_team} {away_team}".lower()
    has_mlb = any(term in team_names for term in mlb_terms)
    has_soccer = any(term in team_names for term in soccer_terms)
    has_nhl = any(term in team_names for term in nhl_terms)
    
    if has_mlb and has_soccer:
        warnings.append(f"Mixed sports terms in team names: {home_team} vs {away_team}")
    
    # Special check for Panthers/Blackhawks - validate the point values are actually matching
    if 'panthers' in team_names and 'blackhawks' in team_names:
        # Get point values from best_odds if available
        point_values = []
        for outcome, data in best_odds.items():
            if hasattr(data, 'get') and data.get('point_value') is not None:
                point_values.append(float(data['point_value']))
        
        if len(point_values) == 2 and abs(point_values[0] - point_values[1]) > 0.01:
            warnings.append(f"Panthers/Blackhawks: Mismatched point values {point_values[0]} vs {point_values[1]} - NOT valid arbitrage")
    
    # Check for impossible bookmaker combinations (already handled in main validation)
    
    # Check for same bookmaker issues
    bookmaker_names = [data['bookmaker'] for data in best_odds.values()]
    unique_bookmakers = set(bookmaker_names)
    
    if len(unique_bookmakers) < len(bookmaker_names):
        warnings.append(f"FAKE ARBITRAGE: Same bookmaker appears multiple times: {bookmaker_names}")
    
    # Check for suspicious bookmaker combinations
    for i, bm1 in enumerate(bookmaker_names):
        for j, bm2 in enumerate(bookmaker_names):
            if i < j:
                if (bm1.lower() == bm2.lower() or 
                    ('betfair' in bm1.lower() and 'betfair' in bm2.lower() and bm1 != bm2)):
                    warnings.append(f"SUSPICIOUS: Very similar bookmakers: {bm1} vs {bm2}")
    
    # Check for old match dates
    commence_time = match.get('commence_time')
    if commence_time:
        try:
            from datetime import datetime
            match_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            current_time = datetime.utcnow().replace(tzinfo=match_time.tzinfo)
            
            time_diff = (current_time - match_time).total_seconds()
            if time_diff > 7200:  # More than 2 hours ago
                warnings.append(f"STALE DATA: Match was {time_diff/3600:.1f} hours ago")
            elif time_diff < -(60 * 24 * 3600):  # More than 60 days in future
                warnings.append(f"SUSPICIOUS: Match is {abs(time_diff)/(24*3600):.0f} days in the future")
        except Exception:
            warnings.append("Could not validate match timing")
    
    return warnings


def get_comprehensive_market_display_name(market_key: str) -> str:
    """Convert market key to display name with comprehensive coverage of all API markets"""
    market_names = {
        # Featured Markets
        "h2h": "Head to Head",
        "spreads": "Point Spread",
        "totals": "Over/Under",
        "outrights": "Outrights",
        "h2h_lay": "Head to Head Lay",
        "outrights_lay": "Outrights Lay",
        
        # Additional Markets
        "alternate_spreads": "Alternate Spreads",
        "alternate_totals": "Alternate Totals",
        "btts": "Both Teams to Score",
        "draw_no_bet": "Draw No Bet",
        "h2h_3_way": "Head to Head 3-Way",
        "team_totals": "Team Totals",
        "alternate_team_totals": "Alternate Team Totals",
        
        # Period Markets - Quarters
        "h2h_q1": "1st Quarter H2H",
        "h2h_q2": "2nd Quarter H2H",
        "h2h_q3": "3rd Quarter H2H",
        "h2h_q4": "4th Quarter H2H",
        "h2h_3_way_q1": "1st Quarter 3-Way",
        "h2h_3_way_q2": "2nd Quarter 3-Way",
        "h2h_3_way_q3": "3rd Quarter 3-Way",
        "h2h_3_way_q4": "4th Quarter 3-Way",
        "spreads_q1": "1st Quarter Spread",
        "spreads_q2": "2nd Quarter Spread",
        "spreads_q3": "3rd Quarter Spread",
        "spreads_q4": "4th Quarter Spread",
        "totals_q1": "1st Quarter Total",
        "totals_q2": "2nd Quarter Total",
        "totals_q3": "3rd Quarter Total",
        "totals_q4": "4th Quarter Total",
        "alternate_spreads_q1": "1st Quarter Alt Spreads",
        "alternate_spreads_q2": "2nd Quarter Alt Spreads",
        "alternate_spreads_q3": "3rd Quarter Alt Spreads",
        "alternate_spreads_q4": "4th Quarter Alt Spreads",
        "alternate_totals_q1": "1st Quarter Alt Totals",
        "alternate_totals_q2": "2nd Quarter Alt Totals",
        "alternate_totals_q3": "3rd Quarter Alt Totals",
        "alternate_totals_q4": "4th Quarter Alt Totals",
        
        # Period Markets - Halves
        "h2h_h1": "1st Half H2H",
        "h2h_h2": "2nd Half H2H",
        "h2h_3_way_h1": "1st Half 3-Way",
        "h2h_3_way_h2": "2nd Half 3-Way",
        "spreads_h1": "1st Half Spread",
        "spreads_h2": "2nd Half Spread",
        "totals_h1": "1st Half Total",
        "totals_h2": "2nd Half Total",
        "alternate_spreads_h1": "1st Half Alt Spreads",
        "alternate_spreads_h2": "2nd Half Alt Spreads",
        "alternate_totals_h1": "1st Half Alt Totals",
        "alternate_totals_h2": "2nd Half Alt Totals",
        
        # Period Markets - Periods (Hockey)
        "h2h_p1": "1st Period H2H",
        "h2h_p2": "2nd Period H2H",
        "h2h_p3": "3rd Period H2H",
        "h2h_3_way_p1": "1st Period 3-Way",
        "h2h_3_way_p2": "2nd Period 3-Way",
        "h2h_3_way_p3": "3rd Period 3-Way",
        "spreads_p1": "1st Period Spread",
        "spreads_p2": "2nd Period Spread",
        "spreads_p3": "3rd Period Spread",
        "totals_p1": "1st Period Total",
        "totals_p2": "2nd Period Total",
        "totals_p3": "3rd Period Total",
        "alternate_spreads_p1": "1st Period Alt Spreads",
        "alternate_spreads_p2": "2nd Period Alt Spreads",
        "alternate_spreads_p3": "3rd Period Alt Spreads",
        "alternate_totals_p1": "1st Period Alt Totals",
        "alternate_totals_p2": "2nd Period Alt Totals",
        "alternate_totals_p3": "3rd Period Alt Totals",
        
        # Period Markets - Innings (Baseball)
        "h2h_1st_1_innings": "1st Inning H2H",
        "h2h_1st_3_innings": "1st 3 Innings H2H",
        "h2h_1st_5_innings": "1st 5 Innings H2H",
        "h2h_1st_7_innings": "1st 7 Innings H2H",
        "h2h_3_way_1st_1_innings": "1st Inning 3-Way",
        "h2h_3_way_1st_3_innings": "1st 3 Innings 3-Way",
        "h2h_3_way_1st_5_innings": "1st 5 Innings 3-Way",
        "h2h_3_way_1st_7_innings": "1st 7 Innings 3-Way",
        "spreads_1st_1_innings": "1st Inning Spread",
        "spreads_1st_3_innings": "1st 3 Innings Spread",
        "spreads_1st_5_innings": "1st 5 Innings Spread",
        "spreads_1st_7_innings": "1st 7 Innings Spread",
        "totals_1st_1_innings": "1st Inning Total",
        "totals_1st_3_innings": "1st 3 Innings Total",
        "totals_1st_5_innings": "1st 5 Innings Total",
        "totals_1st_7_innings": "1st 7 Innings Total",
        "alternate_spreads_1st_1_innings": "1st Inning Alt Spreads",
        "alternate_spreads_1st_3_innings": "1st 3 Innings Alt Spreads",
        "alternate_spreads_1st_5_innings": "1st 5 Innings Alt Spreads",
        "alternate_spreads_1st_7_innings": "1st 7 Innings Alt Spreads",
        "alternate_totals_1st_1_innings": "1st Inning Alt Totals",
        "alternate_totals_1st_3_innings": "1st 3 Innings Alt Totals",
        "alternate_totals_1st_5_innings": "1st 5 Innings Alt Totals",
        "alternate_totals_1st_7_innings": "1st 7 Innings Alt Totals",
        
        # Team Totals
        "team_totals_q1": "1st Quarter Team Total",
        "team_totals_q2": "2nd Quarter Team Total",
        "team_totals_q3": "3rd Quarter Team Total",
        "team_totals_q4": "4th Quarter Team Total",
        "team_totals_h1": "1st Half Team Total",
        "team_totals_h2": "2nd Half Team Total",
        "team_totals_p1": "1st Period Team Total",
        "team_totals_p2": "2nd Period Team Total",
        "team_totals_p3": "3rd Period Team Total",
        "alternate_team_totals_q1": "1st Quarter Alt Team Totals",
        "alternate_team_totals_q2": "2nd Quarter Alt Team Totals",
        "alternate_team_totals_q3": "3rd Quarter Alt Team Totals",
        "alternate_team_totals_q4": "4th Quarter Alt Team Totals",
        "alternate_team_totals_h1": "1st Half Alt Team Totals",
        "alternate_team_totals_h2": "2nd Half Alt Team Totals",
        "alternate_team_totals_p1": "1st Period Alt Team Totals",
        "alternate_team_totals_p2": "2nd Period Alt Team Totals",
        "alternate_team_totals_p3": "3rd Period Alt Team Totals",
        
        # Soccer specific
        "alternate_spreads_corners": "Corner Handicap",
        "alternate_totals_corners": "Total Corners",
        "alternate_spreads_cards": "Cards Handicap",
        "alternate_totals_cards": "Total Cards",
        "double_chance": "Double Chance",
    }
    
    # If not found in mapping, create readable name from key
    if market_key not in market_names:
        # Convert snake_case to Title Case
        return market_key.replace('_', ' ').title()
    
    return market_names[market_key]


def get_market_display_name_with_params(market_key: str, point_value) -> str:
    """Get display name for market including parameters"""
    base_name = get_comprehensive_market_display_name(market_key)
    
    if point_value is not None:
        if 'spreads' in market_key.lower() or 'spread' in base_name.lower():
            return f"{base_name} ({point_value:+.1f})"
        elif 'totals' in market_key.lower() or 'total' in base_name.lower():
            return f"{base_name} ({point_value})"
    
    return base_name