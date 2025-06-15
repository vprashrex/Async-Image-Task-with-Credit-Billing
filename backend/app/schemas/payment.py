from pydantic import BaseModel, conint, Field
from typing import Optional
from datetime import datetime


class PaymentBase(BaseModel):
    amount: float
    credits: int


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    id: int
    user_id: int
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: int
    amount: float
    credits: int
    status: str
    razorpay_order_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreditPurchaseRequest(BaseModel):
    credits: int = Field(..., gt=0, lt=1000, description="Number of credits to purchase (1–999)")


class CreditPurchaseResponse(BaseModel):
    order_id: str
    amount: float
    currency: str
    key: str


class RazorpayWebhook(BaseModel):
    event: str
    payload: dict
