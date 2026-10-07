import duckdb
import pandas as pd

CSV_PATH = "data/telco_churn.csv"
DB_PATH = "data/telco.duckdb"


def load_clean() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce").fillna(0)
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