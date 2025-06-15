from fastapi import Request, Response
from typing import Optional, Dict, Any
import hmac
import hashlib
import json
import base64
from datetime import datetime, timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SecureCookieManager:
    """Advanced cookie security management for authentication"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET.encode()
    
    def sign_cookie_data(self, data: Dict[str, Any]) -> str:
        """Sign cookie data with HMAC for integrity"""
        try:
            json_data = json.dumps(data, separators=(',', ':'))
            signature = hmac.new(
                self.secret_key,
                json_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Combine data and signature
            signed_data = {
                'data': data,
                'signature': signature,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return base64.b64encode(
                json.dumps(signed_data).encode()
            ).decode()
            
        except Exception as e:
            logger.error(f"Failed to sign cookie data: {str(e)}")
            return ""
    
    def verify_cookie_data(self, signed_cookie: str) -> Optional[Dict[str, Any]]:
        """Verify and extract cookie data"""
        try:
            decoded_data = json.loads(
                base64.b64decode(signed_cookie.encode()).decode()
            )
            
            data = decoded_data.get('data')
            signature = decoded_data.get('signature')
            timestamp = decoded_data.get('timestamp')
            
            if not all([data, signature, timestamp]):
                return None
            
            # Verify signature
            json_data = json.dumps(data, separators=(',', ':'))
            expected_signature = hmac.new(
                self.secret_key,
                json_data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Cookie signature verification failed")
                return None
            
            # Check timestamp (optional expiry check)
            cookie_time = datetime.fromisoformat(timestamp)
            if datetime.utcnow() - cookie_time > timedelta(hours=24):
                logger.warning("Cookie data expired")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to verify cookie data: {str(e)}")
            return None


def set_authentication_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    session_id: str,
    device_fingerprint: str,
    remember_me: bool = False
) -> None:
    """Set secure authentication cookies for development"""
    
    cookie_manager = SecureCookieManager()
    
    # Access token in httpOnly cookie for API calls
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,  # False for development HTTP
        samesite=settings.SESSION_COOKIE_SAMESITE,  # Lax for development
        path="/",
        domain=None
    )
      # Refresh token in httpOnly cookie
    refresh_max_age = (30 * 24 * 3600) if remember_me else (7 * 24 * 3600)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,  # False for development HTTP
        samesite=settings.SESSION_COOKIE_SAMESITE,  # Lax for development
        path="/",  # Allow access from all paths
        domain=None  # Use default domain
    )
    
    # Session metadata in signed cookie (readable by client)
    session_data = {
        "session_id": session_id,
        "device_fingerprint": device_fingerprint,
        "remember_me": remember_me
    }
    
    signed_session = cookie_manager.sign_cookie_data(session_data)
    response.set_cookie(
        key="session_info",
        value=signed_session,
        max_age=refresh_max_age,
        httponly=False,  # Readable by client for UI purposes
        secure=settings.SESSION_COOKIE_SECURE,  # False for development HTTP
        samesite=settings.SESSION_COOKIE_SAMESITE,  # Lax for development
        path="/",
        domain=None  # Use default domain
    )
    
    # Also add CORS headers explicitly
    if settings.ENVIRONMENT == "production":
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Origin"] = settings.BACKEND_CORS_ORIGINS[0]

    logger.info(f"Set authentication cookies for session: {session_id}")


def clear_authentication_cookies(response: Response) -> None:
    """Clear all authentication cookies securely"""
    
    auth_cookies = [
        "access_token",
        "refresh_token", 
        "session_info",
        "token",  # Legacy cookie
        "device_fingerprint"  # Legacy cookie
    ]
    
    for cookie_name in auth_cookies:
        response.delete_cookie(
            key=cookie_name,
            path="/",
            secure=settings.SESSION_COOKIE_SECURE,  # False for development HTTP
            samesite=settings.SESSION_COOKIE_SAMESITE  # Lax for development
        )
        
        # Also clear with different paths
        if cookie_name == "refresh_token":
            response.delete_cookie(
                key=cookie_name,
                path="/auth",
                secure=settings.SESSION_COOKIE_SECURE,  # False for development HTTP
                samesite=settings.SESSION_COOKIE_SAMESITE  # Lax for development
            )
    
    logger.info("Cleared all authentication cookies")


def extract_session_info(request: Request) -> Optional[Dict[str, Any]]:
    """Extract and verify session information from cookies"""
    
    try:
        cookie_manager = SecureCookieManager()
        session_cookie = request.cookies.get("session_info")
        
        if not session_cookie:
            return None
        
        session_data = cookie_manager.verify_cookie_data(session_cookie)
        return session_data
        
    except Exception as e:
        logger.error(f"Failed to extract session info: {str(e)}")
        return None


def is_cookie_secure_context(request: Request) -> bool:
    """Check if the request is in a secure context for cookies"""
    
    # In development, HTTP is acceptable
    if settings.ENVIRONMENT == "development":
        return True
    
    # In production, require HTTPS
    return request.url.scheme == "https"


def validate_cookie_security_headers(request: Request) -> Dict[str, bool]:
    """Validate security-related headers for cookie handling"""
    
    headers = request.headers
    security_check = {
        "has_user_agent": "user-agent" in headers,
        "has_referer": "referer" in headers,
        "secure_context": is_cookie_secure_context(request),
        "content_type_safe": headers.get("content-type", "").startswith(
            ("application/json", "application/x-www-form-urlencoded")
        )
    }
    
    return security_check