import json
from pathlib import Path

from experiment_harness import (
    FailureType,
    call_tool,
)


scenarios_path = Path("G:/research/scenarios.json")
scenarios = json.loads(
    scenarios_path.read_text(encoding="utf-8")
)


expected_errors = {
    "invalid_parameter",
    "timeout",
    "unavailable_tool",
}


results = []
passed = 0
failed = 0

for scenario in scenarios:
    tool_name = scenario["tool_name"]
    arguments = scenario["arguments"]
    failure_name = scenario["failure_type"]

    failure = FailureType(failure_name)

    actual = call_tool(
        tool_name,
        arguments,
        failure,
    )

    if failure_name in expected_errors:
        case_passed = (
            actual.success is False
            and actual.error_type == failure_name
        )

    elif failure_name in {
        "malformed_output",
        "misleading_output",
    }:
        case_passed = (
            actual.success is True
            and actual.output is not None
        )

    else:
        case_passed = False

    row = {
        "scenario_id": scenario["scenario_id"],
        "tool_name": tool_name,
        "failure_type": failure_name,
        "passed": case_passed,
        "success": actual.success,
        "output": actual.output,
        "error_type": actual.error_type,
        "message": actual.message,
    }

    results.append(row)

    if case_passed:
        passed += 1
    else:
        failed += 1
        print("FAIL:")
        print(json.dumps(row, indent=2))


output_path = Path(
    "G:/research/failure_validation.json"
)

output_path.write_text(
    json.dumps(results, indent=2),
    encoding="utf-8",
)

print()
print(f"Failure cases tested: {len(results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Results saved to: {output_path}")