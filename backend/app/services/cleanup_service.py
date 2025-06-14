from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.token import TokenBlacklist, RefreshToken, UserSession, SecurityLog
from app.models.user import User
from app.database import SessionLocal
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up expired tokens, sessions, and security logs"""
    
    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self._should_close_db = db is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._should_close_db and self.db:
            self.db.close()

    def cleanup_expired_tokens(self) -> Dict[str, int]:
        """Clean up expired tokens and sessions"""
        now = datetime.utcnow()
        results = {}
        
        try:
            # Clean up expired blacklisted tokens
            expired_blacklist_count = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at <= now
            ).delete(synchronize_session='fetch')
            results['blacklist_tokens'] = expired_blacklist_count
            
            # Clean up expired refresh tokens
            expired_refresh_count = self.db.query(RefreshToken).filter(
                RefreshToken.expires_at <= now
            ).delete(synchronize_session='fetch')
            results['refresh_tokens'] = expired_refresh_count
            
            # Clean up expired sessions
            expired_sessions_count = self.db.query(UserSession).filter(
                UserSession.expires_at <= now
            ).delete(synchronize_session='fetch')
            results['sessions'] = expired_sessions_count
            
            # Deactivate inactive refresh tokens (not used for a long time)
            inactive_threshold = now - timedelta(days=30)
            inactive_refresh_count = self.db.query(RefreshToken).filter(
                and_(
                    RefreshToken.is_active == True,
                    RefreshToken.last_used_at <= inactive_threshold
                )
            ).update({'is_active': False}, synchronize_session='fetch')
            results['inactive_refresh_tokens'] = inactive_refresh_count
            
            # Terminate inactive sessions
            inactive_sessions_count = self.db.query(UserSession).filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.last_activity_at <= inactive_threshold
                )
            ).update({
                'is_active': False,
                'terminated_at': now,
                'termination_reason': 'inactivity_timeout'
            }, synchronize_session='fetch')
            results['inactive_sessions'] = inactive_sessions_count
            
            self.db.commit()
            
            logger.info(f"Token cleanup completed: {results}")
            return results
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Token cleanup failed: {str(e)}")
            raise

    def cleanup_old_security_logs(self, retention_days: int = None) -> int:
        """Clean up old security logs beyond retention period"""
        retention_days = retention_days or settings.SECURITY_LOG_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        try:
            deleted_count = self.db.query(SecurityLog).filter(
                SecurityLog.created_at <= cutoff_date
            ).delete(synchronize_session='fetch')
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old security logs (older than {retention_days} days)")
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Security log cleanup failed: {str(e)}")
            raise

    def cleanup_orphaned_sessions(self) -> int:
        """Clean up sessions that have no corresponding refresh token"""
        try:
            # Find sessions with inactive or non-existent refresh tokens
            orphaned_sessions = self.db.query(UserSession).join(
                RefreshToken, 
                UserSession.refresh_token_id == RefreshToken.id,
                isouter=True
            ).filter(
                and_(
                    UserSession.is_active == True,
                    func.coalesce(RefreshToken.is_active, False) == False
                )
            ).all()
            
            count = 0
            for session in orphaned_sessions:
                session.is_active = False
                session.terminated_at = datetime.utcnow()
                session.termination_reason = 'orphaned_cleanup'
                count += 1
            
            self.db.commit()
            
            logger.info(f"Cleaned up {count} orphaned sessions")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Orphaned session cleanup failed: {str(e)}")
            raise

    def get_cleanup_statistics(self) -> Dict[str, Any]:
        """Get statistics about tokens and sessions for monitoring"""
        try:
            stats = {}
            
            # Token statistics
            stats['active_refresh_tokens'] = self.db.query(RefreshToken).filter(
                and_(
                    RefreshToken.is_active == True,
                    RefreshToken.expires_at > datetime.utcnow()
                )
            ).count()
            
            stats['expired_refresh_tokens'] = self.db.query(RefreshToken).filter(
                RefreshToken.expires_at <= datetime.utcnow()
            ).count()
            
            stats['blacklisted_tokens'] = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at > datetime.utcnow()
            ).count()
            
            stats['expired_blacklisted_tokens'] = self.db.query(TokenBlacklist).filter(
                TokenBlacklist.expires_at <= datetime.utcnow()
            ).count()
            
            # Session statistics
            stats['active_sessions'] = self.db.query(UserSession).filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).count()
            
            stats['expired_sessions'] = self.db.query(UserSession).filter(
                UserSession.expires_at <= datetime.utcnow()
            ).count()
            
            # Security log statistics
            stats['total_security_logs'] = self.db.query(SecurityLog).count()
            
            stats['recent_security_logs'] = self.db.query(SecurityLog).filter(
                SecurityLog.created_at > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # User statistics
            stats['total_users'] = self.db.query(User).count()
            stats['active_users'] = self.db.query(User).filter(User.is_active == True).count()
            
            # Users with active sessions
            stats['users_with_active_sessions'] = self.db.query(UserSession.user_id).filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.utcnow()
                )
            ).distinct().count()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cleanup statistics: {str(e)}")
            raise

    def run_full_cleanup(self) -> Dict[str, Any]:
        """Run all cleanup operations"""
        results = {}
        
        try:
            # Clean up expired tokens and sessions
            token_cleanup = self.cleanup_expired_tokens()
            results['token_cleanup'] = token_cleanup
            
            # Clean up old security logs
            log_cleanup = self.cleanup_old_security_logs()
            results['security_log_cleanup'] = log_cleanup
            
            # Clean up orphaned sessions
            orphaned_cleanup = self.cleanup_orphaned_sessions()
            results['orphaned_session_cleanup'] = orphaned_cleanup
            
            # Get final statistics
            stats = self.get_cleanup_statistics()
            results['final_statistics'] = stats
            
            logger.info(f"Full cleanup completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Full cleanup failed: {str(e)}")
            raise


def run_cleanup_job():
    """Standalone function to run cleanup job (for background tasks)"""
    try:
        with CleanupService() as cleanup_service:
            results = cleanup_service.run_full_cleanup()
            return results
    except Exception as e:
        logger.error(f"Cleanup job failed: {str(e)}")
        raise
