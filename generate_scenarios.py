import json
from pathlib import Path


tools = {
    "calculator": [
        {
            "task": "Calculate 5 + 2.",
            "arguments": {"expression": "5 + 2"},
        },
        {
            "task": "Calculate 27 * 14.",
            "arguments": {"expression": "27 * 14"},
        },
        {
            "task": "Calculate 100 / 4.",
            "arguments": {"expression": "100 / 4"},
        },
        {
            "task": "Calculate 9 - 3.",
            "arguments": {"expression": "9 - 3"},
        },
        {
            "task": "Calculate 12 * 12.",
            "arguments": {"expression": "12 * 12"},
        },
    ],
    "document_search": [
        {
            "task": "Find information about execution provenance.",
            "arguments": {"query": "provenance"},
        },
        {
            "task": "Find information about heart failure.",
            "arguments": {"query": "heart failure"},
        },
        {
            "task": "Find information about tool recovery.",
            "arguments": {"query": "tool recovery"},
        },
        {
            "task": "Find information about malformed output.",
            "arguments": {"query": "malformed output"},
        },
        {
            "task": "Find information about agent reliability.",
            "arguments": {"query": "agent reliability"},
        },
    ],
    "database_lookup": [
        {
            "task": "Look up database record 101.",
            "arguments": {"record_id": 101},
        },
        {
            "task": "Look up database record 202.",
            "arguments": {"record_id": 202},
        },
        {
            "task": "Look up database record 303.",
            "arguments": {"record_id": 303},
        },
        {
            "task": "Look up database record 404.",
            "arguments": {"record_id": 404},
        },
        {
            "task": "Look up database record 505.",
            "arguments": {"record_id": 505},
        },
    ],
    "file_reader": [
        {
            "task": "Read study notes file 1.",
            "arguments": {"filename": "study_notes_1.txt"},
        },
        {
            "task": "Read study notes file 2.",
            "arguments": {"filename": "study_notes_2.txt"},
        },
        {
            "task": "Read study notes file 3.",
            "arguments": {"filename": "study_notes_3.txt"},
        },
        {
            "task": "Read study notes file 4.",
            "arguments": {"filename": "study_notes_4.txt"},
        },
        {
            "task": "Read study notes file 5.",
            "arguments": {"filename": "study_notes_5.txt"},
        },
    ],
    "data_analysis": [
        {
            "task": "Calculate summary statistics for 2, 4, 6, and 8.",
            "arguments": {"values": [2, 4, 6, 8]},
        },
        {
            "task": "Calculate summary statistics for 10, 20, and 30.",
            "arguments": {"values": [10, 20, 30]},
        },
        {
            "task": "Calculate summary statistics for 1, 3, 5, 7, and 9.",
            "arguments": {"values": [1, 3, 5, 7, 9]},
        },
        {
            "task": "Calculate summary statistics for 100, 150, and 200.",
            "arguments": {"values": [100, 150, 200]},
        },
        {
            "task": "Calculate summary statistics for 12, 18, 24, and 30.",
            "arguments": {"values": [12, 18, 24, 30]},
        },
    ],
}


failure_types = [
    "invalid_parameter",
    "timeout",
    "unavailable_tool",
    "malformed_output",
    "misleading_output",
]


scenarios = []
scenario_number = 1

for tool_name, examples in tools.items():
    for failure_type in failure_types:
        for example_number, example in enumerate(examples, start=1):
            scenario = {
                "scenario_id": f"scenario_{scenario_number:03d}",
                "tool_name": tool_name,
                "example_number": example_number,
                "failure_type": failure_type,
                "task": example["task"],
                "arguments": example["arguments"],
                "expected_recovery": (
                    "Diagnose the failure, correct the action when "
                    "possible, and complete the original task using "
                    "supported evidence."
                ),
            }

            scenarios.append(scenario)
            scenario_number += 1


output_path = Path("scenarios.json")
output_path.write_text(
    json.dumps(scenarios, indent=2),
    encoding="utf-8",
)

print(f"Created {len(scenarios)} scenarios.")
print(f"Saved to: {output_path.resolve()}")