import json
import unittest

from experiment_runner import CONDITIONS, ScriptedBackend, build_request, parse_response, run_episode
from recovery_harness import Episode, SCENARIOS


class RunnerTests(unittest.TestCase):
    def test_all_scripted_episodes_complete(self):
        for scenario in SCENARIOS:
            for condition in CONDITIONS:
                with self.subTest(scenario=scenario, condition=condition):
                    result = run_episode(scenario, condition, ScriptedBackend())
                    self.assertTrue(result['verdict']['task_success'])
                    self.assertEqual(len(result['turns']), 2)
                    self.assertEqual(result['verdict']['attempts_used'], 1)

    def test_modes_change_backend_setting_not_prompt(self):
        context = Episode('invalid_arguments').agent_context()
        for left, right in [('A', 'C'), ('B', 'D')]:
            a, b = build_request(context, left), build_request(context, right)
            self.assertEqual(a['messages'], b['messages'])
            self.assertEqual(a['response_format'], 'json')
            self.assertIsInstance(b['response_format'], dict)

    def test_system_instructions_identical_across_conditions(self):
        context = Episode('malformed_output').agent_context()
        systems = [build_request(context, c)['messages'][0] for c in CONDITIONS]
        self.assertTrue(all(s == systems[0] for s in systems))

    def test_invalid_json_consumes_budget_without_tools(self):
        result = run_episode('invalid_arguments', 'A', lambda request: 'not json')
        self.assertEqual(len(result['turns']), 4)
        self.assertEqual(result['action_opportunities_used'], 3)
        self.assertEqual(result['verdict']['attempts_used'], 0)
        self.assertFalse(result['verdict']['task_success'])
        self.assertIn('"remaining_attempts": 0', result['turns'][-1]['request']['messages'][1]['content'])

    def test_final_only_turn_cannot_execute_tool(self):
        action = json.dumps({'action': 'lookup_primary', 'arguments': {'record_id': 202}, 'answer': None})
        result = run_episode('persistent_unavailability', 'C', lambda request: action)
        self.assertEqual(result['verdict']['attempts_used'], 3)
        self.assertFalse(result['turns'][-1]['tool_executed'])
        self.assertIsNotNone(result['turns'][-1]['response_error'])

    def test_schema_setting_does_not_silently_repair_mock_output(self):
        for condition in CONDITIONS:
            result = run_episode('invalid_arguments', condition, lambda request: '{"copied_history": []}')
            self.assertTrue(all(t['json_valid'] and not t['schema_valid'] for t in result['turns']))
            self.assertFalse(result['verdict']['task_success'])

    def test_invented_answer_fails_without_execution(self):
        answer = json.dumps({'action': 'finish', 'arguments': None,
                             'answer': {'record_id': 101, 'item': 'notebook', 'quantity': 17}})
        result = run_episode('invalid_arguments', 'D', lambda request: answer)
        self.assertTrue(result['verdict']['answer_correct'])
        self.assertFalse(result['verdict']['task_success'])

    def test_invalid_then_valid_response_can_recover(self):
        scripted = ScriptedBackend()
        calls = []
        def backend(request):
            calls.append(request)
            return 'invalid' if len(calls) == 1 else scripted(request)
        result = run_episode('invalid_arguments', 'A', backend)
        self.assertTrue(result['verdict']['task_success'])
        self.assertEqual(len(result['turns']), 3)

    def test_schema_rejects_wrong_types_extra_keys_and_unknown_tools(self):
        for obj in [
            {'action': 'unknown', 'arguments': {'record_id': 1}, 'answer': None},
            {'action': 'lookup_primary', 'arguments': {'record_id': True}, 'answer': None},
            {'action': 'lookup_primary', 'arguments': {'record_id': '101'}, 'answer': None},
            {'action': 'finish', 'arguments': None, 'answer': None, 'extra': 1},
        ]:
            self.assertFalse(parse_response(json.dumps(obj))[2])

    def test_cross_field_consistency_is_checked(self):
        for obj in [{'action': 'lookup_primary', 'arguments': None, 'answer': None},
                    {'action': 'finish', 'arguments': {'record_id': 101}, 'answer': None}]:
            parsed, valid_json, valid_schema, error = parse_response(json.dumps(obj))
            self.assertTrue(valid_json and valid_schema)
            self.assertIsNotNone(error)

    def test_nonfinite_and_duplicate_json_are_rejected(self):
        for raw in ['{"x": NaN}', '{"action":"finish","action":"lookup_primary"}']:
            self.assertFalse(parse_response(raw)[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
