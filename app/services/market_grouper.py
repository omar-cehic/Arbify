from typing import List, Dict, Any, Optional
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class MarketGrouper:
    """
    Responsible for grouping odds from different bookmakers into unified markets.
    Handles fuzzy matching of lines (e.g., 2.5 vs 2.50) and strict validation.
    """

    @staticmethod
    def group_markets(odds: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups a list of odds into markets based on event, type, period, and line.
        
        Args:
            odds: List of odd dictionaries from SGO API.
            
        Returns:
            Dictionary mapping unique_market_id to list of odds.
        """
        grouped_odds = defaultdict(list)
        
        for odd in odds:
            # Generate a consistent group key
            group_key = MarketGrouper._generate_group_key(odd)
            if group_key:
                grouped_odds[group_key].append(odd)
                
        return grouped_odds

    @staticmethod
    def _generate_group_key(odd: Dict[str, Any]) -> Optional[str]:
        """
        Generates a unique key for grouping odds.
        
        Key format: {event_id}:{market_type}:{period}:{stat_type}:{player_id}:{normalized_line}
        """
        try:
            # Extract core components
            event_id = odd.get('event_id')
            market_type = odd.get('market_type') # e.g., 'moneyline', 'spread', 'total'
            period_id = odd.get('period_id', 'game')
            stat_id = odd.get('stat_id')
            stat_entity_id = odd.get('stat_entity_id') # 'home', 'away', 'all', or player_id
            
            # Extract line value
            line = odd.get('line')
            
            # Normalize line value
            normalized_line = MarketGrouper._normalize_line(line)
            
            # Construct the key
            # We use a composite key to ensure strict separation of different markets
            key_parts = [
                str(event_id),
                str(market_type),
                str(period_id),
                str(stat_id),
                str(stat_entity_id)
            ]
            
            # Add line to key if it exists (for spreads/totals)
            # For moneylines, line is usually None, so we don't add it (or add 'None')
            if normalized_line is not None:
                key_parts.append(str(normalized_line))
            else:
                key_parts.append("ML") # Explicit marker for Moneyline/No-Line markets
                
            return ":".join(key_parts)
            
        except Exception as e:
            logger.error(f"Error generating group key for odd {odd.get('odd_id')}: {str(e)}")
            return None

    @staticmethod
    def _normalize_line(line: Any) -> Optional[float]:
        """
        Standardizes line values to ensure 2.5 matches 2.50.
        Returns None if line is missing or invalid.
        """
        if line is None or line == "":
            return None
            
        try:
            # Convert to float to handle string variations ("2.5", "2.50", 2.5)
            float_val = float(line)
            
            # Optional: Round to reasonable precision to avoid float math issues
            # 2 decimal places is standard for sports lines
            return round(float_val, 2)
        except (ValueError, TypeError):
            # If it's not a number (shouldn't happen for valid lines), return as is or None
            return None
