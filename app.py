# FILE: app.py
import streamlit as st

from agent.loop import run_agent
from agent.offers import DraftStore, MAX_DISCOUNT_PCT, MAX_DRAFTS_PER_REQUEST

st.set_page_config(page_title="Churn Intelligence Agent", layout="wide")
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