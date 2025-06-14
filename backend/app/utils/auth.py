from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
import hashlib
import secrets
from sqlalchemy.orm import Session
from app.config import settings
from app.models.token import TokenBlacklist, RefreshToken
from app.models.user import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    jti: Optional[str] = None
) -> str:
    """Create a JWT access token with JTI for revocation support"""
    to_encode = data.copy()
    
    # Set expiration time (shorter for security)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add JTI (JWT ID) for token revocation
    if not jti:
        jti = str(uuid.uuid4())
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": jti,
        "token_type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """Create a cryptographically secure refresh token"""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token for secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, db: Session) -> Optional[dict]:
    """Verify and decode a JWT token, checking against blacklist"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        
        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti, db):
            return None
            
        return payload
    except JWTError:
        return None


def is_token_blacklisted(jti: str, db: Session) -> bool:
    """Check if a token JTI is in the blacklist"""
    blacklisted = db.query(TokenBlacklist).filter(
        TokenBlacklist.jti == jti,
        TokenBlacklist.expires_at > datetime.utcnow()
    ).first()
    return blacklisted is not None


def blacklist_token(
    jti: str, 
    user_id: int, 
    token_type: str, 
    reason: str, 
    expires_at: datetime,
    db: Session
) -> None:
    """Add a token to the blacklist"""
    blacklist_entry = TokenBlacklist(
        jti=jti,
        user_id=user_id,
        token_type=token_type,
        reason=reason,
        expires_at=expires_at
    )
    db.add(blacklist_entry)
    db.commit()


def cleanup_expired_blacklist_tokens(db: Session) -> int:
    """Remove expired tokens from blacklist"""
    count = db.query(TokenBlacklist).filter(
        TokenBlacklist.expires_at <= datetime.utcnow()
    ).delete()
    db.commit()
    return count


def revoke_user_tokens(user_id: int, reason: str, db: Session) -> int:
    """Revoke all active tokens for a user"""
    # Get all active refresh tokens for the user
    refresh_tokens = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_active == True,
        RefreshToken.expires_at > datetime.utcnow()
    ).all()
    
    # Mark refresh tokens as inactive
    for rt in refresh_tokens:
        rt.is_active = False
    
    # Note: For access tokens, we would need to maintain a list of active JTIs
    # or implement a different revocation strategy since we can't enumerate all active access tokens
    
    db.commit()
    return len(refresh_tokens)


def create_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """Create a device fingerprint for session tracking"""
    fingerprint_data = f"{user_agent}:{ip_address}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()


def generate_session_id() -> str:
    """Generate a unique session ID"""
    return str(uuid.uuid4())


def generate_token_family_id() -> str:
    """Generate a token family ID for refresh token rotation"""
    return str(uuid.uuid4())
