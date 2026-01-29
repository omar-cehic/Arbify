from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import re
import logging
from pydantic import BaseModel, EmailStr, validator

from app.core.database import SessionLocal
from app.models.user import User, UserProfile
from app.api.v1.auth import get_db, get_current_active_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.config import DEV_MODE
from app.core.security_logger import SecurityLogger
from scripts.password_reset import router as password_reset_router

# Configure logging
logger = logging.getLogger(__name__)

# Create rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

# Include password reset router
router.include_router(password_reset_router, prefix="/password", tags=["Password Reset"])

# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        # Add more password strength requirements
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class UserProfileUpdate(BaseModel):
    preferred_unit: Optional[str] = None
    notification_email: Optional[bool] = None
    notification_browser: Optional[bool] = None
    preferred_sports: Optional[str] = None
    preferred_bookmakers: Optional[str] = None
    minimum_profit_threshold: Optional[float] = None
    full_name: str

class UserNameUpdate(BaseModel):
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
    
    class Config:
        from_attributes = True

class ProfileResponse(BaseModel):
    balance: float
    preferred_unit: str
    notification_email: bool
    notification_browser: bool
    preferred_sports: str
    preferred_bookmakers: str
    minimum_profit_threshold: float
    
    class Config:
        from_attributes = True

# User registration and verification functions
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user_data: UserCreate):
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        is_verified=False  # Default to not verified
    )
    user.password = user_data.password
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Authentication routes
@router.post("/register", response_model=UserResponse)
@limiter.limit("10/minute")  # 10 registration attempts per minute per IP
def register_user(
    request: Request,
    user_data: UserCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if username exists
    db_user = get_user_by_username(db, user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    db_user = get_user_by_email(db, user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user - automatically verified (no email verification needed)
    user = create_user(db, user_data)
    user.is_verified = True  # Auto-verify all new users
    db.commit()
    
    # Create default profile with notification settings enabled
    profile = UserProfile(
        user_id=user.id,
        preferred_sports="soccer_epl,soccer_champions_league,soccer_la_liga",
        preferred_bookmakers="",
        notification_email=True,  # Enable email notifications by default
        notification_browser=True,  # Enable browser notifications by default
        minimum_profit_threshold=1.0  # Default 1% minimum profit threshold
    )
    db.add(profile)
    db.commit()
    
    # Log user registration for security monitoring
    client_ip = SecurityLogger.get_client_ip(request)
    SecurityLogger.log_registration(
        username=user.username,
        email=user.email,
        ip_address=client_ip
    )
    
    # Send welcome email in background
    from app.services.email_service import email_service
    background_tasks.add_task(email_service.send_welcome_email, user.email, user.username)
    
    if DEV_MODE:
        print(f"📧 WELCOME EMAIL: Queued for {user.email} (username: {user.username})")
    
    return user

@router.post("/token", response_model=Token)
@limiter.limit("20/minute")  # 20 login attempts per minute per IP
def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Security: Only log non-sensitive info in production
    if not DEV_MODE:
        logger.info(f"Login attempt for user: {form_data.username}")
    
    client_ip = SecurityLogger.get_client_ip(request)
    user_agent = request.headers.get('user-agent', 'Unknown')
    
    user = get_user_by_username(db, form_data.username)
    if not user:
        # Log failed login attempt
        SecurityLogger.log_login_attempt(
            username=form_data.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.verify_password(form_data.password):
        # Log failed login attempt
        SecurityLogger.log_login_attempt(
            username=user.username,
            success=False,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Log successful login
    SecurityLogger.log_login_attempt(
        username=user.username,
        success=True,
        ip_address=client_ip,
        user_agent=user_agent
    )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name
    }

@router.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.get("/users/me/profile", response_model=ProfileResponse)
def read_user_profile(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not current_user.profile:
        # Create profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    return current_user.profile

@router.put("/users/me/profile", response_model=ProfileResponse)
def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    # Update fields if provided
    if profile_update.preferred_unit is not None:
        profile.preferred_unit = profile_update.preferred_unit
    if profile_update.notification_email is not None:
        profile.notification_email = profile_update.notification_email
    if profile_update.notification_browser is not None:
        profile.notification_browser = profile_update.notification_browser
    if profile_update.preferred_sports is not None:
        profile.preferred_sports = profile_update.preferred_sports
    if profile_update.preferred_bookmakers is not None:
        profile.preferred_bookmakers = profile_update.preferred_bookmakers
    if profile_update.minimum_profit_threshold is not None:
        profile.minimum_profit_threshold = profile_update.minimum_profit_threshold
        
    # Also update full name on user object if provided
    if profile_update.full_name:
        current_user.full_name = profile_update.full_name
        
    db.commit()
    db.refresh(profile)
    return profile