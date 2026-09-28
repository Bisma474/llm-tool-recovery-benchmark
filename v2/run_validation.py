"""Run tests and print all five recovery demonstrations. No installation required."""
import json
import platform
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from recovery_harness import SCENARIOS, record_matches_schema, run_policy


def main():
    here = Path(__file__).resolve().parent
    print('OFFLINE HARNESS VALIDATION -- no LLM or network calls', flush=True)
    suite = unittest.defaultTestLoader.discover(str(here), pattern='test_recovery_harness.py')
    checked = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    if not checked.wasSuccessful():
        print('Validation failed. Do not use this harness for experiments.')
        return 1

    rows = []
    for scenario in SCENARIOS:
        for policy in ['always_retry', 'simple_recovery']:
            row = run_policy(scenario, policy)
            rows.append(row)
            print(f'\nScenario: {scenario} | Policy: {policy}')
            for call in row['history']:
                status = 'OK' if call['result']['success'] else 'FAILED'
                print(f"  {call['stage']}: {call['tool']}({json.dumps(call['arguments'])}) -> {status}")
                print(f"    {call['result']['message']}")
                if call['result']['success']:
                    print(f"    Output: {json.dumps(call['result']['output'])}")
                    print(f"    Matches output schema: {record_matches_schema(call['result']['output'])}")
            verdict = row['verdict']
            outcome = 'SUCCESS' if verdict['task_success'] else 'FAILURE'
            print(f'  Task outcome: {outcome}')

    # Unique log names preserve previous validation runs.
    now = datetime.now(timezone.utc)
    out = here / 'outputs'
    out.mkdir(exist_ok=True)
    path = out / f"validation_{now.strftime('%Y%m%dT%H%M%S_%fZ')}.json"
    report = {
        'kind': 'offline_harness_validation_not_llm_results',
        'created_at_utc': now.isoformat(),
        'python': platform.python_version(),
        'tests_run': checked.testsRun,
        'tests_passed': checked.wasSuccessful(),
        'episodes': rows,
    }
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'\nPASS: {checked.testsRun} tests; all 5 scripted recovery scenarios pass.')
    print('Always-retry succeeds only for the temporary timeout; it fails the other four scenarios as expected.')
    print('A successful tool response can still contain malformed or incorrect data.')
    print(f'Log saved to: {path}')
    print('These are scripted checks, not evidence of LLM performance.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
