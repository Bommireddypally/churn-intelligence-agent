# FILE: tests/test_prompts.py
from agent.prompts import SYSTEM_PROMPT


def test_prompt_builds_and_has_key_parts():
    for part in ["customer_scores", "Do all arithmetic", "call explain_prediction first",
                 "12. Offers", "Maximum discount: 20"]:
        assert part in SYSTEM_PROMPT, part