from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, validator

from app.core.database import SessionLocal
from app.models.user import User
from app.core.config import SECRET_KEY, ALGORITHM

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 4  # 4 hours instead of 24 for better security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Create router
router = APIRouter()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Token creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token verification and user extraction
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Active user check
def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

@router.put("/user/profile", response_model=dict)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user profile details"""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.email is not None:
        # Check if email is already taken by another user
        existing_user = db.query(User).filter(User.email == user_update.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name
    }



# Password change model
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class DirectPasswordChangeRequest(BaseModel):
    username: str
    current_password: str
    new_password: str
    
    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v


# Get current user endpoint
@router.get("/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user details"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "roles": current_user.roles
    }

# Change password endpoint
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password = password_data.new_password
    db.commit()
    
    return {"message": "Password changed successfully"}

# Add this after the change-password endpoint
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password_redirect(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Redirect old reset-password endpoint to change-password for backward compatibility"""
    # Log the request
    print(f"Reset-password endpoint called by user: {current_user.username}")
    
    try:
        # This just calls the change_password function
        return await change_password(password_data, current_user, db)
    except Exception as e:
        print(f"Error in reset_password_redirect: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error changing password: {str(e)}"
        )

# Direct password change endpoint that doesn't require JWT
@router.post("/direct-change-password", status_code=status.HTTP_200_OK)
def direct_change_password(
    password_data: DirectPasswordChangeRequest,
    db: Session = Depends(get_db)
):
    """Direct password change endpoint that doesn't require JWT auth"""
    print(f"Direct password change attempt for user: {password_data.username}")
    
    # Find the user
    user = db.query(User).filter(User.username == password_data.username).first()
    if not user:
        print(f"User not found: {password_data.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    print(f"User found: {user.username} (ID: {user.id})")
    
    # Verify current password
    print(f"Verifying password for user {user.username}")
    print(f"Current password length: {len(password_data.current_password)}")
    print(f"New password length: {len(password_data.new_password)}")
    
    if not user.verify_password(password_data.current_password):
        print(f"Password verification failed for user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    print(f"Password verification successful for user: {user.username}")
    
    # Update password
    try:
        user.password = password_data.new_password
        db.commit()
        print(f"Password updated successfully for user: {user.username}")
        return {"message": "Password changed successfully", "user": user.username}
    except Exception as e:
        print(f"Error updating password: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating password: {str(e)}"
        )

# User registration and verification functions
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user_data):
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