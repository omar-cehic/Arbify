"""
Security-focused logging utilities for the application
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request

# Configure security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Create handler for security logs
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
security_logger.addHandler(handler)

class SecurityLogger:
    """Centralized security event logging"""
    
    @staticmethod
    def log_login_attempt(username: str, success: bool, ip_address: str, user_agent: str = None):
        """Log login attempts"""
        event_data = {
            "event_type": "login_attempt",
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            security_logger.info(f"LOGIN_SUCCESS: {json.dumps(event_data)}")
        else:
            security_logger.warning(f"LOGIN_FAILED: {json.dumps(event_data)}")
    
    @staticmethod
    def log_registration(username: str, email: str, ip_address: str):
        """Log user registrations"""
        event_data = {
            "event_type": "user_registration",
            "username": username,
            "email": email,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        security_logger.info(f"USER_REGISTERED: {json.dumps(event_data)}")
    
    @staticmethod
    def log_password_change(username: str, ip_address: str, success: bool):
        """Log password changes"""
        event_data = {
            "event_type": "password_change",
            "username": username,
            "ip_address": ip_address,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if success:
            security_logger.info(f"PASSWORD_CHANGED: {json.dumps(event_data)}")
        else:
            security_logger.warning(f"PASSWORD_CHANGE_FAILED: {json.dumps(event_data)}")
    
    @staticmethod
    def log_suspicious_activity(event_type: str, details: Dict[str, Any], ip_address: str):
        """Log suspicious activities"""
        event_data = {
            "event_type": f"suspicious_{event_type}",
            "details": details,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        security_logger.warning(f"SUSPICIOUS_ACTIVITY: {json.dumps(event_data)}")
    
    @staticmethod
    def log_rate_limit_exceeded(endpoint: str, ip_address: str, user_agent: str = None):
        """Log rate limit violations"""
        event_data = {
            "event_type": "rate_limit_exceeded",
            "endpoint": endpoint,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        security_logger.warning(f"RATE_LIMIT_EXCEEDED: {json.dumps(event_data)}")
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Safely extract client IP from request"""
        # Check for forwarded IPs (behind proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client
        return getattr(request.client, 'host', 'unknown')