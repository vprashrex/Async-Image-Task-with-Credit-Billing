from celery import Celery
from app.celery_app import app as celery_app
from app.services.cleanup_service import run_cleanup_job
from app.config import settings
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="security.cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Background task to clean up expired tokens and sessions"""
    try:
        logger.info("Starting automated token cleanup task")
        results = run_cleanup_job()
        logger.info(f"Token cleanup completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Token cleanup task failed: {str(e)}")
        raise


@celery_app.task(name="security.monitor_suspicious_activity")
def monitor_suspicious_activity():
    """Background task to monitor and alert on suspicious activity"""
    try:
        logger.info("Starting suspicious activity monitoring")
        
        from app.database import SessionLocal
        from app.services.token_service import TokenService
        from app.models.token import SecurityLog
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        
        db = SessionLocal()
        try:
            # Look for potential security issues in the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            # Check for multiple failed logins from same IP
            failed_logins = db.query(
                SecurityLog.ip_address,
                func.count(SecurityLog.id).label('attempts')
            ).filter(
                and_(
                    SecurityLog.event_type == 'failed_login',
                    SecurityLog.created_at >= one_hour_ago,
                    SecurityLog.success == False
                )
            ).group_by(SecurityLog.ip_address).having(
                func.count(SecurityLog.id) >= settings.SUSPICIOUS_ACTIVITY_THRESHOLD
            ).all()
            
            if failed_logins:
                logger.warning(f"Detected suspicious login activity: {failed_logins}")
                # In a real application, you might send alerts here
            
            # Check for token theft indicators
            token_issues = db.query(SecurityLog).filter(
                and_(
                    SecurityLog.event_type.in_([
                        'device_fingerprint_mismatch',
                        'invalid_refresh_token'
                    ]),
                    SecurityLog.created_at >= one_hour_ago,
                    SecurityLog.severity.in_(['high', 'critical'])
                )
            ).count()
            
            if token_issues > 0:
                logger.warning(f"Detected {token_issues} potential token security issues")
            
            return {
                "suspicious_ips": len(failed_logins),
                "token_security_issues": token_issues,
                "monitoring_period": "1 hour"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Suspicious activity monitoring failed: {str(e)}")
        raise


# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic security tasks"""
    
    # Clean up expired tokens every 6 hours
    sender.add_periodic_task(
        6 * 60 * 60,  # 6 hours in seconds
        cleanup_expired_tokens.s(),
        name='cleanup expired tokens every 6 hours'
    )
    
    # Monitor suspicious activity every hour
    sender.add_periodic_task(
        60 * 60,  # 1 hour in seconds
        monitor_suspicious_activity.s(),
        name='monitor suspicious activity every hour'
    )
    
    logger.info("Security periodic tasks configured")
