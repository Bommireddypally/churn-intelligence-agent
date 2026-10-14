# FILE: tests/test_tools.py
import json

from agent.db import run_query
from agent.tools import dispatch


def _top_id():
    return run_query(
        "SELECT customerID FROM customer_scores ORDER BY churn_prob DESC LIMIT 1"
    )["rows"][0][0]


def test_explain_returns_five_drivers_and_is_json_safe():
    out = dispatch("explain_prediction", {"customer_id": _top_id()})
    assert len(out["drivers"]) == 5
    assert 0 <= out["churn_probability"] <= 1
    json.dumps(out)  # must not raise


def test_explain_unknown_customer_is_an_error_not_a_crash():
    assert "error" in dispatch("explain_prediction", {"customer_id": "NOPE"})


def test_explain_missing_argument_is_an_error():
    assert "error" in dispatch("explain_prediction", {})


def test_unknown_tool_is_an_error():
    assert "error" in dispatch("send_offer", {"customer_id": "x"})