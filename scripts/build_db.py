# FILE: scripts/build_db.py
from pathlib import Path

import duckdb
import pandas as pd

from agent.model_service import score_all

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "telco_churn.csv"
DB_PATH = ROOT / "data" / "telco.duckdb"


def load_clean() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
    return df


def main():
    df = load_clean()
    scores = pd.DataFrame(
        {"customerID": df["customerID"], "churn_prob": score_all(df).round(4)}
    )
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE customers AS SELECT * FROM df")
    con.execute("CREATE OR REPLACE TABLE customer_scores AS SELECT * FROM scores")
    n = con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    m = con.execute("SELECT COUNT(*) FROM customer_scores").fetchone()[0]
    print(f"customers: {n} rows, customer_scores: {m} rows")
    con.close()


if __name__ == "__main__":
    main()