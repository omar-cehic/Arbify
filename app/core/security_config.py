"""
Comprehensive Security Configuration for Arbify
==============================================

This module provides enterprise-grade security configurations including:
- SSL/TLS enforcement
- Database encryption
- Security headers
- Rate limiting
- Monitoring
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any
from cryptography.fernet import Fernet
from fastapi import HTTPException, Request
import logging

# Security Logger
security_logger = logging.getLogger("security.config")

class SecurityConfig:
    """Centralized security configuration and utilities"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        self.setup_encryption()
    
    def setup_encryption(self):
        """Initialize encryption keys for sensitive data"""
        # Database encryption key - more resilient for Railway deployment
        self.db_encryption_key = os.getenv("DB_ENCRYPTION_KEY")
        if not self.db_encryption_key:
            if self.is_production:
                # Generate a temporary key for production if not set, but warn heavily
                self.db_encryption_key = Fernet.generate_key()
                security_logger.warning("🚨 SECURITY WARNING: DB_ENCRYPTION_KEY not set in production! Using temporary key.")
                security_logger.warning("🔑 Please set this environment variable: DB_ENCRYPTION_KEY=" + self.db_encryption_key.decode())
                print(f"🚨 CRITICAL: DB_ENCRYPTION_KEY missing in production! Generated temporary key.")
            else:
                # Generate temporary key for development
                self.db_encryption_key = Fernet.generate_key()
                print(f"⚠️  Generated temporary DB encryption key for development")
                print(f"🔑 Add this to your environment: DB_ENCRYPTION_KEY={self.db_encryption_key.decode()}")
        
        if isinstance(self.db_encryption_key, str):
            self.db_encryption_key = self.db_encryption_key.encode()
        
        try:
            self.cipher = Fernet(self.db_encryption_key)
        except Exception as e:
            security_logger.error(f"Failed to initialize encryption cipher: {e}")
            # Generate new key as fallback
            self.db_encryption_key = Fernet.generate_key()
            self.cipher = Fernet(self.db_encryption_key)
            security_logger.warning("Using fallback encryption key")
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for database storage"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data from database"""
        if not encrypted_data:
            return encrypted_data
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            # Handle legacy unencrypted data
            return encrypted_data

# SSL/TLS Configuration
SSL_CONFIG = {
    "require_https": True if os.getenv("ENVIRONMENT") == "production" else False,
    "hsts_max_age": 31536000,  # 1 year
    "hsts_include_subdomains": True,
    "hsts_preload": True,
}

# Security Headers Configuration
SECURITY_HEADERS = {
    "production": {
        # Content Security Policy - Strict
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.stripe.com https://vercel.live; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://api.stripe.com https://arbify-beige.vercel.app https://web-production-af8b.up.railway.app wss:; "
            "frame-src https://js.stripe.com; "
            "media-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests"
        ),
        # HTTP Strict Transport Security
        "Strict-Transport-Security": f"max-age={SSL_CONFIG['hsts_max_age']}; includeSubDomains; preload",
        # Prevent MIME type sniffing
        "X-Content-Type-Options": "nosniff",
        # Prevent clickjacking
        "X-Frame-Options": "DENY",
        # XSS Protection
        "X-XSS-Protection": "1; mode=block",
        # Referrer Policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # Permissions Policy
        "Permissions-Policy": (
            "geolocation=(), microphone=(), camera=(), payment=(), "
            "usb=(), accelerometer=(), gyroscope=(), magnetometer=(), "
            "fullscreen=(self), display-capture=()"
        ),
        # Cross-Origin Policies
        "Cross-Origin-Embedder-Policy": "require-corp",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
    },
    "development": {
        # More permissive for development
        "Content-Security-Policy": (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "connect-src 'self' http://localhost:* https://api.stripe.com ws://localhost:*; "
            "img-src 'self' data: https: http: blob:; "
            "frame-src https://js.stripe.com"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }
}

# Rate Limiting Configuration
RATE_LIMITS = {
    # Authentication endpoints (most restrictive)
    "auth_register": "3/minute",
    "auth_login": "5/minute", 
    "auth_password_reset": "3/hour",
    
    # API endpoints (moderate) - BALANCED FOR REAL USERS
    "api_odds": "60/minute",  # Restored for normal use
    "api_arbitrage": "30/minute",  # Restored for normal use
    "api_save_arbitrage": "15/minute",  # Reasonable for user actions
    "api_user_profile": "25/minute",  # Enough for profile updates
    "api_subscription": "40/minute",  # CRITICAL: Dashboard makes multiple calls
    
    # General endpoints (reasonable protection)
    "api_general": "100/minute",  # Restored for normal use
    
    # Admin endpoints (very restrictive)
    "admin": "5/hour",  # Reduced from 10
}

# Database Security Configuration
DATABASE_SECURITY = {
    "encrypt_fields": [
        "email",  # Encrypt user emails
        "full_name",  # Encrypt personal names
        "notes",  # Encrypt user notes in arbitrages
    ],
    "hash_fields": [
        "password",  # Already handled by bcrypt
    ],
    "audit_fields": [
        "created_at",
        "updated_at", 
        "last_login",
        "last_password_change",
    ]
}

# Session Security Configuration
SESSION_CONFIG = {
    "secure_cookies": True if os.getenv("ENVIRONMENT") == "production" else False,
    "httponly_cookies": True,
    "samesite_cookies": "strict",
    "session_timeout": 3600,  # 1 hour
    "refresh_token_timeout": 3600 * 24 * 7,  # 1 week
}

# File Upload Security
UPLOAD_SECURITY = {
    "allowed_extensions": [".jpg", ".jpeg", ".png", ".gif", ".pdf"],
    "max_file_size": 5 * 1024 * 1024,  # 5MB
    "scan_uploads": True,
    "quarantine_suspicious": True,
}

# Monitoring Configuration
MONITORING_CONFIG = {
    "log_security_events": True,
    "log_api_calls": True,
    "alert_on_suspicious_activity": True,
    "alert_on_multiple_failed_logins": 5,
    "alert_on_rate_limit_exceeded": True,
}

# Security Event Types for Logging
SECURITY_EVENTS = {
    "LOGIN_SUCCESS": "login_success",
    "LOGIN_FAILED": "login_failed", 
    "REGISTRATION": "user_registration",
    "PASSWORD_CHANGE": "password_change",
    "RATE_LIMIT_EXCEEDED": "rate_limit_exceeded",
    "SUSPICIOUS_ACTIVITY": "suspicious_activity",
    "ADMIN_ACCESS": "admin_access",
    "DATA_EXPORT": "data_export",
    "UNAUTHORIZED_ACCESS": "unauthorized_access",
    "SECURITY_SCAN": "security_scan",
}

def get_client_ip(request: Request) -> str:
    """Safely extract client IP from request headers"""
    # Check X-Forwarded-For (from load balancers/proxies)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP (from reverse proxies)
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    
    # Check CF-Connecting-IP (from Cloudflare)
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    
    # Fallback to direct client IP
    return getattr(request.client, 'host', 'unknown')

def is_suspicious_request(request: Request) -> bool:
    """Detect potentially suspicious requests"""
    user_agent = request.headers.get('user-agent', '').lower()
    
    # CRITICAL: Make suspicious patterns more specific to avoid false positives
    suspicious_patterns = [
        'sqlmap', 'nikto', 'dirb', 'gobuster', 'burp', 'nessus', 'scanner',
        'exploit', 'hack', 'attack', 'inject', 'malware', 'virus',
        # More specific bot patterns that are actually malicious
        'masscan', 'zmap', 'shodan', 'censys', 'nuclei',
        # Remove generic 'bot', 'crawler', 'spider' as they catch legitimate traffic
    ]
    
    # Check for suspicious user agents
    for pattern in suspicious_patterns:
        if pattern in user_agent:
            return True
    
    # Check for empty or very short user agents (more suspicious)
    if not user_agent or len(user_agent) < 10:
        return True
    
    # REMOVED: Suspicious headers check as x-forwarded-* are normal in production
    # These headers are commonly used by legitimate proxies and load balancers
    
    return False

def generate_csrf_token() -> str:
    """Generate a secure CSRF token"""
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, session_token: str) -> bool:
    """Validate CSRF token against session"""
    return secrets.compare_digest(token, session_token)

# Initialize security configuration
security_config = SecurityConfig()

# Export commonly used functions
__all__ = [
    'SecurityConfig', 'security_config', 'SSL_CONFIG', 'SECURITY_HEADERS',
    'RATE_LIMITS', 'DATABASE_SECURITY', 'SESSION_CONFIG', 'UPLOAD_SECURITY',
    'MONITORING_CONFIG', 'SECURITY_EVENTS', 'get_client_ip', 
    'is_suspicious_request', 'generate_csrf_token', 'validate_csrf_token'
]
