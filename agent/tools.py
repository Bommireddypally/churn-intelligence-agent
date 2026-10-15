# FILE: agent/tools.py
from agent import model_service
from agent.db import run_query
from agent.offers import MAX_DISCOUNT_PCT, OFFER_TYPES, MAX_DRAFTS_PER_REQUEST

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
    {
        "type": "function",
        "function": {
            "name": "draft_offer",
            "description": (
                "Create a DRAFT retention offer for ONE customer. Nothing is sent: "
                "a human must approve the draft in the UI. "
                f"Maximum discount {MAX_DISCOUNT_PCT} percent; at most "
                f"{MAX_DRAFTS_PER_REQUEST} drafts per request. If the message "
                "mentions a percentage it must equal discount_pct."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "offer_type": {"type": "string", "enum": list(OFFER_TYPES)},
                    "discount_pct": {"type": "number", "description": "Percent, 0 to the maximum."},
                    "message": {"type": "string", "description": "Short customer-facing message."},
                },
                "required": ["customer_id", "offer_type", "discount_pct", "message"],
            },
        },
    },
]


def dispatch(name: str, args: dict, store=None) -> dict:
    """Run a tool by name. Always returns a dict, never raises.
    `send_offer` is deliberately not a tool: only the UI's Approve button sends."""
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
    if name == "draft_offer":
        if store is None:
            return {"error": "Drafting is not available in this context"}
        return store.draft(
            args.get("customer_id"),
            args.get("offer_type"),
            args.get("discount_pct"),
            args.get("message"),
        )
    return {"error": f"Unknown tool: {name}"}