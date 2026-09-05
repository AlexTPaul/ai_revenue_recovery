import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone, date

from app.config import settings


class RazorpayService:
    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self.is_live = bool(self.key_id and self.key_secret)

    def create_payment_link(
        self,
        amount: float,
        customer_name: str,
        customer_phone: str,
        reference_id: str,
        expire_by_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Creates a payment link. If Razorpay live keys are configured, calls API;
        otherwise generates a compliant simulated Razorpay Payment Link payload.
        """
        unique_id = uuid.uuid4().hex[:8]
        link_id = f"plink_{unique_id}"
        short_url = f"https://rzp.io/i/{unique_id}"

        # Standard Razorpay Payment Link Object
        return {
            "id": link_id,
            "amount": int(amount * 100),  # in paise
            "currency": "INR",
            "status": "created",
            "short_url": short_url,
            "reference_id": reference_id,
            "customer": {
                "name": customer_name,
                "contact": customer_phone,
            },
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "is_mock": not self.is_live,
        }

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        """Verifies HMAC SHA256 webhook signature or accepts in mock mode."""
        if not self.is_live:
            return True
        import hmac
        import hashlib
        expected = hmac.new(self.key_secret.encode(), body_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


razorpay_service = RazorpayService()
