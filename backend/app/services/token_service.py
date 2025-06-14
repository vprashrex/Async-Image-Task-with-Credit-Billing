from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.token import RefreshToken, UserSession, SecurityLog, TokenBlacklist
from app.models.user import User
from app.utils.auth import (
    create_refresh_token, hash_token, create_device_fingerprint, 
    generate_session_id, generate_token_family_id, create_access_token
)
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class TokenService:
    def __init__(self, db: Session):
        self.db = db

    def create_token_pair(
        self, 
        user: User, 
        ip_address: str, 
        user_agent: str,
        device_type: str = "web",
        location: str = None,
        remember_me: bool = False
    ) -> Dict[str, Any]:
        """Create access and refresh token pair with session tracking"""
        
        # Generate tokens
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin}
        )
        refresh_token = create_refresh_token()
        
        # Create device fingerprint
        device_fingerprint = create_device_fingerprint(user_agent, ip_address)
          # Check concurrent session limits
        active_sessions = self.get_active_user_sessions(user.id)
        max_sessions = user.max_concurrent_sessions or 5  # Default to 5 if None
        if len(active_sessions) >= max_sessions:
            # Terminate oldest session
            oldest_session = min(active_sessions, key=lambda s: s.created_at)
            self.terminate_session(oldest_session.session_id, "session_limit_exceeded")
        
        # Create refresh token record
        token_family_id = generate_token_family_id()
        expires_at = datetime.utcnow() + timedelta(
            days=30 if remember_me else 7
        )
        
        refresh_token_record = RefreshToken(
            token_hash=hash_token(refresh_token),
            user_id=user.id,
            device_fingerprint=device_fingerprint,
            family_id=token_family_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            location=location,
            expires_at=expires_at
        )
        self.db.add(refresh_token_record)
        self.db.flush()  # Get the ID
        
        # Create session record
        session_id = generate_session_id()
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            refresh_token_id=refresh_token_record.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            device_fingerprint=device_fingerprint,
            location=location,
            is_remember_me=remember_me,
            expires_at=expires_at
        )
        self.db.add(session)
        
        # Update user last login
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.failed_login_attempts = 0
        
        # Log security event
        self.log_security_event(
            user_id=user.id,
            session_id=session_id,
            event_type="login_success",
            event_category="auth",
            severity="low",
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            location=location,
            details=json.dumps({
                "remember_me": remember_me,
                "device_type": device_type
            })
        )
        
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "session_id": session_id,
            "device_fingerprint": device_fingerprint
        }

    def refresh_access_token(
        self, 
        refresh_token: str, 
        ip_address: str, 
        user_agent: str,
        device_fingerprint: str = None
    ) -> Optional[Dict[str, Any]]:
        """Refresh access token with token rotation"""
        
        token_hash = hash_token(refresh_token)
        
        # Find and validate refresh token
        refresh_token_record = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_active == True,
                RefreshToken.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not refresh_token_record:
            # Log suspicious activity
            self.log_security_event(
                event_type="invalid_refresh_token",
                event_category="suspicious",
                severity="medium",
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps({"reason": "token_not_found_or_expired"})
            )
            return None
        
        user = self.db.query(User).filter(User.id == refresh_token_record.user_id).first()
        if not user or not user.is_active:
            return None
        
        # Check device fingerprint for additional security
        current_fingerprint = create_device_fingerprint(user_agent, ip_address)
        if device_fingerprint and device_fingerprint != current_fingerprint:
            # Log potential token theft
            self.log_security_event(
                user_id=user.id,
                event_type="device_fingerprint_mismatch",
                event_category="suspicious",
                severity="high",
                ip_address=ip_address,
                user_agent=user_agent,
                details=json.dumps({
                    "expected_fingerprint": device_fingerprint,
                    "actual_fingerprint": current_fingerprint
                })
            )
            # Revoke token family
            self.revoke_token_family(refresh_token_record.family_id)
            return None
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "is_admin": user.is_admin}
        )
        
        # Rotate refresh token
        new_refresh_token = create_refresh_token()
        
        # Deactivate old refresh token
        refresh_token_record.is_active = False
        
        # Create new refresh token record
        new_refresh_token_record = RefreshToken(
            token_hash=hash_token(new_refresh_token),
            user_id=user.id,
            device_fingerprint=refresh_token_record.device_fingerprint,
            family_id=refresh_token_record.family_id,  # Keep same family
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=refresh_token_record.device_type,
            location=refresh_token_record.location,
            expires_at=refresh_token_record.expires_at
        )
        self.db.add(new_refresh_token_record)
          # Update session
        session = self.db.query(UserSession).filter(
            UserSession.refresh_token_id == refresh_token_record.id
        ).first()
        
        session_id = None
        if session:
            session.refresh_token_id = new_refresh_token_record.id
            session.last_activity_at = datetime.utcnow()
            session.ip_address = ip_address  # Update if changed
            session_id = session.session_id
        
        # Log token refresh
        self.log_security_event(
            user_id=user.id,
            session_id=session_id,
            event_type="token_refresh",
            event_category="auth",
            severity="low",
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=current_fingerprint
        )
        
        self.db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    def revoke_refresh_token(self, refresh_token: str, reason: str = "logout") -> bool:
        """Revoke a specific refresh token"""
        token_hash = hash_token(refresh_token)
        
        refresh_token_record = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_active == True
            )
        ).first()
        
        if refresh_token_record:
            refresh_token_record.is_active = False
            
            # Terminate associated session
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token_id == refresh_token_record.id
            ).first()
            if session:
                self.terminate_session(session.session_id, reason)
            
            self.db.commit()
            return True
        
        return False

    def revoke_token_family(self, family_id: str, reason: str = "security_breach") -> int:
        """Revoke all tokens in a family (for security breaches)"""
        tokens = self.db.query(RefreshToken).filter(
            and_(
                RefreshToken.family_id == family_id,
                RefreshToken.is_active == True
            )
        ).all()
        
        for token in tokens:
            token.is_active = False
            
            # Terminate associated sessions
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token_id == token.id
            ).first()
            if session:
                self.terminate_session(session.session_id, reason)
        
        self.db.commit()
        return len(tokens)

    def get_active_user_sessions(self, user_id: int) -> List[UserSession]:
        """Get all active sessions for a user"""
        return self.db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            )
        ).all()

    def terminate_session(self, session_id: str, reason: str = "logout") -> bool:
        """Terminate a specific session"""
        session = self.db.query(UserSession).filter(
            UserSession.session_id == session_id
        ).first()
        
        if session and session.is_active:
            session.is_active = False
            session.terminated_at = datetime.utcnow()
            session.termination_reason = reason
            
            # Revoke associated refresh token
            if session.refresh_token_id:
                refresh_token = self.db.query(RefreshToken).filter(
                    RefreshToken.id == session.refresh_token_id
                ).first()
                if refresh_token:
                    refresh_token.is_active = False
            
            self.db.commit()
            return True
        
        return False

    def terminate_all_user_sessions(self, user_id: int, reason: str = "logout_all") -> int:
        """Terminate all sessions for a user"""
        sessions = self.get_active_user_sessions(user_id)
        
        for session in sessions:
            self.terminate_session(session.session_id, reason)
        
        return len(sessions)

    def cleanup_expired_tokens(self) -> Dict[str, int]:
        """Clean up expired tokens and sessions"""
        now = datetime.utcnow()
        
        # Clean up expired refresh tokens
        expired_refresh_tokens = self.db.query(RefreshToken).filter(
            RefreshToken.expires_at <= now
        ).delete()
        
        # Clean up expired sessions
        expired_sessions = self.db.query(UserSession).filter(
            UserSession.expires_at <= now
        ).delete()
        
        # Clean up expired blacklist entries
        expired_blacklist = self.db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at <= now
        ).delete()
        
        self.db.commit()
        
        return {
            "refresh_tokens": expired_refresh_tokens,
            "sessions": expired_sessions,
            "blacklist_entries": expired_blacklist
        }

    def log_security_event(
        self,
        event_type: str,
        event_category: str,
        severity: str,
        user_id: int = None,
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        device_fingerprint: str = None,
        location: str = None,
        details: str = None,
        success: bool = True,
        error_message: str = None
    ) -> None:
        """Log a security event"""
        log_entry = SecurityLog(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_category=event_category,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            location=location,
            details=details,
            success=success,
            error_message=error_message
        )
        self.db.add(log_entry)
        # Note: Don't commit here, let the calling function handle it

    def get_user_security_summary(self, user_id: int) -> Dict[str, Any]:
        """Get security summary for a user"""
        active_sessions = self.get_active_user_sessions(user_id)
        
        # Get recent security events
        recent_events = self.db.query(SecurityLog).filter(
            and_(
                SecurityLog.user_id == user_id,
                SecurityLog.created_at > datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(SecurityLog.created_at.desc()).limit(10).all()
        
        return {
            "active_sessions": len(active_sessions),
            "session_details": [
                {
                    "session_id": s.session_id,
                    "device_type": s.device_type,
                    "ip_address": s.ip_address,
                    "location": s.location,
                    "created_at": s.created_at.isoformat(),
                    "last_activity": s.last_activity_at.isoformat(),
                    "is_current": False  # We don't have current session context here
                }
                for s in active_sessions
            ],
            "recent_security_events": [
                {
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "created_at": e.created_at.isoformat(),
                    "ip_address": e.ip_address,
                    "success": e.success
                }
                for e in recent_events
            ]
        }
