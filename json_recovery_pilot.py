import json
import time
from pathlib import Path

from ollama import Client


MODEL = "qwen3:4b"


def calculator(expression):
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
        "The calculator failed with malformed output. "
        "Recover by selecting the correct tool action."
    ),

    "raw_history": (
        "Previous conversation:\n"
        "User: Calculate 5 + 2.\n"
        "Assistant: I called calculator with expression 5 + 2.\n"
        "Calculator: {\"unexpected\": [7]}\n\n"
        "Recover by selecting the correct tool action."
    ),

    "plain_log": (
        "Execution log:\n"
        "Tool selected: calculator\n"
        "Input: expression = 5 + 2\n"
        "Output: {\"unexpected\": [7]}\n"
        "Error: malformed_output\n\n"
        "Recover by selecting the correct tool action."
    ),

    "structured_provenance": (
        "Structured execution provenance:\n"
        + json.dumps(failure, indent=2)
        + "\n\n"
        "Recover by selecting the correct tool action."
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
                "You are an LLM agent recovering from a tool failure. "
                "Your response must be valid JSON only. "
                "Do not use Markdown. "
                "Select exactly one available tool action. "
                "The only available tool is calculator. "
                "The required expression is exactly 5 + 2."
            ),
        },
        {
            "role": "user",
            "content": (
                "The original task was: calculate 5 + 2.\n\n"
                + recovery_instruction
                + "\n\n"
                "Return exactly this JSON shape:\n"
                "{"
                "\"action\":\"calculator\","
                "\"arguments\":{\"expression\":\"5 + 2\"}"
                "}"
            ),
        },
    ]

    started = time.perf_counter()

    response = client.chat(
        model=MODEL,
        messages=messages,
        format="json",
        think=False,
        options={
            "num_predict": 128,
            "num_ctx": 2048,
        },
        keep_alive=0,
    )

    action_text = response.message.content or ""

    try:
        action = json.loads(action_text)
        action_valid = (
            action.get("action") == "calculator"
            and action.get("arguments", {}).get("expression")
            == "5 + 2"
        )
    except json.JSONDecodeError:
        action = None
        action_valid = False

    tool_output = None

    if action_valid:
        tool_output = calculator(
            action["arguments"]["expression"]
        )

        messages.append({
            "role": "assistant",
            "content": action_text,
        })

        messages.append({
            "role": "user",
            "content": (
                "The tool returned this result:\n"
                + json.dumps({
                    "result": tool_output
                })
                + "\n\n"
                "Return valid JSON only with this shape:\n"
                "{"
                "\"failure_diagnosis\":\"malformed_output\","
                "\"recovery_success\":true,"
                "\"final_answer\":\"5 + 2 = 7\""
                "}"
            ),
        })

        final_response = client.chat(
            model=MODEL,
            messages=messages,
            format="json",
            think=False,
            options={
                "num_predict": 128,
                "num_ctx": 2048,
            },
            keep_alive=0,
        )

        final_text = final_response.message.content or ""
    else:
        final_text = ""

    elapsed_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    row = {
        "condition": condition_name,
        "failure_type": "malformed_output",
        "raw_action": action_text,
        "parsed_action": action,
        "action_valid": action_valid,
        "tool_output": tool_output,
        "final_answer": final_text,
        "latency_ms": elapsed_ms,
    }

    rows.append(row)
    print(json.dumps(row, indent=2))


Path("json_recovery_pilot_log.json").write_text(
    json.dumps(rows, indent=2),
    encoding="utf-8",
)

print("\nJSON recovery pilot complete.")
print("Log written to: json_recovery_pilot_log.json")