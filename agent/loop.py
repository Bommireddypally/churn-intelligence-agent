import json
import os

from dotenv import load_dotenv
from openai import OpenAI

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

# Placeholder. Step F replaces this with the schema and business rules.
SYSTEM_PROMPT = (
    "You are a churn analytics assistant. Answer questions about the Telco "
    "customers table using the query_customers tool."
)


def run_agent(question: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    trace = []  # (tool name, arguments) per call, for evals and debugging

    for step in range(MAX_STEPS):
        # Ask the model what to do next
        resp = client.chat.completions.create(
               model=MODEL,
               messages=messages,
               tools=TOOLS,
               temperature=0,
        )
        msg = resp.choices[0].message

        # No tool requested -> the model has produced its final answer
        if not msg.tool_calls:
            return {
                "answer": msg.content,
                "steps": step + 1,
                "trace": trace,
            }

        # Add the assistant's tool-call message to the conversation
        messages.append(msg)

        # Execute every tool call the model requested
        for call in msg.tool_calls:
            try:
                # Convert the model's JSON arguments into a Python dict
                args = json.loads(call.function.arguments)
                if not isinstance(args, dict):
                    raise TypeError("arguments must be a JSON object")

            except (json.JSONDecodeError, TypeError):
                args = {}
                result = {"error": "Bad arguments"}

            else:
                # Execute the requested tool
                result = dispatch(call.function.name, args)

            # Record the call for debugging and evals
            trace.append((call.function.name, args))

            # Give the tool result back to the model
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str),
                }
            )

    # The model used all allowed steps without a final answer
    return {
        "answer": "Stopped: step limit reached.",
        "steps": MAX_STEPS,
        "trace": trace,
    }