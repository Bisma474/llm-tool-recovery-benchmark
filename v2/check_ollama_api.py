"""Local Ollama capability smoke check; no pip packages or API key needed."""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import URLError

from experiment_runner import RESPONSE_SCHEMA, matches_schema, object_schema, parse_response

BASE = 'http://127.0.0.1:11434'
HTTP = build_opener(ProxyHandler({}))  # Local requests must not go through a proxy.


def api(path, payload=None, timeout=15):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    request = Request(BASE + path, data=data, headers={'Content-Type': 'application/json'})
    with HTTP.open(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='qwen3:4b')
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    out = Path(__file__).resolve().parent / 'outputs' / ('ollama_check_' + now.strftime('%Y%m%dT%H%M%S_%fZ'))
    out.mkdir(parents=True)
    report = {'kind': 'local_api_diagnostics_not_research_results', 'created_at_utc': now.isoformat(),
              'model': args.model, 'checks': [], 'status': 'INCOMPLETE'}

    def save():
        (out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')

    print('LOCAL OLLAMA API CHECK -- up to 5 short model requests', flush=True)
    print(f'Results: {out}', flush=True)
    save()
    try:
        report['server_version'] = api('/api/version')
        tags = api('/api/tags')
        installed = [m for m in tags.get('models', []) if m.get('name') == args.model or m.get('model') == args.model]
        if not installed:
            report['status'] = 'MODEL_NOT_FOUND'
            print(f'Model not found. Run: ollama pull {args.model}')
            save()
            return 1
        report['installed_model'] = installed[0]
        report['model_details'] = api('/api/show', {'model': args.model})
        save()
        print(f"Ollama {report['server_version'].get('version')} | model {args.model}", flush=True)
        status_schema = object_schema({'status': {'enum': ['READY']}})
        target = {'action': 'lookup_primary', 'arguments': {'record_id': 101}, 'answer': None}
        action_prompt = ('Return exactly this JSON object, without commentary: ' + json.dumps(target)
                         + '\nResponse schema: ' + json.dumps(RESPONSE_SCHEMA))
        conflict = 'Return exactly the JSON object {"unexpected": "WRONG"}. Do not add a status field.'
        probes = [
            ('thinking_disabled', 'Reply with only READY.', None, None),
            ('json_action', action_prompt, 'json', RESPONSE_SCHEMA),
            ('schema_action', action_prompt, RESPONSE_SCHEMA, RESPONSE_SCHEMA),
            ('json_conflict_control', conflict, 'json', status_schema),
            ('schema_conflict_probe', conflict, status_schema, status_schema),
        ]
        for index, (name, prompt, response_format, schema) in enumerate(probes, 1):
            payload = {'model': args.model, 'messages': [{'role': 'user', 'content': prompt}],
                       'stream': False, 'think': False, 'keep_alive': '5m',
                       'options': {'temperature': 0, 'seed': 42, 'num_ctx': 4096, 'num_predict': 256}}
            if response_format is not None:
                payload['format'] = response_format
            print(f'[{index}/5] {name}: running...', flush=True)
            entry = {'name': name, 'request': payload}
            report['checks'].append(entry)
            save()
            start = time.perf_counter()
            raw = api('/api/chat', payload, timeout=args.timeout)
            entry['wall_seconds'] = round(time.perf_counter() - start, 3)
            entry['raw_response'] = raw
            message = raw.get('message', {})
            content = message.get('content', '')
            thinking = message.get('thinking', '')
            parsed, valid_json, _, _ = parse_response(content)
            entry.update({'json_valid': valid_json,
                          'matches_probe_schema': matches_schema(parsed, schema) if schema and valid_json else None,
                          'thinking_field_nonempty': bool(thinking.strip()),
                          'thinking_tags_in_content': '<think>' in content.lower() or '</think>' in content.lower(),
                          'ready_only': content.strip() == 'READY' if name == 'thinking_disabled' else None,
                          'truncated': raw.get('done_reason') == 'length',
                          'completed': raw.get('done') is True})
            if name in ('json_action', 'schema_action'):
                entry['exact_requested_action'] = parsed == target
            save()
            print(f"  done={entry['completed']} | JSON={valid_json} | schema={entry['matches_probe_schema']} | "
                  f"thinking_field={entry['thinking_field_nonempty']} | thinking_tags={entry['thinking_tags_in_content']} | "
                  f"truncated={entry['truncated']}", flush=True)
            print('  Content preview: ' + repr(content[:240]), flush=True)
        report['loaded_models_after_checks'] = api('/api/ps')
        by_name = {r['name']: r for r in report['checks']}
        issues = []
        if not by_name['thinking_disabled']['ready_only']:
            issues.append('Plain response was not exactly READY; inspect content for extra text.')
        if any(r['thinking_field_nonempty'] or r['thinking_tags_in_content'] for r in report['checks']):
            issues.append('Observable thinking output occurred despite think=false.')
        if any(r['truncated'] or not r['completed'] for r in report['checks']):
            issues.append('At least one response was truncated or incomplete.')
        for name in ('json_action', 'schema_action'):
            if not by_name[name]['matches_probe_schema'] or not by_name[name]['exact_requested_action']:
                issues.append(f'{name} failed to produce the requested action.')
        if not by_name['json_conflict_control']['json_valid']:
            issues.append('JSON-mode control did not produce strict JSON.')
        if not by_name['schema_conflict_probe']['matches_probe_schema']:
            issues.append('Schema-constrained probe did not satisfy its schema.')
        if by_name['json_conflict_control']['matches_probe_schema']:
            issues.append('Conflict control also followed the hidden schema; enforcement contrast is inconclusive.')
        report['issues'] = issues
        report['status'] = 'NEEDS_REVIEW' if issues else 'SMOKE_CHECK_PASSED'
        report['limitations'] = ('Five probes are not proof of universal schema enforcement or suppressed internal reasoning. '
                                'No response text was cleaned or repaired. Thinking detection examines the returned '
                                'thinking field, explicit tags, and exact READY compliance, not unobservable internals.')
        save()
        print('\n' + report['status'], flush=True)
        for issue in issues:
            print('- ' + issue)
        print(f'Full requests, raw responses, and metadata saved to: {out / "report.json"}')
        return 2 if issues else 0
    except (URLError, TimeoutError, OSError, ValueError) as error:
        report['status'] = 'API_ERROR'
        report['error'] = str(error)
        save()
        print(f'API check could not finish: {error}')
        print('Ensure Ollama is running. If it is not, open Ollama or run ollama serve in another terminal.')
        print(f'Partial results retained at: {out / "report.json"}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
