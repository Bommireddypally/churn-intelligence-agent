# FILE: evals/show_failures.py
import json
import sys

from agent.db import run_query

with open("evals/cases.json", encoding="utf-8") as f:
    cases = {c["id"]: c for c in json.load(f)}
with open(f"evals/results_{sys.argv[1]}.json", encoding="utf-8") as f:
    results = json.load(f)

for r in results:
    if r["passed"] is False:
        print("=" * 60)
        print(r["id"], "|", cases[r["id"]]["question"])
        print("AGENT SQL:", r["sql"])
        got = run_query(r["sql"]) if r["sql"] else None
        print("AGENT ROWS:", got.get("rows", got) if got else None)
        gold = run_query(cases[r["id"]]["gold_sql"])
        print("GOLD ROWS: ", gold.get("rows", gold))
        print("AGENT SAID:", r["answer"])
    elif r["passed"] is None:
        print("=" * 60)
        print("MANUAL CASE:", r["id"])
        print("AGENT SAID:", r["answer"])