from agent.db import run_query


def test_count():
    r = run_query("SELECT COUNT(*) AS n FROM customers")
    assert r["rows"][0][0] == 7043


def test_row_limit_and_truncated_flag():
    r = run_query("SELECT * FROM customers")
    assert r["row_count"] == 50 and r["truncated"] is True


def test_small_result_not_truncated():
    r = run_query("SELECT DISTINCT Contract FROM customers")
    assert r["truncated"] is False and r["row_count"] == 3


def test_blocked_returns_error_not_exception():
    assert "error" in run_query("DROP TABLE customers")


def test_bad_sql_returns_error():
    assert "error" in run_query("SELECT nope FROM customers")