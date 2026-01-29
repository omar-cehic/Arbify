import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from collections import defaultdict
from app.core.config import RATE_LIMIT_PER_USER

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit_per_minute = RATE_LIMIT_PER_USER
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exclude health check or static assets if needed
        if request.url.path == "/health" or request.url.path == "/":
            return await call_next(request)

        client_ip = request.client.host
        current_time = time.time()
        
        # Clean up old history for this IP (keep only last minute)
        # Filter timestamps older than 60 seconds
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip] 
            if current_time - t < 60
        ]
        
        # Check limit
        if len(self.request_history[client_ip]) >= self.rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={"error": "Too Many Requests", "detail": f"Rate limit exceeded ({self.rate_limit_per_minute}/min)"}
            )
            
        # Add current request
        self.request_history[client_ip].append(current_time)
        
        # Periodic cleanup of empty keys could be added here to save memory, 
        # but for this scale it's negligible.
        
        response = await call_next(request)
        return response
