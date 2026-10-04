from pathlib import Path

import duckdb

from agent.guardrails import check_sql, GuardrailError, MAX_ROWS


# Absolute path, so it works no matter which folder you launch from
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "telco.duckdb"


def run_query(sql: str) -> dict:
    try:
        clean = check_sql(sql)
    except GuardrailError as e:
        return {"error": f"Blocked: {e}"}

    con = None
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)

        result = con.execute(
            f"SELECT * FROM ({clean}) LIMIT {MAX_ROWS + 1}"
        )

        rows = result.fetchall()
        columns = [d[0] for d in result.description]

        truncated = len(rows) > MAX_ROWS

        if truncated:
            rows = rows[:MAX_ROWS]

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
        }

    except duckdb.Error as e:
        return {"error": str(e)}

    finally:
        if con is not None:
            con.close()