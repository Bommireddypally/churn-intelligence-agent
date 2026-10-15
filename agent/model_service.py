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

def explain_row(raw: dict, top_n: int = 5) -> dict:
    """Exact SHAP values for a linear model: coefficient x scaled value.
    The scaler centers every feature, so the base value is the intercept."""
    x_scaled = scaler.transform(encode_row(raw).reshape(1, -1))[0]
    contribs = model.coef_[0] * x_scaled  # log-odds contribution per feature
    order = np.argsort(-np.abs(contribs))[:top_n]
    drivers = [
        {
            "feature": FEATURES[i],
            "value": raw[FEATURES[i]],  # the readable value, not the encoded number
            "contribution": float(round(contribs[i], 4)),
            "direction": "raises churn risk" if contribs[i] > 0 else "lowers churn risk",
        }
        for i in order
    ]
    return {
        "churn_probability": round(score_row(raw), 4),
        "base_logit": float(round(model.intercept_[0], 4)),
        "drivers": drivers,
    }
def score_all(df):
    """Vectorized scores for a customers DataFrame."""
    X = df[FEATURES].copy()
    for col, le in encoders.items():
        if col in X.columns:  # skips the leftover 'Churn' encoder
            X[col] = le.transform(X[col])
    return model.predict_proba(scaler.transform(X.to_numpy()))[:, 1]