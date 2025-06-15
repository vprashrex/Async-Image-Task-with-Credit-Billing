from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.payment import CreditPurchaseRequest, CreditPurchaseResponse
from app.services.payment_service import PaymentService
from app.services.user_service import UserService
from app.utils.razorpay_utils import create_razorpay_order, verify_webhook_signature
from app.utils.security import log_security_event, handle_service_error
from app.models.user import User
from app.config import settings
import json
from app.models.webhook_event import WebhookEvent
from app.models.payment import Payment
import logging, time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("/balance")
async def get_credit_balance(
    current_user: User = Depends(get_current_user)
):
    return {
        "user_id": current_user.id,
        "credits": current_user.credits,
        "email": current_user.email
    }


@router.post("/purchase", response_model=CreditPurchaseResponse)
async def purchase_credits(
    purchase_request: CreditPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Razorpay order for credit purchase"""
    try:
        payment_service = PaymentService(db)
        
        # Calculate amount (1 credit = ₹10)
        amount = purchase_request.credits * 10.0
        
        # Create Razorpay order
        order = create_razorpay_order(amount)
        
        # Create PaymentCreate object first
        from app.schemas.payment import PaymentCreate
        payment_create = PaymentCreate(
            amount=amount,
            credits=purchase_request.credits
        )
        
        # Create payment record with correct parameters
        payment_service.create_payment(
            payment_create=payment_create,
            user_id=current_user.id,
            razorpay_order_id=order["id"]
        )
        
        logger.info(f"Payment order created for user {current_user.id}: {order['id']}")
        
        return CreditPurchaseResponse(
            order_id=order["id"],
            amount=amount,
            currency="INR",
            key=settings.RAZORPAY_KEY_ID
        )
        
    except Exception as e:
        logger.error(f"Payment order creation failed for user {current_user.id}: {str(e)}")
        raise handle_service_error(e, "Failed to create payment order")


# Secure Razorpay webhook handler
@router.post("/webhook/rzp-x2394h5kjh", status_code=200)
async def secure_razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    logger = logging.getLogger(__name__)

    # 1) Limit payload size (~1MB)
    body = await request.body()
    if len(body) > 1_048_576:
        raise HTTPException(status_code=413, detail="Payload too large")
    payload = body.decode("utf-8")

    # 2) Auth headers: signature and webhook-id
    sig = request.headers.get("X-Razorpay-Signature")
    wid = request.headers.get("x-razorpay-event-id")

    if not sig or not wid:
        logger.warning("Invalid webhook auth headers: %s", dict(request.headers))
        raise HTTPException(status_code=400, detail="Invalid webhook request")

    # 3) Replay protection
    if db.query(WebhookEvent).filter_by(webhook_id=wid).first():
        logger.info("Duplicate webhook skipped: %s", wid)
        return {"status": "duplicate"}

    # 4) Verify signature
    if not verify_webhook_signature(payload, sig):
        logger.warning("Invalid signature for webhook %s", wid)
        raise HTTPException(status_code=400, detail="Invalid webhook request")

    # 5) Record received event
    event_rec = WebhookEvent(webhook_id=wid, status="received", payload=payload)
    db.add(event_rec)
    db.commit()

    data = json.loads(payload)
    ev = data.get("event")
    ent = data.get("payload", {}).get("payment", {}).get("entity", {})

    # 6) Timestamp-based replay guard (5-minute window)
    ts = ent.get("created_at")
    if ts and abs(time.time() - ts) > 300:
        event_rec.status = "failed"
        db.commit()
        logger.warning("Stale webhook %s (ts=%s)", wid, ts)
        raise HTTPException(status_code=400, detail="Invalid webhook request")

    # 7) Handle payment.captured
    if ev == "payment.captured":
        payment_id = ent.get("id")
        order_id = ent.get("order_id")

        # Idempotency check on payment_id
        if db.query(Payment).filter_by(razorpay_payment_id=payment_id).first():
            event_rec.status = "duplicate"
            db.commit()
            logger.info("Payment %s already processed", payment_id)
            return {"status": "duplicate"}

        ps = PaymentService(db)
        payment = ps.get_payment_by_order_id(order_id)
        
        # Validate payload against DB
        if not payment or int(payment.amount * 100) != ent.get("amount") or ent.get("currency") != "INR":
            event_rec.status = "failed"
            db.commit()
            logger.error("Payment mismatch for order %s", order_id)
            raise HTTPException(status_code=400, detail="Invalid payment data")

        try:
            # Manual transaction - all operations in one commit
            ps.update_payment_status(order_id, "paid", payment_id)
            UserService(db).add_credits(payment.user_id, payment.credits)
            event_rec.status = "processed"
            db.commit()
        except Exception as e:
            event_rec.status = "failed"
            db.rollback()
            db.add(event_rec)
            db.commit()
            logger.exception("Error processing payment %s", payment_id)
            raise HTTPException(status_code=500, detail="Internal Server Error")

    else:
        # Mark other events as processed
        event_rec.status = "processed"
        db.commit()

    return {"status": event_rec.status}