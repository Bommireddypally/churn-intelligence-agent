from agent.db import run_query


def test_total_charges_is_numeric():
    r = run_query("SELECT typeof(TotalCharges) AS t, COUNT(*) AS n FROM customers GROUP BY 1")
    assert r["rows"] == [("DOUBLE", 7043)]