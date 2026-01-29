from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Float, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base
from app.core.security_utils import hash_password, verify_password

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    saved_strategies = relationship("ArbitrageStrategy", back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")
    email_verifications = relationship("EmailVerification", back_populates="user")
    subscription = relationship("UserSubscription", back_populates="user", uselist=False)
    arbitrage_history = relationship("UserArbitrage", back_populates="user")
    notification_logs = relationship("UserEmailNotificationLog", back_populates="user")

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")
    
    @password.setter
    def password(self, password):
        # Truncate to 72 bytes to prevent bcrypt errors
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        self.hashed_password = hash_password(password)
    
    def verify_password(self, password):
        return verify_password(password, self.hashed_password)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    balance = Column(Float, default=0.0)
    preferred_unit = Column(String, default="USD")
    notification_email = Column(Boolean, default=True)
    notification_browser = Column(Boolean, default=True)
    preferred_sports = Column(String) # Comma-separated list of sport keys
    preferred_bookmakers = Column(String) # Comma-separated list of bookmaker keys
    minimum_profit_threshold = Column(Float, default=0.5) # Minimum % profit for notifications
    odds_format = Column(String, default="decimal")  # 'decimal' or 'american'

    # Relationships
    user = relationship("User", back_populates="profile")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    currency = Column(String, default="USD")
    transaction_type = Column(String) # 'deposit', 'withdrawal', 'subscription', 'refund'
    status = Column(String) # 'pending', 'completed', 'failed'
    description = Column(String)
    stripe_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")

class ArbitrageStrategy(Base):
    __tablename__ = "arbitrage_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    min_profit = Column(Float, default=1.0)
    max_profit = Column(Float, nullable=True)
    sports = Column(String) # JSON or comma-separated
    bookmakers = Column(String) # JSON or comma-separated
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_strategies")

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="password_resets")

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, index=True)
    expires = Column(DateTime)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="email_verifications")

class UserArbitrage(Base):
    __tablename__ = "user_arbitrage_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    sport_key = Column(String)
    sport_title = Column(String)
    event_id = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    commence_time = Column(DateTime)
    odds = Column(JSON)
    profit_percentage = Column(Float)
    bet_amount = Column(Float)
    profit = Column(Float) # Monetary profit
    winning_outcome = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="arbitrage_history")

class UserEmailNotificationLog(Base):
    __tablename__ = "user_email_notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email_type = Column(String) # 'welcome', 'reset_password', 'arbitrage_alert'
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # 'sent', 'failed'
    details = Column(String, nullable=True)
    
    user = relationship("User", back_populates="notification_logs")