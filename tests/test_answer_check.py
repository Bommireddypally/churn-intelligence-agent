# FILE: tests/test_answer_check.py
from agent.answer_check import ungrounded_numbers


def test_grounded_counts_with_commas():
    assert ungrounded_numbers("There are 7,043 customers, 1,869 churned.", [(7043, 1869)]) == []


def test_computed_rate_is_flagged():
    assert ungrounded_numbers("The churn rate is 26.5%.", [(7043, 1869)]) == [26.5]


def test_rounding_of_returned_value_is_ok():
    assert ungrounded_numbers("About 26.5% churned.", [(26.54,)]) == []
    assert ungrounded_numbers("About 27% churned.", [(26.54,)]) == []


def test_hundred_and_question_numbers_allowed():
    assert ungrounded_numbers("Top 5 shown, x 100", [(1,)], question="List the top 5") == []


def test_code_blocks_and_list_markers_ignored():
    text = "1. First point\n```sql\nSELECT 99 FROM t\n```"
    assert ungrounded_numbers(text, [(7,)]) == []