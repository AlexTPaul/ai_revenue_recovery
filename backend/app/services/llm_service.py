import re
from datetime import datetime, date, timedelta
from typing import Optional
import httpx

from app.config import settings
from app.schemas.chat import ParsedCommitment


class LLMService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.openai_key = settings.OPENAI_API_KEY
        self.anthropic_key = settings.ANTHROPIC_API_KEY

    def parse_hinglish_commitment(
        self,
        message: str,
        current_date: date,
        amount: float,
        customer_name: str = "Customer",
        prior_clarification_asked: bool = False
    ) -> ParsedCommitment:
        """
        Parses customer message in English/Hindi/Hinglish to extract structured payment commitment.
        Uses live LLM if API key is provided; otherwise uses intelligent heuristic NLU parser.
        """
        # Try live LLM if key is configured
        if self.openai_key:
            try:
                return self._parse_with_openai(message, current_date, amount, customer_name)
            except Exception:
                pass

        if self.gemini_key:
            try:
                return self._parse_with_gemini(message, current_date, amount, customer_name)
            except Exception:
                pass

        # Robust Heuristic / Rule-based NLP Parser (Works 100% offline)
        return self._heuristic_hinglish_parser(message, current_date, amount, customer_name, prior_clarification_asked)

    def _heuristic_hinglish_parser(
        self,
        message: str,
        current_date: date,
        amount: float,
        customer_name: str,
        prior_clarification_asked: bool
    ) -> ParsedCommitment:
        text = message.lower().strip()

        # 1. Refusal Detection
        refusal_patterns = [
            r"\b(nahi|nahi dunga|nahi dungi|cancel|band karo|fraud|mat karo|no way|wont pay|won't pay|don't charge)\b"
        ]
        for pat in refusal_patterns:
            if re.search(pat, text):
                return ParsedCommitment(
                    has_commitment=False,
                    is_ambiguous=False,
                    promised_date=None,
                    refused=True,
                    confidence=0.95,
                    clarification_message=None,
                    confirmation_message=None
                )

        # 2. Ambiguity Detection (e.g. "soon", "jaldi", "baad me", "de dunga")
        ambiguous_patterns = [
            r"\b(jaldi|thode din|baad me|baad mein|dekhunga|dekhte hain|soon|later|kuch din|aane do|karta hu|karti hu|de dunga|de dungi|koshish|try karunga)\b"
        ]
        is_potentially_vague = any(re.search(pat, text) for pat in ambiguous_patterns)

        # 3. Explicit Date Match: e.g. "5th", "5 tareekh", "5 ko", "05/09", "2026-09-05"
        # Match day of month: "5 tareekh", "5 ko", "5th sep", "5th"
        day_match = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:tareekh|tarikh|ko|date|september|sep|october|oct|august|aug)?\b", text)
        iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text)
        slash_match = re.search(r"\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b", text)

        target_date: Optional[date] = None

        if iso_match:
            try:
                y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                target_date = date(y, m, d)
            except ValueError:
                pass
        elif slash_match and int(slash_match.group(1)) <= 31 and int(slash_match.group(2)) <= 12:
            try:
                d = int(slash_match.group(1))
                m = int(slash_match.group(2))
                y = int(slash_match.group(3)) if slash_match.group(3) else current_date.year
                if y < 100:
                    y += 2000
                target_date = date(y, m, d)
            except ValueError:
                pass

        # Check relative keywords
        if not target_date:
            if "kal" in text or "tomorrow" in text:
                target_date = current_date + timedelta(days=1)
            elif "parso" in text or "day after tomorrow" in text:
                target_date = current_date + timedelta(days=2)
            elif "tarso" in text:
                target_date = current_date + timedelta(days=3)
            elif "agle hafte" in text or "next week" in text:
                target_date = current_date + timedelta(days=7)
            elif "somvar" in text or "monday" in text:
                target_date = self._next_weekday(current_date, 0)
            elif "mangalwar" in text or "tuesday" in text:
                target_date = self._next_weekday(current_date, 1)
            elif "budhwar" in text or "wednesday" in text:
                target_date = self._next_weekday(current_date, 2)
            elif "guruwar" in text or "brihaspatiwar" in text or "thursday" in text:
                target_date = self._next_weekday(current_date, 3)
            elif "shukrawar" in text or "friday" in text:
                target_date = self._next_weekday(current_date, 4)
            elif "shaniwar" in text or "saturday" in text:
                target_date = self._next_weekday(current_date, 5)
            elif "ravivar" in text or "itwar" in text or "sunday" in text:
                target_date = self._next_weekday(current_date, 6)

        # Check numeric day like "5 tareekh" or "10th"
        if not target_date and day_match:
            day_num = int(day_match.group(1))
            if 1 <= day_num <= 31:
                # If day is greater than current day, it's this month; otherwise next month
                if day_num >= current_date.day:
                    try:
                        target_date = date(current_date.year, current_date.month, day_num)
                    except ValueError:
                        target_date = date(current_date.year, current_date.month, 28)
                else:
                    next_m = current_date.month + 1 if current_date.month < 12 else 1
                    next_y = current_date.year if current_date.month < 12 else current_date.year + 1
                    try:
                        target_date = date(next_y, next_m, day_num)
                    except ValueError:
                        target_date = date(next_y, next_m, 28)

        # Evaluate if commitment is definite or ambiguous
        if target_date:
            formatted_date = target_date.strftime("%d %B, %Y")
            return ParsedCommitment(
                has_commitment=True,
                is_ambiguous=False,
                promised_date=target_date,
                refused=False,
                confidence=0.92,
                clarification_message=None,
                confirmation_message=(
                    f"Shukriya {customer_name} ji! Humne {formatted_date} ka promise note kar liya hai. "
                    f"Aap is payment link se kisi bhi samay payment complete kar sakte hain."
                )
            )

        # If vague or ambiguous and no date could be extracted
        if is_potentially_vague or not target_date:
            sample_date = (current_date + timedelta(days=3)).strftime("%d %B")
            return ParsedCommitment(
                has_commitment=False,
                is_ambiguous=True,
                promised_date=None,
                refused=False,
                confidence=0.85,
                clarification_message=(
                    f"Dhanyawad {customer_name} ji! Kya aap koi anumaanit tareekh bata sakte hain "
                    f"(jaise ki {sample_date} ya agle Somvar) taaki hum tab tak link active rakhein?"
                ),
                confirmation_message=None
            )

    def _next_weekday(self, current_date: date, target_weekday: int) -> date:
        """Returns the next occurrence of the given weekday (0=Monday, 6=Sunday)."""
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return current_date + timedelta(days=days_ahead)

    def generate_decision_explanation(
        self,
        event_type: str,
        failure_reason: Optional[str],
        attempt_number: int,
        salary_day: int,
        target_date: Optional[datetime],
        action: str
    ) -> str:
        """Generates clear, human-readable compliance explainability text for audit trail."""
        if action == "schedule_retry" and failure_reason == "insufficient_funds" and target_date:
            return (
                f"Mandate failed due to insufficient funds (Attempt {attempt_number}). "
                f"In accordance with liquidity timing policy, retry scheduled for {target_date.strftime('%Y-%m-%d')} "
                f"(2 days post-salary credit day {salary_day}) to maximize recovery chance."
            )
        elif action == "schedule_retry" and failure_reason in ["bank_timeout", "technical_decline"] and target_date:
            return (
                f"Transient bank switch/timeout error detected ({failure_reason}, Attempt {attempt_number}). "
                f"Scheduled technical retry for next calendar day ({target_date.strftime('%Y-%m-%d')})."
            )
        elif action == "route_to_ptp" and failure_reason == "mandate_expired":
            return (
                "Mandate authorization lapsed. Automated retries bypassed as re-authorization is required; "
                "routed directly to conversational Promise-to-Pay negotiation."
            )
        elif action == "route_to_ptp" and attempt_number >= 3:
            return (
                f"Maximum retry cap (3/3 attempts) reached for insufficient funds. "
                "Halted automated debit retries to protect customer from bank bounce penalties; routed to Promise-to-Pay."
            )
        elif action == "escalate" and failure_reason == "account_closed":
            return (
                "Bank account permanently closed. Both retries and conversational negotiation bypassed; "
                "escalated immediately to human operations queue."
            )
        elif action == "grace_nudge_sent":
            return (
                "Promised payment date elapsed without payment. Dispatched single compliant grace nudge. "
                "Further automated retries held pending customer action."
            )
        elif action == "escalated":
            return (
                "Broken promise stopping rule triggered. Customer did not fulfill commitment after grace nudge. "
                "Automated agent halted permanently; handed off to human support queue with full conversation history."
            )
        elif action == "recovered":
            return (
                "Payment successfully completed. Revenue recovered and mandate cycle fulfilled."
            )
        else:
            return f"Action '{action}' executed for entity under standard operating recovery policy."

    def _parse_with_openai(self, message: str, current_date: date, amount: float, customer_name: str) -> ParsedCommitment:
        # Implementation when OpenAI key is present
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        prompt = (
            f"Current Date: {current_date.isoformat()}\n"
            f"Customer Message: '{message}'\n"
            f"Due Amount: ₹{amount}\n"
            "Extract structured commitment JSON: {has_commitment: bool, is_ambiguous: bool, promised_date: 'YYYY-MM-DD'|null, refused: bool, clarification_message: str|null, confirmation_message: str|null}"
        )
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a Hinglish payment promise extractor. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                import json
                data = json.loads(resp.json()["choices"][0]["message"]["content"])
                p_date = datetime.strptime(data["promised_date"], "%Y-%m-%d").date() if data.get("promised_date") else None
                return ParsedCommitment(
                    has_commitment=data.get("has_commitment", False),
                    is_ambiguous=data.get("is_ambiguous", False),
                    promised_date=p_date,
                    refused=data.get("refused", False),
                    clarification_message=data.get("clarification_message"),
                    confirmation_message=data.get("confirmation_message")
                )
        raise RuntimeError("OpenAI parsing failed")

    def _parse_with_gemini(self, message: str, current_date: date, amount: float, customer_name: str) -> ParsedCommitment:
        # Implementation when Gemini key is present
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        prompt = (
            f"Current Date: {current_date.isoformat()}\n"
            f"Customer Message: '{message}'\n"
            f"Extract JSON: {{has_commitment: bool, is_ambiguous: bool, promised_date: 'YYYY-MM-DD'|null, refused: bool, clarification_message: str|null, confirmation_message: str|null}}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                import json
                raw_text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = json.loads(raw_text)
                p_date = datetime.strptime(data["promised_date"], "%Y-%m-%d").date() if data.get("promised_date") else None
                return ParsedCommitment(
                    has_commitment=data.get("has_commitment", False),
                    is_ambiguous=data.get("is_ambiguous", False),
                    promised_date=p_date,
                    refused=data.get("refused", False),
                    clarification_message=data.get("clarification_message"),
                    confirmation_message=data.get("confirmation_message")
                )
        raise RuntimeError("Gemini parsing failed")


llm_service = LLMService()
