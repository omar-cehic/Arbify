#!/usr/bin/env python3
"""
Database initialization script for PostgreSQL production database
Run this script after setting up PostgreSQL on Railway to create all tables
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Import all models to ensure tables are created
from app.core.database import Base, engine, SessionLocal
from app.models.user import User, UserProfile, UserArbitrage, UserEmailNotificationLog
from app.models.subscription import SubscriptionPlan, UserSubscription, SubscriptionPayment, FeatureAccess
from app.core.config import DATABASE_URL, ENVIRONMENT

def create_all_tables():
    """Create all database tables"""
    try:
        print(f"🔗 Connecting to database: {DATABASE_URL[:50]}...")
        print(f"🌍 Environment: {ENVIRONMENT}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"📋 Created tables: {', '.join(tables)}")
            
        return True
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def seed_initial_data():
    """Seed initial subscription plans"""
    try:
        db = SessionLocal()
        
        # Check if plans already exist
        existing_plans = db.query(SubscriptionPlan).count()
        if existing_plans > 0:
            print(f"📊 Found {existing_plans} existing subscription plans")
            return True
            
        # Create subscription plans
        plans = [
            SubscriptionPlan(
                id=1,
                name='Basic',
                price_monthly=19.99,
                price_annual=0.0,
                description='Get started with arbitrage betting',
                max_strategies=2,
                max_alerts=10,
                refresh_rate=60,
                advanced_features=False
            ),
            SubscriptionPlan(
                id=2,
                name='Premium',
                price_monthly=59.99,
                price_annual=0.0,
                description='Full access to all features',
                max_strategies=100,
                max_alerts=1000,
                refresh_rate=30,
                advanced_features=True
            ),
        ]
        
        for plan in plans:
            db.add(plan)
        
        db.commit()
        print("✅ Subscription plans seeded successfully!")
        
        # Show created plans
        all_plans = db.query(SubscriptionPlan).all()
        for plan in all_plans:
            print(f"  - {plan.name}: ${plan.price_monthly}/month (ID: {plan.id})")
            
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error seeding data: {str(e)}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False

def main():
    """Main initialization function"""
    print("🚀 Starting database initialization...")
    print("=" * 50)
    
    # Check database connection
    if "sqlite" in DATABASE_URL:
        print("⚠️  WARNING: Still using SQLite. For production, use PostgreSQL!")
        print("   Set DATABASE_URL environment variable to PostgreSQL connection string")
    else:
        print("✅ Using PostgreSQL database")
    
    # Create tables
    if not create_all_tables():
        print("❌ Failed to create tables")
        sys.exit(1)
    
    # Seed initial data
    if not seed_initial_data():
        print("❌ Failed to seed initial data")
        sys.exit(1)
    
    print("=" * 50)
    print("🎉 Database initialization completed successfully!")
    print("\n📋 Next steps:")
    print("1. Your database is ready for use")
    print("2. User accounts will now persist across deployments")
    print("3. You can create accounts that won't be lost")

if __name__ == "__main__":
    main() 