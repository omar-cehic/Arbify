"""
Enhanced Input Validation and Sanitization for Arbify
====================================================

Comprehensive input validation including:
- SQL injection prevention
- XSS protection
- Data sanitization
- Business logic validation
"""

import re
import html
import bleach
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, validator, EmailStr
from fastapi import HTTPException, status

# Security logger
security_logger = logging.getLogger("security.validation")

class SecureValidator:
    """Enhanced input validation and sanitization"""
    
    # Allowed HTML tags for user content (very restrictive)
    ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'br']
    ALLOWED_ATTRIBUTES = {}
    
    # Regex patterns for validation
    PATTERNS = {
        'username': re.compile(r'^[a-zA-Z0-9_]{3,30}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'password': re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$'),
        'sport_key': re.compile(r'^[a-z_]+$'),
        'team_name': re.compile(r'^[a-zA-Z0-9\s\-\.\']{1,100}$'),
        'bookmaker': re.compile(r'^[a-zA-Z0-9\s\-\.&]{1,50}$'),
        'notes': re.compile(r'^[a-zA-Z0-9\s\-\.\,\!\?\(\)]{0,1000}$'),
    }
    
    # Dangerous SQL patterns to block
    SQL_INJECTION_PATTERNS = [
        r'(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bCREATE\b|\bALTER\b)',
        r'(\b(OR|AND)\b\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+[\'\"]?)',
        r'(--|\#|\/\*|\*\/)',
        r'(\bxp_cmdshell\b|\bsp_executesql\b)',
        r'([\'\"];?\s*(OR|AND))',
    ]
    
    # XSS patterns to block
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>.*?</embed>',
        r'<form[^>]*>.*?</form>',
        r'<input[^>]*>',
        r'<textarea[^>]*>.*?</textarea>',
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: int = 1000) -> str:
        """Sanitize string input against XSS and injection attacks"""
        if not value:
            return ""
        
        # Convert to string and strip whitespace
        value = str(value).strip()
        
        # Check length
        if len(value) > max_length:
            raise ValueError(f"Input too long (max {max_length} characters)")
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                security_logger.warning(f"SQL injection attempt blocked: {pattern}")
                raise ValueError("Invalid input detected")
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                security_logger.warning(f"XSS attempt blocked: {pattern}")
                raise ValueError("Invalid input detected")
        
        # HTML encode to prevent XSS
        value = html.escape(value)
        
        # Additional cleaning with bleach
        value = bleach.clean(value, tags=cls.ALLOWED_TAGS, attributes=cls.ALLOWED_ATTRIBUTES)
        
        return value
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Validate and sanitize username"""
        if not username:
            raise ValueError("Username is required")
        
        username = cls.sanitize_string(username, 30)
        
        if not cls.PATTERNS['username'].match(username):
            raise ValueError("Username must be 3-30 characters, alphanumeric and underscores only")
        
        # Check for reserved usernames
        reserved = ['admin', 'root', 'api', 'www', 'mail', 'ftp', 'test', 'demo', 'system']
        if username.lower() in reserved:
            raise ValueError("Username is reserved")
        
        return username
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and sanitize email"""
        if not email:
            raise ValueError("Email is required")
        
        email = email.lower().strip()
        
        if not cls.PATTERNS['email'].match(email):
            raise ValueError("Invalid email format")
        
        # Check for disposable email domains
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'temp-mail.org', 'throwaway.email'
        ]
        
        domain = email.split('@')[1]
        if domain in disposable_domains:
            raise ValueError("Disposable email addresses are not allowed")
        
        return email
    
    @classmethod
    def validate_password(cls, password: str) -> str:
        """Validate password strength"""
        if not password:
            raise ValueError("Password is required")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if len(password) > 128:
            raise ValueError("Password too long (max 128 characters)")
        
        if not cls.PATTERNS['password'].match(password):
            raise ValueError("Password must contain at least one uppercase letter, one lowercase letter, and one number")
        
        # Check for common passwords
        common_passwords = [
            'password', '12345678', 'qwerty123', 'password123',
            'admin123', 'letmein', 'welcome123', 'changeme'
        ]
        
        if password.lower() in common_passwords:
            raise ValueError("Password is too common, please choose a stronger password")
        
        return password
    
    @classmethod
    def validate_decimal(cls, value: Union[str, int, float], min_val: float = 0, max_val: float = 1000000) -> Decimal:
        """Validate and convert to decimal"""
        try:
            decimal_value = Decimal(str(value))
            
            if decimal_value < min_val or decimal_value > max_val:
                raise ValueError(f"Value must be between {min_val} and {max_val}")
            
            # Limit decimal places
            if abs(decimal_value.as_tuple().exponent) > 2:
                raise ValueError("Maximum 2 decimal places allowed")
            
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid number format: {str(e)}")
    
    @classmethod
    def validate_odds(cls, odds: Union[str, int, float]) -> float:
        """Validate betting odds"""
        try:
            odds_value = float(odds)
            
            if odds_value < 1.01 or odds_value > 1000:
                raise ValueError("Odds must be between 1.01 and 1000")
            
            return round(odds_value, 2)
            
        except (ValueError, TypeError):
            raise ValueError("Invalid odds format")
    
    @classmethod
    def validate_sport_key(cls, sport_key: str) -> str:
        """Validate sport key"""
        if not sport_key:
            raise ValueError("Sport key is required")
        
        sport_key = cls.sanitize_string(sport_key, 50)
        
        if not cls.PATTERNS['sport_key'].match(sport_key):
            raise ValueError("Invalid sport key format")
        
        return sport_key
    
    @classmethod
    def validate_team_name(cls, team_name: str) -> str:
        """Validate team name"""
        if not team_name:
            raise ValueError("Team name is required")
        
        team_name = cls.sanitize_string(team_name, 100)
        
        if not cls.PATTERNS['team_name'].match(team_name):
            raise ValueError("Invalid team name format")
        
        return team_name
    
    @classmethod
    def validate_notes(cls, notes: str) -> str:
        """Validate user notes"""
        if not notes:
            return ""
        
        notes = cls.sanitize_string(notes, 1000)
        
        if not cls.PATTERNS['notes'].match(notes):
            raise ValueError("Notes contain invalid characters")
        
        return notes

# Enhanced Pydantic models with security validation
class SecureUserCreate(BaseModel):
    """Secure user creation model"""
    username: str
    email: EmailStr
    full_name: str
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        return SecureValidator.validate_username(v)
    
    @validator('email')
    def validate_email(cls, v):
        return SecureValidator.validate_email(str(v))
    
    @validator('full_name')
    def validate_full_name(cls, v):
        return SecureValidator.sanitize_string(v, 100)
    
    @validator('password')
    def validate_password(cls, v):
        return SecureValidator.validate_password(v)

class SecureArbitrageRequest(BaseModel):
    """Secure arbitrage save request"""
    sport_key: str
    sport_title: str
    home_team: str
    away_team: str
    match_time: str
    odds: Dict[str, Union[int, float]]
    bookmakers: Dict[str, str]
    profit_percentage: float
    bet_amount: float = 0.0
    status: str = "open"
    notes: str = ""
    
    @validator('sport_key')
    def validate_sport_key(cls, v):
        return SecureValidator.validate_sport_key(v)
    
    @validator('sport_title')
    def validate_sport_title(cls, v):
        return SecureValidator.sanitize_string(v, 100)
    
    @validator('home_team', 'away_team')
    def validate_team_names(cls, v):
        return SecureValidator.validate_team_name(v)
    
    @validator('match_time')
    def validate_match_time(cls, v):
        try:
            # Validate ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid date format')
    
    @validator('odds')
    def validate_odds(cls, v):
        if not isinstance(v, dict) or len(v) < 2:
            raise ValueError('At least 2 odds required')
        
        validated_odds = {}
        for outcome, odds in v.items():
            validated_outcome = SecureValidator.sanitize_string(outcome, 50)
            validated_odds[validated_outcome] = SecureValidator.validate_odds(odds)
        
        return validated_odds
    
    @validator('bookmakers')
    def validate_bookmakers(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Bookmakers must be a dictionary')
        
        validated_bookmakers = {}
        for outcome, bookmaker in v.items():
            validated_outcome = SecureValidator.sanitize_string(outcome, 50)
            validated_bookmaker = SecureValidator.sanitize_string(bookmaker, 50)
            
            if not SecureValidator.PATTERNS['bookmaker'].match(validated_bookmaker):
                raise ValueError('Invalid bookmaker name')
            
            validated_bookmakers[validated_outcome] = validated_bookmaker
        
        return validated_bookmakers
    
    @validator('profit_percentage')
    def validate_profit_percentage(cls, v):
        return float(SecureValidator.validate_decimal(v, -100, 1000))
    
    @validator('bet_amount')
    def validate_bet_amount(cls, v):
        return float(SecureValidator.validate_decimal(v, 0, 1000000))
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['open', 'closed', 'cancelled', 'completed']
        status = SecureValidator.sanitize_string(v, 20).lower()
        
        if status not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        
        return status
    
    @validator('notes')
    def validate_notes(cls, v):
        return SecureValidator.validate_notes(v)

class SecurePasswordChange(BaseModel):
    """Secure password change model"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        return SecureValidator.validate_password(v)

def validate_api_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize API request data"""
    validated_data = {}
    
    for key, value in request_data.items():
        # Sanitize key
        clean_key = SecureValidator.sanitize_string(str(key), 100)
        
        # Sanitize value based on type
        if isinstance(value, str):
            clean_value = SecureValidator.sanitize_string(value)
        elif isinstance(value, (int, float)):
            clean_value = value
        elif isinstance(value, dict):
            clean_value = validate_api_request(value)  # Recursive validation
        elif isinstance(value, list):
            clean_value = [SecureValidator.sanitize_string(str(item)) if isinstance(item, str) else item for item in value]
        else:
            clean_value = str(value)
        
        validated_data[clean_key] = clean_value
    
    return validated_data

# Export classes and functions
__all__ = [
    'SecureValidator',
    'SecureUserCreate',
    'SecureArbitrageRequest', 
    'SecurePasswordChange',
    'validate_api_request'
]
