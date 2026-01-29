"""
Custom Sentry middleware for enhanced error tracking
"""
import sentry_sdk
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import time
import logging

logger = logging.getLogger(__name__)

async def sentry_middleware(request: Request, call_next):
    """Custom middleware to enhance Sentry context"""
    
    # Start timing the request
    start_time = time.time()
    
    # Set Sentry context
    with sentry_sdk.configure_scope() as scope:
        # Add request information
        scope.set_tag("request_method", request.method)
        scope.set_tag("request_path", request.url.path)
        scope.set_context("request", {
            "url": str(request.url),
            "method": request.method,
            "headers": dict(request.headers),
            "query_params": dict(request.query_params)
        })
        
        # Add user information if available
        if hasattr(request.state, 'user') and request.state.user:
            scope.set_user({
                "id": request.state.user.id,
                "username": request.state.user.username,
                "email": request.state.user.email
            })
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Add response information
            scope.set_tag("response_status", response.status_code)
            scope.set_context("response", {
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2)
            })
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                sentry_sdk.capture_message(
                    f"Slow request: {request.method} {request.url.path} took {duration:.2f}s",
                    level="warning"
                )
            
            return response
            
        except Exception as exc:
            # Calculate request duration for failed requests
            duration = time.time() - start_time
            
            # Add error context
            scope.set_context("error_context", {
                "request_duration": duration,
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            })
            
            # Capture the exception
            sentry_sdk.capture_exception(exc)
            
            # Log the error
            logger.error(f"Request failed: {request.method} {request.url.path} - {exc}")
            
            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

def add_sentry_context_to_api():
    """Decorator to add Sentry context to API endpoints"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with sentry_sdk.configure_scope() as scope:
                scope.set_tag("api_endpoint", func.__name__)
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    scope.set_context("api_error", {
                        "function": func.__name__,
                        "args": str(args)[:200],  # Limit size
                        "kwargs": str(kwargs)[:200]  # Limit size
                    })
                    sentry_sdk.capture_exception(e)
                    raise
        return wrapper
    return decorator
