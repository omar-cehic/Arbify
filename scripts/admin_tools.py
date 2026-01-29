#!/usr/bin/env python3
"""
Admin Tools for Arbify - Access User Data and Analytics
Run this script to view user information, subscriptions, and analytics
"""

import os
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, func
from app.models.user import User, UserProfile, UserArbitrage, UserEmailNotificationLog
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.core.config import DATABASE_URL

def get_database_stats():
    """Get overall database statistics"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # User statistics
        total_users = db.query(User).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Subscription statistics
        total_subscriptions = db.query(UserSubscription).count()
        active_subscriptions = db.query(UserSubscription).filter(
            UserSubscription.status.in_(["active", "trialing"])
        ).count()
        
        # Plan breakdown
        basic_subs = db.query(UserSubscription).join(SubscriptionPlan).filter(
            SubscriptionPlan.name == "Basic",
            UserSubscription.status.in_(["active", "trialing"])
        ).count()
        
        premium_subs = db.query(UserSubscription).join(SubscriptionPlan).filter(
            SubscriptionPlan.name == "Premium", 
            UserSubscription.status.in_(["active", "trialing"])
        ).count()
        
        # Recent activity
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = db.query(User).filter(User.created_at >= week_ago).count()
        
        print("=" * 60)
        print("🏢 ARBIFY ADMIN DASHBOARD")
        print("=" * 60)
        print(f"👥 Total Users: {total_users}")
        print(f"✅ Verified Users: {verified_users}")
        print(f"🟢 Active Users: {active_users}")
        print(f"📅 New Users (7 days): {new_users_week}")
        print()
        print("💳 SUBSCRIPTION STATS")
        print("-" * 30)
        print(f"📊 Total Subscriptions: {total_subscriptions}")
        print(f"🟢 Active Subscriptions: {active_subscriptions}")
        print(f"🥉 Basic Plan: {basic_subs}")
        print(f"🏆 Premium Plan: {premium_subs}")
        print()
        
        # Revenue calculation (approximate)
        monthly_revenue = (basic_subs * 19.99) + (premium_subs * 59.99)
        annual_revenue = monthly_revenue * 12
        print("💰 REVENUE ESTIMATE")
        print("-" * 30)
        print(f"📈 Monthly Revenue: ${monthly_revenue:.2f}")
        print(f"📊 Annual Revenue: ${annual_revenue:.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Error getting stats: {str(e)}")
    finally:
        db.close()

def list_recent_users(limit=10):
    """List most recent users"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
        
        print(f"👥 RECENT USERS (Last {limit})")
        print("=" * 60)
        print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Verified':<10} {'Created'}")
        print("-" * 60)
        
        for user in users:
            verified = "✅" if user.is_verified else "❌"
            created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "N/A"
            print(f"{user.id:<5} {user.username:<15} {user.email:<25} {verified:<10} {created}")
        print()
        
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")
    finally:
        db.close()

def list_active_subscriptions():
    """List all active subscriptions"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        subscriptions = db.query(UserSubscription).filter(
            UserSubscription.status.in_(["active", "trialing"])
        ).order_by(UserSubscription.created_at.desc()).all()
        
        print("💳 ACTIVE SUBSCRIPTIONS")
        print("=" * 80)
        print(f"{'User':<15} {'Plan':<10} {'Status':<10} {'Started':<12} {'Ends':<12} {'Revenue'}")
        print("-" * 80)
        
        for sub in subscriptions:
            # Get user info
            user = db.query(User).filter(User.id == sub.user_id).first()
            username = user.username if user else "Unknown"
            
            # Format dates
            started = sub.current_period_start.strftime("%Y-%m-%d") if sub.current_period_start else "N/A"
            ends = sub.current_period_end.strftime("%Y-%m-%d") if sub.current_period_end else "N/A"
            
            # Calculate revenue
            revenue = f"${sub.plan.price_monthly}/mo" if sub.plan else "N/A"
            
            print(f"{username:<15} {sub.plan.name if sub.plan else 'N/A':<10} {sub.status:<10} {started:<12} {ends:<12} {revenue}")
        print()
        
    except Exception as e:
        print(f"❌ Error listing subscriptions: {str(e)}")
    finally:
        db.close()

def search_user(search_term):
    """Search for a specific user by username or email"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Search by username or email
        users = db.query(User).filter(
            (User.username.ilike(f"%{search_term}%")) |
            (User.email.ilike(f"%{search_term}%"))
        ).all()
        
        if not users:
            print(f"❌ No users found matching '{search_term}'")
            return
        
        print(f"🔍 SEARCH RESULTS FOR '{search_term}'")
        print("=" * 60)
        
        for user in users:
            print(f"👤 User ID: {user.id}")
            print(f"📧 Email: {user.email}")
            print(f"👥 Username: {user.username}")
            print(f"✅ Verified: {'Yes' if user.is_verified else 'No'}")
            print(f"🟢 Active: {'Yes' if user.is_active else 'No'}")
            print(f"📅 Created: {user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else 'N/A'}")
            
            # Check subscription
            subscription = db.query(UserSubscription).filter(
                UserSubscription.user_id == user.id,
                UserSubscription.status.in_(["active", "trialing"])
            ).first()
            
            if subscription:
                print(f"💳 Subscription: {subscription.plan.name if subscription.plan else 'Unknown'} ({subscription.status})")
            else:
                print(f"💳 Subscription: None")
            
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error searching users: {str(e)}")
    finally:
        db.close()

def export_users_csv():
    """Export all users to CSV file"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        
        filename = f"arbify_users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            # Write header
            f.write("ID,Username,Email,Verified,Active,Created,Subscription_Plan,Subscription_Status\n")
            
            for user in users:
                # Get subscription info
                subscription = db.query(UserSubscription).filter(
                    UserSubscription.user_id == user.id,
                    UserSubscription.status.in_(["active", "trialing"])
                ).first()
                
                plan_name = subscription.plan.name if subscription and subscription.plan else "None"
                sub_status = subscription.status if subscription else "None"
                
                # Write user row
                f.write(f"{user.id},{user.username},{user.email},{user.is_verified},{user.is_active},"
                       f"{user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'},"
                       f"{plan_name},{sub_status}\n")
        
        print(f"✅ Users exported to: {filename}")
        print(f"📊 Total users exported: {len(users)}")
        
    except Exception as e:
        print(f"❌ Error exporting users: {str(e)}")
    finally:
        db.close()

def main():
    """Main admin interface"""
    print("🔧 ARBIFY ADMIN TOOLS")
    print("Choose an option:")
    print("1. Database Statistics")
    print("2. Recent Users (10)")
    print("3. Active Subscriptions")
    print("4. Search User")
    print("5. Export All Users (CSV)")
    print("6. Exit")
    
    while True:
        try:
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == "1":
                get_database_stats()
            elif choice == "2":
                list_recent_users()
            elif choice == "3":
                list_active_subscriptions()
            elif choice == "4":
                search_term = input("Enter username or email to search: ").strip()
                if search_term:
                    search_user(search_term)
                else:
                    print("❌ Please enter a search term")
            elif choice == "5":
                export_users_csv()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 