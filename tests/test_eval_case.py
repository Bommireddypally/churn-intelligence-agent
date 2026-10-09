import json

from agent.db import run_query


def _cases():
    with open("evals/cases.json", encoding="utf-8") as f:
        return json.load(f)


def test_case_ids_are_unique():
    ids = [c["id"] for c in _cases()]
    assert len(ids) == len(set(ids))


def test_gold_queries_run_and_return_rows():
    for c in _cases():
        if "gold_sql" in c:
            r = run_query(c["gold_sql"])
            assert "error" not in r, c["id"]
            assert r["row_count"] > 0, c["id"]