from agent.db import run_query

TOOLS = [
       {
           "type": "function",
           "function": {
               "name": "query_customers",
               "description": (
                   "Run ONE read-only SQL query (SELECT or WITH only) on the DuckDB "
                   "table `customers` (Telco customers, one row per customer). "
                   "Returns at most 50 rows plus a `truncated` flag."
               ),
               "parameters": {
                   "type": "object",
                   "properties": {
                       "sql": {"type": "string", "description": "A single SELECT/WITH query."}
                   },
                   "required": ["sql"],
               },
           },
       }
]


def dispatch(name: str, args: dict) -> dict:
    """Run a tool by name. Always returns a dict, never raises."""
    if name == "query_customers":
       return run_query(args.get("sql", ""))
    return {"error": f"Unknown tool: {name}"}