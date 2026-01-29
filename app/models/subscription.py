# subscription_models.py - completely revised version
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    price_monthly = Column(Float)
    price_annual = Column(Float, default=0.0)
    max_strategies = Column(Integer, default=1)
    max_alerts = Column(Integer, default=5)
    refresh_rate = Column(Integer, default=60)  # in seconds
    advanced_features = Column(Boolean, default=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Use string references only - no back_populates
    subscriptions = relationship("UserSubscription")
    features = relationship("FeatureAccess")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    status = Column(String)  # "pending" (checkout not completed), "trialing", "active", "canceled", "past_due", "unpaid"
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Use only one-way string references - no back_populates or backrefs
    plan = relationship("SubscriptionPlan", overlaps="subscriptions")
    payment_history = relationship("SubscriptionPayment", overlaps="subscription")
    
    # User relationship - matched with User.subscription
    user = relationship("User", back_populates="subscription")


class SubscriptionPayment(Base):
    __tablename__ = "subscription_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("user_subscriptions.id"))
    stripe_payment_id = Column(String)
    amount = Column(Float)
    currency = Column(String)
    status = Column(String)  # "succeeded", "failed", "pending"
    payment_method = Column(String)
    invoice_url = Column(String)
    receipt_url = Column(String)
    payment_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Use string reference - no back_populates
    subscription = relationship("UserSubscription", overlaps="payment_history")


class FeatureAccess(Base):
    __tablename__ = "feature_access"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    feature_key = Column(String)  # e.g. "real_time_alerts", "api_access", etc.
    feature_name = Column(String)
    is_enabled = Column(Boolean, default=False)
    
    # Use string reference - no back_populates
    plan = relationship("SubscriptionPlan", overlaps="features")

def seed_subscription_plans(db):
    # Single Plan Strategy: "Arbitrage Pro"
    # User requested simplification. One tier to rule them all.
    pro_plan = SubscriptionPlan(
        name='Pro', 
        price_monthly=49.99, 
        price_annual=499.99, 
        description='Full access to all arbitrage tools, real-time alerts, and advanced calculators.',
        max_strategies=10,
        max_alerts=50,
        refresh_rate=30,
        advanced_features=True
    )
    
    existing = db.query(SubscriptionPlan).filter_by(name='Pro').first()
    if not existing:
        db.add(pro_plan)
        print("✅ Seeded new 'Pro' subscription plan")
    else:
        # Update existing if needed (optional, but good for price adjustments)
        existing.price_monthly = 49.99
        existing.price_annual = 499.99
        print("ℹ️ 'Pro' plan already exists")
        
    db.commit()