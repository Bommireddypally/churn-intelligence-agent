# FILE: evals/show_failures.py
import json
import sys

from agent.db import run_query

with open("evals/cases.json", encoding="utf-8") as f:
    cases = {c["id"]: c for c in json.load(f)}
with open(f"evals/results_{sys.argv[1]}.json", encoding="utf-8") as f:
    results = json.load(f)

for r in results:
    case = cases[r["id"]]
    if r["passed"] is False or r["passed"] is None:
        print("=" * 60)
        label = "MANUAL" if r["passed"] is None else "FAILED"
        print(label, r["id"], f"[{r['kind']}]", "|", case["question"])
        print("TOOLS CALLED:", r["tools"])
        if r["kind"] == "sql":
            sql = r["detail"].get("sql")
            got = run_query(sql) if sql else None
            print("AGENT SQL:", sql)
            print("AGENT ROWS:", got.get("rows", got) if got else None)
            print("GOLD ROWS: ", run_query(case["gold_sql"]).get("rows"))
        else:
            print("DETAIL:", r["detail"])
        print("AGENT SAID:", r["answer"])