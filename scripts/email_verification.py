from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets
import requests
import os
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse

from app.core.database import SessionLocal
from app.models.user import User, EmailVerification
from app.api.v1.auth import get_db
from app.core.config import DEV_MODE, IS_RAILWAY_DEPLOYMENT

# Load environment variables
load_dotenv()

router = APIRouter()

# Email configuration - Updated for Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "notifications@arbify.net")

# Set BASE_URL based on environment
if IS_RAILWAY_DEPLOYMENT:
    BASE_URL = "https://arbify.net"  # Use production domain for email links
else:
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8001")

# Models
class ResendVerificationRequest(BaseModel):
    email: str

# Helper function to send emails using Resend
def send_email(to_email: str, subject: str, html_content: str):
    """Send an email using Resend API with detailed logging"""
    try:
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=data,
            timeout=10
        )
        
        # Log all details 
        print(f"\n==== EMAIL SENT VIA RESEND ====")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"==============================\n")
        
        if response.status_code == 200:
            return True
        else:
            print(f"Resend API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"\n==== EMAIL ERROR ====")
        print(f"Failed to send email to {to_email}")
        print(f"Error type: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        print(f"======================\n")
        return False

# Background task to send verification email
def send_verification_email(email: str, token: str):
    """Send verification email with detailed logging"""
    verify_url = f"{BASE_URL}/verify-email?token={token}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Email</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .container {{ background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px; padding: 20px; }}
            .logo {{ text-align: center; margin-bottom: 20px; }}
            .button {{ display: inline-block; padding: 10px 20px; color: #fff; background-color: #d4af37; text-decoration: none; border-radius: 5px; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #999; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <h1>Arbify</h1>
            </div>
            <h2>Verify Your Email Address</h2>
            <p>Thank you for signing up! To complete your registration, please click the button below to verify your email address:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verify_url}" class="button">Verify Email Address</a>
            </p>
            <p>If the button doesn't work, copy and paste the following link into your browser:</p>
            <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 3px;">
                {verify_url}
            </p>
            <p>If you did not create an account, please ignore this email.</p>
            <p>This link will expire in 24 hours.</p>
            <div class="footer">
                <p>&copy; 2025 Arbify - Arbitrage Betting Platform</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Add detailed logging with prominent verification links
    print(f"\n==== SENDING VERIFICATION EMAIL ====")
    print(f"To: {email}")
    print(f"\n📧 VERIFICATION LINKS:")
    print(f"🔗 Regular link: {verify_url}")
    print(f"🔗 Direct token verification: {BASE_URL}/api/auth/email/dev-verify-token/{token}")
    print(f"🔗 Manual verification page: {BASE_URL}/direct-verify")
    print(f"\n💡 QUICK VERIFICATION OPTIONS:")
    print(f"1. Click one of the links above")
    print(f"2. Go to {BASE_URL}/direct-verify and paste token: {token}")
    print(f"3. Use endpoint: {BASE_URL}/api/auth/email/dev-verify-token/{token}")
    
    # In development mode, we can just print the email and skip sending
    if DEV_MODE:
        print("\nDEVELOPMENT MODE: Email not actually sent, but would be sent with the content above.")
        print(f"====================================\n")
        return True
    
    # In production mode, actually send the email
    if not RESEND_API_KEY:
        print("\nERROR: RESEND_API_KEY not set - cannot send emails in production!")
        print("Please set RESEND_API_KEY environment variable in Railway")
        return False
    
    # Try to send email, but handle Resend credits exceeded gracefully
    email_sent = send_email(
        to_email=email,
        subject="Verify Your Email Address", 
        html_content=html_content
    )
    
    if not email_sent:
        print("\n🚨 EMAIL SENDING FAILED - Likely Resend credits exceeded")
        print("📧 MANUAL VERIFICATION REQUIRED:")
        print(f"   Use: {BASE_URL}/api/auth/email/prod-verify/{email.split('@')[0]}")
        print("   Or register with a different email and manually verify")
    
    return email_sent

# Generate and send verification token
def generate_verification_token(user_id: int, email: str, db: Session):
    """Generate verification token with detailed logging"""
    # Generate token
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    # Store token in database
    db_token = EmailVerification(
        user_id=user_id,
        token=token,
        expires=expires
    )
    db.add(db_token)
    db.commit()
    
    # Log token info
    print(f"\n==== VERIFICATION TOKEN GENERATED ====")
    print(f"User ID: {user_id}")
    print(f"Email: {email}")
    print(f"Token: {token}")
    print(f"Expires: {expires}")
    print(f"=======================================\n")
    
    return token

# Verify email (with path parameter)
@router.get("/verify-email/{token}", status_code=status.HTTP_200_OK)
async def verify_email(token: str, db: Session = Depends(get_db)):
    # Find token in database
    db_token = db.query(EmailVerification).filter(
        EmailVerification.token == token,
        EmailVerification.expires > datetime.utcnow(),
        EmailVerification.used == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Mark user as verified
    user.is_verified = True
    
    # Mark token as used
    db_token.used = True
    
    db.commit()
    
    return {"message": "Email verified successfully"}

# Verify email (with query parameter)
@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email_query(token: str, db: Session = Depends(get_db)):
    """Verify email with token provided as a query parameter"""
    print(f"\n==== EMAIL VERIFICATION ATTEMPT ====")
    print(f"Token: {token}")
    print(f"Token Length: {len(token) if token else 0}")
    
    if not token:
        print("Error: Missing token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing verification token"
        )
    
    try:
        # Find token in database
        db_token = db.query(EmailVerification).filter(
            EmailVerification.token == token
        ).first()
        
        if not db_token:
            print("Error: Token not found in database")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
            
        # Get user first (so we can return username even if verification fails)
        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user:
            print(f"Error: User not found for token user_id={db_token.user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        username = user.username
            
        # Check if token is expired
        if db_token.expires < datetime.utcnow():
            print(f"Error: Token expired (Expired: {db_token.expires}, Current: {datetime.utcnow()})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
                headers={"X-Username": username}
            )
            
        # Check if token was already used
        if db_token.used:
            print("Error: Token already used")
            return {"message": "This verification link has already been used", "username": username}
        
        # Check if user is already verified
        if user.is_verified:
            print(f"Notice: User {user.username} (ID: {user.id}) is already verified")
            return {"message": "Email already verified", "username": username}
        
        # Mark user as verified
        user.is_verified = True
        
        # Mark token as used
        db_token.used = True
        
        print(f"Success: User {user.username} (ID: {user.id}) email verified")
        
        db.commit()
        
        return {"message": "Email verified successfully", "username": username}
    except HTTPException as e:
        # Add username to error response if possible
        if 'user' in locals() and user:
            e.detail = {"detail": e.detail, "username": user.username}
        raise e
    except Exception as e:
        # Log and handle any other exceptions
        print(f"Error: Unexpected error during verification: {str(e)}")
        # Add username to error response if possible
        if 'user' in locals() and user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"detail": "An unexpected error occurred during verification", "username": user.username}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred during verification"
            )

# Debug endpoint to print token information 
@router.get("/debug-token", status_code=status.HTTP_200_OK)
async def debug_token(token: str):
    """Print token information for debugging"""
    print(f"\n==== DEBUG TOKEN ====")
    print(f"Received token: {token}")
    print(f"Token length: {len(token)}")
    print(f"===================\n")
    
    return {
        "message": "Token debug information printed to console",
        "token": token,
        "token_length": len(token)
    }

# Development endpoint to verify a token directly in the browser
@router.get("/dev-token-verify/{token}", status_code=status.HTTP_200_OK)
async def dev_token_verify(token: str, db: Session = Depends(get_db)):
    """Development endpoint to verify a token directly (for debugging purposes)"""
    # Only allow in development mode
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    print(f"\n==== DEV TOKEN VERIFICATION ====")
    print(f"Token: {token}")
    
    # Find token in database
    db_token = db.query(EmailVerification).filter(
        EmailVerification.token == token
    ).first()
    
    if not db_token:
        print(f"Error: Token '{token}' not found in database")
        return {
            "message": "Token not found in database", 
            "valid": False,
            "token": token
        }
    
    print(f"Token found: {db_token.token}")
    print(f"User ID: {db_token.user_id}")
    print(f"Expires: {db_token.expires}")
    print(f"Already used: {db_token.used}")
    print(f"Expired: {db_token.expires < datetime.utcnow()}")
    
    # Get user
    user = db.query(User).filter(User.id == db_token.user_id).first()
    
    if not user:
        print(f"Error: User not found for token user_id={db_token.user_id}")
        return {
            "message": "User not found for this token", 
            "valid": False,
            "token": token,
            "user_id": db_token.user_id
        }
    
    print(f"User found: {user.username} ({user.email})")
    print(f"User already verified: {user.is_verified}")
    print(f"================================\n")
    
    return {
        "message": "Token information", 
        "valid": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified
        },
        "token_info": {
            "expires": str(db_token.expires),
            "used": db_token.used,
            "expired": db_token.expires < datetime.utcnow()
        }
    }

# Resend verification email
@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(
    request: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        # We still return success to prevent email enumeration
        return {"message": "If this email exists and is not verified, a new verification link will be sent."}
    
    # Check if already verified
    if user.is_verified:
        return {"message": "This email is already verified."}
    
    # Generate new token
    token = generate_verification_token(user.id, user.email, db)
    
    # Send email in background
    if DEV_MODE:
        # In development, send immediately
        send_verification_email(user.email, token)
    else:
        # In production, use background task
        background_tasks.add_task(send_verification_email, user.email, token)
    
    return {"message": "If this email exists and is not verified, a new verification link will be sent."}

@router.get("/dev/verify/{username}", status_code=status.HTTP_200_OK)
async def dev_verify_by_username(username: str, db: Session = Depends(get_db)):
    """Development endpoint to verify email by username directly (WITHOUT token)
    
    This endpoint should only be available in development mode!
    """
    # Check if we're in development mode
    if os.getenv("ENVIRONMENT", "development") != "production":
        # Find user by username
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with username {username} not found"
            )
        
        # Mark user as verified
        user.is_verified = True
        db.commit()
        
        return {"message": f"Email for user {username} verified successfully in development mode"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode"
        )

@router.get("/prod-verify/{username}", status_code=status.HTTP_200_OK)
async def prod_verify_by_username(username: str, db: Session = Depends(get_db)):
    """TEMPORARY production endpoint to verify email by username - REMOVE AFTER TESTING"""
    
    # Find user by username
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    
    # Mark user as verified
    user.is_verified = True
    db.commit()
    
    print(f"\n[PROD-VERIFY] User {username} manually verified via production endpoint")
    
    return {"message": f"Email for user {username} verified successfully", "username": username}

@router.get("/dev/verify/{email}", status_code=status.HTTP_200_OK)
async def dev_verify_by_email(email: str, db: Session = Depends(get_db)):
    """Development endpoint to verify email directly (WITHOUT token)
    
    This endpoint should only be available in development mode!
    """
    # Check if we're in development mode
    if os.getenv("ENVIRONMENT", "development") != "production":
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        
        # Mark user as verified
        user.is_verified = True
        db.commit()
        
        return {"message": f"Email {email} verified successfully in development mode"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode"
        )
    
    
@router.get("/dev/verify/email/{email}", status_code=status.HTTP_200_OK)
async def dev_verify_by_email(email: str, db: Session = Depends(get_db)):
    """Development endpoint to verify email directly"""
    # Check if we're in development mode
    if os.getenv("ENVIRONMENT", "development") != "production":
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email} not found"
            )
        
        # Mark user as verified
        user.is_verified = True
        db.commit()
        
        return {"message": f"Email {email} verified successfully in development mode"}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode"
        )

@router.get("/dev/manual-verify/{username}", status_code=status.HTTP_200_OK)
async def dev_manual_verify(username: str, db: Session = Depends(get_db)):
    """Development endpoint to manually verify a user by username"""
    # Only allow in development mode
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    print(f"\n==== DEV MANUAL VERIFICATION ====")
    print(f"Attempting to verify user: {username}")
    
    # Find user by username
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"Error: User '{username}' not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    
    # Mark user as verified
    user.is_verified = True
    db.commit()
    
    print(f"Success: User {user.username} (ID: {user.id}) manually verified")
    print(f"=====================================\n")
    
    return {
        "message": f"User '{username}' verified successfully",
        "username": user.username,
        "email": user.email,
        "id": user.id
    }

# Development endpoint for manual verification
@router.get("/direct-verify/{username}", status_code=status.HTTP_302_FOUND)
async def direct_verify(username: str, db: Session = Depends(get_db)):
    """Development endpoint to verify and redirect to success page"""
    # Only allow in development mode
    if os.getenv("ENVIRONMENT", "development") == "production":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    print(f"\n==== DIRECT VERIFICATION ====")
    print(f"Verifying user: {username}")
    
    # Find user by username
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"Error: User '{username}' not found")
        return RedirectResponse(url=f"/verification-failed?error=User+'{username}'+not+found")
    
    # Mark user as verified
    user.is_verified = True
    db.commit()
    
    print(f"Success: User {user.username} (ID: {user.id}) verified")
    print(f"===========================\n")
    
    # Redirect to success page
    return RedirectResponse(url="/verification-success")

# Static verification success page endpoint
@router.get("/verification-success", response_class=HTMLResponse)
async def verification_success_page():
    """Static HTML page for verification success"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Verified</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                background-color: #111111;
                max-width: 100%;
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background-color: #222222;
                border-radius: 10px;
                padding: 40px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                text-align: center;
            }
            .logo {
                margin-bottom: 20px;
                display: inline-block;
            }
            .logo-img {
                max-width: 180px;
                height: auto;
            }
            .logo-placeholder {
                background-color: #d4af37;
                color: #000000;
                font-weight: bold;
                padding: 12px 20px;
                font-size: 18px;
                letter-spacing: 1px;
                display: inline-block;
            }
            h1 {
                color: #d4af37;
                margin-bottom: 20px;
                font-size: 28px;
            }
            .button {
                display: inline-block;
                background-color: #d4af37;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 30px;
                transition: background-color 0.3s, transform 0.2s;
                border: none;
                font-size: 16px;
                cursor: pointer;
            }
            .button:hover {
                background-color: #e5be42;
                transform: translateY(-2px);
            }
            .success-icon {
                color: #00cc66;
                font-size: 64px;
                margin-bottom: 20px;
            }
            .user-message {
                color: #ffffff;
                font-size: 18px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img 
                    src="/images/arbify-logo.png" 
                    alt="Arbify" 
                    class="logo-img"
                    onerror="this.style.display='none'; this.parentNode.innerHTML='<div class=\'logo-placeholder\'>ARBIFY</div>';"
                />
            </div>
            <div class="success-icon">✓</div>
            <h1>Email Verified Successfully!</h1>
            <p class="user-message">Your email has been successfully verified. You can now log in to your account.</p>
            <a href="/login" class="button">Log In Now</a>
        </div>
    </body>
    </html>
    """
    return html_content

# Static verification failed page endpoint
@router.get("/verification-failed", response_class=HTMLResponse)
async def verification_failed_page(error: str = "Verification failed"):
    """Static HTML page for verification failure"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verification Failed</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #ffffff;
                background-color: #111111;
                max-width: 100%;
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background-color: #222222;
                border-radius: 10px;
                padding: 40px;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
                text-align: center;
            }}
            .logo {{
                margin-bottom: 20px;
                display: inline-block;
            }}
            .logo-img {{
                max-width: 180px;
                height: auto;
            }}
            .logo-placeholder {{
                background-color: #d4af37;
                color: #000000;
                font-weight: bold;
                padding: 12px 20px;
                font-size: 18px;
                letter-spacing: 1px;
                display: inline-block;
            }}
            h1 {{
                color: #cc4444;
                margin-bottom: 20px;
                font-size: 28px;
            }}
            .button {{
                display: inline-block;
                background-color: #d4af37;
                color: #000;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 6px;
                font-weight: bold;
                margin-top: 30px;
                transition: background-color 0.3s, transform 0.2s;
                border: none;
                font-size: 16px;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #e5be42;
                transform: translateY(-2px);
            }}
            .error-icon {{
                color: #cc4444;
                font-size: 64px;
                margin-bottom: 20px;
            }}
            .error-message {{
                background-color: rgba(204, 68, 68, 0.2);
                padding: 15px;
                border-radius: 6px;
                margin: 20px 0;
                border: 1px solid rgba(204, 68, 68, 0.3);
            }}
            .secondary-link {{
                color: #d4af37;
                text-decoration: none;
                margin-top: 20px;
                display: inline-block;
                font-size: 15px;
                transition: color 0.3s;
            }}
            .secondary-link:hover {{
                color: #e5be42;
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <img 
                    src="/images/arbify-logo.png" 
                    alt="Arbify" 
                    class="logo-img"
                    onerror="this.style.display='none'; this.parentNode.innerHTML='<div class=\'logo-placeholder\'>ARBIFY</div>';"
                />
            </div>
            <div class="error-icon">✕</div>
            <h1>Verification Failed</h1>
            <div class="error-message">
                {error.replace('+', ' ')}
            </div>
            <p>We couldn't verify your email address. The link may be invalid or expired.</p>
            <a href="/resend-verification" class="button">Resend Verification</a>
            <br>
            <a href="/login" class="secondary-link">Back to Login</a>
        </div>
    </body>
    </html>
    """
    return html_content