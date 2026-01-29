# email_service.py - Centralized Email Service
import os
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.config import IS_RAILWAY_DEPLOYMENT, DEV_MODE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Centralized email service using Resend API"""
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("EMAIL_FROM", "notifications@arbify.net")
        self.base_url = "https://api.resend.com/emails"
        
        # Set BASE_URL based on environment
        if IS_RAILWAY_DEPLOYMENT:
            self.base_url_web = "https://arbify.net"
        else:
            self.base_url_web = os.getenv("BASE_URL", "http://localhost:8001")
    
    def _validate_config(self) -> bool:
        """Validate email configuration"""
        if not self.api_key:
            logger.error("❌ RESEND_API_KEY not set - cannot send emails")
            return False
        
        if not self.api_key.startswith("re_"):
            logger.error("❌ Invalid RESEND_API_KEY format - should start with 're_'")
            return False
            
        return True
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   email_type: str = "general") -> bool:
        """
        Send email using Resend API with comprehensive logging
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            email_type: Type of email for logging (verification, password_reset, notification)
        """
        try:
            # In development mode, just log and skip sending
            if DEV_MODE:
                logger.info(f"📧 DEV MODE: Would send {email_type} email to {to_email}")
                logger.info(f"📧 Subject: {subject}")
                logger.info(f"📧 Content preview: {html_content[:200]}...")
                return True
            
            # Validate configuration
            if not self._validate_config():
                return False
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            # Send email
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=15  # Increased timeout
            )
            
            # Log results
            logger.info(f"📧 {email_type.upper()} EMAIL SENT")
            logger.info(f"   To: {to_email}")
            logger.info(f"   Subject: {subject}")
            logger.info(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                email_id = response_data.get('id', 'unknown')
                logger.info(f"   ✅ Success - Email ID: {email_id}")
                return True
            else:
                logger.error(f"   ❌ Failed - Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Email timeout sending to {to_email}")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Email request error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Email error sending to {to_email}: {str(e)}")
            return False
    
    def send_verification_email(self, email: str, token: str) -> bool:
        """Send email verification email"""
        verify_url = f"{self.base_url_web}/verify-email?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - Arbify</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #1a1a1a;">
            <div style="background-color: #374151; border-radius: 10px; padding: 30px; border-left: 4px solid #f59e0b;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #f59e0b; margin: 0; font-size: 32px;">Arbify</h1>
                    <p style="color: #d1d5db; margin: 10px 0; font-size: 16px;">Arbitrage Betting Platform</p>
                </div>
                
                <div style="background-color: #4b5563; border-radius: 8px; padding: 20px; margin: 20px 0;">
                    <h2 style="color: #f59e0b; margin-top: 0;">Verify Your Email Address</h2>
                    <p style="color: #d1d5db; line-height: 1.6; margin-bottom: 20px;">
                        Welcome to Arbify! To complete your registration and start finding arbitrage opportunities, 
                        please verify your email address by clicking the button below:
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background-color: #f59e0b; color: #1a1a1a; padding: 15px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 16px; display: inline-block;">
                        Verify Email Address →
                    </a>
                </div>
                
                <div style="background-color: #374151; border-radius: 6px; padding: 15px; margin: 20px 0;">
                    <p style="color: #9ca3af; font-size: 14px; margin: 0;">
                        <strong>Can't click the button?</strong> Copy and paste this link into your browser:
                    </p>
                    <p style="color: #d1d5db; font-size: 12px; word-break: break-all; background-color: #4b5563; padding: 10px; border-radius: 4px; margin: 10px 0;">
                        {verify_url}
                    </p>
                </div>
                
                <div style="border-top: 1px solid #4b5563; padding-top: 20px; margin-top: 30px;">
                    <p style="color: #9ca3af; font-size: 14px; text-align: center; margin: 0;">
                        If you didn't create an account with Arbify, you can safely ignore this email.
                    </p>
                    <p style="color: #6b7280; font-size: 12px; text-align: center; margin: 10px 0;">
                        This verification link expires in 24 hours.
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">
                        © 2025 Arbify - Professional Arbitrage Betting Platform
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=email,
            subject="Verify Your Email - Arbify Account",
            html_content=html_content,
            email_type="verification"
        )
    
    def send_password_reset_email(self, email: str, token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.base_url_web}/reset-password?token={token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - Arbify</title>
        </head>
        <body style="margin: 0; padding: 20px; background-color: #2d2d2d; font-family: Arial, sans-serif;">
            <!-- Header Section -->
            <div style="text-align: center; background-color: #2d2d2d; padding: 20px 0; margin-bottom: 20px;">
                <h1 style="color: #f59e0b; font-size: 28px; font-weight: bold; margin: 0;">
                    <span style="background-color: #1a1a1a; padding: 8px 16px; border-radius: 8px;">Arbify</span> 
                    <span style="color: #f59e0b;">Security</span>
                </h1>
                <p style="color: #cccccc; margin: 10px 0; font-size: 16px;">Password Reset Request</p>
            </div>

            <!-- Main Content Card -->
            <div style="background-color: #1a1a1a; border: 2px solid #f59e0b; border-radius: 12px; padding: 30px; max-width: 600px; margin: 0 auto;">
                
                <!-- Title -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #f59e0b; font-size: 24px; margin: 0;">Reset Your Password</h2>
                </div>

                <!-- Simple Message -->
                <div style="text-align: center; margin: 20px 0;">
                    <p style="color: #cccccc; margin: 0; font-size: 16px; line-height: 1.6;">
                        You requested to reset your password for your Arbify account. Click the button below to set a new password:
                    </p>
                </div>

                <!-- Call to Action Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #f59e0b; color: #000000; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px; display: inline-block;">
                        Reset Password
                    </a>
                </div>

                <!-- Alternative Link Section -->
                <div style="margin: 30px 0;">
                    <p style="color: #cccccc; margin: 0 0 15px 0; text-align: center; font-size: 14px;">Can't click the button? Copy and paste this link:</p>
                    <div style="background-color: #000000; border: 1px solid #f59e0b; border-radius: 6px; padding: 12px; margin: 10px 0;">
                        <a href="{reset_url}" style="color: #f59e0b; font-size: 14px; text-decoration: none; word-break: break-all; font-family: 'Courier New', monospace; line-height: 1.4; display: block;">
                            {reset_url}
                        </a>
                    </div>
                </div>

                <!-- Bottom Message -->
                <div style="border-left: 4px solid #f59e0b; background-color: #2d2d2d; padding: 15px; margin: 30px 0;">
                    <p style="color: #cccccc; margin: 0; font-size: 14px;">
                        If you didn't request this password reset, you can safely ignore this email. This reset link expires in 1 hour for security.
                    </p>
                </div>

                <!-- Footer -->
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f59e0b;">
                    <p style="color: #999999; font-size: 12px; margin: 0;">
                        © 2025 Arbify - Professional Arbitrage Betting Platform
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_email=email,
            subject="Reset Your Arbify Password",
            html_content=html_content,
            email_type="password_reset"
        )
    
    def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email to new users"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Arbify</title>
        </head>
        <body style="margin: 0; padding: 20px; background-color: #2d2d2d; font-family: Arial, sans-serif;">
            <!-- Header Section -->
            <div style="text-align: center; background-color: #2d2d2d; padding: 20px 0; margin-bottom: 20px;">
                <h1 style="color: #f59e0b; font-size: 28px; font-weight: bold; margin: 0;">
                    <span style="background-color: #1a1a1a; padding: 8px 16px; border-radius: 8px;">Arbify</span> 
                    <span style="color: #f59e0b;">Welcome</span>
                </h1>
                <p style="color: #cccccc; margin: 10px 0; font-size: 16px;">Account Successfully Created</p>
            </div>

            <!-- Main Content Card -->
            <div style="background-color: #1a1a1a; border: 2px solid #f59e0b; border-radius: 12px; padding: 30px; max-width: 600px; margin: 0 auto;">
                
                <!-- Welcome Header -->
                <div style="text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #f59e0b; font-size: 24px; margin: 0;">Welcome, {username}!</h2>
                </div>

                <!-- Simple Welcome Message -->
                <div style="text-align: center; margin: 20px 0;">
                    <p style="color: #cccccc; font-size: 16px; line-height: 1.6; margin: 0;">
                        Thank you for joining Arbify! Your account is ready and you can start finding profitable arbitrage opportunities right away.
                    </p>
                </div>

                <!-- Call to Action Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{self.base_url_web}/dashboard" 
                       style="background-color: #f59e0b; color: #000000; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px; display: inline-block;">
                        Start Finding Opportunities
                    </a>
                </div>

                <!-- Bottom Message -->
                <div style="border-left: 4px solid #f59e0b; background-color: #2d2d2d; padding: 15px; margin: 30px 0;">
                    <p style="color: #cccccc; margin: 0; font-size: 14px;">
                        <strong style="color: #f59e0b;">Ready to profit?</strong> Access your personalized dashboard to see complete odds breakdowns, calculate optimal stakes, and track all opportunities in real-time.
                    </p>
                </div>

                <!-- Footer -->
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #f59e0b;">
                    <p style="color: #999999; font-size: 12px; margin: 0;">
                        © 2025 Arbify - Professional Arbitrage Betting Platform
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        logger.info(f"📧 WELCOME EMAIL: Attempting to send to {email} for user {username}")
        result = self.send_email(
            to_email=email,
            subject="Welcome to Arbify - Start Finding Arbitrage Opportunities",
            html_content=html_content,
            email_type="welcome"
        )
        if result:
            logger.info(f"📧 WELCOME EMAIL: Successfully sent to {email}")
        else:
            logger.error(f"📧 WELCOME EMAIL: Failed to send to {email}")
        return result

# Global email service instance
email_service = EmailService()
