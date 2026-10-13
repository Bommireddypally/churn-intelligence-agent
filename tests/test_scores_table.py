# FILE: tests/test_scores_table.py
from agent import model_service as ms
from agent.db import run_query


def test_scores_table_complete():
    r = run_query("SELECT COUNT(*), COUNT(DISTINCT customerID) FROM customer_scores")
    assert r["rows"] == [(7043, 7043)]


def test_scores_match_live_scoring():
    r = run_query("SELECT customerID, churn_prob FROM customer_scores LIMIT 5")
    for cid, p in r["rows"]:
        assert abs(ms.score_row(ms.get_customer(cid)) - p) < 1e-3