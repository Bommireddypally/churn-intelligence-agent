import json
from pathlib import Path

import duckdb
import joblib
import numpy as np

from agent.db import DB_PATH

ART = Path(__file__).resolve().parent.parent / "artifacts"

model = joblib.load(ART / "model.pkl")
scaler = joblib.load(ART / "scaler.pkl")
encoders = joblib.load(ART / "encoders.pkl")
with open(ART / "feature_columns.json") as f:
    FEATURES = json.load(f)


def get_customer(customer_id: str) -> dict | None:
    """Fetch one customer's row. The ? placeholder is safe against injection."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        con.execute("SELECT * FROM customers WHERE customerID = ?", [customer_id])
        row = con.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in con.description]
        return dict(zip(cols, row))
    finally:
        con.close()


def encode_row(raw: dict) -> np.ndarray:
    row = []
    for col in FEATURES:
        value = raw[col]
        if col in encoders:
            le = encoders[col]
            if value not in le.classes_:
                raise ValueError(
                    f"Unrecognized value {value!r} for {col!r}. "
                    f"Expected one of: {list(le.classes_)}"
                )
            value = le.transform([value])[0]
        row.append(value)
    return np.array(row, dtype=float)


def score_row(raw: dict) -> float:
    X = encode_row(raw).reshape(1, -1)
    return float(model.predict_proba(scaler.transform(X))[0][1])