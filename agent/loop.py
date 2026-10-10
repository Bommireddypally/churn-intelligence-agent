# FILE: agent/loop.py
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agent.answer_check import ungrounded_numbers
from agent.prompts import SYSTEM_PROMPT
from agent.tools import TOOLS, dispatch

load_dotenv()

MAX_STEPS = 8
MAX_ANSWER_RETRIES = 1
MODEL = os.environ["GROQ_MODEL"]

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
    timeout=30.0,
    max_retries=2,
)


def run_agent(question: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    trace = []      # (tool name, arguments) per call, for evals and debugging
    tool_rows = []  # every row any tool returned, for the answer check
    retries = 0
    flagged = []

    for step in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )
        msg = resp.choices[0].message

        # No tool requested -> the model wants to give its final answer
        if not msg.tool_calls:
            flagged = ungrounded_numbers(msg.content or "", tool_rows, question)
            if flagged and retries < MAX_ANSWER_RETRIES:
                retries += 1
                messages.append(msg)
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your answer contains numbers that no tool returned: {flagged}. "
                            "Run a query that returns them (do the arithmetic inside SQL), "
                            "or remove them from your answer."
                        ),
                    }
                )
                continue
            return {
                "answer": msg.content,
                "steps": step + 1,
                "trace": trace,
                "flagged": flagged,
            }

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
                result = dispatch(call.function.name, args)

            if isinstance(result, dict) and "rows" in result:
                tool_rows.extend(result["rows"])

            trace.append((call.function.name, args))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    return {
        "answer": "Stopped: step limit reached.",
        "steps": MAX_STEPS,
        "trace": trace,
        "flagged": flagged,
    }