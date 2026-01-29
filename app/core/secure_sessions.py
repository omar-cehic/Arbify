"""
Secure Session Management for Arbify
===================================

Enhanced session security including:
- Secure cookie handling
- Session encryption
- Token refresh mechanism
- Session monitoring
"""

import os
import json
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any
from jose import jwt, JWTError
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet

from security_config import SESSION_CONFIG, security_config

# Security logger
security_logger = logging.getLogger("security.sessions")

class SecureSessionManager:
    """Enhanced secure session management"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(hours=1)  # Short-lived access tokens
        self.refresh_token_expire = timedelta(days=7)  # Longer-lived refresh tokens
        
        # Session encryption
        self.session_key = os.getenv("SESSION_ENCRYPTION_KEY")
        if not self.session_key:
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("SESSION_ENCRYPTION_KEY must be set in production!")
            else:
                self.session_key = Fernet.generate_key()
                print(f"⚠️  Generated temporary session key for development")
                print(f"🔑 Add this to your environment: SESSION_ENCRYPTION_KEY={self.session_key.decode()}")
        
        if isinstance(self.session_key, str):
            self.session_key = self.session_key.encode()
        
        self.cipher = Fernet(self.session_key)
        
        # Active sessions tracking
        self.active_sessions: Dict[str, Dict] = {}
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create secure access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.access_token_expire
        
        # Add security claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(16),  # JWT ID for tracking
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # Log token creation
            security_logger.info(f"Access token created for user: {data.get('sub', 'unknown')}")
            
            return encoded_jwt
        except Exception as e:
            security_logger.error(f"Token creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Create secure refresh token"""
        to_encode = {
            "sub": user_data["sub"],
            "type": "refresh",
            "exp": datetime.utcnow() + self.refresh_token_expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }
        
        try:
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            # Store refresh token info
            self.active_sessions[to_encode["jti"]] = {
                "user": user_data["sub"],
                "created": datetime.utcnow(),
                "last_used": datetime.utcnow(),
                "ip": user_data.get("ip", "unknown"),
                "user_agent": user_data.get("user_agent", "unknown"),
            }
            
            security_logger.info(f"Refresh token created for user: {user_data['sub']}")
            
            return encoded_jwt
        except Exception as e:
            security_logger.error(f"Refresh token creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Refresh token creation failed"
            )
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise JWTError("Token expired")
            
            # Update session tracking for refresh tokens
            if token_type == "refresh":
                jti = payload.get("jti")
                if jti in self.active_sessions:
                    self.active_sessions[jti]["last_used"] = datetime.utcnow()
            
            return payload
            
        except JWTError as e:
            security_logger.warning(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def refresh_access_token(self, refresh_token: str, client_ip: str) -> Dict[str, str]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token, "refresh")
            
            # Check if refresh token is in active sessions
            jti = payload.get("jti")
            if jti not in self.active_sessions:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token revoked"
                )
            
            # Verify IP consistency (optional security check)
            session_info = self.active_sessions[jti]
            if session_info["ip"] != client_ip:
                security_logger.warning(f"IP mismatch for refresh token: {jti}")
                # Could block or require re-authentication
            
            # Create new access token
            user_data = {"sub": payload["sub"]}
            new_access_token = self.create_access_token(user_data)
            
            # Update session last used
            session_info["last_used"] = datetime.utcnow()
            
            security_logger.info(f"Access token refreshed for user: {payload['sub']}")
            
            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": int(self.access_token_expire.total_seconds())
            }
            
        except Exception as e:
            security_logger.error(f"Token refresh failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token refresh failed"
            )
    
    def revoke_token(self, token: str):
        """Revoke a refresh token"""
        try:
            payload = self.verify_token(token, "refresh")
            jti = payload.get("jti")
            
            if jti in self.active_sessions:
                del self.active_sessions[jti]
                security_logger.info(f"Token revoked for user: {payload['sub']}")
            
        except Exception as e:
            security_logger.warning(f"Token revocation failed: {str(e)}")
    
    def revoke_all_user_tokens(self, username: str):
        """Revoke all tokens for a user"""
        revoked_count = 0
        sessions_to_remove = []
        
        for jti, session_info in self.active_sessions.items():
            if session_info["user"] == username:
                sessions_to_remove.append(jti)
        
        for jti in sessions_to_remove:
            del self.active_sessions[jti]
            revoked_count += 1
        
        security_logger.info(f"Revoked {revoked_count} tokens for user: {username}")
        return revoked_count
    
    def set_secure_cookie(self, response: Response, name: str, value: str, max_age: int = None):
        """Set secure HTTP-only cookie"""
        if max_age is None:
            max_age = int(self.refresh_token_expire.total_seconds())
        
        # Encrypt cookie value
        encrypted_value = self.cipher.encrypt(value.encode()).decode()
        
        response.set_cookie(
            key=name,
            value=encrypted_value,
            max_age=max_age,
            httponly=True,  # Prevent XSS
            secure=SESSION_CONFIG["secure_cookies"],  # HTTPS only in production
            samesite=SESSION_CONFIG["samesite_cookies"],  # CSRF protection
            path="/",
        )
    
    def get_secure_cookie(self, request: Request, name: str) -> Optional[str]:
        """Get and decrypt secure cookie"""
        encrypted_value = request.cookies.get(name)
        if not encrypted_value:
            return None
        
        try:
            decrypted_value = self.cipher.decrypt(encrypted_value.encode()).decode()
            return decrypted_value
        except Exception as e:
            security_logger.warning(f"Cookie decryption failed: {str(e)}")
            return None
    
    def clear_secure_cookie(self, response: Response, name: str):
        """Clear secure cookie"""
        response.delete_cookie(
            key=name,
            path="/",
            secure=SESSION_CONFIG["secure_cookies"],
            samesite=SESSION_CONFIG["samesite_cookies"],
        )
    
    def get_active_sessions(self, username: str = None) -> Dict[str, Any]:
        """Get active sessions (for monitoring)"""
        if username:
            return {
                jti: info for jti, info in self.active_sessions.items()
                if info["user"] == username
            }
        return self.active_sessions.copy()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for jti, session_info in self.active_sessions.items():
            # Consider session expired if not used for 24 hours
            if (now - session_info["last_used"]).total_seconds() > 86400:
                expired_sessions.append(jti)
        
        for jti in expired_sessions:
            del self.active_sessions[jti]
        
        if expired_sessions:
            security_logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global session manager instance
session_manager = SecureSessionManager()

# Custom security scheme
class SecureBearer(HTTPBearer):
    """Enhanced bearer token security"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials = await super().__call__(request)
        
        if credentials:
            # Additional security checks
            from security_config import get_client_ip
            client_ip = get_client_ip(request)
            
            # Log token usage
            security_logger.debug(f"Token used from IP: {client_ip}")
            
            # Could add additional checks here (rate limiting, etc.)
        
        return credentials

# Security dependencies
security_scheme = SecureBearer()

def get_current_user_secure(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    """Enhanced current user dependency with security checks"""
    try:
        # Verify access token
        payload = session_manager.verify_token(credentials.credentials, "access")
        username = payload.get("sub")
        
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Additional security checks could go here
        # (e.g., check if user is still active, account not locked, etc.)
        
        return {
            "username": username,
            "token_id": payload.get("jti"),
            "issued_at": payload.get("iat"),
        }
        
    except Exception as e:
        security_logger.warning(f"User authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Session monitoring functions
def get_session_stats() -> Dict[str, Any]:
    """Get session statistics for monitoring"""
    sessions = session_manager.get_active_sessions()
    now = datetime.utcnow()
    
    active_count = len(sessions)
    recent_count = len([
        s for s in sessions.values()
        if (now - s["last_used"]).total_seconds() < 3600  # Last hour
    ])
    
    return {
        "total_active_sessions": active_count,
        "recently_active_sessions": recent_count,
        "session_details": sessions
    }

# Export classes and functions
__all__ = [
    'SecureSessionManager',
    'session_manager',
    'SecureBearer',
    'get_current_user_secure',
    'get_session_stats'
]
