from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class TokenBlacklist(Base):
    """Token blacklist for JWT revocation"""
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(36), unique=True, index=True, nullable=False)  # JWT ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_type = Column(String(20), nullable=False)  # 'access' or 'refresh'
    reason = Column(String(100))  # logout, password_change, admin_revoke, etc.
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="blacklisted_tokens")
    
    # Index for performance
    __table_args__ = (
        Index('ix_token_blacklist_jti_user_id', 'jti', 'user_id'),
        Index('ix_token_blacklist_expires_at', 'expires_at'),
    )


class RefreshToken(Base):
    """Refresh token storage for secure token renewal"""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)  # SHA256 hash
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_fingerprint = Column(String(64), index=True)  # Device identification
    family_id = Column(String(36), index=True)  # Token family for rotation detection
    
    # Session and device info
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_type = Column(String(50))
    location = Column(String(100))
    
    # Token metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="refresh_tokens")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_refresh_tokens_user_device', 'user_id', 'device_fingerprint'),
        Index('ix_refresh_tokens_family_id', 'family_id'),
        Index('ix_refresh_tokens_expires_at', 'expires_at'),
    )


class UserSession(Base):
    """User session tracking and management"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token_id = Column(Integer, ForeignKey("refresh_tokens.id"), nullable=True)
    
    # Session metadata
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    device_type = Column(String(50))
    device_fingerprint = Column(String(64))
    location = Column(String(100))
    
    # Session state
    is_active = Column(Boolean, default=True)
    is_remember_me = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    terminated_at = Column(DateTime(timezone=True))
    termination_reason = Column(String(50))  # logout, timeout, admin, suspicious
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    refresh_token = relationship("RefreshToken")
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_user_sessions_user_active', 'user_id', 'is_active'),
        Index('ix_user_sessions_device', 'device_fingerprint'),
        Index('ix_user_sessions_expires_at', 'expires_at'),
    )


class SecurityLog(Base):
    """Security events and audit log"""
    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(36), index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, token_refresh, etc.
    event_category = Column(String(20), nullable=False)  # auth, session, security, suspicious
    severity = Column(String(10), nullable=False)  # low, medium, high, critical
    
    # Context information
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_fingerprint = Column(String(64))
    location = Column(String(100))
    
    # Event data
    details = Column(Text)  # JSON string with additional details
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="security_logs")
    
    # Indexes for performance and security monitoring
    __table_args__ = (
        Index('ix_security_logs_event_time', 'event_type', 'created_at'),
        Index('ix_security_logs_user_time', 'user_id', 'created_at'),
        Index('ix_security_logs_severity', 'severity'),
        Index('ix_security_logs_ip_time', 'ip_address', 'created_at'),
    )
