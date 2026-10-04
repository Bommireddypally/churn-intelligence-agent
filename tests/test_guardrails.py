import pytest
from agent.guardrails import check_sql, GuardrailError


def test_allows_select():
    assert check_sql("SELECT COUNT(*) FROM customers")


def test_allows_with():
    assert check_sql("WITH t AS (SELECT * FROM customers) SELECT COUNT(*) FROM t")


def test_allows_trailing_semicolon():
    assert check_sql("SELECT 1;")


def test_no_false_positive_on_column_names():
    assert check_sql("SELECT customerID, TotalCharges, StreamingTV FROM customers")


@pytest.mark.parametrize("bad", [
    "DROP TABLE customers",
   "DELETE FROM customers",
       "UPDATE customers SET Churn = 'No'",
       "SELECT 1; DROP TABLE customers",
       "SELECT 1; SELECT 2",
       "ATTACH 'x.db'",
       "COPY customers TO 'out.csv'",
       "SELECT * FROM read_csv('data/telco_churn.csv')",
       "",
])
def test_blocks(bad):
    with pytest.raises(GuardrailError):
       check_sql(bad)