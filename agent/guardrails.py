import re

MAX_ROWS = 50

FORBIDDEN_KEYWORDS = [
    "ATTACH",
    "COPY",
    "INSTALL",
    "LOAD",
    "PRAGMA",
    "EXPORT",
    "GLOB",
]


class GuardrailError(Exception):
    pass


def check_sql(sql: str) -> str:
    # 1. Strip whitespace and remove one trailing semicolon
    sql = sql.strip()

    if sql.endswith(";"):
        sql = sql[:-1].rstrip()

    # 2. Empty query
    if not sql:
        raise GuardrailError("empty query")

    # 3. Must start with SELECT or WITH
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise GuardrailError("query must start with SELECT or WITH")

    # 4. Block any remaining semicolons
    if ";" in sql:
        raise GuardrailError("multi-statement query")

    # 5. Block forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", sql, re.IGNORECASE):
            raise GuardrailError(f"forbidden keyword: {keyword}")

    # 6. Block read_csv, read_parquet, etc.
    if re.search(r"\bread_\w+", sql, re.IGNORECASE):
        raise GuardrailError("read_* functions are not allowed")

    # 7. Return cleaned SQL
    return sql