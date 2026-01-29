# db.py

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .config import DATABASE_URL

Base = declarative_base()

class BettingOdds(Base):
    __tablename__ = "betting_odds"
    
    id = Column(Integer, primary_key=True)
    sportsbook = Column(String)
    sport_key = Column(String)
    sport_title = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    commence_time = Column(DateTime)
    outcome = Column(String)
    odds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()