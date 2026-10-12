# Churn Intelligence Agent

An LLM agent that answers questions about Telco customer churn by calling tools over a DuckDB table and a trained churn model. The design rule is simple: **the LLM decides what to look up and say; code decides what is allowed.** The model never executes code, writes to the database, or sends anything.

> **Status: work in progress.** Phase 1 (SQL agent + eval) is done. Phase 2 (model scoring and explanations) is partly done. Offers, the approval UI and deployment are not built yet. See [Status](#status).

## What it will do

Answer questions like *"Who is most likely to churn, why, and what should we offer them?"* by:

1. finding at-risk customers,
2. scoring them with a trained model,
3. explaining the drivers behind each score,
4. drafting a retention offer, and
5. waiting for a human to click Approve before anything counts as "sent".

## Status

| Phase | What | State |
|---|---|---|
| 1 | SQL agent on Telco data (DuckDB), guardrails, tool-calling loop, mini eval | Done |
| 2 | Model scoring (`get_customer`, `encode_row`, `score_row`) | Done, tested |
| 2 | Per-customer explanations (`explain_row`) and the agent tool for it | In progress |
| 3 | `draft_offer`, mock send, Streamlit approval step | Not started |
| 4 | Full eval set (10 cases) and failure analysis | Not started |
| 5 | Deployment on Streamlit Community Cloud, final README | Not started |

## Architecture

```
User question
     |
     v
 Streamlit UI (planned)  --->  Agent loop (agent/loop.py, max 8 steps)
                                   |  model -> tool call -> result -> model
                                   v
                          Tool dispatcher (agent/tools.py)
                  _______________|________________________
                 |                |                       |
        query_customers   explain_prediction (planned)   draft_offer (planned)
                 |                |                       |
        guardrails.py +     model_service.py         offers.py + cap
        read-only DuckDB    (encoders, scaler,       (limits in code)
                            logistic regression)
                                                          |
                                           Human clicks Approve in the UI
                                                          |
                                                 send_offer (mock, code only)
```

Key design choices:

- **Guardrails live in code, not in the prompt.** The SQL check, the read-only database connection and (planned) the discount cap are all enforced by code and covered by tests.
- **Tools take customer IDs, not feature values.** The code looks up the row, so the model cannot mistype features.
- **`send_offer` is not a model tool.** Only the Approve button's code calls it, so approval is enforced by structure.
- **The model may only state churn drivers that `explain_prediction` returned** (planned; the tool is not wired in yet).

## Tools

| Tool | State | Notes |
|---|---|---|
| `query_customers(sql)` | Built | One read-only `SELECT`/`WITH` over the `customers` table, 50-row cap, returns a `truncated` flag |
| `explain_prediction(customer_id)` | In progress | Probability plus top drivers, shown with readable feature values |
| `draft_offer(...)` | Planned | Discount cap and per-request draft limit enforced in code |
| `send_offer` | Planned | Mock only, never exposed to the model |

## Guardrails

Built:

- SQL must start with `SELECT` or `WITH`; one statement only.
- Whole-word keyword blocklist (writes, `ATTACH`, `COPY`, `INSTALL`, `LOAD`, `PRAGMA`, `EXPORT`, `read_*`, `glob`).
- DuckDB is opened `read_only=True`, so a write fails even if the keyword check were bypassed.
- Result rows capped at 50, with a `truncated` flag so the model cannot imply it saw everything.
- Tool errors are returned as data, so the model can read them instead of the loop crashing.
- `temperature=0` and a client timeout.

Planned: maximum discount, allowlist of offer types, at most 5 drafts per request, no bulk send, and logs that contain tool names and counts but no argument values or message text.

## The model

The scoring model comes from a separate project, [churn-mlops](https://github.com/Bommireddypally/churn-mlops). It is a **logistic regression** with per-column label encoders and a standard scaler, saved as separate files in `artifacts/`:

`model.pkl`, `scaler.pkl`, `encoders.pkl`, `feature_columns.json`

Scoring replays the training recipe: label-encode each categorical column, order columns as in `feature_columns.json`, scale, then `predict_proba`. A test checks the per-customer path against an independent vectorized path.

Because the model is linear, each feature's SHAP value has a closed form (coefficient times the scaled value), so explanations need no extra runtime dependency.

## Project structure

```
agent/
  db.py              read-only run_query with row cap
  guardrails.py      check_sql
  loop.py            tool-calling loop (max 8 steps)
  model_service.py   load artifacts, encode, score
  prompts.py         schema (read from the DB) + business rules
  tools.py           tool schemas and dispatcher
artifacts/           model, scaler, encoders, feature order
data/telco_churn.csv
evals/               cases.json, run_evals.py, show_failures.py, RESULTS.md
scripts/build_db.py  CSV -> DuckDB (cleans TotalCharges)
tests/               guardrails, run_query, data, model service, eval cases
```

## Setup (Windows `cmd`)

`requirements.txt` is not written yet (Phase 5). For now:

```
git clone https://github.com/Bommireddypally/churn-intelligence-agent.git
cd churn-intelligence-agent
python -m venv venv
venv\Scripts\activate
pip install duckdb pandas openai python-dotenv pytest joblib==1.5.3 scikit-learn==1.8.0
```

Create a `.env` file (never commit it):

```
GROQ_API_KEY=your_key
GROQ_MODEL=a_groq_model_that_supports_tool_calling
```

Build the database and run the tests:

```
python scripts\build_db.py
python -m pytest -q
```

Ask the agent a question:

```
python -c "from agent.loop import run_agent; r = run_agent('What is the churn rate by contract type?'); print(r['answer']); print(r['trace'])"
```

Pickles must be loaded with the scikit-learn version that wrote them (1.8.0). The `artifacts/` files are copied from the churn-mlops project.

## Evaluation

The eval compares the **result rows of the agent's last SQL query** with the rows from a hand-written gold query (values compared after rounding to 2 decimals; extra columns allowed; wrong or missing values are not). A trap question with no answer in the data is graded by hand.

| Run | Change | Auto score | Trap case |
|---|---|---|---|
| v8_baseline | none (first clean baseline) | 4/5 | fail |
| v9_arith | prompt rule: do all arithmetic in SQL | 4/5 | fail |

Earlier runs are excluded: four gold queries were still placeholders, so those scores measured nothing. A guard test now fails if any gold query errors or case ids repeat.

## Known issues (open)

- **`churn_rate`:** the model fetches the two counts and divides them itself, answering "about 26.5%" instead of the SQL-computed 26.54. A prompt rule asking for SQL-side arithmetic was loaded and ignored, so prompt rules alone are not reliable here.
- **Trap question ("customers churned last month"):** the table has no date column, yet the agent sometimes substitutes a different question (for example, tenure of one month) and answers with a real but irrelevant number.
- **Currency:** the agent sometimes prints a `$` sign although the data has no currency.
- **Causal language:** the agent sometimes suggests causes ("could significantly reduce churn") that the data does not support.

## Limitations

- **Sending is a mock.** The Telco data has no contact details, so nothing is ever emailed.
- **Scores are in-sample.** The model was trained on all 7,043 rows with no holdout, so a customer's score is not an out-of-sample prediction.
- **Label-encoded categoricals.** The linear model treats each encoded category as a number, so contributions for multi-valued columns (for example payment method) reflect that ordering rather than a true per-category effect.
- **No time dimension.** The data is a snapshot, so questions about periods or trends cannot be answered.
- **Small eval.** Five automatic cases and one manual case so far; scores are indicative, not statistically meaningful.
- **Free tiers.** The LLM runs on Groq's free tier and is subject to its rate limits; runs are close to, but not perfectly, repeatable.

## Roadmap

1. Finish `explain_row` and wire it in as `explain_prediction`; add per-customer scores to the database build.
2. `draft_offer` with the cap and limits, plus the Streamlit approval page.
3. Grow the eval to 10 cases (tool choice, refusals such as an over-cap offer or "email every customer", and a second, different unanswerable question) and write the failure analysis.
4. `requirements.txt`, deployment on Streamlit Community Cloud, final README and pitch.
