import duckdb
import pytest

from agent import model_service as ms
from agent.db import DB_PATH


def _all_customers():
    con = duckdb.connect(str(DB_PATH), read_only=True)

    try:
        return con.execute("SELECT * FROM customers").df()
    finally:
        con.close()


def _vectorized_probs(df):
    X = df[ms.FEATURES].copy()

    for col, le in ms.encoders.items():
        if col in X.columns:  # skips the leftover 'Churn' encoder
            X[col] = le.transform(X[col])

    return ms.model.predict_proba(
        ms.scaler.transform(X.to_numpy())
    )[:, 1]


def test_matches_vectorized_path():
    df = _all_customers()

    probs = _vectorized_probs(df)

    for i in [0, 1, 100, 2000, 7000]:
        raw = ms.get_customer(
            df.loc[i, "customerID"]
        )

        assert abs(
            ms.score_row(raw) - probs[i]
        ) < 1e-9


def test_sanity_in_sample_accuracy():
    # Sanity check, not a quality claim:
    # about 0.80 is expected.
    #
    # Near 0.27 or 0.50 means there is likely
    # an encoding or column-order bug.

    df = _all_customers()

    probs = _vectorized_probs(df)

    acc = (
        (probs >= 0.5)
        == (df["Churn"] == "Yes")
    ).mean()

    assert 0.78 < acc < 0.84


def test_unknown_category_raises():
    raw = ms.get_customer(
        _all_customers().loc[0, "customerID"]
    )

    raw["Contract"] = "Lifetime"

    with pytest.raises(ValueError):
        ms.encode_row(raw)


def test_unknown_customer_returns_none():
    assert ms.get_customer("NOT-A-REAL-ID") is None