# FILE: agent/offers.py
import re
from datetime import datetime, timezone

from agent import model_service

MAX_DISCOUNT_PCT = 20
MAX_DRAFTS_PER_REQUEST = 5
MAX_MESSAGE_CHARS = 500
OFFER_TYPES = ("bill_discount", "contract_upgrade", "tech_support_trial")



def check_message_percentages(message: str, discount_pct: float) -> str | None:
    """Return an error string if the message mentions any percentage other than
    the approved discount, otherwise None."""
    percentages = re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:%|percent)",
        message,
        re.IGNORECASE,
    )

    for value in percentages:
        if float(value) != float(discount_pct):
            return (
                f"Message contains an unapproved percentage: {value}%. "
                f"Only {discount_pct}% is allowed."
            )

        return None

    


class DraftStore:
    """Holds drafts for one session. The agent can only create drafts; approve()
    is called by the UI's Approve button, never by the model."""

    def __init__(self):
        self.drafts = []
        self._this_request = 0

    def new_request(self):
        self._this_request = 0

    def draft(self, customer_id, offer_type, discount_pct, message) -> dict:
        if self._this_request >= MAX_DRAFTS_PER_REQUEST:
            return {"error": f"Limit reached: at most {MAX_DRAFTS_PER_REQUEST} drafts per request."}
        if offer_type not in OFFER_TYPES:
            return {"error": f"offer_type must be one of {list(OFFER_TYPES)}"}
        if isinstance(discount_pct, bool) or not isinstance(discount_pct, (int, float)):
            return {"error": "discount_pct must be a number"}
        if not 0 <= discount_pct <= MAX_DISCOUNT_PCT:
            return {"error": f"Rejected: discount must be between 0 and {MAX_DISCOUNT_PCT} percent."}
        if not isinstance(message, str) or not message.strip():
            return {"error": "message is required"}
        if len(message) > MAX_MESSAGE_CHARS:
            return {"error": f"message is longer than {MAX_MESSAGE_CHARS} characters"}
        problem = check_message_percentages(message, discount_pct)
        if problem:
            return {"error": problem}
        if not isinstance(customer_id, str) or model_service.get_customer(customer_id) is None:
            return {"error": f"Unknown customer_id: {customer_id}"}

        self._this_request += 1
        draft = {
            "id": f"D{len(self.drafts) + 1}",
            "customer_id": customer_id,
            "offer_type": offer_type,
            "discount_pct": discount_pct,
            "message": message.strip(),
            "status": "drafted",
        }
        self.drafts.append(draft)
        return {
            "draft_id": draft["id"],
            "status": "drafted",
            "note": "Not sent. A human must approve it in the UI.",
        }

    def approve(self, draft_id: str) -> dict:
        """Mock send. Called by the Approve button only."""
        for d in self.drafts:
            if d["id"] == draft_id:
                if d["status"] != "drafted":
                    return {"error": f"Draft {draft_id} is already {d['status']}"}
                d["status"] = "sent (mock)"
                d["sent_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                return d
        return {"error": f"Unknown draft: {draft_id}"}