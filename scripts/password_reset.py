from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import secrets
import os
from dotenv import load_dotenv

from app.core.database import SessionLocal
from app.models.user import User, PasswordReset
from app.api.v1.auth import get_db
from app.core.config import IS_RAILWAY_DEPLOYMENT

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
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# Import centralized email service
from app.services.email_service import email_service

# Background task to send password reset email
def send_password_reset_email(email: str, token: str):
    """Send password reset email using centralized email service"""
    return email_service.send_password_reset_email(email, token)

# Request password reset
@router.post("/request-reset", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    request: PasswordResetRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # We still return success to prevent email enumeration attacks
        return {"message": "If this email exists in our system, a password reset link will be sent."}
    
    # Generate token
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)
    
    # Store token in database
    db_token = PasswordReset(
        user_id=user.id,
        token=token,
        expires=expires
    )
    db.add(db_token)
    db.commit()
    
    # Log token information for debugging and development
    print(f"\n==== PASSWORD RESET TOKEN GENERATED ====")
    print(f"User: {user.username} ({user.email})")
    print(f"Token: {token}")
    print(f"Reset URL: {BASE_URL}/reset-password?token={token}")
    print(f"Development URL: {BASE_URL}/api/auth/password/dev-reset/{token}")
    print(f"Expires: {expires}")
    print(f"==========================================\n")
    
    # Send email in background
    background_tasks.add_task(send_password_reset_email, user.email, token)
    
    return {"message": "If this email exists in our system, a password reset link will be sent."}

# Confirm password reset
@router.post("/confirm-reset", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    # Find token in database
    db_token = db.query(PasswordReset).filter(
        PasswordReset.token == reset_data.token,
        PasswordReset.expires > datetime.utcnow(),
        PasswordReset.used == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Set new password
    user.password = reset_data.new_password
    
    # Mark token as used
    db_token.used = True
    
    db.commit()
    
    return {"message": "Password has been reset successfully"}

# Verify token validity (for frontend to check before showing password reset form)
@router.get("/verify-reset-token/{token}")
async def verify_reset_token(token: str, db: Session = Depends(get_db)):
    db_token = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.expires > datetime.utcnow(),
        PasswordReset.used == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    return {"valid": True}

# Development endpoint for easier testing
@router.get("/dev-reset/{token}", status_code=status.HTTP_200_OK)
async def dev_reset_password(token: str, db: Session = Depends(get_db)):
    """Development endpoint to reset password to 'Password123' for testing"""
    # Find token in database
    db_token = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.expires > datetime.utcnow(),
        PasswordReset.used == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Set default testing password
    user.password = "Password123"
    
    # Mark token as used
    db_token.used = True
    
    db.commit()
    
    return {
        "message": f"Password for {user.username} has been reset to 'Password123' for testing",
        "username": user.username
    }

# Add this to password_reset.py
@router.get("/dev-tokens", tags=["Development"])
async def get_active_tokens(db: Session = Depends(get_db)):
    """Development endpoint to list all active password reset tokens"""
    # Check if we're in development mode
    if os.getenv("ENVIRONMENT", "development") != "production":
        # Get all non-expired and unused tokens
        tokens = db.query(PasswordReset).filter(
            PasswordReset.expires > datetime.utcnow(),
            PasswordReset.used == False
        ).all()
        
        token_info = []
        for token in tokens:
            # Get user
            user = db.query(User).filter(User.id == token.user_id).first()
            if user:
                reset_url = f"{BASE_URL}/reset-password?token={token.token}"
                dev_reset_url = f"{BASE_URL}/api/auth/password/dev-reset/{token.token}"
                
                token_info.append({
                    "username": user.username,
                    "email": user.email,
                    "token": token.token,
                    "reset_url": reset_url,
                    "dev_reset_url": dev_reset_url,
                    "expires": token.expires.isoformat()
                })
        
        return {"active_tokens": token_info}
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development mode"
        )

# Quick fix endpoint for debugging
@router.post("/quick-reset/{username}")
def quick_reset_password(username: str, db: Session = Depends(get_db)):
    """Quick password reset for debugging - sets password to 'newpass123'"""
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"error": "User not found"}
        
        # Set password to a known value using new bcrypt method
        user.password = "newpass123"
        db.commit()
        
        return {
            "message": f"Password reset for {username}",
            "new_password": "newpass123",
            "note": "Use this password to log in"
        }
    except Exception as e:
        return {"error": str(e)}