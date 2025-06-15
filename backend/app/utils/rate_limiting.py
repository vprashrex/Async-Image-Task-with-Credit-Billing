from fastapi import Request, Response, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
import time
import logging

logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "auth": settings.AUTH_RATE_LIMIT,  # "5/minute"
    "task_creation": settings.TASK_CREATION_RATE_LIMIT,  # "10/minute"
    "general": f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"  # "60/minute"
}


def get_rate_limit(endpoint_type: str = "general") -> str:
    """Get rate limit string for endpoint type"""
    return RATE_LIMITS.get(endpoint_type, RATE_LIMITS["general"])


async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Remove server information
    if "Server" in response.headers:
        del response.headers["Server"]
    
    return response


async def request_logging_middleware(request: Request, call_next):
    """Log all requests for security monitoring"""
    start_time = time.time()
    
    # Log request details
    client_ip = get_remote_address(request)
    user_agent = request.headers.get("User-Agent", "Unknown")
    
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    # Detect potential security threats
    suspicious_patterns = [
        "../", "..\\", "<script", "javascript:", "vbscript:",
        "union select", "drop table", "insert into", "delete from",
        "exec(", "eval(", "system(", "cmd.exe"
    ]
    
    query_string = str(request.url.query).lower()
    path = str(request.url.path).lower()
    
    for pattern in suspicious_patterns:
        if pattern in query_string or pattern in path:
            logger.warning(f"Suspicious request detected from {client_ip}: {request.method} {request.url}")
            break
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"Response: {response.status_code} in {process_time:.2f}s")
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url.path} in {process_time:.2f}s - {str(e)}")
        raise


class RateLimitHandler:
    """Custom rate limit handler with enhanced logging"""
    
    @staticmethod
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded errors"""
        client_ip = get_remote_address(request)
        logger.warning(f"Rate limit exceeded for {client_ip}: {request.method} {request.url.path}")
        
        response = Response(
            content=f"Rate limit exceeded: {exc.detail}",
            status_code=429,
            headers={"Retry-After": str(exc.retry_after)}
        )
        return response


def validate_authorization_header(authorization: str) -> tuple[str, str]:
    """Validate and parse authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    scheme, token = get_authorization_scheme_param(authorization)
    
    if not scheme or scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    return scheme, token
