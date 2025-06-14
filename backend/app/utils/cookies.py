from fastapi import Response
from app.config import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def set_secure_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: Optional[int] = None,
    httponly: bool = True,
    secure: bool = None,
    samesite: str = None
) -> None:
    """Set a secure cookie with appropriate security settings for development"""
    
    # Use configuration defaults if not specified
    if secure is None:
        secure = settings.SESSION_COOKIE_SECURE  # False for development HTTP
    
    if samesite is None:
        samesite = settings.SESSION_COOKIE_SAMESITE  # "lax" for development
    
    if max_age is None and key == "refresh_token":
        max_age = settings.SESSION_COOKIE_MAX_AGE
    
    try:
        response.set_cookie(
            key=key,
            value=value,
            max_age=max_age,
            httponly=httponly,
            secure=secure,
            samesite=samesite,
            path="/"
        )
        logger.debug(f"Set secure cookie: {key} (secure={secure}, samesite={samesite}, httponly={httponly})")
        
    except Exception as e:
        logger.error(f"Failed to set cookie {key}: {str(e)}")


def clear_auth_cookies(response: Response) -> None:
    """Clear all authentication-related cookies"""
    cookies_to_clear = [
        "refresh_token",
        "session_id", 
        "device_fingerprint",
        "token"  # Just in case it's set as cookie
    ]
    
    for cookie_name in cookies_to_clear:
        try:
            response.delete_cookie(
                key=cookie_name,
                path="/",
                secure=settings.SESSION_COOKIE_SECURE,
                samesite=settings.SESSION_COOKIE_SAMESITE
            )
            logger.debug(f"Cleared cookie: {cookie_name}")
        except Exception as e:
            logger.warning(f"Failed to clear cookie {cookie_name}: {str(e)}")


def extract_cookie_value(request, cookie_name: str) -> Optional[str]:
    """Safely extract cookie value from request"""
    try:
        return request.cookies.get(cookie_name)
    except Exception as e:
        logger.warning(f"Failed to extract cookie {cookie_name}: {str(e)}")
        return None
