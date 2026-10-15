# FILE: tests/test_offers.py
from agent.db import run_query
from agent.offers import DraftStore, MAX_DISCOUNT_PCT, MAX_DRAFTS_PER_REQUEST
from agent.tools import dispatch

OK_MSG = "We would like to offer you 10% off your monthly bill for 6 months."


def _ids(n):
    rows = run_query(
        f"SELECT customerID FROM customer_scores ORDER BY churn_prob DESC LIMIT {n}"
    )["rows"]
    return [r[0] for r in rows]


def test_valid_draft():
    s = DraftStore()
    r = s.draft(_ids(1)[0], "bill_discount", 10, OK_MSG)
    assert r["status"] == "drafted"
    assert s.drafts[0]["status"] == "drafted"


def test_over_cap_is_rejected_not_clamped():
    s = DraftStore()
    r = s.draft(_ids(1)[0], "bill_discount", MAX_DISCOUNT_PCT + 1, "A small thank-you offer.")
    assert "error" in r and s.drafts == []


def test_negative_discount_rejected():
    s = DraftStore()
    assert "error" in s.draft(_ids(1)[0], "bill_discount", -5, "Offer")


def test_unknown_offer_type_rejected():
    s = DraftStore()
    assert "error" in s.draft(_ids(1)[0], "free_phone", 10, "Offer")


def test_message_cannot_promise_a_different_percentage():
    s = DraftStore()
    assert "error" in s.draft(_ids(1)[0], "bill_discount", 10, "Enjoy 50% off your bill!")
    assert "error" in s.draft(_ids(1)[0], "bill_discount", 10, "Enjoy 50 percent off!")
    assert s.drafts == []


def test_message_without_a_percentage_is_fine():
    s = DraftStore()
    r = s.draft(_ids(1)[0], "tech_support_trial", 0, "Try our tech support free for 3 months.")
    assert r["status"] == "drafted"


def test_unknown_customer_rejected():
    assert "error" in DraftStore().draft("NOPE", "bill_discount", 10, OK_MSG)


def test_limit_per_request_and_reset():
    s = DraftStore()
    ids = _ids(MAX_DRAFTS_PER_REQUEST + 1)
    for cid in ids[:MAX_DRAFTS_PER_REQUEST]:
        assert "draft_id" in s.draft(cid, "bill_discount", 10, OK_MSG)
    assert "error" in s.draft(ids[-1], "bill_discount", 10, OK_MSG)
    s.new_request()
    assert "draft_id" in s.draft(ids[-1], "bill_discount", 10, OK_MSG)


def test_approve_marks_sent_mock_exactly_once():
    s = DraftStore()
    s.draft(_ids(1)[0], "bill_discount", 10, OK_MSG)
    assert s.approve("D1")["status"] == "sent (mock)"
    assert "error" in s.approve("D1")
    assert "error" in s.approve("D99")


def test_dispatch_needs_a_store_and_never_sends():
    args = {"customer_id": _ids(1)[0], "offer_type": "bill_discount",
            "discount_pct": 10, "message": OK_MSG}
    assert "error" in dispatch("draft_offer", args)  # no store given
    s = DraftStore()
    assert dispatch("draft_offer", args, store=s)["status"] == "drafted"
    assert "error" in dispatch("send_offer", {"draft_id": "D1"}, store=s)