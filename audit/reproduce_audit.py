"""Read-only audit of original experiments; writes only to audit/outputs.

Run: python audit/reproduce_audit.py
No model calls or third-party dependencies are required.
"""
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiment_harness import call_tool, FailureType

OUT = ROOT / 'audit' / 'outputs'
OUT.mkdir(exist_ok=True)
scenarios = json.loads((ROOT / 'scenarios.json').read_text())
lookup = {s['scenario_id']: s for s in scenarios}
conditions = ['no_history', 'raw_history', 'plain_log', 'structured_provenance']
expected = {(s['scenario_id'], c) for s in scenarios for c in conditions}
summary, checks, examples = [], {}, []
for filename in ['main_experiment_log.json', 'main_blinded_experiment_log.json']:
    rows = json.loads((ROOT / filename).read_text())
    pairs = Counter((r['scenario_id'], r['condition']) for r in rows)
    mismatches = Counter()
    for r in rows:
        s = lookup[r['scenario_id']]
        try:
            parsed = json.loads(r['raw_action'])
        except json.JSONDecodeError:
            parsed = None
        a = parsed if isinstance(parsed, dict) else {}
        action = a.get('action') == s['tool_name'] and a.get('arguments') == s['arguments']
        diag = isinstance(a.get('diagnosis'), str) and s['failure_type'] in a['diagnosis'].lower()
        for key, actual in [('parsed_action', parsed), ('action_valid', action), ('diagnosis_correct', diag)]:
            if r[key] != actual:
                mismatches[key] += 1
        failed = call_tool(s['tool_name'], s['arguments'], FailureType(s['failure_type']))
        if r['failure_output'] != failed.output:
            mismatches['failure_output'] += 1
        normal = call_tool(s['tool_name'], s['arguments'])
        if r['recovery_output'] != (normal.output if action else None):
            mismatches['recovery_output'] += 1
        if 'retry_success' in r and r['retry_success'] != action:
            mismatches['retry_success'] += 1
        if 'direct_recovery_score' in r and r['direct_recovery_score'] != int(action) + int(diag):
            mismatches['direct_recovery_score'] += 1
        if 'recovery_score' in r:
            score = int(diag) + int(action) + int(r['recovery_output'] is not None) + int(bool(r['final_diagnosis_correct'] and r['final_answer']))
            if r['recovery_score'] != score:
                mismatches['recovery_score'] += 1
        normalized = str(a.get('diagnosis', '')).lower().replace('_', ' ').replace('-', ' ')
        if not diag and s['failure_type'].replace('_', ' ') in normalized:
            examples.append({'file': filename, 'scenario_id': r['scenario_id'], 'condition': r['condition'], 'failure_type': s['failure_type'], 'diagnosis': a.get('diagnosis'), 'note': 'Surface-form sensitivity example, not an adjudicated corrected label.'})
    checks[filename] = {'rows': len(rows), 'unique_pairs': len(pairs), 'missing_pairs': len(expected - set(pairs)), 'unexpected_pairs': len(set(pairs) - expected), 'duplicate_pairs': sum(n-1 for n in pairs.values()), 'recomputed_mismatches': dict(mismatches)}
    for c in conditions:
        group = [r for r in rows if r['condition'] == c]
        actions = [r['parsed_action'] if isinstance(r['parsed_action'], dict) else {} for r in group]
        summary.append({'experiment': filename, 'condition': c, 'n': len(group), 'json_objects': sum(isinstance(r['parsed_action'], dict) for r in group), 'required_keys_present': sum(all(k in a for k in ['action','arguments','diagnosis']) for a in actions), 'provenance_shaped_objects': sum(('task' in a and ('attempt' in a or 'input_arguments' in a)) for a in actions), 'action_correct': sum(r['action_valid'] for r in group), 'diagnosis_correct': sum(r['diagnosis_correct'] for r in group), 'direct_score_mean': sum(int(r['action_valid'])+int(r['diagnosis_correct']) for r in group)/len(group)})

normal_pass = 0
leaked_messages = 0
for s in scenarios:
    result = call_tool(s['tool_name'], s['arguments'])
    normal_pass += int(result.success and result.error_type is None)
    failure = call_tool(s['tool_name'], s['arguments'], FailureType(s['failure_type']))
    leaked_messages += int(s['failure_type'] in (failure.message or ''))
checks['harness'] = {'scenarios': len(scenarios), 'unique_base_tasks': len({(s['tool_name'], json.dumps(s['arguments'],sort_keys=True)) for s in scenarios}), 'unchanged_normal_retries_successful': normal_pass, 'scenarios_with_label_in_failure_message': leaked_messages}
checks['surface_form_examples_count'] = len(examples)
with (OUT / 'recomputed_summary.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
(OUT / 'integrity_checks.json').write_text(json.dumps(checks, indent=2))
(OUT / 'diagnosis_surface_form_examples.json').write_text(json.dumps(examples, indent=2))
files = sorted(ROOT.glob('*.py')) + sorted(ROOT.glob('*.json')) + sorted(ROOT.glob('*.jsonl'))
(OUT / 'source_sha256.json').write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}, indent=2))
print(json.dumps(checks, indent=2))
for r in summary:
    print(json.dumps(r))
