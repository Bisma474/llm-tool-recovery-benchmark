import json
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


class FailureType(str, Enum):
    NONE = "none"
    INVALID_PARAMETER = "invalid_parameter"
    TIMEOUT = "timeout"
    UNAVAILABLE_TOOL = "unavailable_tool"
    MALFORMED_OUTPUT = "malformed_output"
    MISLEADING_OUTPUT = "misleading_output"


@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: object
    error_type: str | None = None
    message: str | None = None
    latency_ms: float = 0.0


def make_result(
    name,
    started,
    output=None,
    success=True,
    error_type=None,
    message=None,
):
    return ToolResult(
        tool_name=name,
        success=success,
        output=output,
        error_type=error_type,
        message=message,
        latency_ms=round(
            (time.perf_counter() - started) * 1000,
            3,
        ),
    )


def simulated_failure(name, started, failure):
    return make_result(
        name,
        started,
        None,
        False,
        failure.value,
        f"simulated {failure.value}",
    )


def apply_failure(name, started, output, failure):
    if failure in {
        FailureType.INVALID_PARAMETER,
        FailureType.TIMEOUT,
        FailureType.UNAVAILABLE_TOOL,
    }:
        return simulated_failure(name, started, failure)

    if failure == FailureType.MALFORMED_OUTPUT:
        output = {"unexpected": [output]}

    if failure == FailureType.MISLEADING_OUTPUT:
        output = "This output is valid-looking but irrelevant."

    return make_result(name, started, output)


def calculator(args, failure):
    started = time.perf_counter()

    values = {
        "5 + 2": 7,
        "27 * 14": 378,
        "100 / 4": 25,
        "9 - 3": 6,
        "12 * 12": 144,
    }

    expression = args.get("expression")

    if expression not in values:
        return make_result(
            "calculator",
            started,
            None,
            False,
            "invalid_parameter",
            "unsupported expression",
        )

    return apply_failure(
        "calculator",
        started,
        values[expression],
        failure,
    )


def document_search(args, failure):
    started = time.perf_counter()

    documents = {
        "provenance": (
            "Execution provenance records actions, "
            "inputs, outputs, and failure information."
        ),
        "heart failure": (
            "Heart failure is a clinical syndrome "
            "involving impaired cardiac pumping."
        ),
        "tool recovery": (
            "Tool recovery means diagnosing a failure "
            "and selecting an appropriate next action."
        ),
        "malformed output": (
            "Malformed output does not follow the expected format."
        ),
        "agent reliability": (
            "Agent reliability measures correct and consistent behavior."
        ),
    }

    query = args.get("query")

    if query not in documents:
        return make_result(
            "document_search",
            started,
            None,
            False,
            "invalid_parameter",
            "document query not found",
        )

    return apply_failure(
        "document_search",
        started,
        documents[query],
        failure,
    )


def database_lookup(args, failure):
    started = time.perf_counter()

    records = {
        101: {"name": "Amina", "status": "active"},
        202: {"name": "Bilal", "status": "inactive"},
        303: {"name": "Sara", "status": "active"},
        404: {"name": "Usman", "status": "inactive"},
        505: {"name": "Hina", "status": "active"},
    }

    record_id = args.get("record_id")

    if record_id not in records:
        return make_result(
            "database_lookup",
            started,
            None,
            False,
            "invalid_parameter",
            "record does not exist",
        )

    return apply_failure(
        "database_lookup",
        started,
        records[record_id],
        failure,
    )


def file_reader(args, failure):
    started = time.perf_counter()

    files = {
        "study_notes_1.txt": (
            "The pilot study uses deterministic tools "
            "and four history conditions."
        ),
        "study_notes_2.txt": (
            "Invalid parameters occur when inputs use the wrong format."
        ),
        "study_notes_3.txt": (
            "Timeouts occur when a tool does not respond in time."
        ),
        "study_notes_4.txt": (
            "Malformed output does not match the expected schema."
        ),
        "study_notes_5.txt": (
            "Misleading output looks valid but does not answer the task."
        ),
    }

    filename = args.get("filename")

    if filename not in files:
        return make_result(
            "file_reader",
            started,
            None,
            False,
            "invalid_parameter",
            "unknown filename",
        )

    return apply_failure(
        "file_reader",
        started,
        files[filename],
        failure,
    )


def data_analysis(args, failure):
    started = time.perf_counter()
    values = args.get("values")

    if (
        not isinstance(values, list)
        or not values
        or not all(
            isinstance(value, (int, float))
            for value in values
        )
    ):
        return make_result(
            "data_analysis",
            started,
            None,
            False,
            "invalid_parameter",
            "values must be a nonempty numeric list",
        )

    output = {
        "count": len(values),
        "mean": sum(values) / len(values),
        "minimum": min(values),
        "maximum": max(values),
    }

    return apply_failure(
        "data_analysis",
        started,
        output,
        failure,
    )


HANDLERS = {
    "calculator": calculator,
    "document_search": document_search,
    "database_lookup": database_lookup,
    "file_reader": file_reader,
    "data_analysis": data_analysis,
}


def call_tool(name, arguments, failure=FailureType.NONE):
    if name not in HANDLERS:
        return ToolResult(
            name,
            False,
            None,
            "unavailable_tool",
            "unknown tool",
            0.0,
        )

    return HANDLERS[name](arguments, failure)


def run_pilot():
    cases = [
        (
            "calculator",
            {"expression": "5 + 2"},
            FailureType.NONE,
        ),
        (
            "calculator",
            {"expression": "27 * 14"},
            FailureType.NONE,
        ),
        (
            "document_search",
            {"query": "provenance"},
            FailureType.NONE,
        ),
        (
            "database_lookup",
            {"record_id": 303},
            FailureType.NONE,
        ),
        (
            "file_reader",
            {"filename": "study_notes_4.txt"},
            FailureType.NONE,
        ),
        (
            "data_analysis",
            {"values": [2, 4, 6, 8]},
            FailureType.NONE,
        ),
        (
            "calculator",
            {"expression": "5 + 2"},
            FailureType.MALFORMED_OUTPUT,
        ),
    ]

    log_path = Path("pilot_tool_log.jsonl")

    with log_path.open("w", encoding="utf-8") as log_file:
        for name, arguments, failure in cases:
            tool_result = call_tool(
                name,
                arguments,
                failure,
            )

            row = {
                "task_id": f"pilot_{name}_{failure.value}",
                "tool_name": name,
                "arguments": arguments,
                "failure_category": failure.value,
                "result": asdict(tool_result),
            }

            log_file.write(
                json.dumps(row) + "\n"
            )

            print(
                json.dumps(
                    row,
                    indent=2,
                )
            )

    print(
        f"Pilot log written to: "
        f"{log_path.resolve()}"
    )


if __name__ == "__main__":
    run_pilot()