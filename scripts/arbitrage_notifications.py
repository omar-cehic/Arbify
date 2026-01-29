"""
Arbitrage Opportunity Notification System

This module handles:
1. Checking for new arbitrage opportunities
2. Matching opportunities against user preferences  
3. Sending email notifications to users with subscription-based limits
4. Preventing duplicate notifications and spam

IMPORTANT: This system only sends emails when REAL arbitrage opportunities are found.
No fake/fallback data is used. If no real opportunities exist, no emails are sent.
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.core.database import SessionLocal
from app.models.user import User, UserProfile, UserEmailNotificationLog
from app.models.subscription import UserSubscription
from scripts.email_verification import send_email
from app.core.config import IS_RAILWAY_DEPLOYMENT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArbitrageNotificationService:
    def __init__(self):
        self.last_check_time = datetime.utcnow()
        self.sent_notifications = {}  # Track sent notifications to prevent duplicates
        self.consecutive_errors = 0  # Track consecutive errors to prevent spam loops
        
    def get_user_subscription_status(self, user_id: int, db: Session) -> str:
        """Get user's subscription status"""
        try:
            subscription = db.query(UserSubscription).filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(["active", "trialing"])
            ).first()
            
            if subscription:
                if subscription.status == "trialing":
                    return "premium"  # Trial users get premium features
                else:
                    # Check plan name to determine tier
                    if "premium" in subscription.plan.name.lower():
                        return "premium"
                    else:
                        return "basic"
            
            return "no_subscription"  # Users without subscription should not get basic access
        except Exception as e:
            logger.error(f"Error getting subscription status for user {user_id}: {str(e)}")
            return "no_subscription"
    
    def get_daily_email_limit(self, subscription_status: str) -> int:
        """Get daily email limit based on subscription status"""
        limits = {
            "basic": 1,              # Basic users get 1 email per day
            "premium": 3,            # Premium users get 3 emails per day (includes trial)
            "no_subscription": 0     # Users without subscription get 0 emails
        }
        return limits.get(subscription_status, 0)  # Default to 0 emails (no subscription)
    
    def get_daily_email_count(self, user_id: int, db: Session) -> int:
        """Get number of arbitrage emails sent to user today"""
        try:
            today_start = datetime.combine(date.today(), datetime.min.time())
            count = db.query(UserEmailNotificationLog).filter(
                UserEmailNotificationLog.user_id == user_id,
                UserEmailNotificationLog.sent_at >= today_start,
                UserEmailNotificationLog.email_type == 'arbitrage_alert'
            ).count()
            return count
        except Exception as e:
            logger.error(f"Error counting daily emails for user {user_id}: {str(e)}")
            return 0

    def get_last_email_time(self, user_id: int, db: Session) -> Optional[datetime]:
        """Get timestamp of last arbitrage email"""
        try:
            last_log = db.query(UserEmailNotificationLog).filter(
                UserEmailNotificationLog.user_id == user_id,
                UserEmailNotificationLog.email_type == 'arbitrage_alert'
            ).order_by(UserEmailNotificationLog.sent_at.desc()).first()
            
            return last_log.sent_at if last_log else None
        except Exception as e:
            logger.error(f"Error getting last email time for user {user_id}: {str(e)}")
            return None

    def can_send_email_today(self, user_id: int, subscription_status: str, db: Session) -> bool:
        """Check if user can receive another email today with cooldown logic"""
        try:
            daily_limit = self.get_daily_email_limit(subscription_status)
            today_count = self.get_daily_email_count(user_id, db)
            
            # Check daily limit first
            if today_count >= daily_limit:
                logger.info(f"📧 User {user_id} daily limit reached: {today_count}/{daily_limit} emails sent today (subscription: {subscription_status})")
                return False
            
            # Implement cooldown periods based on subscription
            last_sent = self.get_last_email_time(user_id, db)
            if last_sent:
                # Ensure last_sent is timezone-aware if needed, or naive if comparing to naive
                # Assuming sent_at is stored as naive UTC in DB (default behavior)
                now = datetime.utcnow()
                time_since_last = now - last_sent
                
                if subscription_status in ["premium", "trialing"]:
                    cooldown_hours = 4  # Premium: 4 hour cooldown
                else:
                    cooldown_hours = 24  # Basic: 24 hour cooldown
                
                if time_since_last < timedelta(hours=cooldown_hours):
                    remaining_time = timedelta(hours=cooldown_hours) - time_since_last
                    remaining_hours = int(remaining_time.total_seconds() / 3600)
                    remaining_minutes = int((remaining_time.total_seconds() % 3600) / 60)
                    
                    plan_name = "Premium" if subscription_status in ["premium", "trialing"] else "Basic"
                    logger.info(f"📧 User {user_id} in cooldown: {remaining_hours}h {remaining_minutes}m remaining until next email ({plan_name} {cooldown_hours}h cooldown)")
                    return False
            
            logger.info(f"📧 User {user_id} email check: {today_count}/{daily_limit} emails sent today (subscription: {subscription_status}) - ✅ Can send")
            return True
            
        except Exception as e:
            logger.error(f"Error checking email limit for user {user_id}: {str(e)}")
            return False  # Fail closed

    def log_notification(self, user_id: int, db: Session, status: str = "sent", details: str = None):
        """Log a sent notification"""
        try:
            log_entry = UserEmailNotificationLog(
                user_id=user_id,
                email_type='arbitrage_alert',
                sent_at=datetime.utcnow(),
                status=status,
                details=details
            )
            db.add(log_entry)
            db.commit()
            logger.info(f"📧 Logged notification for user {user_id}")
        except Exception as e:
            logger.error(f"Error logging notification for user {user_id}: {str(e)}")
            db.rollback()
    
    def cleanup_old_email_logs(self, db: Session):
        """Clean up email logs older than 7 days to keep database lean"""
        try:
            cutoff_date = date.today() - timedelta(days=7)
            
            deleted_count = db.query(UserEmailNotificationLog).filter(
                UserEmailNotificationLog.sent_at < cutoff_date
            ).delete()
            
            if deleted_count > 0:
                db.commit()
                logger.info(f"🧹 Cleaned up {deleted_count} old email log records (older than {cutoff_date})")
            
        except Exception as e:
            logger.error(f"Error cleaning up old email logs: {str(e)}")
            db.rollback()
    
    async def check_and_notify_users(self):
        """Main function to check for opportunities and notify users"""
        try:
            logger.info("🔍 Checking for arbitrage opportunities...")
            
            # Reset consecutive errors on successful start
            self.consecutive_errors = 0
            
            db = SessionLocal()
            
            # Clean up old email logs (run once per check cycle)
            self.cleanup_old_email_logs(db)
            try:
                # Get all users with email notifications enabled
                users_to_notify = db.query(User).join(UserProfile).filter(
                    and_(
                        User.is_active == True,
                        User.is_verified == True,
                        UserProfile.notification_email == True
                    )
                ).all()
                
                logger.info(f"📧 Found {len(users_to_notify)} users with email notifications enabled")
                
                if not users_to_notify:
                    logger.info("ℹ️ No users found with email notifications enabled")
                    return
                
                # Check if we have any real opportunities first before processing users
                has_real_opportunities = await self.check_for_any_real_opportunities()
                
                if not has_real_opportunities:
                    logger.info("ℹ️ No real arbitrage opportunities found - skipping email notifications")
                    return
                
                for user in users_to_notify:
                    try:
                        await self.check_user_opportunities(user, db)
                        # Add small delay between users to respect rate limits
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"❌ Error processing user {user.email}: {str(e)}")
                        continue
                        
            finally:
                db.close()
            
        except Exception as e:
            self.consecutive_errors += 1
            logger.error(f"❌ Error in check_and_notify_users (attempt {self.consecutive_errors}): {str(e)}")
            
            # If we have too many consecutive errors, wait longer to prevent spam
            if self.consecutive_errors >= 5:
                logger.error("❌ Too many consecutive errors - extending wait time")
                raise Exception("Too many consecutive errors - stopping to prevent spam")
    
    async def check_for_any_real_opportunities(self) -> bool:
        """Quick check to see if any real arbitrage opportunities exist using NEW SGO API"""
        try:
            # Import the NEW SGO service
            from app.services.sgo_pro_live_service import SGOProLiveService
            
            async with SGOProLiveService() as sgo_service:
                # Check for upcoming arbitrage opportunities
                opportunities = await sgo_service.get_upcoming_arbitrage_opportunities()
                
                # Filter for valid opportunities
                valid_opps = [
                    opp for opp in opportunities
                    if opp.get('profit_percentage', 0) >= 0.5
                ]
                
                if valid_opps:
                    logger.info(f"✅ Found {len(valid_opps)} real SGO arbitrage opportunities")
                    return True
                else:
                    logger.info("ℹ️ No SGO arbitrage opportunities found above 0.5% profit threshold")
                    return False
            
        except Exception as e:
            logger.error(f"Error checking SGO opportunities: {str(e)}")
            return False
    
    async def check_user_opportunities(self, user: User, db: Session):
        """Check opportunities for a specific user and send notifications"""
        try:
            profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
            if not profile or not profile.notification_email:
                return
            
            # Check subscription status and daily limits
            subscription_status = self.get_user_subscription_status(user.id, db)
            
            if not self.can_send_email_today(user.id, subscription_status, db):
                logger.info(f"📧 Daily email limit reached for user {user.email} (subscription: {subscription_status})")
                return
            
            # Parse user preferences
            preferred_sports = profile.preferred_sports.split(",") if profile.preferred_sports else []
            min_profit_threshold = profile.minimum_profit_threshold or 1.0
            
            # Get REAL arbitrage opportunities with frontend-identical filtering
            opportunities = await self.fetch_real_arbitrage_opportunities(preferred_sports, min_profit_threshold, profile)
            
            if opportunities:
                # Filter out opportunities we've already notified about
                new_opportunities = self.filter_new_opportunities(user.id, opportunities)
                
                if new_opportunities:
                    logger.info(f"📧 Sending notification to {user.email} for {len(new_opportunities)} new REAL opportunities (subscription: {subscription_status})")
                    success = await self.send_notification_email(user.email, new_opportunities, subscription_status)
                    
                    if success:
                        # Track that we've notified about these opportunities
                        self.mark_opportunities_notified(user.id, new_opportunities)
                        # Log notification
                        self.log_notification(user.id, db, status="sent", details=f"Sent {len(new_opportunities)} opportunities")
                else:
                    logger.info(f"ℹ️ No new opportunities for user {user.email}")
            else:
                logger.info(f"ℹ️ No real arbitrage opportunities found for user {user.email} (min profit: {min_profit_threshold}%)")
            
        except Exception as e:
            logger.error(f"❌ Error checking opportunities for user {user.email}: {str(e)}")
    
    def format_match_time(self, time_str: str) -> str:
        """Format match time to be more readable"""
        try:
            # Parse the ISO format time string
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            
            # Convert to a more readable format
            # Format: "July 3, 2025 at 4:30 PM UTC"
            return dt.strftime("%B %d, %Y at %I:%M %p UTC")
        except Exception as e:
            logger.error(f"Error formatting time {time_str}: {str(e)}")
            return time_str
    
    async def fetch_real_arbitrage_opportunities(self, preferred_sports: List[str], min_profit: float, user_profile=None) -> List[Dict]:
        """Fetch REAL arbitrage opportunities using NEW SGO API with frontend-identical filtering"""
        try:
            # Import the NEW SGO service
            from app.services.sgo_pro_live_service import SGOProLiveService
            
            async with SGOProLiveService() as sgo_service:
                # Get upcoming arbitrage opportunities from SGO
                all_opportunities = await sgo_service.get_upcoming_arbitrage_opportunities()
                
                # Apply frontend-identical filtering
                filtered_opportunities = self._apply_frontend_filtering(all_opportunities, min_profit, user_profile)
                
                if filtered_opportunities:
                    logger.info(f"📧 Found {len(filtered_opportunities)} REAL arbitrage opportunities after frontend filtering (min profit: {min_profit}%)")
                    
                    # Limit opportunities to prevent email overload
                    from app.core.config import DEV_MODE
                    max_opportunities = 5 if DEV_MODE else 10
                    limited_opportunities = filtered_opportunities[:max_opportunities]
                    
                    return limited_opportunities
                else:
                    logger.info(f"📧 No REAL arbitrage opportunities found after frontend filtering (min profit: {min_profit}%)")
                    return []
            
        except Exception as e:
            logger.error(f"Error fetching SGO arbitrage opportunities: {str(e)}")
            return []
    
    def _apply_frontend_filtering(self, opportunities: List[Dict], min_profit: float, user_profile=None) -> List[Dict]:
        """Apply the exact same filtering logic as frontend ArbitrageFinder and LiveOdds components"""
        if not opportunities:
            return []
        
        # Get user's selected bookmakers (if available)
        selected_bookmakers = []
        if user_profile and hasattr(user_profile, 'preferred_bookmakers') and user_profile.preferred_bookmakers:
            selected_bookmakers = user_profile.preferred_bookmakers.split(",")
        
        # If no bookmakers selected, use default reputable bookmakers to prevent spam
        if not selected_bookmakers:
            # Default to major US bookmakers to filter out fantasy/DFS platforms
            selected_bookmakers = ['fanduel', 'draftkings', 'betmgm', 'caesars', 'espnbet', 'pinnacle', 'bet365']
        
        filtered = []
        
        for opp in opportunities:
            # Filter by minimum profit
            if opp.get('profit_percentage', 0) < min_profit:
                continue
            
            # Apply bookmaker filtering - ALL bookmakers in opportunity must be in selected list
            bookmakers_involved = opp.get('bookmakers_involved', [])
            if len(bookmakers_involved) < 2:
                continue  # Need at least 2 bookmakers for arbitrage
            
            # Check if ALL bookmakers are in the selected list (frontend logic)
            all_bookmakers_selected = True
            for bm in bookmakers_involved:
                bookmaker_key = bm.lower() if isinstance(bm, str) else str(bm).lower()
                
                # Check if this bookmaker is in selected list
                bookmaker_found = any(
                    selected.lower() == bookmaker_key 
                    for selected in selected_bookmakers
                )
                
                if not bookmaker_found:
                    all_bookmakers_selected = False
                    break
            
            if all_bookmakers_selected:
                filtered.append(opp)
        
        return filtered
    
    def filter_new_opportunities(self, user_id: int, opportunities: List[Dict]) -> List[Dict]:
        """Filter out opportunities we've already notified this user about"""
        if user_id not in self.sent_notifications:
            self.sent_notifications[user_id] = set()
        
        new_opportunities = []
        for opp in opportunities:
            # Create a unique identifier for this opportunity using NEW data structure
            opp_id = f"{opp.get('league', '')}-{opp.get('home_team', '')}-{opp.get('away_team', '')}-{opp.get('profit_percentage', 0):.2f}"
            
            if opp_id not in self.sent_notifications[user_id]:
                new_opportunities.append(opp)
        
        return new_opportunities
    
    def mark_opportunities_notified(self, user_id: int, opportunities: List[Dict]):
        """Mark opportunities as notified to prevent duplicates"""
        if user_id not in self.sent_notifications:
            self.sent_notifications[user_id] = set()
        
        for opp in opportunities:
            opp_id = f"{opp.get('league', '')}-{opp.get('home_team', '')}-{opp.get('away_team', '')}-{opp.get('profit_percentage', 0):.2f}"
            self.sent_notifications[user_id].add(opp_id)
        
        # Clean up old notifications (keep only last 24 hours worth)
        # In a production system, you'd want to use a database table for this
        if len(self.sent_notifications[user_id]) > 100:
            # Keep only the 50 most recent
            recent_notifications = list(self.sent_notifications[user_id])[-50:]
            self.sent_notifications[user_id] = set(recent_notifications)
    
    async def send_notification_email(self, email: str, opportunities: List[Dict], subscription_status: str = "free") -> bool:
        """Send email notification about arbitrage opportunities"""
        try:
            # Always use production domain for email links - ready for launch
            base_url = "https://arbify.net"  # Production backend
            frontend_url = "https://arbify.net"  # Production frontend - always use this for email links
            
            if len(opportunities) == 1:
                opp = opportunities[0]
                # Check if this is a test email
                is_test = subscription_status == "test" or "[TEST]" in str(opp.get('match', {}).get('home_team', ''))
                if is_test:
                    subject = f"[TEST EMAIL] Arbify Notification Test - {opp.get('profit_percentage', 0):.2f}% Sample"
                else:
                    subject = f"New Arbitrage Opportunity: {opp.get('profit_percentage', 0):.2f}% Profit"
                
                # Single opportunity email with professional design
                best_odds = opp.get('best_odds', {})
                home_odds = best_odds.get('home', {})
                away_odds = best_odds.get('away', {})
                
                # Add test header if it's a test email - matching website design
                test_header = ""
                if is_test:
                    test_header = """
                    <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 20px; text-align: center; margin-bottom: 0; border: 2px solid #d4af37; border-bottom: none;">
                        <h2 style="margin: 0; color: #d4af37; font-size: 18px; font-weight: 700;">TEST EMAIL - NOT REAL DATA</h2>
                        <p style="margin: 8px 0 0 0; color: #e5e5e5; font-size: 14px;">This is a test to verify your email notifications are working</p>
                    </div>
                    """
                
                header_text = "New Arbitrage Opportunity Found" if not is_test else "Email Notification Test"
                
                html_content = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #0f0f0f; border-radius: 12px; overflow: hidden;">
                    {test_header}
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 30px 40px; text-align: center; border-bottom: 3px solid #d4af37;">
                        <h1 style="color: #d4af37; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">Arbify Alert</h1>
                        <p style="color: #e5e5e5; margin: 8px 0 0 0; font-size: 16px; font-weight: 400;">{header_text}</p>
                    </div>
                    
                    <!-- Main Content -->
                    <div style="padding: 40px;">
                        <!-- Opportunity Card -->
                        <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); border-radius: 12px; padding: 30px; margin-bottom: 30px; border: 1px solid #d4af37;">
                            <h2 style="color: #d4af37; margin: 0 0 20px 0; font-size: 24px; font-weight: 600; text-align: center;">
                                {opp.get('home_team', 'Team A')} vs {opp.get('away_team', 'Team B')}
                            </h2>
                            
                            <div style="display: table; width: 100%; margin-bottom: 25px;">
                                <div style="display: table-row;">
                                    <div style="display: table-cell; padding: 8px 0; width: 30%; color: #b5b5b5; font-size: 14px; font-weight: 500;">Sport:</div>
                                    <div style="display: table-cell; padding: 8px 0; color: #ffffff; font-size: 14px; font-weight: 600;">{opp.get('league', opp.get('sport', 'Unknown'))}</div>
                                </div>
                                <div style="display: table-row;">
                                    <div style="display: table-cell; padding: 8px 0; width: 30%; color: #b5b5b5; font-size: 14px; font-weight: 500;">Match Time:</div>
                                    <div style="display: table-cell; padding: 8px 0; color: #ffffff; font-size: 14px; font-weight: 600;">{self.format_match_time(opp.get('start_time', ''))}</div>
                                </div>
                                <div style="display: table-row;">
                                    <div style="display: table-cell; padding: 8px 0; width: 30%; color: #b5b5b5; font-size: 14px; font-weight: 500;">Profit:</div>
                                    <div style="display: table-cell; padding: 8px 0; color: #10b981; font-size: 18px; font-weight: 700;">{opp.get('profit_percentage', 0):.1f}%</div>
                                </div>
                            </div>
                            
                            <!-- Betting Details -->
                            <div style="background-color: #0f0f0f; border-radius: 8px; padding: 20px; border: 1px solid #333333; margin-bottom: 20px;">
                                <h4 style="color: #d4af37; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">How to Bet:</h4>
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #ffffff; font-size: 14px; font-weight: 600; margin-bottom: 5px;">
                                        {best_odds.get('side1', {}).get('team_name', 'Team 1')}: ${best_odds.get('side1', {}).get('stake', 50):.0f} at {best_odds.get('side1', {}).get('american_odds', 'N/A')}
                                    </div>
                                    <div style="color: #b5b5b5; font-size: 12px;">Bookmaker: {best_odds.get('side1', {}).get('bookmaker', 'N/A')}</div>
                                </div>
                                <div style="margin-bottom: 15px;">
                                    <div style="color: #ffffff; font-size: 14px; font-weight: 600; margin-bottom: 5px;">
                                        {best_odds.get('side2', {}).get('team_name', 'Team 2')}: ${best_odds.get('side2', {}).get('stake', 50):.0f} at {best_odds.get('side2', {}).get('american_odds', 'N/A')}
                                    </div>
                                    <div style="color: #b5b5b5; font-size: 12px;">Bookmaker: {best_odds.get('side2', {}).get('bookmaker', 'N/A')}</div>
                                </div>
                                <div style="border-top: 1px solid #333; padding-top: 15px; margin-top: 15px;">
                                    <div style="color: #10b981; font-size: 14px; font-weight: 600;">
                                        Total stake: $100 → Guaranteed profit: ${opp.get('profit_percentage', 0) * 1:.1f}
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Verification Tips -->
                            <div style="background-color: #0f0f0f; border-radius: 8px; padding: 20px; border: 1px solid #333333;">
                                <h4 style="color: #f59e0b; margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">⚠️ Verification Required:</h4>
                                <div style="color: #b5b5b5; font-size: 12px; line-height: 1.6;">
                                    <div style="margin-bottom: 5px;">• Check odds are still available before betting</div>
                                    <div style="margin-bottom: 5px;">• Verify {opp.get('market_description', 'market')} - {opp.get('verification_tips', 'check market details')}</div>
                                    <div>• Place bets quickly - odds change frequently</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Call to Action -->
                        <div style="text-align: center; margin: 40px 0;">
                            <a href="{frontend_url}/dashboard?tab=arbitrage" 
                               style="background: linear-gradient(135deg, #d4af37 0%, #f4c430 100%); 
                                      color: #1a1a1a; 
                                      padding: 18px 40px; 
                                      border-radius: 8px; 
                                      text-decoration: none; 
                                      font-weight: 700; 
                                      font-size: 16px; 
                                      display: inline-block; 
                                      box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
                                      transition: all 0.3s ease;">
                                View Full Details & Start Betting
                            </a>
                        </div>
                        
                        <!-- Info Box -->
                        <div style="background-color: #1a1a1a; border-radius: 8px; padding: 20px; margin: 30px 0; border-left: 4px solid #d4af37;">
                            <p style="margin: 0; font-size: 14px; color: #e5e5e5; line-height: 1.6;">
                                <strong style="color: #d4af37;">Ready to profit?</strong> Access your personalized dashboard to see complete odds breakdowns, 
                                calculate optimal stakes, and track all opportunities in real-time.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #1a1a1a; padding: 25px 40px; text-align: center; border-top: 1px solid #333333;">
                        <p style="margin: 0; font-size: 13px; color: #888888;">
                            <a href="{frontend_url}/subscription" style="color: #d4af37; text-decoration: none; font-weight: 500;">Upgrade Plan</a> | 
                            <a href="{frontend_url}/profile" style="color: #d4af37; text-decoration: none; font-weight: 500;">Manage Notifications</a>
                        </p>
                        <p style="margin: 15px 0 0 0; font-size: 12px; color: #666666;">© 2025 Arbify - Professional Arbitrage Betting Platform</p>
                    </div>
                </div>
                """
            else:
                # Multiple opportunities email with professional design
                subject = f"{len(opportunities)} New Arbitrage Opportunities Found"
                
                opportunities_html = ""
                for i, opp in enumerate(opportunities[:5]):  # Show top 5
                    best_odds = opp.get('best_odds', {})
                    home_odds = best_odds.get('home', {})
                    away_odds = best_odds.get('away', {})
                    
                    opportunities_html += f"""
                    <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); border-radius: 8px; padding: 20px; margin: 15px 0; border: 1px solid #d4af37;">
                        <h3 style="color: #d4af37; margin: 0 0 15px 0; font-size: 18px; font-weight: 600;">{opp.get('home_team', 'Team A')} vs {opp.get('away_team', 'Team B')}</h3>
                        <div style="display: table; width: 100%; margin-bottom: 15px;">
                            <div style="display: table-row;">
                                <div style="display: table-cell; padding: 4px 0; width: 25%; color: #b5b5b5; font-size: 13px;">Sport:</div>
                                <div style="display: table-cell; padding: 4px 0; color: #ffffff; font-size: 13px; font-weight: 500;">{opp.get('league', opp.get('sport', 'Unknown'))}</div>
                            </div>
                            <div style="display: table-row;">
                                <div style="display: table-cell; padding: 4px 0; width: 25%; color: #b5b5b5; font-size: 13px;">Match Time:</div>
                                <div style="display: table-cell; padding: 4px 0; color: #ffffff; font-size: 13px; font-weight: 500;">{self.format_match_time(opp.get('start_time', ''))}</div>
                            </div>
                            <div style="display: table-row;">
                                <div style="display: table-cell; padding: 4px 0; width: 25%; color: #b5b5b5; font-size: 13px;">Profit:</div>
                                <div style="display: table-cell; padding: 4px 0; color: #10b981; font-size: 16px; font-weight: 700;">{opp.get('profit_percentage', 0):.1f}%</div>
                            </div>
                        </div>
                        <div style="background-color: #0f0f0f; border-radius: 6px; padding: 12px; border: 1px solid #333333;">
                            <div style="color: #b5b5b5; font-size: 11px; line-height: 1.4;">
                                <span>• Arbitrage confirmed</span> • <span>Stakes calculated</span> • <span>Live tracking</span>
                            </div>
                        </div>
                    </div>
                    """
                
                # Add message if there are more opportunities available
                more_opportunities_msg = ""
                total_opportunities = len(opportunities)
                if total_opportunities > 5:
                    more_opportunities_msg = f"""
                    <div style="background-color: #1a1a1a; border-radius: 8px; padding: 20px; margin: 25px 0; border: 2px solid #d4af37; text-align: center;">
                        <p style="margin: 0; font-size: 16px; color: #d4af37; font-weight: 600;">
                            Plus {total_opportunities - 5} more opportunities available!
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 13px; color: #e5e5e5;">View all opportunities and detailed analysis on your dashboard</p>
                    </div>
                    """
                
                html_content = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 0; background-color: #0f0f0f; border-radius: 12px; overflow: hidden;">
                    <!-- Header -->
                    <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 30px 40px; text-align: center; border-bottom: 3px solid #d4af37;">
                        <h1 style="color: #d4af37; margin: 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">Arbify Alert</h1>
                        <p style="color: #e5e5e5; margin: 8px 0 0 0; font-size: 16px; font-weight: 400;">{len(opportunities)} New Arbitrage Opportunities!</p>
                    </div>
                    
                    <!-- Main Content -->
                    <div style="padding: 40px;">
                        <!-- Opportunities List -->
                        <div style="margin: 0 0 30px 0;">
                            {opportunities_html}
                        </div>
                        
                        {more_opportunities_msg}
                        
                        <!-- Call to Action -->
                        <div style="text-align: center; margin: 40px 0;">
                            <a href="{frontend_url}/dashboard?tab=arbitrage" 
                               style="background: linear-gradient(135deg, #d4af37 0%, #f4c430 100%); 
                                      color: #1a1a1a; 
                                      padding: 18px 40px; 
                                      border-radius: 8px; 
                                      text-decoration: none; 
                                      font-weight: 700; 
                                      font-size: 16px; 
                                      display: inline-block; 
                                      box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
                                      transition: all 0.3s ease;">
                                View All Opportunities & Start Betting
                            </a>
                        </div>
                        
                        <!-- Info Box -->
                        <div style="background-color: #1a1a1a; border-radius: 8px; padding: 20px; margin: 30px 0; border-left: 4px solid #d4af37;">
                            <p style="margin: 0; font-size: 14px; color: #e5e5e5; line-height: 1.6;">
                                <strong style="color: #d4af37;">Ready to profit?</strong> Access your personalized dashboard to see complete odds breakdowns, 
                                calculate optimal stakes, and track all opportunities in real-time.
                            </p>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="background-color: #1a1a1a; padding: 25px 40px; text-align: center; border-top: 1px solid #333333;">
                        <p style="margin: 0; font-size: 13px; color: #888888;">
                            <a href="{frontend_url}/subscription" style="color: #d4af37; text-decoration: none; font-weight: 500;">Upgrade Plan</a> | 
                            <a href="{frontend_url}/profile" style="color: #d4af37; text-decoration: none; font-weight: 500;">Manage Notifications</a>
                        </p>
                        <p style="margin: 15px 0 0 0; font-size: 12px; color: #666666;">© 2025 Arbify - Professional Arbitrage Betting Platform</p>
                    </div>
                </div>
                """
            
            # Send the email using the existing email service
            success = send_email(
                to_email=email,
                subject=subject,
                html_content=html_content
            )
            
            # Add rate limiting delay to prevent 429 errors (Resend limit: 2 requests/second)
            await asyncio.sleep(1.0)  # Wait 1 second between emails to stay well under 2/second
            
            if success:
                logger.info(f"✅ Notification email sent successfully to {email}")
            else:
                logger.error(f"❌ Failed to send notification email to {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error sending notification email to {email}: {str(e)}")
            return False

# Global instance
notification_service = ArbitrageNotificationService()

async def run_notification_checker():
    """Background task that checks for opportunities and sends immediate notifications"""
    logger.info("🚀 Starting arbitrage notification service...")
    logger.info("📧 IMMEDIATE NOTIFICATIONS: Emails sent as soon as opportunities are found")
    logger.info("⏰ RATE LIMITING: Basic (1/day, 24h cooldown) | Premium (3/day, 4h cooldown)")
    
    consecutive_failures = 0
    
    while True:
        try:
            await notification_service.check_and_notify_users()
            
            # Reset failure counter on success
            consecutive_failures = 0
            
            # Check every 2 minutes for immediate notifications
            wait_seconds = 120  # 2 minutes - frequent checks for immediate notifications
            
            logger.info(f"💫 Checking every 2 minutes for new opportunities")
            await asyncio.sleep(wait_seconds)
            
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"❌ Error in notification checker (failure #{consecutive_failures}): {str(e)}")
            
            # Exponential backoff for consecutive failures to prevent spam
            if consecutive_failures >= 5:
                wait_time = 3600  # 1 hour for persistent errors
                logger.error(f"❌ Too many consecutive failures ({consecutive_failures}) - waiting {wait_time//60} minutes")
            elif consecutive_failures >= 3:
                wait_time = 1800  # 30 minutes for multiple errors
                logger.error(f"❌ Multiple failures ({consecutive_failures}) - waiting {wait_time//60} minutes")
            else:
                wait_time = 600   # 10 minutes for single errors
                logger.error(f"❌ Error occurred - waiting {wait_time//60} minutes before retry")
            
            await asyncio.sleep(wait_time)

# Manual trigger function for testing
async def send_test_notification(user_email: str):
    """Send a test notification to a specific user"""
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.email == user_email).first()
        
        if not user:
            logger.error(f"User with email {user_email} not found")
            return False
        
        await notification_service.check_user_opportunities(user, db)
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        return False 