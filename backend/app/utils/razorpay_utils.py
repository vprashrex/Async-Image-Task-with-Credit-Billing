import razorpay
import hmac
import hashlib
from app.config import settings

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount: float, currency: str = "INR") -> dict:
    """Create a Razorpay order"""
    order_data = {
        "amount": int(amount * 100),  # Amount in paise
        "currency": currency,
        "payment_capture": 1  # Auto capture payment
    }
    
    order = razorpay_client.order.create(data=order_data)
    return order


def verify_razorpay_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify Razorpay payment signature"""
    try:
        # Create signature string
        signature_string = f"{razorpay_order_id}|{razorpay_payment_id}"
        
        # Generate expected signature
        expected_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, razorpay_signature)
    except Exception:
        return False


def verify_webhook_signature(payload: str, signature: str) -> bool:
    """Verify Razorpay webhook signature"""
    try:
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    except Exception:
        return False
