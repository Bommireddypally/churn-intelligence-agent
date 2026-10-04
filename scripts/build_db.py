import duckdb
import pandas as pd

CSV_PATH = "data/telco_churn.csv"
DB_PATH = "data/telco.duckdb"


def load_clean() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    # YOUR TURN: fix TotalCharges here (the same two lines as in
    # churn-mlops/src/data_prep.py). Do NOT drop customerID this time.
    return df


def main():
    df = load_clean()
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE OR REPLACE TABLE customers AS SELECT * FROM df")
    n = con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    print(f"customers table: {n} rows")
    con.close()


if __name__ == "__main__":
    main()