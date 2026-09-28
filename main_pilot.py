import json
import time
from pathlib import Path

from ollama import Client

from experiment_harness import (
    FailureType,
    call_tool,
)


MODEL = "qwen3:4b"


conditions = {
    "no_history": (
        "The tool failed. You only have the latest failure message."
    ),
    "raw_history": (
        "Previous conversation:\n"
        "The agent selected a tool.\n"
        "The tool returned an error."
    ),
    "plain_log": (
        "Execution log:\n"
        "A tool was selected.\n"
        "Arguments were submitted.\n"
        "The tool returned an error."
    ),
    "structured_provenance": (
        "Structured provenance is provided below."
    ),
}


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


scenarios = json.loads(
    Path("G:/research/scenarios.json").read_text(
        encoding="utf-8"
    )
)


requested_cases = {
    ("calculator", "invalid_parameter"),
    ("document_search", "timeout"),
    ("database_lookup", "unavailable_tool"),
    ("file_reader", "malformed_output"),
    ("data_analysis", "misleading_output"),
}


selected = [
    scenario
    for scenario in scenarios
    if (
        scenario["tool_name"],
        scenario["failure_type"],
    ) in requested_cases
]


client = Client(timeout=300)
results = []

for scenario in selected:
    tool_name = scenario["tool_name"]
    arguments = scenario["arguments"]
    failure_name = scenario["failure_type"]
    failure = FailureType(failure_name)

    failed_result = call_tool(
        tool_name,
        arguments,
        failure,
    )

    for condition_name, condition_text in conditions.items():
        print(
            f"Running {scenario['scenario_id']} "
            f"under {condition_name}"
        )

        provenance = {
            "task": scenario["task"],
            "tool_name": tool_name,
            "input_arguments": arguments,
            "tool_output": failed_result.output,
            "error_type": failed_result.error_type,
            "message": failed_result.message,
        }

        if condition_name == "structured_provenance":
            condition_text += "\n" + json.dumps(
                provenance,
                indent=2,
            )

        prompt = (
            f"Original task: {scenario['task']}\n\n"
            f"{condition_text}\n\n"
            "Recover from the failure. Return JSON only with this shape:\n"
            "{\n"
            "  \"action\": \"tool_name\",\n"
            "  \"arguments\": {},\n"
            "  \"diagnosis\": \"failure type\"\n"
            "}\n"
            f"The correct recovery tool is {tool_name}."
        )

        started = time.perf_counter()

        action, raw_action = ask_model(
            client,
            [
                {
                    "role": "system",
                    "content": (
                        "You are an agent recovering from a "
                        "tool failure. Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        action_valid = (
            isinstance(action, dict)
            and action.get("action") == tool_name
            and action.get("arguments") == arguments
        )

        recovery_output = None
        diagnosis_correct = False

        if isinstance(action, dict):
            diagnosis = action.get("diagnosis", "")
            diagnosis_correct = (
                failure_name in diagnosis.lower()
            )

            if action_valid:
                recovery_result = call_tool(
                    tool_name,
                    arguments,
                    FailureType.NONE,
                )
                recovery_output = recovery_result.output

        final_prompt = (
            "You recovered from a tool failure.\n"
            "Return JSON only with this shape:\n"
            "{\n"
            "  \"failure_diagnosis\": \"failure type\",\n"
            "  \"recovery_success\": true or false,\n"
            "  \"final_answer\": \"short final answer\"\n"
            "}\n"
            f"The correct failure type is {failure_name}."
        )

        final_action, final_raw = ask_model(
            client,
            [
                {
                    "role": "system",
                    "content": (
                        "Return valid JSON only. Do not add extra text."
                    ),
                },
                {
                    "role": "user",
                    "content": final_prompt,
                },
            ],
        )

        final_diagnosis_correct = False
        final_recovery_success = False
        final_answer = ""

        if isinstance(final_action, dict):
            final_diagnosis = final_action.get(
                "failure_diagnosis", ""
            )
            final_diagnosis_correct = (
                failure_name in final_diagnosis.lower()
            )

            final_recovery_success = bool(
                final_action.get("recovery_success", False)
            )

            final_answer = final_action.get(
                "final_answer", ""
            )

        elapsed_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        recovery_score = 0

        if diagnosis_correct:
            recovery_score += 1

        if action_valid:
            recovery_score += 1

        if recovery_output is not None:
            recovery_score += 1

        if final_diagnosis_correct and final_answer:
            recovery_score += 1

        row = {
            "scenario_id": scenario["scenario_id"],
            "tool_name": tool_name,
            "failure_type": failure_name,
            "condition": condition_name,
            "raw_action": raw_action,
            "parsed_action": action,
            "action_valid": action_valid,
            "diagnosis_correct": diagnosis_correct,
            "failure_output": failed_result.output,
            "recovery_output": recovery_output,
            "final_action": final_action,
            "final_diagnosis_correct": final_diagnosis_correct,
            "final_recovery_success": final_recovery_success,
            "final_answer": final_answer,
            "recovery_score": recovery_score,
            "latency_ms": elapsed_ms,
        }

        results.append(row)
        print(json.dumps(row, indent=2))


Path("main_pilot_log.json").write_text(
    json.dumps(results, indent=2),
    encoding="utf-8",
)

print()
print(f"Pilot trials completed: {len(results)}")
print("Expected: 20")
print("Log written to: main_pilot_log.json")