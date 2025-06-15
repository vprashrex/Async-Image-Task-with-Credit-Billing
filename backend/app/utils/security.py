import logging
from typing import Optional
from fastapi import HTTPException
import traceback

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


def handle_service_error(error: Exception, user_message: str = "An error occurred", log_details: bool = True) -> HTTPException:
    """
    Securely handle service errors without exposing internal details
    
    Args:
        error: The original exception
        user_message: Safe message to show to users
        log_details: Whether to log full error details
        
    Returns:
        HTTPException with safe user message
    """
    if log_details:
        logger.error(f"Service error: {str(error)}")
        logger.debug(f"Full traceback: {traceback.format_exc()}")
    
    # Don't expose internal error details to users
    return HTTPException(status_code=500, detail=user_message)


def validate_user_input(value: str, field_name: str, max_length: int = 1000) -> str:
    """
    Validate and sanitize user input
    
    Args:
        value: Input value to validate
        field_name: Name of the field for error messages
        max_length: Maximum allowed length
        
    Returns:
        Sanitized value
        
    Raises:
        HTTPException: If validation fails
    """
    if not value:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    
    if len(value) > max_length:
        raise HTTPException(status_code=400, detail=f"{field_name} is too long")
    
    # Basic sanitization - remove null bytes and control characters
    sanitized = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
    
    return sanitized.strip()


def log_security_event(event_type: str, user_id: Optional[int] = None, details: Optional[dict] = None):
    """
    Log security-related events for monitoring
    
    Args:
        event_type: Type of security event
        user_id: ID of the user involved (if applicable)
        details: Additional details to log
    """
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "details": details or {}
    }
    
    logger.warning(f"Security event: {log_data}")
