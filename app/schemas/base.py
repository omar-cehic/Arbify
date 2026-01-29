# schemas.py
from pydantic import BaseModel
from typing import List, Optional

class OddsOutcome(BaseModel):
    name: str
    price: float

class OddsMarket(BaseModel):
    key: str
    outcomes: List[OddsOutcome]

class OddsBookmaker(BaseModel):
    key: str
    title: str
    markets: List[OddsMarket]

class OddsMatch(BaseModel):
    id: Optional[str]
    sport_key: Optional[str]
    sport_title: Optional[str]
    commence_time: str
    home_team: str
    away_team: str
    bookmakers: List[OddsBookmaker]

class OddsResponse(BaseModel):
    odds: List[OddsMatch]
