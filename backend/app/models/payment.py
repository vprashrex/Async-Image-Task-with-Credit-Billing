from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    razorpay_order_id = Column(String, unique=True, nullable=False)
    razorpay_payment_id = Column(String, unique=True, nullable=True, index=True)  # Changed to nullable=True
    amount = Column(Float, nullable=False)  # Amount in INR
    credits = Column(Integer, nullable=False)  # Credits purchased
    status = Column(String, default="created")  # created, paid, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="payments")


# Add payments relationship to User model
from app.models.user import User
User.payments = relationship("Payment", back_populates="user")
