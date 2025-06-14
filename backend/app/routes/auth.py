from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, RefreshTokenRequest
from app.services.user_service import UserService
from app.services.token_service import TokenService
from app.utils.auth import create_access_token
from app.utils.security import validate_user_input, log_security_event, handle_service_error
from app.utils.client_info import get_client_info
from app.utils.cookie_security import set_authentication_cookies, clear_authentication_cookies, extract_session_info
from app.dependencies import get_current_user, get_current_user_from_cookie
from app.models.user import User
from app.models.token import UserSession
from app.config import settings
import logging
import json
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def get_client_info(request: Request) -> dict:
    """Extract client information for security logging"""
    return {
        "ip_address": getattr(request.client, 'host', 'unknown'),
        "user_agent": request.headers.get('user-agent', 'unknown'),
        "device_type": "web",  # Could be enhanced with user agent parsing
        "location": None  # Could be enhanced with IP geolocation
    }


@router.post("/signup", response_model=UserResponse)
async def signup(
    user_create: UserCreate, 
    db: Session = Depends(get_db)
):
    """Create a new user account"""
    try:
        user_service = UserService(db)

        # Validate and sanitize user input
        user_create.email = validate_user_input(user_create.email, "Email", max_length=255)
        user_create.username = validate_user_input(user_create.username, "Username", max_length=50)
        user_create.password = validate_user_input(user_create.password, "Password", max_length=1000)
        
        if not user_create.email or not user_create.username or not user_create.password:
            log_security_event("empty_signup_fields", details={
                "email": user_create.email,
                "username": user_create.username
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, username, and password are required"
            )

        # Check if user already exists
        if user_service.get_user_by_email(user_create.email):
            log_security_event("duplicate_email_signup", details={"email": user_create.email})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if user_service.get_user_by_username(user_create.username):
            log_security_event("duplicate_username_signup", details={"username": user_create.username})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        user = user_service.create_user(user_create)
        logger.info(f"New user created: {user.email}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        raise handle_service_error(e, "Failed to create account")


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db),
    remember_me: bool = False
):
    """Authenticate user and return JWT tokens with enhanced security"""
    try:
        user_service = UserService(db)
        token_service = TokenService(db)
        client_info = get_client_info(request)

        # Validate and sanitize user input
        form_data.username = validate_user_input(form_data.username, "Email", max_length=255)
        form_data.password = validate_user_input(form_data.password, "Password", max_length=1000)
        
        if not form_data.username or not form_data.password:
            token_service.log_security_event(
                event_type="empty_login_fields",
                event_category="auth",
                severity="low",
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                details=json.dumps({"email": form_data.username})
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        # Authenticate user (using email as username)
        user = user_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            # Log failed login attempt
            token_service.log_security_event(
                event_type="failed_login",
                event_category="auth",
                severity="medium",
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                details=json.dumps({"email": form_data.username}),
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            token_service.log_security_event(
                event_type="inactive_user_login",
                event_category="auth",
                severity="medium",
                user_id=user.id,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                details=json.dumps({"email": user.email}),
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create token pair with session tracking
        token_data = token_service.create_token_pair(
            user=user,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            device_type=client_info["device_type"],
            location=client_info["location"],
            remember_me=remember_me
        )
        
        # Set secure authentication cookies
        set_authentication_cookies(
            response=response,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            session_id=token_data["session_id"],
            device_fingerprint=token_data["device_fingerprint"],
            remember_me=remember_me
        )
        
        logger.info(f"Successful login: {user.email} from {client_info['ip_address']}")
        
        return {
            "access_token": token_data["access_token"],
            "token_type": token_data["token_type"],
            "expires_in": token_data["expires_in"],
            "refresh_token": token_data["refresh_token"]  # Also return in body for compatibility
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise handle_service_error(e, "Authentication failed")


@router.post("/validate-token")
async def validate_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """Validate current token and return user info"""
    try:
        # Try to get user from cookies first
        try:
            current_user = await get_current_user_from_cookie(request, db)
        except:
            # Fallback to header-based authentication
            from app.dependencies import oauth2_scheme
            from app.utils.auth import verify_token
            from app.services.user_service import UserService
            
            token = await oauth2_scheme(request)
            payload = verify_token(token, db)
            if payload is None:
                raise HTTPException(status_code=401, detail="Invalid token")
                
            user_service = UserService(db)
            current_user = user_service.get_user_by_email(payload.get("sub"))
            if not current_user or not current_user.is_active:
                raise HTTPException(status_code=401, detail="User not found or inactive")
        
        client_info = get_client_info(request)
        
        # Log token validation
        token_service = TokenService(db)
        token_service.log_security_event(
            user_id=current_user.id,
            event_type="token_validation",
            event_category="auth",
            severity="low",
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        return {
            "valid": True,
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.username,
                "is_admin": current_user.is_admin,
                "is_active": current_user.is_active,
                "credits": current_user.credits
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):   
    try:
        """Refresh access token using refresh token"""
        token_service = TokenService(db)
        client_info = get_client_info(request)
        
        # Debug logging
        logger.info(f"Refresh token request - Body: {refresh_token_request.refresh_token}")
        logger.info(f"Refresh token request - Cookies: {dict(request.cookies)}")
        
        # Extract refresh token from request body or cookie
        refresh_token = refresh_token_request.refresh_token
        if not refresh_token:
            refresh_token = request.cookies.get("refresh_token")
            logger.info(f"Got refresh token from cookie: {refresh_token is not None}")
        
        if not refresh_token:
            logger.warning("No refresh token found in body or cookies")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required"
            )
        
        # Get session info from secure cookie
        session_info = extract_session_info(request)
        device_fingerprint = session_info.get("device_fingerprint") if session_info else None
        
        # Refresh the token
        token_data = token_service.refresh_access_token(
            refresh_token=refresh_token,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            device_fingerprint=device_fingerprint
        )
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Update secure cookies with new tokens
        set_authentication_cookies(
            response=response,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            session_id=session_info.get("session_id") if session_info else "",
            device_fingerprint=device_fingerprint or "",
            remember_me=session_info.get("remember_me", False) if session_info else False
        )
        
        return token_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise handle_service_error(e, "Token refresh failed")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logout user and invalidate tokens"""
    try:
        token_service = TokenService(db)
        client_info = get_client_info(request)
        
        # Get refresh token from cookie
        refresh_token = request.cookies.get("refresh_token")
        session_id = request.cookies.get("session_id")
        
        if refresh_token:
            # Revoke refresh token
            token_service.revoke_refresh_token(refresh_token, "logout")
        
        if session_id:
            # Terminate session
            token_service.terminate_session(session_id, "logout")
        
        # Log security event
        token_service.log_security_event(
            user_id=current_user.id,
            session_id=session_id,
            event_type="logout",
            event_category="auth",
            severity="low",
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"]
        )
        
        # Clear authentication cookies
        clear_authentication_cookies(response)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise handle_service_error(e, "Logout failed")
