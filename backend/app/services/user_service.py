from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.auth import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user"""
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password,
            credits=5  # Give 5 free credits to new users
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def update_user_credits(self, user_id: int, credits: int) -> Optional[User]:
        """Update user credits - DEPRECATED: Use add_credits instead"""
        user = self.get_user_by_id(user_id)
        if user:
            user.credits += credits
            self.db.commit()
            self.db.refresh(user)
        return user

    def deduct_credit(self, user_id: int) -> bool:
        """Deduct one credit from user using atomic operation to prevent race conditions"""
        try:
            # Use atomic update to prevent race conditions
            result = self.db.query(User).filter(
                User.id == user_id,
                User.credits > 0,
                User.is_active == True
            ).update({
                User.credits: User.credits - 1
            }, synchronize_session=False)
            
            self.db.commit()
            return result > 0        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deducting credit: {e}")
            return False

    def add_credits(self, user_id: int, credits: int) -> bool:
        """Add credits to user account using atomic operation"""
        if credits <= 0:
            return False
            
        try:
            # Use atomic update to prevent race conditions
            result = self.db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).update({
                User.credits: User.credits + credits
            }, synchronize_session=False)
            
            self.db.commit()
            return result > 0        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding credits: {e}")
            return False

    def get_all_users(self, skip: int = 0, limit: int = 100):
        """Get all users (admin only)"""
        return self.db.query(User).offset(skip).limit(limit).all()
