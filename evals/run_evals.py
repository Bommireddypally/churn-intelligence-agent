# FILE: evals/run_evals.py
import json
import sys
import time
from decimal import Decimal

from agent.db import run_query
from agent.loop import run_agent

CASES_PATH = "evals/cases.json"


def _norm_val(v):
    if isinstance(v, (float, Decimal)):
        return round(float(v), 2)
    return v


def rows_match(gold_rows, got_rows) -> bool:
    """Same row count; every gold row's values appear inside a distinct agent row.
    Extra agent columns are allowed; wrong or missing values are not."""
    if len(gold_rows) != len(got_rows):
        return False
    remaining = [[_norm_val(v) for v in r] for r in got_rows]
    for g in gold_rows:
        g_vals = [_norm_val(v) for v in g]
        for i, cand in enumerate(remaining):
            if all(v in cand for v in g_vals):
                remaining.pop(i)
                break
        else:
            return False
    return True


def last_sql(trace):
    sqls = [a.get("sql") for name, a in trace if name == "query_customers" and a.get("sql")]
    return sqls[-1] if sqls else None


def main(tag: str):
    with open(CASES_PATH, encoding="utf-8") as f:
        cases = json.load(f)

    results, auto_total, auto_passed = [], 0, 0
    for case in cases:
        try:
            out = run_agent(case["question"])
        except Exception as e:
            out = {"answer": f"AGENT ERROR: {type(e).__name__}", "steps": 0, "trace": []}

        sql = last_sql(out["trace"])
        record = {"id": case["id"], "answer": out["answer"], "sql": sql, "steps": out["steps"],
                  "flagged": out.get("flagged", [])}

        if case.get("manual"):
            record["passed"] = None  # graded by hand
        else:
            gold = run_query(case["gold_sql"])
            if "error" in gold:
                raise SystemExit(f"Gold SQL broken for {case['id']}: {gold['error']}")
            got = run_query(sql) if sql else {"error": "agent ran no query"}
            record["passed"] = "error" not in got and rows_match(gold["rows"], got["rows"])
            auto_total += 1
            auto_passed += int(record["passed"])

        results.append(record)
        print(case["id"], "->", record["passed"])
        time.sleep(3)  # stay under the free-tier rate limit

    print(f"SCORE ({tag}): {auto_passed}/{auto_total}")
    out_path = f"evals/results_{tag}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Results saved to:", out_path)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "baseline")