# FILE: app.py
import os
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Churn Intelligence Agent", layout="wide")

# --- Startup: secrets and database ---------------------------------------
# On Streamlit Cloud the Groq settings come from the app's Secrets; locally from .env.
try:
    for _key in ("GROQ_API_KEY", "GROQ_MODEL"):
        if _key not in os.environ and _key in st.secrets:
            os.environ[_key] = st.secrets[_key]
except Exception:
    pass  # no secrets file locally: .env is used instead

# The .duckdb file is not in git, so build it on first run (about a second).
if not (Path(__file__).parent / "data" / "telco.duckdb").exists():
    from scripts.build_db import main as build_db

    build_db()

from agent.loop import run_agent  # noqa: E402  (must come after the setup above)
from agent.offers import DraftStore, MAX_DISCOUNT_PCT, MAX_DRAFTS_PER_REQUEST  # noqa: E402

# --- Page ----------------------------------------------------------------
st.title("Churn Intelligence Agent")
st.warning(
    "Demo on the public Telco dataset. Sending is a MOCK: the data has no contact "
    "details, so nothing is ever emailed. Churn scores are model estimates."
)

if "store" not in st.session_state:
    st.session_state.store = DraftStore()
    st.session_state.history = []
store: DraftStore = st.session_state.store

with st.sidebar:
    st.header("Guardrails (enforced in code)")
    st.write(f"- Max discount: {MAX_DISCOUNT_PCT}%")
    st.write(f"- Max drafts per request: {MAX_DRAFTS_PER_REQUEST}")
    st.write("- Nothing is sent without your click")
    st.write("- Read-only database")

left, right = st.columns([3, 2])

with left:
    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.write(turn["q"])
        with st.chat_message("assistant"):
            st.markdown(turn["a"])
            if turn["tools"]:
                st.caption("Tools used: " + ", ".join(turn["tools"]))

    question = st.chat_input(
        "Ask about churn, e.g. 'Which 3 customers are most likely to churn and why?'"
    )
    if question:
        with st.spinner("Thinking..."):
            try:
                out = run_agent(question, store=store)
                answer, tools = out["answer"], [name for name, _ in out["trace"]]
            except Exception as e:
                answer = f"Something went wrong ({type(e).__name__}). Try again in a moment."
                tools = []
        st.session_state.history.append({"q": question, "a": answer, "tools": tools})
        st.rerun()

with right:
    st.subheader("Draft offers")
    if not store.drafts:
        st.caption("No drafts yet.")
    for d in store.drafts:
        with st.container(border=True):
            st.markdown(f"**{d['id']}** · customer `{d['customer_id']}`")
            st.write(f"{d['offer_type']} · {d['discount_pct']}%")
            st.write(d["message"])
            if d["status"] == "drafted":
                if st.button("Approve (mock send)", key=f"approve_{d['id']}"):
                    store.approve(d["id"])
                    st.rerun()
            else:
                st.success(d["status"])