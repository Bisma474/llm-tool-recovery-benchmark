"""Run real local-model episodes. Development pilot, not confirmatory evidence."""
import argparse
import csv
import hashlib
import json
import platform
import random
import time
from datetime import datetime, timezone
from pathlib import Path

from check_ollama_api import api
from experiment_runner import CONDITIONS, run_episode
from recovery_harness import SCENARIOS

DEFAULT_OPTIONS = {'temperature': 0, 'seed': 42, 'num_ctx': 4096, 'num_predict': 256}


def append(path, value):
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False) + '\n')
        f.flush()


class LocalBackend:
    def __init__(self, out, episode_id, model, options):
        self.out, self.episode_id, self.model = out, episode_id, model
        self.options = dict(options)
        self.calls = []

    def __call__(self, request):
        payload = {'model': self.model, 'messages': request['messages'],
                   'format': request['response_format'], 'think': False,
                   'stream': False, 'keep_alive': '5m', 'options': self.options}
        call_id = f'{self.episode_id}_turn_{len(self.calls) + 1}'
        append(self.out / 'requests.jsonl', {'call_id': call_id, 'request': payload})
        started = time.perf_counter()
        try:
            response = api('/api/chat', payload, timeout=300)
        except Exception as error:
            append(self.out / 'responses.jsonl', {'call_id': call_id, 'error': str(error)})
            raise
        message = response.get('message', {})
        content = message.get('content', '')
        row = {'call_id': call_id, 'raw_response': response,
               'wall_seconds': time.perf_counter() - started,
               'thinking_field': bool(message.get('thinking', '').strip()),
               'thinking_tags': '<think>' in content.lower() or '</think>' in content.lower(),
               'truncated': response.get('done_reason') == 'length',
               'incomplete': response.get('done') is not True}
        self.calls.append(row)
        append(self.out / 'responses.jsonl', row)
        # Preserve every character. No repair, stripping, or retry of a response.
        return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='qwen3:4b')
    parser.add_argument('--seed', type=int, default=DEFAULT_OPTIONS['seed'])
    parser.add_argument('--max-episodes', type=int, default=None,
                        help='Optional shakedown limit; omit for the full scenario x condition schedule.')
    args = parser.parse_args()
    if args.max_episodes is not None and args.max_episodes < 1:
        raise SystemExit('--max-episodes must be positive')
    here = Path(__file__).resolve().parent
    now = datetime.now(timezone.utc)
    out = here / 'outputs' / ('local_pilot_' + now.strftime('%Y%m%dT%H%M%S_%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    print(f'Real local pilot: {args.model}. Output: {out}', flush=True)
    options = dict(DEFAULT_OPTIONS)
    options['seed'] = args.seed
    schedule = [(s, c) for s in SCENARIOS for c in CONDITIONS]
    random.Random(20260926).shuffle(schedule)
    if args.max_episodes is not None:
        schedule = schedule[:args.max_episodes]
    manifest = {'kind': 'development_pilot', 'status': 'RUNNING', 'model': args.model,
                'options': options, 'think': False, 'created_at_utc': now.isoformat(),
                'python': platform.python_version(), 'platform': platform.platform(),
                'order_seed': 20260926, 'generation_seed': args.seed, 'schedule': schedule,
                'max_episodes': args.max_episodes,
                'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in here.glob('*.py')},
                'limitations': 'Development fixtures, one model, one seed; not a format-effect estimate. Cold/warm loading and caching can affect timing.'}
    def save_manifest():
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    save_manifest()
    results = []
    try:
        manifest['ollama_version'] = api('/api/version')
        manifest['model_details'] = api('/api/show', {'model': args.model})
        manifest['installed_models'] = api('/api/tags')
        save_manifest()
        for index, (scenario, condition) in enumerate(schedule, 1):
            print(f'[{index}/{len(schedule)}] {condition} {scenario}: running', flush=True)
            backend = LocalBackend(out, f'episode_{index:02d}', args.model, options)
            result = run_episode(scenario, condition, backend)
            result['episode_id'] = backend.episode_id
            result['source'] = 'real_local_ollama'
            result['api_calls'] = backend.calls
            append(out / 'episodes.jsonl', result)
            results.append(result)
            print(f"  success={result['verdict']['task_success']} turns={len(result['turns'])} "
                  f"schema_errors={sum(not t['schema_valid'] for t in result['turns'])} "
                  f"truncated={sum(c['truncated'] for c in backend.calls)}", flush=True)
        manifest['loaded_models_end'] = api('/api/ps')
        manifest['status'] = 'COMPLETED'
    except Exception as error:
        manifest['status'] = 'INTERRUPTED_BY_ERROR'
        manifest['error'] = str(error)
        print(f'Stopped on infrastructure error: {error}. Partial logs retained; no automatic retries.', flush=True)
    manifest['completed_episodes'] = len(results)
    save_manifest()
    summary = []
    for condition, (history, mode) in CONDITIONS.items():
        rows = [r for r in results if r['condition'] == condition]
        turns = [t for r in rows for t in r['turns']]
        calls = [c for r in rows for c in r['api_calls']]
        summary.append({'condition': condition, 'history': history, 'mode': mode,
                        'episodes': len(rows), 'task_successes': sum(r['verdict']['task_success'] for r in rows),
                        'responses': len(turns), 'json_errors': sum(not t['json_valid'] for t in turns),
                        'schema_errors': sum(not t['schema_valid'] for t in turns),
                        'response_errors': sum(t['response_error'] is not None for t in turns),
                        'thinking_observed': sum(c['thinking_field'] or c['thinking_tags'] for c in calls),
                        'truncated': sum(c['truncated'] for c in calls),
                        'incomplete': sum(c['incomplete'] for c in calls),
                        'wall_seconds': round(sum(c['wall_seconds'] for c in calls), 2)})
    with (out / 'summary.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)
    print('\n' + manifest['status'], flush=True)
    for row in summary:
        print(json.dumps(row), flush=True)
    print(f'Results saved to {out}', flush=True)
    return 0 if manifest['status'] == 'COMPLETED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
