import json
import unittest
from copy import deepcopy

from evidence_formats import build_pair, canonical_json, parse_plain, render_plain
from recovery_harness import Episode, SCENARIOS


class EvidenceTests(unittest.TestCase):
    def test_all_initial_histories_preserve_information(self):
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                context = Episode(name).agent_context()
                pair = build_pair(context)
                self.assertTrue(pair['information_equal'])
                self.assertEqual(canonical_json(parse_plain(pair['plain_history'])), canonical_json(context['history']))
                self.assertEqual(json.loads(pair['structured_history']), context['history'])

    def test_history_after_recovery_and_budget_are_preserved(self):
        episode = Episode('invalid_arguments')
        episode.act('lookup_primary', {'record_id': 101})
        pair = build_pair(episode.agent_context())
        self.assertEqual(len(parse_plain(pair['plain_history'])), 2)
        self.assertEqual(pair['common_context']['remaining_attempts'], 2)

    def test_string_argument_is_not_changed_to_integer(self):
        pair = build_pair(Episode('invalid_arguments').agent_context())
        self.assertIs(type(parse_plain(pair['plain_history'])[0]['arguments']['record_id']), str)
        self.assertIs(type(json.loads(pair['structured_history'])[0]['arguments']['record_id']), str)

    def test_newlines_equals_unicode_and_empty_values_roundtrip(self):
        context = Episode('malformed_output').agent_context()
        context['history'][0]['result']['message'] = 'line 1\nkey=value; "quoted" \\ Unicode: اردو'
        context['history'][0]['result']['output'] = {'empty': [], 'null': None, 'false': False, 'zero': 0, 'text': ''}
        pair = build_pair(context)
        self.assertEqual(canonical_json(parse_plain(pair['plain_history'])), canonical_json(context['history']))

    def test_missing_field_is_rejected(self):
        text = render_plain(Episode('invalid_arguments').agent_context()['history'])
        with self.assertRaises(ValueError):
            parse_plain('\n'.join(text.splitlines()[:-1]))

    def test_duplicate_or_changed_field_is_rejected(self):
        text = render_plain(Episode('invalid_arguments').agent_context()['history'])
        with self.assertRaises(ValueError):
            parse_plain(text.replace('event[0].tool=', 'event[0].stage='))

    def test_changed_value_is_detectable(self):
        pair = build_pair(Episode('invalid_arguments').agent_context())
        changed = pair['plain_history'].replace('"record_id":"101"', '"record_id":101')
        self.assertNotEqual(canonical_json(parse_plain(changed)), canonical_json(pair['canonical_history']))

    def test_private_fields_rejected(self):
        for location in ('context', 'history', 'result'):
            context = Episode('invalid_arguments').agent_context()
            target = context if location == 'context' else context['history'][0]
            if location == 'result':
                target = target['result']
            target['expected_answer'] = 'hidden'
            with self.assertRaises(ValueError):
                build_pair(context)

    def test_original_context_unchanged(self):
        context = Episode('temporary_timeout').agent_context()
        before = deepcopy(context)
        build_pair(context)
        self.assertEqual(context, before)

    def test_shared_context_identical_in_both_evidence_blocks(self):
        pair = build_pair(Episode('plausible_incorrect_output').agent_context())
        plain_prefix, plain_history = pair['plain_evidence'].split('\n\nExecution history:\n', 1)
        json_prefix, json_history = pair['structured_evidence'].split('\n\nExecution history:\n', 1)
        self.assertEqual(plain_prefix, json_prefix)
        self.assertNotEqual(plain_history, json_history)
        self.assertNotIn('plausible_incorrect_output', pair['plain_evidence'])

    def test_empty_history_roundtrip(self):
        context = Episode('temporary_timeout').agent_context()
        context['history'] = []
        self.assertTrue(build_pair(context)['information_equal'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
