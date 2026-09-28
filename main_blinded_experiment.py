import json
import time
from pathlib import Path

from ollama import Client

from experiment_harness import (
    FailureType,
    call_tool,
)


MODEL = "qwen3:4b"

OUTPUT_PATH = Path(
    "G:/research/main_blinded_experiment_log.json"
)

SCENARIO_PATH = Path(
    "G:/research/scenarios.json"
)


def ask_model(client, messages):
    response = client.chat(
        model=MODEL,
        messages=messages,
        format="json",
        think=False,
        options={
            "num_predict": 256,
            "num_ctx": 2048,
        },
        keep_alive=0,
    )

    text = response.message.content or ""

    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        return None, text


def make_condition_context(
    condition_name,
    scenario,
    failed_result,
):
    tool_name = scenario["tool_name"]
    arguments = scenario["arguments"]

    if condition_name == "no_history":
        return (
            "The previous tool attempt failed.\n"
            "No execution history is available."
        )

    if condition_name == "raw_history":
        return (
            "Previous conversation:\n"
            f"User task: {scenario['task']}\n"
            f"Agent attempted tool: {tool_name}\n"
            f"Agent submitted arguments: {arguments}\n"
            f"Tool response message: {failed_result.message}\n"
            f"Tool response output: {failed_result.output}\n"
            "The attempt did not complete successfully."
        )

    if condition_name == "plain_log":
        return (
            "Execution log:\n"
            f"task={scenario['task']}\n"
            f"tool={tool_name}\n"
            f"arguments={json.dumps(arguments)}\n"
            f"message={failed_result.message}\n"
            f"output={json.dumps(failed_result.output)}\n"
            "status=failed"
        )

    if condition_name == "structured_provenance":
        provenance = {
            "task": scenario["task"],
            "attempt": {
                "tool_name": tool_name,
                "input_arguments": arguments,
            },
            "observed_result": {
                "output": failed_result.output,
                "message": failed_result.message,
            },
            "status": "failed",
        }

        return (
            "Structured execution provenance:\n"
            + json.dumps(provenance, indent=2)
        )

    raise ValueError(
        f"Unknown condition: {condition_name}"
    )


conditions = [
    "no_history",
    "raw_history",
    "plain_log",
    "structured_provenance",
]

scenarios = json.loads(
    SCENARIO_PATH.read_text(encoding="utf-8")
)

client = Client(timeout=300)
results = []

for scenario in scenarios:
    tool_name = scenario["tool_name"]
    arguments = scenario["arguments"]
    failure_name = scenario["failure_type"]

    failed_result = call_tool(
        tool_name,
        arguments,
        FailureType(failure_name),
    )

    for condition_name in conditions:
        print(
            f"Running {scenario['scenario_id']} "
            f"under {condition_name}"
        )

        context = make_condition_context(
            condition_name,
            scenario,
            failed_result,
        )

        prompt = (
            f"Original task:\n{scenario['task']}\n\n"
            f"{context}\n\n"
            "Recover from the failed tool attempt.\n"
            "You may retry the same tool, choose another tool, "
            "or state that recovery is not possible.\n\n"
            "Return JSON only in exactly this form:\n"
            "{\n"
            '  "action": "tool_name_or_no_action",\n'
            '  "arguments": {},\n'
            '  "diagnosis": "short_failure_diagnosis"\n'
            "}\n"
            "Do not repeat the execution record. "
            "Choose one recovery action."
        )

        started = time.perf_counter()

        action, raw_action = ask_model(
            client,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a tool-using agent. "
                        "Recover from failed executions using only "
                        "the evidence shown. Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        latency_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        response_is_json = isinstance(action, dict)

        predicted_action = None
        predicted_arguments = None
        predicted_diagnosis = None

        if response_is_json:
            predicted_action = action.get("action")
            predicted_arguments = action.get("arguments")
            predicted_diagnosis = action.get(
                "diagnosis",
                "",
            )

        tool_correct = (
            predicted_action == tool_name
        )

        arguments_correct = (
            predicted_arguments == arguments
        )

        action_valid = (
            tool_correct
            and arguments_correct
        )

        diagnosis_correct = (
            isinstance(predicted_diagnosis, str)
            and failure_name in predicted_diagnosis.lower()
        )

        recovery_output = None
        retry_success = False

        if action_valid:
            retry_result = call_tool(
                tool_name,
                arguments,
                FailureType.NONE,
            )

            recovery_output = retry_result.output

            retry_success = (
                retry_result.error_type is None
            )

        direct_recovery_score = (
            int(diagnosis_correct)
            + int(action_valid)
        )

        row = {
            "scenario_id": scenario["scenario_id"],
            "tool_name": tool_name,
            "failure_type": failure_name,
            "condition": condition_name,
            "raw_action": raw_action,
            "parsed_action": action,
            "response_is_json": response_is_json,
            "predicted_action": predicted_action,
            "predicted_arguments": predicted_arguments,
            "predicted_diagnosis": predicted_diagnosis,
            "tool_correct": tool_correct,
            "arguments_correct": arguments_correct,
            "action_valid": action_valid,
            "diagnosis_correct": diagnosis_correct,
            "retry_success": retry_success,
            "failure_output": failed_result.output,
            "failure_message": failed_result.message,
            "recovery_output": recovery_output,
            "direct_recovery_score": direct_recovery_score,
            "latency_ms": latency_ms,
        }

        results.append(row)

        print(
            json.dumps(
                {
                    "scenario_id": row["scenario_id"],
                    "condition": row["condition"],
                    "diagnosis_correct": row[
                        "diagnosis_correct"
                    ],
                    "action_valid": row["action_valid"],
                    "retry_success": row["retry_success"],
                    "direct_recovery_score": row[
                        "direct_recovery_score"
                    ],
                    "latency_ms": row["latency_ms"],
                },
                indent=2,
            )
        )

OUTPUT_PATH.write_text(
    json.dumps(results, indent=2),
    encoding="utf-8",
)

print()
print(f"Blinded trials completed: {len(results)}")
print("Expected: 500")
print(f"Log written to: {OUTPUT_PATH}")