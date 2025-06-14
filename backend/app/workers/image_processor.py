import os
import time
from PIL import Image, ImageFilter, ImageEnhance
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.celery_app import celery_app
from app.database import SessionLocal
from app.services.task_service import TaskService
from app.services.user_service import UserService


@celery_app.task(
    bind=True,
    soft_time_limit=300,  # 5 minutes
    time_limit=330,       # Hard limit
    max_retries=3,
    rate_limit='20/m',    # Rate limiting for production load
    acks_late=True,       # Ensure task completion acknowledgment
    reject_on_worker_lost=True
)
def process_image_task(
    self, task_id: int, image_path: str, user_id: int, processing_options: dict = None
):
    """
    Celery task to process images asynchronously with proper transaction management
    and credit rollback on failure
    """
    # Create a new database session for this task
    db = SessionLocal()
    task_service = TaskService(db)
    user_service = UserService(db)
    processed_path = None

    try:
        # Update task status to processing
        task_service.update_task_status(task_id, "processing")
        db.commit()

        # Load and process the image
        with Image.open(image_path) as img:
            # Get processing options
            options = processing_options or {}
            operation = options.get("operation", "grayscale")

            # Process the image based on operation
            if operation == "grayscale":
                processed_img = img.convert("L")
            elif operation == "blur":
                processed_img = img.filter(ImageFilter.BLUR)
            elif operation == "sharpen":
                processed_img = img.filter(ImageFilter.SHARPEN)
            elif operation == "enhance":
                enhancer = ImageEnhance.Contrast(img)
                processed_img = enhancer.enhance(1.5)
            elif operation == "resize":
                width = options.get("width", 800)
                height = options.get("height", 600)
                processed_img = img.resize((width, height), Image.Resampling.LANCZOS)
            else:
                # Default: apply a slight enhancement
                enhancer = ImageEnhance.Color(img)
                processed_img = enhancer.enhance(1.2)

            # Generate processed image path
            base_path, ext = os.path.splitext(image_path)
            processed_path = f"{base_path}_processed{ext}"

            # Save processed image
            processed_img.save(processed_path, quality=95)

        # Update task with success
        task_service.update_task_status(
            task_id,
            "completed",
            processed_image_path=processed_path,
            completed_at=datetime.utcnow(),
        )
        db.commit()

        return {
            "status": "completed",
            "processed_image_path": processed_path,
            "message": f"Image processed successfully with {operation} operation",
        }

    except (IOError, OSError) as img_exc:
        # Image processing errors - mark as failed and rollback credit
        error_message = f"Image processing error: {str(img_exc)}"
        _mark_task_failed_with_credit_rollback(
            db,
            task_service,
            user_service,
            task_id,
            user_id,
            error_message,
            processed_path,
        )

        return {"status": "failed", "error": error_message, "credit_refunded": True}

    except SQLAlchemyError as db_exc:
        # Database errors - retry with backoff
        error_message = f"Database error: {str(db_exc)}"
        db.rollback()

        # Clean up any created files
        _cleanup_file(processed_path)

        # Handle retry logic for transient database errors
        if self.request.retries < 3:
            raise self.retry(
                exc=db_exc, countdown=60 * (2**self.request.retries), max_retries=3
            )

        # Max retries reached - mark as failed and rollback credit
        _mark_task_failed_with_credit_rollback(
            db,
            task_service,
            user_service,
            task_id,
            user_id,
            error_message,
            processed_path,
        )

        return {"status": "failed", "error": error_message, "credit_refunded": True}

    except Exception as exc:
        db.rollback()
        # Other unexpected errors
        error_message = f"Unexpected error: {str(exc)}"

        # Retry for transient errors
        if self.request.retries < 2:
            raise self.retry(exc=exc, countdown=30, max_retries=2)

        # Max retries reached - mark as failed and rollback credit
        _mark_task_failed_with_credit_rollback(
            db,
            task_service,
            user_service,
            task_id,
            user_id,
            error_message,
            processed_path,
        )

        return {"status": "failed", "error": error_message, "credit_refunded": True}

    finally:
        db.close()


def _mark_task_failed_with_credit_rollback(
    db, task_service, user_service, task_id, user_id, error_message, processed_path=None
):
    """
    Helper function to mark task as failed and rollback credit with proper transaction handling
    """
    try:
        # Start a new transaction for cleanup operations
        task_service.update_task_status(task_id, "failed", error_message=error_message)

        # Rollback credit atomically
        credit_refunded = user_service.add_credits(user_id, 1)

        if credit_refunded:
            print(f"✅ Credit refunded to user {user_id} for failed task {task_id}")
        else:
            print(f"❌ Failed to refund credit to user {user_id} for task {task_id}")

        db.commit()

        # Clean up any partially created files
        _cleanup_file(processed_path)

    except Exception as final_exc:
        # If we can't even update the status, log it but don't raise
        print(
            f"Critical: Failed to update task {task_id} status to failed: {final_exc}"
        )
        db.rollback()
        _cleanup_file(processed_path)

        # Try to refund credit in a separate transaction as last resort
        try:
            db_new = SessionLocal()
            user_service_new = UserService(db_new)
            credit_refunded = user_service_new.add_credits(user_id, 1)
            db_new.close()

            if credit_refunded:
                print(f"✅ Emergency credit refund successful for user {user_id}")
            else:
                print(f"❌ Emergency credit refund failed for user {user_id}")

        except Exception as emergency_exc:
            print(f"💥 Emergency credit refund failed: {emergency_exc}")


def _cleanup_file(file_path):
    """
    Helper function to safely clean up files
    """
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass  # Ignore cleanup errors


@celery_app.task
def cleanup_old_files():
    """
    Periodic task to cleanup old processed files
    """
    # This would run periodically to clean up old files
    # Implementation depends on your retention policy
    pass


@celery_app.task(rate_limit='1/m')
def health_check():
    """
    Simple health check for monitoring system status
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        print(f"Health check failed: {e}")
        return {
            "status": "unhealthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }