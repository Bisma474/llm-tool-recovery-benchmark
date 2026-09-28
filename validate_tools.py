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

unique_cases = {}
for scenario in scenarios:
    key = (
        scenario["tool_name"],
        json.dumps(
            scenario["arguments"],
            sort_keys=True,
        ),
    )
    unique_cases[key] = scenario


results = []
passed = 0
failed = 0

for scenario in unique_cases.values():
    tool_name = scenario["tool_name"]
    arguments = scenario["arguments"]

    result = call_tool(
        tool_name,
        arguments,
        FailureType.NONE,
    )

    passed_case = (
        result.success
        and result.error_type is None
    )

    row = {
        "scenario_id": scenario["scenario_id"],
        "tool_name": tool_name,
        "arguments": arguments,
        "passed": passed_case,
        "output": result.output,
        "error_type": result.error_type,
        "message": result.message,
    }

    results.append(row)

    if passed_case:
        passed += 1
        print(
            f"PASS: {tool_name} "
            f"{arguments}"
        )
    else:
        failed += 1
        print(
            f"FAIL: {tool_name} "
            f"{arguments} "
            f"{result.message}"
        )


output_path = Path(
    "G:/research/normal_tool_validation.json"
)

output_path.write_text(
    json.dumps(results, indent=2),
    encoding="utf-8",
)

print()
print(f"Unique normal cases tested: {len(results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Results saved to: {output_path}")