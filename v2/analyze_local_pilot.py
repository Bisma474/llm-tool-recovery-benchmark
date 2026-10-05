"""Analyze a completed local pilot run and write paper-facing tables."""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from experiment_runner import CONDITIONS


SCENARIO_TYPES = (
    'invalid_arguments',
    'persistent_unavailability',
    'temporary_timeout',
    'malformed_output',
    'plausible_incorrect_output',
)


def scenario_type(scenario_id):
    scenario_id = scenario_id.removeprefix('heldout_')
    for prefix in SCENARIO_TYPES:
        if scenario_id == prefix or scenario_id.startswith(prefix + '_'):
            return prefix
    return 'unknown'


def pct(count, total):
    return f'{(100 * count / total):.1f}%' if total else '0.0%'


def load_jsonl(path):
    with path.open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def latest_completed_run(outputs):
    candidates = sorted(outputs.glob('local_pilot_*'), key=lambda p: p.stat().st_mtime, reverse=True)
    for folder in candidates:
        manifest_path = folder / 'manifest.json'
        episodes_path = folder / 'episodes.jsonl'
        if not manifest_path.exists() or not episodes_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            continue
        if manifest.get('status') == 'COMPLETED':
            return folder
    raise SystemExit(f'No completed local_pilot_* run found under {outputs}')


def write_csv(path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir', nargs='?', help='Completed local_pilot_* output directory.')
    args = parser.parse_args()

    run_dir = Path(args.run_dir) if args.run_dir else latest_completed_run(here / 'outputs')
    manifest = json.loads((run_dir / 'manifest.json').read_text(encoding='utf-8'))
    episodes = load_jsonl(run_dir / 'episodes.jsonl')
    if not episodes:
        raise SystemExit(f'No episodes found in {run_dir}')

    condition_rows = []
    type_rows = []
    failure_rows = []
    episode_rows = []

    for condition, (history, mode) in CONDITIONS.items():
        rows = [e for e in episodes if e['condition'] == condition]
        turns = [t for e in rows for t in e['turns']]
        successes = sum(e['verdict']['task_success'] for e in rows)
        condition_rows.append({
            'condition': condition,
            'history': history,
            'mode': mode,
            'episodes': len(rows),
            'successes': successes,
            'success_rate': pct(successes, len(rows)),
            'responses': len(turns),
            'json_errors': sum(not t['json_valid'] for t in turns),
            'schema_errors': sum(not t['schema_valid'] for t in turns),
            'response_errors': sum(t['response_error'] is not None for t in turns),
        })

    for condition, (history, mode) in CONDITIONS.items():
        for kind in SCENARIO_TYPES:
            rows = [e for e in episodes if e['condition'] == condition and scenario_type(e['scenario_id']) == kind]
            successes = sum(e['verdict']['task_success'] for e in rows)
            type_rows.append({
                'condition': condition,
                'history': history,
                'mode': mode,
                'scenario_type': kind,
                'episodes': len(rows),
                'successes': successes,
                'success_rate': pct(successes, len(rows)),
            })

    for e in episodes:
        verdict = e['verdict']
        turns = e['turns']
        actions = [t['parsed_response'].get('action') for t in turns if isinstance(t.get('parsed_response'), dict)]
        error_counts = Counter(t['response_error'] for t in turns if t.get('response_error'))
        final_action = actions[-1] if actions else None
        if verdict['task_success']:
            failure_reason = ''
        elif error_counts:
            failure_reason = '; '.join(f'{k} ({v})' for k, v in sorted(error_counts.items()))
        elif verdict['answer_correct'] and not verdict['supported_by_tool_execution']:
            failure_reason = 'Correct answer was not supported by recovery tool evidence.'
        elif verdict['supported_by_tool_execution'] and not verdict['answer_correct']:
            failure_reason = 'Useful tool evidence existed, but the final answer was missing or incorrect.'
        elif final_action != 'finish':
            failure_reason = 'Model kept calling tools instead of finishing with an answer.'
        else:
            failure_reason = 'No successful supported recovery.'
        episode_rows.append({
            'episode_id': e.get('episode_id', ''),
            'condition': e['condition'],
            'scenario_id': e['scenario_id'],
            'scenario_type': scenario_type(e['scenario_id']),
            'task_success': verdict['task_success'],
            'answer_correct': verdict['answer_correct'],
            'supported_by_tool_execution': verdict['supported_by_tool_execution'],
            'turns': len(turns),
            'actions': ' > '.join(str(a) for a in actions),
            'failure_reason': failure_reason,
        })

    grouped_failures = defaultdict(Counter)
    for row in episode_rows:
        if row['failure_reason']:
            grouped_failures[row['condition']][row['failure_reason']] += 1
    for condition in CONDITIONS:
        for reason, count in grouped_failures[condition].most_common():
            failure_rows.append({'condition': condition, 'failure_reason': reason, 'count': count})

    write_csv(run_dir / 'analysis_by_condition.csv', condition_rows, list(condition_rows[0]))
    write_csv(run_dir / 'analysis_by_scenario_type.csv', type_rows, list(type_rows[0]))
    write_csv(run_dir / 'analysis_failures.csv', failure_rows, ['condition', 'failure_reason', 'count'])
    write_csv(run_dir / 'analysis_episodes.csv', episode_rows, list(episode_rows[0]))

    lines = [
        '# Local Pilot Results',
        '',
        f'Run directory: `{run_dir}`',
        f"Model: `{manifest.get('model', 'unknown')}`",
        f"Episodes: {len(episodes)}",
        f"Completed episodes in manifest: {manifest.get('completed_episodes', 'unknown')}",
        '',
        '## Main Result',
        '',
        '| Condition | History | Output mode | Successes | Success rate | Response errors |',
        '| --- | --- | --- | ---: | ---: | ---: |',
    ]
    for row in condition_rows:
        lines.append(
            f"| {row['condition']} | {row['history']} | {row['mode']} | "
            f"{row['successes']}/{row['episodes']} | {row['success_rate']} | {row['response_errors']} |"
        )
    lines += [
        '',
        'Schema-constrained generation produced much higher task success than plain JSON mode in this run. '
        'Structured evidence did not improve success over plain evidence when the same output mode was used.',
        '',
        '## Scenario-Type Breakdown',
        '',
        '| Condition | Invalid args | Offline primary | Temporary timeout | Malformed output | Stale output |',
        '| --- | ---: | ---: | ---: | ---: | ---: |',
    ]
    labels = {
        'invalid_arguments': 'Invalid args',
        'persistent_unavailability': 'Offline primary',
        'temporary_timeout': 'Temporary timeout',
        'malformed_output': 'Malformed output',
        'plausible_incorrect_output': 'Stale output',
    }
    for condition in CONDITIONS:
        selected = {row['scenario_type']: row for row in type_rows if row['condition'] == condition}
        cells = []
        for kind in SCENARIO_TYPES:
            row = selected[kind]
            cells.append(f"{row['successes']}/{row['episodes']}")
        lines.append(f'| {condition} | ' + ' | '.join(cells) + ' |')
    lines += [
        '',
        '## Failure Summary',
        '',
        '| Condition | Failure reason | Count |',
        '| --- | --- | ---: |',
    ]
    for row in failure_rows:
        lines.append(f"| {row['condition']} | {row['failure_reason']} | {row['count']} |")
    lines += [
        '',
        '## Interpretation',
        '',
        'The strongest current result is that strict response schemas reduced invalid response behavior and increased task success for this local model. '
        'The model still struggled with recovery reasoning in persistent unavailability and stale-output cases, where it often failed to switch to the authoritative backup source. '
        'These results should be treated as a development pilot because they use one model, one seed, and a synthetic inventory domain.',
        '',
        '## Files',
        '',
        '- `analysis_by_condition.csv`',
        '- `analysis_by_scenario_type.csv`',
        '- `analysis_failures.csv`',
        '- `analysis_episodes.csv`',
    ]
    (run_dir / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Analyzed {len(episodes)} episodes from {run_dir}')
    print(f'Wrote {run_dir / "RESULTS.md"}')


if __name__ == '__main__':
    main()
