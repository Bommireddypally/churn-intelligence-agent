# FILE: tests/test_explain.py
import math

from agent import model_service as ms
from agent.db import run_query


def _ids(n=5):
    return [r[0] for r in run_query(f"SELECT customerID FROM customers LIMIT {n}")["rows"]]


def test_contributions_add_up_to_the_model_output():
    for cid in _ids():
        raw = ms.get_customer(cid)
        out = ms.explain_row(raw, top_n=len(ms.FEATURES))
        logit = out["base_logit"] + sum(d["contribution"] for d in out["drivers"])
        assert abs(1 / (1 + math.exp(-logit)) - ms.score_row(raw)) < 0.01


def test_drivers_sorted_and_readable():
    raw = ms.get_customer(_ids(1)[0])
    out = ms.explain_row(raw, top_n=5)
    strengths = [abs(d["contribution"]) for d in out["drivers"]]
    assert len(out["drivers"]) == 5 and strengths == sorted(strengths, reverse=True)
    for d in out["drivers"]:
        assert d["value"] == raw[d["feature"]]
        assert d["direction"] in ("raises churn risk", "lowers churn risk")