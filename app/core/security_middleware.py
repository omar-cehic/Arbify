"""
Advanced Security Middleware for Arbify
=====================================

Comprehensive security middleware including:
- HTTPS enforcement
- Security headers
- Rate limiting
- Request monitoring
- Threat detection
"""

import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Set
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from security_config import (
    security_config, SSL_CONFIG, SECURITY_HEADERS, MONITORING_CONFIG,
    get_client_ip, is_suspicious_request, SECURITY_EVENTS
)

# Security logger
security_logger = logging.getLogger("security.middleware")

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
        self.is_production = environment == "production"
        
        # Rate limiting storage (in production, use Redis)
        self.rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())
        self.blocked_ips: Set[str] = set()
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        
        # Security event tracking
        self.security_events: deque = deque(maxlen=1000)
        
    async def dispatch(self, request: Request, call_next):
        """Main middleware handler"""
        start_time = time.time()
        client_ip = get_client_ip(request)
        
        try:
            # CRITICAL: Always allow health checks to pass through without any security checks
            if request.url.path in ["/status", "/health", "/healthz"]:
                response = await call_next(request)
                return response
            
            # CRITICAL: Relax security for API endpoints to avoid blocking legitimate requests
            is_api_request = request.url.path.startswith("/api/")
        
            # 1. HTTPS Enforcement
            if self.is_production and not self._is_https(request):
                return self._redirect_to_https(request)
            
            # 2. IP Blocking Check (only for non-API requests or already blocked IPs)
            if client_ip in self.blocked_ips and not is_api_request:
                self._log_security_event("BLOCKED_IP_ACCESS", client_ip, request)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # 3. Suspicious Request Detection (relaxed for API endpoints)
            if is_suspicious_request(request) and not is_api_request:
                self._handle_suspicious_request(client_ip, request)
            
            # 4. Rate Limiting
            if not self._check_rate_limit(client_ip, request):
                self._log_security_event("RATE_LIMIT_EXCEEDED", client_ip, request)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            # 5. Process Request
            response = await call_next(request)
            
            # 6. Add Security Headers
            self._add_security_headers(response)
            
            # 7. Log Request (if monitoring enabled)
            if MONITORING_CONFIG["log_api_calls"]:
                self._log_api_call(request, response, time.time() - start_time)
            
            return response
            
        except HTTPException as e:
            # Handle known exceptions with proper security logging
            self._log_security_event("HTTP_EXCEPTION", client_ip, request, {
                "status_code": e.status_code,
                "detail": str(e.detail)
            })
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            # Handle unexpected exceptions
            self._log_security_event("INTERNAL_ERROR", client_ip, request, {
                "error": str(e)
            })
            security_logger.error(f"Unexpected error in security middleware: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
    
    def _is_https(self, request: Request) -> bool:
        """Check if request is using HTTPS"""
        # Check direct HTTPS
        if request.url.scheme == "https":
            return True
        
        # Check proxy headers (for load balancers)
        proto = request.headers.get("x-forwarded-proto")
        if proto and proto.lower() == "https":
            return True
        
        return False
    
    def _redirect_to_https(self, request: Request) -> Response:
        """Redirect HTTP to HTTPS"""
        https_url = str(request.url).replace("http://", "https://", 1)
        return JSONResponse(
            status_code=status.HTTP_301_MOVED_PERMANENTLY,
            content={"detail": "Redirecting to HTTPS"},
            headers={"Location": https_url}
        )
    
    def _check_rate_limit(self, client_ip: str, request: Request) -> bool:
        """Check if request exceeds rate limits"""
        endpoint = self._get_endpoint_category(request)
        
        # Get rate limit for endpoint (default to general)
        from security_config import RATE_LIMITS
        rate_limit = RATE_LIMITS.get(endpoint, RATE_LIMITS["api_general"])
        
        # Parse rate limit (e.g., "10/minute")
        try:
            limit, period = rate_limit.split("/")
            limit = int(limit)
            
            if period == "minute":
                window = 60
            elif period == "hour":
                window = 3600
            elif period == "day":
                window = 86400
            else:
                window = 60  # default to minute
                
        except (ValueError, IndexError):
            # Invalid rate limit format, allow request
            return True
        
        # Check rate limit
        now = time.time()
        key = f"{client_ip}:{endpoint}"
        
        # Clean old entries
        while (self.rate_limit_storage[key] and 
               self.rate_limit_storage[key][0] < now - window):
            self.rate_limit_storage[key].popleft()
        
        # Check if limit exceeded
        if len(self.rate_limit_storage[key]) >= limit:
            # Track excessive requests
            self.suspicious_ips[client_ip] += 1
            
            # Block IP if too many violations
            if self.suspicious_ips[client_ip] > 10:
                self.blocked_ips.add(client_ip)
                security_logger.warning(f"Blocked IP due to excessive rate limit violations: {client_ip}")
            
            return False
        
        # Add current request
        self.rate_limit_storage[key].append(now)
        return True
    
    def _get_endpoint_category(self, request: Request) -> str:
        """Categorize endpoint for rate limiting"""
        path = request.url.path.lower()
        
        if "/api/auth/register" in path:
            return "auth_register"
        elif "/api/auth/token" in path or "/api/auth/login" in path:
            return "auth_login"
        elif "/api/auth/password" in path:
            return "auth_password_reset"
        elif "/api/odds" in path:
            return "api_odds"
        elif "/api/arbitrage" in path:
            return "api_arbitrage"
        elif "/api/my-arbitrage" in path and request.method == "POST":
            return "api_save_arbitrage"
        elif "/api/subscription" in path:
            return "api_subscription"
        elif "/api/auth/user/profile" in path:
            return "api_user_profile"
        elif "/admin" in path:
            return "admin"
        else:
            return "api_general"
    
    def _handle_suspicious_request(self, client_ip: str, request: Request):
        """Handle potentially suspicious requests"""
        self.suspicious_ips[client_ip] += 1
        
        self._log_security_event("SUSPICIOUS_REQUEST", client_ip, request, {
            "user_agent": request.headers.get("user-agent", ""),
            "suspicious_count": self.suspicious_ips[client_ip]
        })
        
        # Block IP if too many suspicious requests
        if self.suspicious_ips[client_ip] > 5:
            self.blocked_ips.add(client_ip)
            security_logger.warning(f"Blocked suspicious IP: {client_ip}")
    
    def _add_security_headers(self, response: Response):
        """Add comprehensive security headers"""
        headers = SECURITY_HEADERS.get(self.environment, SECURITY_HEADERS["development"])
        
        for header, value in headers.items():
            response.headers[header] = value
        
        # Add additional security headers
        response.headers["Server"] = "Arbify/1.0"  # Hide server details
        response.headers["X-Powered-By"] = ""  # Remove framework info
        
        # Add timestamp for debugging (non-production only)
        if not self.is_production:
            response.headers["X-Response-Time"] = str(datetime.utcnow().isoformat())
    
    def _log_security_event(self, event_type: str, client_ip: str, request: Request, extra_data: Dict = None):
        """Log security events"""
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent", ""),
            "path": request.url.path,
            "method": request.method,
            "query_params": str(request.query_params),
        }
        
        if extra_data:
            event_data.update(extra_data)
        
        # Store in memory (in production, send to SIEM)
        self.security_events.append(event_data)
        
        # Log to file/stdout
        security_logger.warning(f"SECURITY_EVENT: {json.dumps(event_data)}")
    
    def _log_api_call(self, request: Request, response: Response, duration: float):
        """Log API calls for monitoring"""
        if self.environment == "development":
            # More verbose logging in development
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "client_ip": get_client_ip(request),
                "user_agent": request.headers.get("user-agent", "")[:100],  # Truncate
            }
            security_logger.info(f"API_CALL: {json.dumps(log_data)}")

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Simple HTTPS redirect middleware for production"""
    
    async def dispatch(self, request: Request, call_next):
        # CRITICAL: Allow Railway health checks to pass through
        if request.url.path in ["/status", "/health", "/healthz"]:
            # Always allow health check endpoints without HTTPS redirect
            response = await call_next(request)
            return response
        
        # Check for Railway internal requests (they often come from internal IPs)
        user_agent = request.headers.get("user-agent", "").lower()
        if "railway" in user_agent or "healthcheck" in user_agent:
            response = await call_next(request)
            return response
        
        if (request.url.scheme != "https" and 
            request.headers.get("x-forwarded-proto") != "https" and
            request.url.hostname not in ["localhost", "127.0.0.1"]):
            
            # Redirect to HTTPS
            https_url = str(request.url).replace("http://", "https://", 1)
            return JSONResponse(
                status_code=status.HTTP_301_MOVED_PERMANENTLY,
                content={"message": "Redirecting to HTTPS"},
                headers={"Location": https_url}
            )
        
        response = await call_next(request)
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Lightweight security headers middleware"""
    
    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        headers = SECURITY_HEADERS.get(self.environment, SECURITY_HEADERS["development"])
        for header, value in headers.items():
            response.headers[header] = value
        
        return response

# Export middleware classes
__all__ = [
    'SecurityMiddleware', 
    'HTTPSRedirectMiddleware', 
    'SecurityHeadersMiddleware'
]
