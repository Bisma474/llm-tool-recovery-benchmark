"""Lossless history renderings from public observations; standard library only."""
import json
from copy import deepcopy


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def split_context(context):
    expected = {'task', 'recovery_notice', 'tools', 'history', 'remaining_attempts'}
    if set(context) != expected:
        raise ValueError('Unexpected public context fields; review before exposing them.')
    history = deepcopy(context['history'])
    validate_history(history)
    common = deepcopy({k: v for k, v in context.items() if k != 'history'})
    return common, history


def validate_history(history):
    if not isinstance(history, list):
        raise ValueError('History must be a list.')
    for row in history:
        if not isinstance(row, dict) or set(row) != {'stage', 'tool', 'arguments', 'result'}:
            raise ValueError('Unexpected execution-record fields.')
        if not isinstance(row['result'], dict) or set(row['result']) != {'success', 'output', 'message'}:
            raise ValueError('Unexpected tool-result fields.')
    canonical_json(history)  # Reject non-JSON data rather than silently coercing it.


FIELDS = ('stage', 'tool', 'arguments', 'result.success', 'result.output', 'result.message')


def render_plain(history):
    """Line-oriented key=value log. JSON values preserve types and newlines.

    Nested arguments/output remain JSON values, as in common application logs.
    This is a plain log versus a nested JSON record, not prose versus JSON.
    """
    validate_history(history)
    lines = []
    for index, row in enumerate(history):
        for field in FIELDS:
            value = row['result'][field.split('.')[1]] if field.startswith('result.') else row[field]
            lines.append(f'event[{index}].{field}={canonical_json(value)}')
    return '\n'.join(lines)


def parse_plain(text):
    if not text:
        return []
    lines = text.splitlines()
    if len(lines) % len(FIELDS):
        raise ValueError('Missing or additional log fields.')
    history = []
    for index in range(len(lines) // len(FIELDS)):
        row = {'result': {}}
        for offset, field in enumerate(FIELDS):
            key, separator, encoded = lines[index * len(FIELDS) + offset].partition('=')
            if not separator or key != f'event[{index}].{field}':
                raise ValueError('Unexpected field, order, or event index.')
            value = json.loads(encoded)
            if field.startswith('result.'):
                row['result'][field.split('.')[1]] = value
            else:
                row[field] = value
        history.append(row)
    validate_history(history)
    return history


def render_structured(history):
    validate_history(history)
    return json.dumps(history, ensure_ascii=False, indent=2, allow_nan=False)


def build_pair(context):
    common, history = split_context(context)
    plain = render_plain(history)
    structured = render_structured(history)
    # Canonical serialization distinguishes true from 1 and "101" from 101.
    same = canonical_json(parse_plain(plain)) == canonical_json(history) == canonical_json(json.loads(structured))
    if not same:
        raise ValueError('Evidence lost or changed during rendering.')
    prefix = 'Task and tool information:\n' + json.dumps(common, ensure_ascii=False, indent=2) + '\n\nExecution history:\n'
    suffix = '\n\nEnd of execution history.'
    return {
        'common_context': common,
        'canonical_history': history,
        'plain_history': plain,
        'structured_history': structured,
        'plain_evidence': prefix + plain + suffix,
        'structured_evidence': prefix + structured + suffix,
        'information_equal': same,
    }
