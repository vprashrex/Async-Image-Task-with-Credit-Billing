from fastapi import Request, Response
from typing import Dict, Any, Optional
from app.config import settings
import user_agents
import logging

logger = logging.getLogger(__name__)


def get_client_info(request: Request) -> Dict[str, Any]:
    """Extract client information from request for security tracking"""
    try:
        # Get client IP (considering proxy headers)
        client_ip = get_client_ip(request)
        
        # Get and parse user agent
        user_agent_string = request.headers.get('user-agent', 'unknown')
        user_agent = user_agents.parse(user_agent_string)
        
        # Determine device type
        device_type = "web"  # default
        if user_agent.is_mobile:
            device_type = "mobile"
        elif user_agent.is_tablet:
            device_type = "tablet"
        elif user_agent.is_pc:
            device_type = "desktop"
        
        # Extract location info (placeholder - would integrate with IP geolocation service)
        location = get_location_from_ip(client_ip) if settings.ENABLE_LOCATION_TRACKING else None
        
        return {
            "ip_address": client_ip,
            "user_agent": user_agent_string,
            "device_type": device_type,
            "device_info": {
                "browser": f"{user_agent.browser.family} {user_agent.browser.version_string}",
                "os": f"{user_agent.os.family} {user_agent.os.version_string}",
                "device": user_agent.device.family if user_agent.device.family != 'Other' else None
            },
            "location": location
        }
        
    except Exception as e:
        logger.warning(f"Failed to extract client info: {str(e)}")
        return {
            "ip_address": "unknown",
            "user_agent": "unknown",
            "device_type": "web",
            "device_info": {},
            "location": None
        }


def get_client_ip(request: Request) -> str:
    """Get client IP address considering proxy headers"""
    # Check for common proxy headers
    forwarded_for = request.headers.get('x-forwarded-for')
    if forwarded_for:
        # Take the first IP if multiple are present
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('x-real-ip')
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client IP
    if hasattr(request.client, 'host'):
        return request.client.host
    
    return "unknown"


def get_location_from_ip(ip_address: str) -> Optional[str]:
    """Get location from IP address (placeholder implementation)"""
    # In a real implementation, you would use a service like:
    # - MaxMind GeoIP2
    # - ipinfo.io
    # - ipapi.co
    # For now, return None to maintain privacy
    return None


def set_secure_cookie(
    response: Response, 
    name: str, 
    value: str, 
    max_age: int = None,
    http_only: bool = True,
    secure: bool = None,
    same_site: str = None
) -> None:
    """Set a secure cookie with appropriate security settings for development"""
    
    # Use config defaults if not specified
    if secure is None:
        secure = settings.SESSION_COOKIE_SECURE
    
    if same_site is None:
        same_site = settings.SESSION_COOKIE_SAMESITE
    
    if max_age is None:
        max_age = settings.SESSION_COOKIE_MAX_AGE
    
    try:
        response.set_cookie(
            key=name,
            value=value,
            max_age=max_age,
            httponly=http_only,
            secure=secure,  # False for development HTTP
            samesite=same_site,
            path="/"
        )
    except Exception as e:
        logger.error(f"Failed to set cookie {name}: {str(e)}")


def clear_auth_cookies(response: Response) -> None:
    """Clear all authentication-related cookies"""
    cookies_to_clear = [
        "refresh_token",
        "session_id", 
        "device_fingerprint",
        "token"  # For compatibility
    ]
    
    for cookie_name in cookies_to_clear:
        response.delete_cookie(
            key=cookie_name,
            path="/",
            secure=settings.SESSION_COOKIE_SECURE,
            samesite=settings.SESSION_COOKIE_SAMESITE
        )


def validate_device_fingerprint(request: Request, expected_fingerprint: str) -> bool:
    """Validate device fingerprint for additional security"""
    try:
        client_info = get_client_info(request)
        from app.utils.auth import create_device_fingerprint
        
        current_fingerprint = create_device_fingerprint(
            client_info["user_agent"], 
            client_info["ip_address"]
        )
        
        return current_fingerprint == expected_fingerprint
        
    except Exception as e:
        logger.warning(f"Device fingerprint validation failed: {str(e)}")
        return False
