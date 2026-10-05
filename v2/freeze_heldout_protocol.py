"""Write a deterministic manifest for the held-out scenario protocol."""
import argparse
import hashlib
import json
from pathlib import Path

from recovery_harness import HELDOUT_SCENARIOS
from experiment_runner import CONDITIONS, RESPONSE_SCHEMA


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('v2/heldout_protocol.json'))
    args = parser.parse_args()
    scenarios = {key: HELDOUT_SCENARIOS[key] for key in sorted(HELDOUT_SCENARIOS)}
    payload = {
        'protocol': 'heldout_v1',
        'scenario_set': 'heldout',
        'scenario_count': len(scenarios),
        'conditions': CONDITIONS,
        'response_schema': RESPONSE_SCHEMA,
        'scenarios': scenarios,
        'notes': 'Freeze this file before running any held-out model evaluation. Do not change scenarios after observing results.',
    }
    digest = hashlib.sha256(canonical(payload).encode('utf-8')).hexdigest()
    payload['protocol_sha256'] = digest
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(f'Frozen {len(scenarios)} scenarios across {len(CONDITIONS)} conditions.')
    print(f'Protocol SHA-256: {digest}')
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
