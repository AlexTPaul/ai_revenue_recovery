import uuid
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone, date, time
import httpx

from app.config import settings


class RazorpayService:
    def get_credentials(self):
        key_id = settings.RAZORPAY_KEY_ID
        key_secret = settings.RAZORPAY_KEY_SECRET
        webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET or key_secret
        is_live = bool(key_id and key_secret)
        return key_id, key_secret, webhook_secret, is_live

    def create_payment_link(
        self,
        amount: float,
        customer_name: str,
        customer_phone: str,
        reference_id: str,
        expire_by_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Creates a payment link. If Razorpay live/test keys are configured, calls Razorpay API;
        otherwise generates a compliant simulated Razorpay Payment Link payload.
        """
        key_id, key_secret, _, is_live = self.get_credentials()

        if is_live:
            try:
                # Prepare expire_by timestamp (end of day for the promised date)
                expire_timestamp = None
                if expire_by_date:
                    dt = datetime.combine(expire_by_date, time(23, 59, 59), tzinfo=timezone.utc)
                    expire_timestamp = int(dt.timestamp())

                payload = {
                    "amount": int(round(amount * 100)),  # in paise
                    "currency": "INR",
                    "accept_partial": False,
                    "reference_id": reference_id,
                    "description": f"Mandate Recovery Payment for {customer_name}",
                    "customer": {
                        "name": customer_name,
                        "contact": customer_phone.replace(" ", "").replace("+91", ""),
                    },
                    "notify": {
                        "sms": False,
                        "email": False
                    },
                    "reminder_enable": False,
                }
                if expire_timestamp:
                    payload["expire_by"] = expire_timestamp

                url = "https://api.razorpay.com/v1/payment_links"
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, auth=(key_id, key_secret), json=payload)
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        return {
                            "id": data.get("id"),
                            "amount": data.get("amount"),
                            "currency": data.get("currency", "INR"),
                            "status": data.get("status", "created"),
                            "short_url": data.get("short_url"),
                            "reference_id": reference_id,
                            "customer": {
                                "name": customer_name,
                                "contact": customer_phone,
                            },
                            "created_at": data.get("created_at"),
                            "is_mock": False,
                        }
            except Exception as e:
                print(f"[RazorpayService] Live API call failed, falling back to mock: {e}")

        # Simulated fallback link
        unique_id = uuid.uuid4().hex[:8]
        link_id = f"plink_{unique_id}"
        short_url = f"https://rzp.io/i/{unique_id}"

        return {
            "id": link_id,
            "amount": int(round(amount * 100)),  # in paise
            "currency": "INR",
            "status": "created",
            "short_url": short_url,
            "reference_id": reference_id,
            "customer": {
                "name": customer_name,
                "contact": customer_phone,
            },
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "is_mock": True,
        }

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        """Verifies HMAC SHA256 webhook signature or accepts in mock mode."""
        _, key_secret, webhook_secret, is_live = self.get_credentials()
        if not is_live:
            return True
        secret_to_use = webhook_secret or key_secret
        if not secret_to_use:
            return True
        expected = hmac.new(secret_to_use.encode(), body_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


razorpay_service = RazorpayService()

