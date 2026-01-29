from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.user import User, UserArbitrage
from app.api.v1.auth import get_current_active_user

router = APIRouter()

@router.get("", response_model=dict)
def get_my_arbitrages(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all saved arbitrages for the current user."""
    result = []
    try:
        arbitrages = db.query(UserArbitrage).filter(UserArbitrage.user_id == current_user.id).all()
        
        # Transform to list of dicts for JSON response
        for arb in arbitrages:
            result.append({
                "id": arb.id,
                "sport_key": arb.sport_key,
                "sport_title": arb.sport_title or arb.sport_key, # Fallback
                "matches": [], 
                "home_team": arb.home_team,
                "away_team": arb.away_team,
                "match_time": arb.commence_time, 
                "created_at": arb.timestamp,
                "profit": arb.profit,
                "profit_percentage": arb.profit_percentage,
                "bet_amount": arb.bet_amount,
                "odds": arb.odds,
                "winning_outcome": arb.winning_outcome
            })
    except Exception as e:
        print(f"ERROR fetching my arbitrages: {str(e)}")
        # Return empty list instead of 500
        return {"arbitrages": [], "error": str(e)}
        
    return {"arbitrages": result}

@router.post("", response_model=dict)
def save_arbitrage(
    arbitrage_data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Save a new arbitrage opportunity."""
    
    # Extract data with fallbacks for flat structure
    match_data = arbitrage_data.get("match", {})
    best_odds = arbitrage_data.get("best_odds", {})
    
    # Try getting data from nested 'match' first, then top-level
    sport_key = arbitrage_data.get("sport_key") or match_data.get("sport_key")
    sport_title = arbitrage_data.get("sport_title") or match_data.get("sport_title") or sport_key
    home_team = match_data.get("home_team") or arbitrage_data.get("home_team")
    away_team = match_data.get("away_team") or arbitrage_data.get("away_team")
    
    # Handle commence_time
    commence_time_str = match_data.get("commence_time") or arbitrage_data.get("commence_time") or arbitrage_data.get("start_time")
    commence_time = None
    if commence_time_str:
        try:
            # Handle standard ISO format
            commence_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))
        except:
            pass

    profit_percentage = arbitrage_data.get("profit_percentage")
    
    # DUPLICATE CHECK: Check if this user already saved this match/arb
    # We check for same teams and very similar profit percentage (within small margin) to detect duplicates
    existing_arb = db.query(UserArbitrage).filter(
        UserArbitrage.user_id == current_user.id,
        UserArbitrage.home_team == home_team,
        UserArbitrage.away_team == away_team,
        UserArbitrage.sport_key == sport_key
    ).first()

    if existing_arb:
        start_time_match = True
        # If we have times for both, check if they match (handle float/precision issues with profit)
        if existing_arb.profit_percentage == profit_percentage:
             return {"success": True, "arbitrage": {
                "id": existing_arb.id,
                "home_team": existing_arb.home_team,
                "away_team": existing_arb.away_team,
                "message": "Already saved"
            }}

    # Create new record
    try:
        new_arb = UserArbitrage(
            user_id=current_user.id,
            sport_key=sport_key,
            sport_title=sport_title,
            home_team=home_team,
            away_team=away_team,
            commence_time=commence_time,
            profit_percentage=profit_percentage,
            odds=best_odds,
            bet_amount=0.0, # Default to 0 until user sets it
            profit=0.0
        )
        
        db.add(new_arb)
        db.commit()
        db.refresh(new_arb)
        
        return {"success": True, "arbitrage": {
            "id": new_arb.id,
            "home_team": new_arb.home_team,
            "away_team": new_arb.away_team
        }}
    except Exception as e:
        print(f"ERROR saving arbitrage: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save arbitrage: {str(e)}")

@router.delete("/{arbitrage_id}", response_model=dict)
def delete_arbitrage(
    arbitrage_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a saved arbitrage."""
    arb = db.query(UserArbitrage).filter(UserArbitrage.id == arbitrage_id, UserArbitrage.user_id == current_user.id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage not found")
        
    db.delete(arb)
    db.commit()
    
    return {"success": True}

@router.patch("/{arbitrage_id}", response_model=dict)
def update_arbitrage(
    arbitrage_id: int,
    data: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update arbitrage details (bet amount, profit)."""
    arb = db.query(UserArbitrage).filter(UserArbitrage.id == arbitrage_id, UserArbitrage.user_id == current_user.id).first()
    if not arb:
        raise HTTPException(status_code=404, detail="Arbitrage not found")
        
    if "bet_amount" in data:
        bet_amount = float(data["bet_amount"])
        arb.bet_amount = bet_amount
        
        # Calculate guaranteed profit if we have odds
        # Profit = stake * (1/sum(1/odds) - 1)
        # OR generically: Profit = stake * (profit_percentage / 100)
        # But let's try to be precise if we have odds
        
        odds_data = arb.odds or {}
        odds_values = []
        if isinstance(odds_data, dict):
            for k, v in odds_data.items():
                # Check if value is a number directly or a dict with 'odds' key
                if isinstance(v, (int, float)):
                    odds_values.append(v)
                elif isinstance(v, dict) and 'odds' in v:
                    odds_values.append(v['odds'])
        
        if len(odds_values) >= 2:
            try:
                # Calculate implied probability
                total_implied_prob = sum(1/o for o in odds_values if o > 0)
                if total_implied_prob > 0:
                    roi = (1 / total_implied_prob) - 1
                    arb.profit = round(bet_amount * roi, 2)
                else:
                    arb.profit = 0
            except:
                arb.profit = 0
        else:
            # Fallback to stored percentage
            arb.profit = round(bet_amount * (arb.profit_percentage / 100), 2)
            
    db.commit()
    db.refresh(arb)
    
    return {"success": True, "arbitrage": {
        "id": arb.id,
        "bet_amount": arb.bet_amount,
        "profit": arb.profit
    }}
