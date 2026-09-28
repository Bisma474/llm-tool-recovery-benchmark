import json
import time
from pathlib import Path

from ollama import Client


MODEL = "qwen3:4b"


def calculator(expression: str) -> str:
    values = {
        "5 + 2": "7",
        "27 * 14": "378",
    }

    return values.get(
        expression,
        "Rejected: unsupported expression.",
    )


failure = {
    "tool_name": "calculator",
    "input_arguments": {
        "expression": "5 + 2"
    },
    "tool_output": {
        "unexpected": [7]
    },
    "error_type": "malformed_output",
    "failed_step": (
        "The calculator returned an invalid output structure."
    ),
}


conditions = {
    "no_history": (
        "The calculator tool failed. "
        "Diagnose the failure and recover."
    ),

    "raw_history": (
        "Previous conversation:\n"
        "User: Calculate 5 + 2.\n"
        "Assistant: I called calculator with expression 5 + 2.\n"
        "Calculator: {\"unexpected\": [7]}\n\n"
        "The calculator tool failed. "
        "Diagnose the failure and recover."
    ),

    "plain_log": (
        "Execution log:\n"
        "1. Tool selected: calculator\n"
        "2. Input: expression = 5 + 2\n"
        "3. Output: {\"unexpected\": [7]}\n"
        "4. Error: malformed_output\n\n"
        "Diagnose the failure and recover."
    ),

    "structured_provenance": (
        "Structured execution provenance:\n"
        + json.dumps(failure, indent=2)
        + "\n\nDiagnose the failure and recover."
    ),
}


client = Client(timeout=300)
rows = []


for condition_name, recovery_instruction in conditions.items():
    print(f"\nRunning condition: {condition_name}")

    messages = [
        {
            "role": "system",
            "content": (
                "You are being evaluated on tool-failure recovery. "
                "You must use the calculator tool to recover. "
                "Call the calculator with expression exactly '5 + 2'. "
                "Do not calculate mentally. "
                "Do not invent tool results. "
                "After the tool returns, provide a short final answer."
            ),
        },
        {
            "role": "user",
            "content": (
                "The original task was: calculate 5 + 2.\n\n"
                + recovery_instruction
                + "\n\n"
                "Your recovery action must be to call the calculator "
                "tool now with expression exactly '5 + 2'."
            ),
        },
    ]

    started = time.perf_counter()

    response = client.chat(
        model=MODEL,
        messages=messages,
        tools=[calculator],
        think=False,
        options={
            "num_predict": 256,
            "num_ctx": 2048,
        },
        keep_alive=0,
    )

    assistant_message = response.message
    tool_calls = assistant_message.tool_calls or []
    tool_results = []

    if tool_calls:
        messages.append(assistant_message)

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        if isinstance(arguments, str):
            arguments = json.loads(arguments)

        if tool_name == "calculator":
            output = calculator(**arguments)

            tool_results.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "output": output,
            })

            messages.append({
                "role": "tool",
                "tool_name": tool_name,
                "content": output,
            })

    final_text = assistant_message.content or ""

    if tool_results:
        final_response = client.chat(
            model=MODEL,
            messages=messages,
            think=False,
            options={
                "num_predict": 256,
                "num_ctx": 2048,
            },
            keep_alive=0,
        )

        final_text = final_response.message.content or ""

    elapsed_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    row = {
        "condition": condition_name,
        "failure_type": "malformed_output",
        "tool_calls": tool_results,
        "final_answer": final_text,
        "latency_ms": elapsed_ms,
    }

    rows.append(row)
    print(json.dumps(row, indent=2))


Path("recovery_pilot_log.json").write_text(
    json.dumps(rows, indent=2),
    encoding="utf-8",
)

print("\nRecovery pilot complete.")
print("Log written to: recovery_pilot_log.json")