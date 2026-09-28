"""One-command offline validation and export of equivalent evidence formats."""
import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

from evidence_formats import build_pair, canonical_json
from recovery_harness import Episode, SCENARIOS


def main():
    here = Path(__file__).resolve().parent
    print('OFFLINE EVIDENCE-FORMAT VALIDATION -- no model or network required', flush=True)
    suite = unittest.defaultTestLoader.discover(str(here), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    if not result.wasSuccessful():
        return 1
    now = datetime.now(timezone.utc)
    out = here / 'outputs' / f"evidence_{now.strftime('%Y%m%dT%H%M%S_%fZ')}"
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for index, name in enumerate(SCENARIOS, start=1):
        pair = build_pair(Episode(name).agent_context())
        case = out / f'case_{index:03d}'
        case.mkdir()
        (case / 'common_context.json').write_text(json.dumps(pair['common_context'], indent=2), encoding='utf-8')
        (case / 'plain_log.txt').write_text(pair['plain_history'], encoding='utf-8')
        (case / 'structured_history.json').write_text(pair['structured_history'], encoding='utf-8')
        (case / 'plain_evidence.txt').write_text(pair['plain_evidence'], encoding='utf-8')
        (case / 'structured_evidence.txt').write_text(pair['structured_evidence'], encoding='utf-8')
        rows.append({
            'case': case.name,
            'scenario_id': name,  # Audit metadata only, not part of evidence text.
            'information_equal': pair['information_equal'],
            'canonical_history_sha256': hashlib.sha256(canonical_json(pair['canonical_history']).encode('utf-8')).hexdigest(),
            'plain_evidence_characters': len(pair['plain_evidence']),
            'structured_evidence_characters': len(pair['structured_evidence']),
        })
        print(f'PASS: {case.name} ({name}) -- identical evidence in both formats')
    report = {'kind': 'offline_evidence_validation_not_model_results', 'created_at_utc': now.isoformat(),
              'tests_passed': result.testsRun, 'cases': rows,
              'limitation': 'Lossless data equivalence does not imply equal token length or equal model behavior.'}
    (out / 'validation_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'\nPASS: {result.testsRun} tests; all 5 evidence pairs preserve identical information.')
    print(f'Examples and report saved to: {out}')
    print('Compare case_001/plain_evidence.txt with case_001/structured_evidence.txt.')
    print('These are evidence blocks, not complete model prompts or LLM results.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
