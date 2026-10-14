# FILE: agent/tools.py
from agent import model_service
from agent.db import run_query

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_customers",
            "description": (
                "Run ONE read-only SQL query (SELECT or WITH only) on the DuckDB "
                "tables `customers` (Telco customers, one row per customer) and "
                "`customer_scores` (model churn probability per customer). "
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
    },
    {
        "type": "function",
        "function": {
            "name": "explain_prediction",
            "description": (
                "For ONE customer, return the model's estimated churn probability "
                "and the top 5 features pushing it up or down. Use this for any "
                "'why' question about a specific customer. Only features returned "
                "here may be named as drivers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "A customerID, e.g. taken from customer_scores.",
                    }
                },
                "required": ["customer_id"],
            },
        },
    },
]


def dispatch(name: str, args: dict) -> dict:
    """Run a tool by name. Always returns a dict, never raises."""
    if name == "query_customers":
        return run_query(args.get("sql", ""))
    if name == "explain_prediction":
        cid = args.get("customer_id")
        if not isinstance(cid, str) or not cid:
            return {"error": "customer_id (a string) is required"}
        raw = model_service.get_customer(cid)
        if raw is None:
            return {"error": f"Unknown customer_id: {cid}"}
        return model_service.explain_row(raw, top_n=5)
    return {"error": f"Unknown tool: {name}"}