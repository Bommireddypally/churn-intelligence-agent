# FILE: agent/loop.py
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agent.offers import DraftStore
from agent.prompts import SYSTEM_PROMPT
from agent.tools import TOOLS, dispatch

load_dotenv()

MAX_STEPS = 8
MODEL = os.environ["GROQ_MODEL"]

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
    timeout=30.0,
    max_retries=2,
)


def run_agent(question: str, store: DraftStore | None = None) -> dict:
    store = store if store is not None else DraftStore()
    store.new_request()  # the per-request draft limit starts fresh

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    trace = []  # (tool name, arguments) per call, for evals and debugging

    for step in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            return {"answer": msg.content, "steps": step + 1, "trace": trace}

        messages.append(msg)

        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments)
                if not isinstance(args, dict):
                    raise TypeError("arguments must be a JSON object")
            except (json.JSONDecodeError, TypeError):
                args = {}
                result = {"error": "Bad arguments"}
            else:
                result = dispatch(call.function.name, args, store=store)

            trace.append((call.function.name, args))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    return {"answer": "Stopped: step limit reached.", "steps": MAX_STEPS, "trace": trace}