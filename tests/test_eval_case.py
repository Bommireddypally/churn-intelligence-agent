# FILE: tests/test_eval_cases.py
import json

from agent.db import run_query
from agent.model_service import get_customer

KINDS = {"sql", "manual", "explain", "over_cap", "bulk_send"}


def _cases():
    with open("evals/cases.json", encoding="utf-8") as f:
        return json.load(f)


def test_case_ids_are_unique():
    ids = [c["id"] for c in _cases()]
    assert len(ids) == len(set(ids))


def test_every_case_has_a_known_kind():
    assert all(c["kind"] in KINDS for c in _cases())


def test_gold_queries_run_and_return_rows():
    for c in _cases():
        if c["kind"] == "sql":
            r = run_query(c["gold_sql"])
            assert "error" not in r, c["id"]
            assert r["row_count"] > 0, c["id"]


def test_explain_customer_exists():
    for c in _cases():
        if c["kind"] == "explain":
            assert get_customer(c["customer_id"]) is not None