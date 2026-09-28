"""Behavioral checks for persistence, task correctness, and isolated episodes."""
import unittest

from recovery_harness import SCENARIOS, Episode, record_matches_schema, run_policy


class RecoveryTests(unittest.TestCase):
    def test_original_bad_arguments_never_fix_themselves(self):
        episode = Episode('invalid_arguments')
        for _ in range(3):
            self.assertFalse(episode.act('lookup_primary', {'record_id': '101'}).success)
        self.assertFalse(episode.finish(None)['task_success'])

    def test_corrected_argument_recovers_after_failed_retry(self):
        episode = Episode('invalid_arguments')
        self.assertFalse(episode.act('lookup_primary', {'record_id': '101'}).success)
        result = episode.act('lookup_primary', {'record_id': 101})
        self.assertTrue(result.success)
        self.assertTrue(episode.finish(result.output)['task_success'])

    def test_primary_stays_offline_even_after_backup_succeeds(self):
        episode = Episode('persistent_unavailability')
        self.assertFalse(episode.act('lookup_primary', {'record_id': 202}).success)
        backup = episode.act('lookup_backup', {'record_id': 202})
        self.assertTrue(backup.success)
        self.assertFalse(episode.act('lookup_primary', {'record_id': 202}).success)
        self.assertTrue(episode.finish(backup.output)['task_success'])

    def test_wrong_record_is_not_task_success(self):
        episode = Episode('persistent_unavailability')
        result = episode.act('lookup_backup', {'record_id': 303})
        self.assertTrue(result.success)
        self.assertFalse(episode.finish(result.output)['task_success'])

    def test_invented_correct_answer_without_execution_is_rejected(self):
        episode = Episode('invalid_arguments')
        verdict = episode.finish({'record_id': 101, 'item': 'notebook', 'quantity': 17})
        self.assertTrue(verdict['answer_correct'])
        self.assertFalse(verdict['task_success'])

    def test_wrong_final_answer_after_successful_call_is_rejected(self):
        episode = Episode('invalid_arguments')
        result = episode.act('lookup_primary', {'record_id': 101})
        result.output['quantity'] = 999
        self.assertFalse(episode.finish(result.output)['task_success'])

    def test_budget_prevents_extra_execution(self):
        episode = Episode('invalid_arguments')
        for _ in range(3):
            episode.act('unknown', {})
        with self.assertRaises(RuntimeError):
            episode.act('lookup_primary', {'record_id': 101})
        self.assertEqual(len(episode.history), 4)

    def test_episode_isolation_and_observation_copies(self):
        offline = Episode('persistent_unavailability')
        healthy = Episode('invalid_arguments')
        self.assertFalse(offline.act('lookup_primary', {'record_id': 202}).success)
        self.assertTrue(healthy.act('lookup_primary', {'record_id': 202}).success)
        context = healthy.agent_context()
        context['history'].clear()
        context['tools'].clear()
        self.assertEqual(len(healthy.agent_context()['history']), 2)
        self.assertEqual(len(healthy.agent_context()['tools']), 2)
        self.assertNotIn('expected_answer', context)
        self.assertNotIn('unavailable', context)

    def test_invalid_contracts_are_rejected(self):
        for arguments in [None, [], {}, {'record_id': True}, {'record_id': 101.0}, {'record_id': 101, 'extra': 1}]:
            with self.subTest(arguments=arguments):
                episode = Episode('invalid_arguments')
                self.assertFalse(episode.act('lookup_primary', arguments).success)

    def test_multiple_legal_paths_can_succeed(self):
        episode = Episode('invalid_arguments')
        result = episode.act('lookup_backup', {'record_id': 101})
        self.assertTrue(episode.finish(result.output)['task_success'])

    def test_scripted_controls_have_expected_outcomes(self):
        for scenario in SCENARIOS:
            self.assertEqual(run_policy(scenario, 'always_retry')['verdict']['task_success'],
                             scenario.startswith('temporary_timeout'))
            recovered = run_policy(scenario, 'simple_recovery')['verdict']
            self.assertTrue(recovered['task_success'])
            self.assertEqual(recovered['attempts_used'], 1)

    def test_timeout_clears_after_initial_request_only(self):
        episode = Episode('temporary_timeout')
        self.assertFalse(episode.history[0]['result']['success'])
        result = episode.act('lookup_primary', {'record_id': 303})
        self.assertTrue(result.success)
        self.assertTrue(episode.act('lookup_primary', {'record_id': 303}).success)
        self.assertTrue(episode.finish(result.output)['task_success'])

    def test_timeout_state_resets_in_new_episode(self):
        first = Episode('temporary_timeout')
        self.assertTrue(first.act('lookup_primary', {'record_id': 303}).success)
        second = Episode('temporary_timeout')
        self.assertFalse(second.history[0]['result']['success'])

    def test_malformed_output_persists_despite_success_status(self):
        episode = Episode('malformed_output')
        for _ in range(3):
            result = episode.act('lookup_primary', {'record_id': 101})
            self.assertTrue(result.success)
            self.assertFalse(record_matches_schema(result.output))
        verdict = episode.finish({'record_id': 101, 'item': 'notebook', 'quantity': 17})
        self.assertTrue(verdict['task_success'])
        self.assertTrue(verdict['supported_by_tool_execution'])

    def test_wrapped_evidence_does_not_support_wrong_answer(self):
        episode = Episode('malformed_output')
        episode.act('lookup_primary', {'record_id': 101})
        verdict = episode.finish({'record_id': 101, 'item': 'notebook', 'quantity': 999})
        self.assertFalse(verdict['answer_correct'])
        self.assertFalse(verdict['task_success'])

    def test_malformed_output_recovers_using_valid_source(self):
        episode = Episode('malformed_output')
        bad = episode.act('lookup_primary', {'record_id': 101})
        good = episode.act('lookup_backup', {'record_id': 101})
        self.assertFalse(record_matches_schema(bad.output))
        self.assertTrue(record_matches_schema(good.output))
        self.assertTrue(episode.finish(good.output)['task_success'])

    def test_plausible_wrong_data_passes_schema_but_fails_task(self):
        episode = Episode('plausible_incorrect_output')
        for _ in range(3):
            result = episode.act('lookup_primary', {'record_id': 202})
            self.assertTrue(result.success)
            self.assertTrue(record_matches_schema(result.output))
        verdict = episode.finish(result.output)
        self.assertFalse(verdict['answer_correct'])
        self.assertFalse(verdict['task_success'])

    def test_authoritative_source_resolves_disagreement(self):
        episode = Episode('plausible_incorrect_output')
        stale = episode.history[0]['result']['output']
        current = episode.act('lookup_backup', {'record_id': 202})
        self.assertNotEqual(stale['quantity'], current.output['quantity'])
        still_stale = episode.act('lookup_primary', {'record_id': 202})
        self.assertEqual(still_stale.output, stale)
        self.assertTrue(episode.finish(current.output)['task_success'])

    def test_rejects_stale_answer_even_after_authoritative_lookup(self):
        episode = Episode('plausible_incorrect_output')
        stale = episode.history[0]['result']['output']
        episode.act('lookup_backup', {'record_id': 202})
        verdict = episode.finish(stale)
        self.assertTrue(verdict['supported_by_tool_execution'])
        self.assertFalse(verdict['task_success'])

    def test_output_contract_rejects_wrong_types_and_extra_fields(self):
        for record in [None, [], {'record_id': True, 'item': 'x', 'quantity': 1},
                       {'record_id': 1, 'item': 'x', 'quantity': '1'},
                       {'record_id': 1, 'item': 'x', 'quantity': 1, 'extra': 0}]:
            self.assertFalse(record_matches_schema(record))

    def test_finished_episode_cannot_be_reused(self):
        episode = Episode('invalid_arguments')
        episode.finish(None)
        with self.assertRaises(RuntimeError):
            episode.act('lookup_primary', {'record_id': 101})


if __name__ == '__main__':
    unittest.main(verbosity=2)
