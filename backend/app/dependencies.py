from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.auth import verify_token
from app.services.user_service import UserService
from app.utils.security import log_security_event
from app.utils.cookie_security import extract_session_info
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user with enhanced security and blacklist checking"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Try to get token from Authorization header first
        auth_header = request.headers.get("authorization")
        auth_token = None
        
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header.split(" ")[1]
          # If no Authorization header, try to get from httpOnly cookie
        if not auth_token:
            auth_token = request.cookies.get("access_token")
            logger.info(f"No auth header, trying cookie: {auth_token[:20] + '...' if auth_token else 'None'}")
        else:
            logger.info(f"Using auth header token: {auth_token[:20] + '...' if auth_token else 'None'}")
        
        if not auth_token:
            # Get client info for logging
            client_ip = getattr(request.client, 'host', 'unknown')
            user_agent = request.headers.get('user-agent', 'unknown')
            
            logger.warning(f"No token found for {client_ip} - Available cookies: {list(request.cookies.keys())}")
            
            log_security_event(
                "no_token_provided", 
                details={
                    "reason": "no_authorization_header_or_cookie",
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
            raise credentials_exception

        # Verify token with blacklist checking
        payload = verify_token(auth_token, db)
        if payload is None:
            # Get client info for logging
            client_ip = getattr(request.client, 'host', 'unknown')
            user_agent = request.headers.get('user-agent', 'unknown')
            
            log_security_event(
                "invalid_token", 
                details={
                    "reason": "token_verification_failed",
                    "ip_address": client_ip,
                    "user_agent": user_agent
                }
            )
            raise credentials_exception

        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if email is None or user_id is None:
            log_security_event("invalid_token", details={"reason": "missing_claims"})
            raise credentials_exception

        # Get user from database
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        if user is None:
            log_security_event("user_not_found", details={"email": email})
            raise credentials_exception

        if not user.is_active:
            log_security_event("inactive_user_access", user.id, {"email": user.email})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )

        # Additional security: Check if user ID matches
        if user.id != user_id:
            log_security_event(
                "user_id_mismatch", 
                user.id, 
                {"token_user_id": user_id, "actual_user_id": user.id}
            )
            raise credentials_exception

        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        log_security_event("authentication_error", details={"error": str(e)})
        raise credentials_exception


async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from cookie (for SSE)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    
    # Log available cookies for debugging
    available_cookies = list(request.cookies.keys())
    logger.info(f"SSE Auth - Available cookies: {available_cookies}")
    
    # Extract token from secure cookie
    token = request.cookies.get("access_token")
    logger.info(f"SSE Auth - Access token found: {bool(token)}")
    if token:
        logger.info(f"SSE Auth - Token preview: {token[:20]}...")
    
    if not token:
        logger.warning("SSE Auth - No access token found in cookies")
        raise credentials_exception
    
    # Verify token
    payload = verify_token(token, db)
    logger.info(f"SSE Auth - Token verification: {bool(payload)}")
    
    if payload is None:
        logger.warning("SSE Auth - Token verification failed")
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        logger.warning("SSE Auth - No email in token payload")
        raise credentials_exception
    
    # Get user from database
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if user is None:
        logger.warning(f"SSE Auth - User not found: {email}")
        raise credentials_exception
    
    if not user.is_active:
        logger.warning(f"SSE Auth - User inactive: {email}")
        raise HTTPException(status_code=400, detail="Inactive user")
    
    logger.info(f"SSE Auth - Authentication successful: {user.email}")
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current authenticated admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
