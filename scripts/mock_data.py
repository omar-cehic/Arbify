# mock_data.py
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.core.sports_config import SUPPORTED_SPORTS
from app.core.config import MOCK_BOOKMAKERS

# Sample matches data for different sports
def get_mock_match_time():
    """Generate a realistic future match time"""
    now = datetime.now()
    days_ahead = random.randint(1, 14)
    hours = random.choice([12, 14, 15, 16, 17, 19, 20])
    minutes = random.choice([0, 30])
    
    future_date = now + timedelta(days=days_ahead)
    return datetime(
        future_date.year,
        future_date.month,
        future_date.day,
        hours,
        minutes
    )

MOCK_MATCHES = {
    # Soccer leagues
    "soccer_epl": [
        ("Arsenal", "Manchester United"),
        ("Liverpool", "Manchester City"),
        ("Chelsea", "Tottenham"),
        ("Newcastle", "Aston Villa"),
        ("Brighton", "West Ham"),
    ],
    "soccer_champions_league": [
        ("Real Madrid", "Bayern Munich"),
        ("Manchester City", "Inter Milan"),
        ("Barcelona", "PSG"),
        ("Liverpool", "Juventus"),
        ("Atletico Madrid", "Borussia Dortmund"),
    ],
    "soccer_la_liga": [
        ("Real Madrid", "Barcelona"),
        ("Atletico Madrid", "Sevilla"),
        ("Real Sociedad", "Athletic Bilbao"),
        ("Valencia", "Villarreal"),
        ("Real Betis", "Getafe"),
    ],
    
    # Basketball leagues
    "basketball_nba": [
        ("LA Lakers", "Golden State Warriors"),
        ("Boston Celtics", "Miami Heat"),
        ("Milwaukee Bucks", "Philadelphia 76ers"),
        ("Phoenix Suns", "Dallas Mavericks"),
        ("Denver Nuggets", "Memphis Grizzlies"),
    ],
    "basketball_ncaab": [
        ("Duke", "North Carolina"),
        ("Kentucky", "Kansas"),
        ("Gonzaga", "Baylor"),
        ("UCLA", "Arizona"),
        ("Villanova", "Michigan"),
    ],
    
    # Football leagues
    "football_nfl": [
        ("Kansas City Chiefs", "San Francisco 49ers"),
        ("Dallas Cowboys", "Philadelphia Eagles"),
        ("Buffalo Bills", "Miami Dolphins"),
        ("Cincinnati Bengals", "Baltimore Ravens"),
        ("Green Bay Packers", "Detroit Lions"),
    ],
}

def generate_mock_odds(sport_key: Optional[str] = None, force_no_arbitrage: bool = False) -> List[Dict]:
    """
    Generate mock odds data with realistic arbitrage opportunities
    If sport_key is provided, only generate for that sport
    If force_no_arbitrage is True, ensure no arbitrage opportunities are generated
    """
    all_matches = []
    
    # Determine which sports to generate for
    sports_to_generate = []
    if sport_key:
        if sport_key in SUPPORTED_SPORTS and sport_key in MOCK_MATCHES:
            sports_to_generate = [(sport_key, SUPPORTED_SPORTS[sport_key])]
    else:
        sports_to_generate = [(key, info) for key, info in SUPPORTED_SPORTS.items() 
                              if key in MOCK_MATCHES and info["active"]]
    
    # Generate for each sport
    for sport_key, sport_info in sports_to_generate:
        outcomes_count = sport_info["outcomes"]
        matches = MOCK_MATCHES.get(sport_key, [])
        
        for home_team, away_team in matches:
            match_data = {
                "id": f"{sport_key}_{home_team.replace(' ', '_')}_{away_team.replace(' ', '_')}",
                "home_team": home_team,
                "away_team": away_team,
                "sport_title": sport_info["title"],
                "sport_key": sport_key,
                "commence_time": get_mock_match_time().isoformat(),
                "bookmakers": []
            }
            
            # Only generate arbitrage opportunities in specific test mode
            # For normal development, don't create fake arbitrage opportunities
            should_create_arbitrage = not force_no_arbitrage and random.random() < 0.01  # 1% chance of arbitrage (very rare, like real life)
            
            if should_create_arbitrage:
                # Generate realistic arbitrage opportunity based on sport type
                total_prob = random.uniform(0.98, 0.995)  # Much smaller margins (0.5-2% profit)
                
                if outcomes_count == 3:  # 3-way (soccer)
                    prob_home = random.uniform(0.35, 0.45) * total_prob
                    prob_away = random.uniform(0.25, 0.35) * total_prob
                    prob_draw = (1 - prob_home - prob_away) * total_prob
                    
                    base_home = round(1 / prob_home, 2)
                    base_away = round(1 / prob_away, 2)
                    base_draw = round(1 / prob_draw, 2)
                    
                    # Only print for first match to reduce logging spam
                    if home_team == matches[0][0]:
                        print(f"Generated 3-way arbitrage: {home_team} vs {away_team}")
                        print(f"Odds: {base_home:.2f} / {base_draw:.2f} / {base_away:.2f}")
                        print(f"Total probability: {(total_prob * 100):.2f}%")
                    
                else:  # 2-way (basketball, football)
                    prob_home = random.uniform(0.45, 0.55) * total_prob
                    prob_away = (1 - prob_home) * total_prob
                    
                    base_home = round(1 / prob_home, 2)
                    base_away = round(1 / prob_away, 2)
                    
                    # Only print for first match to reduce logging spam
                    if home_team == matches[0][0]:
                        print(f"Generated 2-way arbitrage: {home_team} vs {away_team}")
                        print(f"Odds: {base_home:.2f} / {base_away:.2f}")
                        print(f"Total probability: {(total_prob * 100):.2f}%")
            else:
                # Normal odds with typical bookmaker margin
                margin = random.uniform(0.03, 0.06)  # 3-6% margin
                
                if outcomes_count == 3:  # 3-way (soccer)
                    prob_home = random.uniform(0.35, 0.45)
                    prob_away = random.uniform(0.25, 0.35)
                    prob_draw = 1 - prob_home - prob_away
                    total = (1 + margin)
                    
                    base_home = round(total / prob_home, 2)
                    base_away = round(total / prob_away, 2)
                    base_draw = round(total / prob_draw, 2)
                else:  # 2-way (basketball, football)
                    prob_home = random.uniform(0.45, 0.55)
                    prob_away = 1 - prob_home
                    total = (1 + margin)
                    
                    base_home = round(total / prob_home, 2)
                    base_away = round(total / prob_away, 2)

            # Generate slightly different odds for each bookmaker
            for bookmaker in MOCK_BOOKMAKERS:
                variation = 0.08  # Reduced variation to keep odds more realistic
                
                if outcomes_count == 3:  # 3-way (soccer)
                    outcomes = [
                        {
                            "name": home_team,
                            "price": round(base_home + (random.random() * variation - variation/2), 2)
                        },
                        {
                            "name": away_team,
                            "price": round(base_away + (random.random() * variation - variation/2), 2)
                        },
                        {
                            "name": "Draw",
                            "price": round(base_draw + (random.random() * variation - variation/2), 2)
                        }
                    ]
                else:  # 2-way (basketball, football)
                    outcomes = [
                        {
                            "name": home_team,
                            "price": round(base_home + (random.random() * variation - variation/2), 2)
                        },
                        {
                            "name": away_team,
                            "price": round(base_away + (random.random() * variation - variation/2), 2)
                        }
                    ]
                
                bookmaker_data = {
                    "key": bookmaker.lower().replace(" ", "_"),
                    "title": bookmaker,
                    "markets": [{
                        "key": "h2h",
                        "outcomes": outcomes
                    }]
                }
                match_data["bookmakers"].append(bookmaker_data)
            
            all_matches.append(match_data)
    
    return all_matches