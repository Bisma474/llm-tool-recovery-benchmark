"""Validate and dry-run the four-condition experiment, without any LLM."""
import csv
import json
import random
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from experiment_runner import CONDITIONS, RESPONSE_SCHEMA, ScriptedBackend, run_episode
from recovery_harness import SCENARIOS


def main():
    here = Path(__file__).resolve().parent
    print('OFFLINE RUNNER VALIDATION -- SCRIPTED RESPONSES, NOT LLM RESULTS', flush=True)
    suite = unittest.defaultTestLoader.discover(str(here), pattern='test_*.py')
    tests = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    if not tests.wasSuccessful():
        return 1
    now = datetime.now(timezone.utc)
    out = here / 'outputs' / f"offline_runner_{now.strftime('%Y%m%dT%H%M%S_%fZ')}"
    out.mkdir(parents=True, exist_ok=False)
    (out / 'response_schema.json').write_text(json.dumps(RESPONSE_SCHEMA, indent=2), encoding='utf-8')
    schedule = [(s, c) for s in SCENARIOS for c in CONDITIONS]
    random.Random(20260926).shuffle(schedule)
    results = []
    with (out / 'scripted_episodes.jsonl').open('w', encoding='utf-8') as log:
        for scenario, condition in schedule:
            row = run_episode(scenario, condition, ScriptedBackend())
            row['source'] = 'scripted_offline_validation'
            row['backend_schema_enforcement_exercised'] = False
            log.write(json.dumps(row) + '\n')
            log.flush()
            results.append(row)
            print(f"{condition} | {scenario} | {'PASS' if row['verdict']['task_success'] else 'FAIL'}")
    with (out / 'scripted_summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['condition', 'history_format', 'requested_response_mode', 'scripted_episodes', 'scripted_successes'])
        for c, (history, mode) in CONDITIONS.items():
            selected = [r for r in results if r['condition'] == c]
            writer.writerow([c, history, mode, len(selected), sum(r['verdict']['task_success'] for r in selected)])
    report = {'kind': 'offline_runner_validation_not_research_results', 'created_at_utc': now.isoformat(),
              'tests_passed': tests.testsRun, 'episodes': len(results), 'order_seed': 20260926,
              'backend': 'ScriptedBackend', 'real_schema_enforcement_tested': False,
              'limitation': 'This checks runner wiring. Scripted success cannot measure format effects or model performance.'}
    (out / 'validation_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if not all(r['verdict']['task_success'] for r in results):
        print('FAIL: unexpected scripted outcome. See saved logs.')
        return 1
    print(f'\nPASS: {tests.testsRun} tests; all {len(results)} scripted episodes completed across A/B/C/D.')
    print(f'Saved to: {out}')
    print('No model was called. Actual schema-constrained generation still needs backend integration.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
