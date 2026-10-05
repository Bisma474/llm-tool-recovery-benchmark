"""Offline recovery scenarios. Standard library only; no model calls."""
from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Any


CATALOG = {
    'lookup_primary': {
        'description': 'Read an inventory record from the primary service, which may use cached data.',
        'arguments': {'record_id': 'Required integer; no other arguments.'},
        'returns': {'record_id': 'integer', 'item': 'string', 'quantity': 'integer'},
    },
    'lookup_backup': {
        'description': 'Read current inventory from an independently available authoritative replica. Prefer this source if it disagrees with cached primary data.',
        'arguments': {'record_id': 'Required integer; no other arguments.'},
        'returns': {'record_id': 'integer', 'item': 'string', 'quantity': 'integer'},
    },
}

SCENARIOS = {
    'invalid_arguments': {
        'task': 'Retrieve inventory record 101 and report its record_id, item, and quantity.',
        'record_id': 101,
        'initial_tool': 'lookup_primary',
        'initial_arguments': {'record_id': '101'},
        'unavailable': (),
    },
    'persistent_unavailability': {
        'task': 'Retrieve inventory record 202 and report its record_id, item, and quantity.',
        'record_id': 202,
        'initial_tool': 'lookup_primary',
        'initial_arguments': {'record_id': 202},
        'unavailable': ('lookup_primary',),
    },
    'temporary_timeout': {
        'task': 'Retrieve inventory record 303 and report its record_id, item, and quantity.',
        'record_id': 303,
        'initial_tool': 'lookup_primary',
        'initial_arguments': {'record_id': 303},
        'unavailable': (),
        'primary_timeouts': 1,
    },
    'malformed_output': {
        'task': 'Retrieve inventory record 101 and report its record_id, item, and quantity.',
        'record_id': 101,
        'initial_tool': 'lookup_primary',
        'initial_arguments': {'record_id': 101},
        'unavailable': (),
        'primary_output': 'malformed',
    },
    'plausible_incorrect_output': {
        'task': 'Retrieve inventory record 202 and report its current record_id, item, and quantity.',
        'record_id': 202,
        'initial_tool': 'lookup_primary',
        'initial_arguments': {'record_id': 202},
        'unavailable': (),
        'primary_output': 'stale',
    },
}

# Hidden fixture data. It is not included in agent_context().
_RECORDS = {
    101: {'record_id': 101, 'item': 'notebook', 'quantity': 17},
    202: {'record_id': 202, 'item': 'stapler', 'quantity': 6},
    303: {'record_id': 303, 'item': 'folder', 'quantity': 42},
    404: {'record_id': 404, 'item': 'marker', 'quantity': 29},
    505: {'record_id': 505, 'item': 'binder', 'quantity': 13},
    606: {'record_id': 606, 'item': 'envelope', 'quantity': 31},
    707: {'record_id': 707, 'item': 'scissors', 'quantity': 8},
    808: {'record_id': 808, 'item': 'clipboard', 'quantity': 24},
    909: {'record_id': 909, 'item': 'eraser', 'quantity': 19},
    1001: {'record_id': 1001, 'item': 'ruler', 'quantity': 12},
}


def _extra_scenarios() -> dict:
    records = [
        (404, 'marker'),
        (505, 'binder'),
        (101, 'notebook_repeat'),
        (202, 'stapler_repeat'),
    ]
    scenarios = {}
    for record_id, label in records:
        task = f'Retrieve inventory record {record_id} and report its record_id, item, and quantity.'
        scenarios[f'invalid_arguments_{label}'] = {
            'task': task,
            'record_id': record_id,
            'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': str(record_id)},
            'unavailable': (),
        }
        scenarios[f'persistent_unavailability_{label}'] = {
            'task': task,
            'record_id': record_id,
            'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id},
            'unavailable': ('lookup_primary',),
        }
        scenarios[f'temporary_timeout_{label}'] = {
            'task': task,
            'record_id': record_id,
            'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id},
            'unavailable': (),
            'primary_timeouts': 1,
        }
        scenarios[f'malformed_output_{label}'] = {
            'task': task,
            'record_id': record_id,
            'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id},
            'unavailable': (),
            'primary_output': 'malformed',
        }
        scenarios[f'plausible_incorrect_output_{label}'] = {
            'task': f'Retrieve inventory record {record_id} and report its current record_id, item, and quantity.',
            'record_id': record_id,
            'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id},
            'unavailable': (),
            'primary_output': 'stale',
        }
    return scenarios


SCENARIOS.update(_extra_scenarios())


def _heldout_scenarios() -> dict:
    """Locked evaluation scenarios using unseen records and new variants."""
    records = [(606, 'envelope'), (707, 'scissors'), (808, 'clipboard'),
               (909, 'eraser'), (1001, 'ruler')]
    scenarios = {}
    for record_id, label in records:
        task = f'Retrieve inventory record {record_id} and report its record_id, item, and quantity.'
        scenarios[f'heldout_invalid_arguments_{label}'] = {
            'task': task, 'record_id': record_id, 'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': str(record_id)}, 'unavailable': (),
        }
        scenarios[f'heldout_persistent_unavailability_{label}'] = {
            'task': task, 'record_id': record_id, 'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id}, 'unavailable': ('lookup_primary',),
        }
        scenarios[f'heldout_temporary_timeout_{label}'] = {
            'task': task, 'record_id': record_id, 'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id}, 'unavailable': (), 'primary_timeouts': 1,
        }
        scenarios[f'heldout_malformed_output_{label}'] = {
            'task': task, 'record_id': record_id, 'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id}, 'unavailable': (), 'primary_output': 'malformed',
        }
        scenarios[f'heldout_plausible_incorrect_output_{label}'] = {
            'task': f'Retrieve inventory record {record_id} and report its current record_id, item, and quantity.',
            'record_id': record_id, 'initial_tool': 'lookup_primary',
            'initial_arguments': {'record_id': record_id}, 'unavailable': (), 'primary_output': 'stale',
        }
    return scenarios


HELDOUT_SCENARIOS = _heldout_scenarios()
SCENARIO_SETS = {'development': SCENARIOS, 'heldout': HELDOUT_SCENARIOS}


@dataclass
class ToolResult:
    success: bool
    output: Any = None
    message: str = ''


class Episode:
    """A fresh environment per episode; faults follow explicit state rules.

    The supplied initial failure is outside the three recovery opportunities.
    Invalid calls consume an opportunity. Calls after exhaustion never execute.
    """

    def __init__(self, scenario_id: str, max_attempts: int = 3):
        if scenario_id not in SCENARIOS and scenario_id not in HELDOUT_SCENARIOS:
            raise ValueError(f'Unknown scenario: {scenario_id}')
        if type(max_attempts) is not int or max_attempts < 1:
            raise ValueError('max_attempts must be a positive integer')
        self.scenario_id = scenario_id
        scenario_map = HELDOUT_SCENARIOS if scenario_id in HELDOUT_SCENARIOS else SCENARIOS
        self._scenario = deepcopy(scenario_map[scenario_id])
        self._unavailable = frozenset(self._scenario['unavailable'])
        self._timeouts_remaining = self._scenario.get('primary_timeouts', 0)
        self.max_attempts = max_attempts
        self.attempts_used = 0
        self.history = []
        self._finished = False
        self._execute_and_record(
            self._scenario['initial_tool'],
            self._scenario['initial_arguments'],
            'initial',
        )

    def _execute(self, tool: str, arguments: Any) -> ToolResult:
        if not isinstance(tool, str) or tool not in CATALOG:
            return ToolResult(False, message='Unknown tool. Consult the available tool catalog.')
        if not isinstance(arguments, dict) or set(arguments) != {'record_id'}:
            return ToolResult(False, message='Expected exactly one argument: record_id (integer).')
        record_id = arguments['record_id']
        # bool is a subclass of int in Python; reject it explicitly via exact type.
        if type(record_id) is not int:
            return ToolResult(False, message='record_id must be an integer; a string or boolean is not accepted.')
        if tool in self._unavailable:
            return ToolResult(False, message='Service is offline for this entire session; repeating this request will not restore it.')
        if record_id not in _RECORDS:
            return ToolResult(False, message='No record exists for this identifier.')
        if tool == 'lookup_primary':
            if self._timeouts_remaining:
                self._timeouts_remaining -= 1
                return ToolResult(False, message='Request deadline exceeded. A subsequent request may succeed.')
            if self._scenario.get('primary_output') == 'malformed':
                return ToolResult(True, {'payload': [deepcopy(_RECORDS[record_id])]}, 'Request completed.')
            if self._scenario.get('primary_output') == 'stale':
                stale = deepcopy(_RECORDS[record_id])
                stale['quantity'] += 5
                return ToolResult(True, stale, 'Record retrieved.')
        return ToolResult(True, deepcopy(_RECORDS[record_id]), 'Record retrieved.')

    def _execute_and_record(self, tool: str, arguments: Any, stage: str) -> ToolResult:
        result = self._execute(tool, arguments)
        self.history.append({
            'stage': stage,
            'tool': deepcopy(tool),
            'arguments': deepcopy(arguments),
            'result': asdict(result),
        })
        return result

    def act(self, tool: str, arguments: Any) -> ToolResult:
        if self._finished:
            raise RuntimeError('Episode already finished.')
        if self.attempts_used >= self.max_attempts:
            raise RuntimeError('Recovery budget exhausted; no tool executed.')
        self.attempts_used += 1
        return self._execute_and_record(tool, arguments, 'recovery')

    def agent_context(self) -> dict:
        """Public observations only: no expected answer or internal fault label."""
        return deepcopy({
            'task': self._scenario['task'],
            'recovery_notice': 'The initial attempt did not reliably complete the task. Recover using the available evidence and tools.',
            'tools': CATALOG,
            'history': self.history,
            'remaining_attempts': self.max_attempts - self.attempts_used,
        })

    def finish(self, answer: Any) -> dict:
        if self._finished:
            raise RuntimeError('Episode already finished.')
        self._finished = True
        expected = _RECORDS[self._scenario['record_id']]
        correct = (
            isinstance(answer, dict)
            and set(answer) == set(expected)
            and all(type(answer[k]) is type(v) and answer[k] == v for k, v in expected.items())
        )
        evidence = any(
            row['stage'] == 'recovery'
            and row['result']['success']
            and output_contains_record(row['result']['output'], expected)
            for row in self.history
        )
        return {
            'task_success': bool(correct and evidence),
            'answer_correct': bool(correct),
            'supported_by_tool_execution': evidence,
            'attempts_used': self.attempts_used,
            'final_answer': deepcopy(answer),
        }


def output_contains_record(output: Any, expected: dict) -> bool:
    if output == expected:
        return True
    if not isinstance(output, dict):
        return False
    payload = output.get('payload')
    if isinstance(payload, list):
        return any(item == expected for item in payload)
    if isinstance(payload, dict):
        return payload == expected
    return False


def record_matches_schema(output: Any) -> bool:
    """Public contract check only; this cannot detect a plausible wrong value."""
    return (
        isinstance(output, dict)
        and set(output) == {'record_id', 'item', 'quantity'}
        and type(output['record_id']) is int
        and type(output['item']) is str
        and type(output['quantity']) is int
    )


def run_policy(scenario_id: str, policy: str) -> dict:
    """Scripted controls, not LLM results.

    Both policies see only the public observation when selecting their action.
    The rule policy is intentionally specific to these development fixtures.
    """
    if policy not in {'always_retry', 'simple_recovery'}:
        raise ValueError(f'Unknown policy: {policy}')
    episode = Episode(scenario_id)
    answer = None
    while episode.attempts_used < episode.max_attempts:
        context = episode.agent_context()
        initial = context['history'][0]
        tool, args = initial['tool'], deepcopy(initial['arguments'])
        if policy == 'simple_recovery':
            message = context['history'][-1]['result']['message']
            if 'must be an integer' in message:
                value = args.get('record_id')
                if isinstance(value, str) and value.isdecimal():
                    args['record_id'] = int(value)
            elif 'offline for this entire session' in message:
                tool = 'lookup_backup'
            elif initial['result']['success']:
                # The public recovery notice says the initial result is unreliable.
                # A malformed record needs a valid source; a schema-valid one
                # needs verification. The catalog names the authoritative source.
                tool = 'lookup_backup'
        result = episode.act(tool, args)
        if result.success:
            answer = result.output
            break
    return {
        'scenario_id': scenario_id,
        'policy': policy,
        'source': 'scripted_validation_not_model_experiment',
        'history': deepcopy(episode.history),
        'verdict': episode.finish(answer),
    }
