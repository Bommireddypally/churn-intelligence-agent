# FILE: agent/answer_check.py
import re
from decimal import Decimal

NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
ALWAYS_OK = {100.0}  # e.g. "x 100" in a percentage formula


def _clean(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)       # fenced code
    text = re.sub(r"`[^`]*`", " ", text)                      # inline code
    text = re.sub(r"(?m)^\s*\d+[.)]\s+", "", text)            # list markers: "1. "
    return text


def _parse(text: str):
    """Return (value, decimals) for every number in text."""
    found = []
    for m in NUM_RE.findall(_clean(text)):
        s = m.replace(",", "")
        decimals = len(s.split(".")[1]) if "." in s else 0
        found.append((float(s), decimals))
    return found


def _tool_numbers(rows):
    nums = []
    for row in rows:
        for v in row:
            if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
                nums.append(float(v))
    return nums


def ungrounded_numbers(answer: str, rows: list, question: str = "") -> list:
    """Numbers in the answer that no tool returned (and the question didn't contain).
    A returned value may be rounded to the precision the answer uses."""
    allowed = _tool_numbers(rows) + [v for v, _ in _parse(question)]
    bad = []
    for value, decimals in _parse(answer):
        if value in ALWAYS_OK:
            continue
        if any(round(a, decimals) == value for a in allowed):
            continue
        bad.append(value)
    return bad