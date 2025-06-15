from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.payment import Payment
from app.schemas.payment import PaymentCreate


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def create_payment(self, payment_create: PaymentCreate, user_id: int, razorpay_order_id: str) -> Payment:
        """Create a new payment record"""
        db_payment = Payment(
            user_id=user_id,
            amount=payment_create.amount,
            credits=payment_create.credits,
            razorpay_order_id=razorpay_order_id,
            status="created"
        )
        self.db.add(db_payment)
        self.db.commit()
        self.db.refresh(db_payment)
        return db_payment

    def get_payment_by_order_id(self, order_id: str) -> Optional[Payment]:
        """Get payment by Razorpay order ID"""
        return self.db.query(Payment).filter(Payment.razorpay_order_id == order_id).first()

    def update_payment_status(self, order_id: str, status: str, payment_id: str = None) -> Optional[Payment]:
        """Update payment status"""
        payment = self.get_payment_by_order_id(order_id)
        if payment:
            payment.status = status
            if payment_id:
                payment.razorpay_payment_id = payment_id
            self.db.commit()
            self.db.refresh(payment)
        return payment

    def get_user_payments(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        """Get all payments for a user"""
        return (
            self.db.query(Payment)
            .filter(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
