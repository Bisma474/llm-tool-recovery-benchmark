# Local Pilot Results

Run directory: `F:\research\v2\outputs\local_pilot_20260928T134617_595431Z`
Model: `llama3.2:3b`
Episodes: 100
Completed episodes in manifest: 100

## Main Result

| Condition | History | Output mode | Successes | Success rate | Response errors |
| --- | --- | --- | ---: | ---: | ---: |
| A | plain | json | 6/25 | 24.0% | 50 |
| B | structured | json | 8/25 | 32.0% | 20 |
| C | plain | schema | 11/25 | 44.0% | 40 |
| D | structured | schema | 13/25 | 52.0% | 0 |

Schema-constrained generation produced much higher task success than plain JSON mode in this run. Structured evidence did not improve success over plain evidence when the same output mode was used.

## Scenario-Type Breakdown

| Condition | Invalid args | Offline primary | Temporary timeout | Malformed output | Stale output |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 0/5 | 0/5 | 0/5 | 5/5 | 1/5 |
| B | 0/5 | 0/5 | 4/5 | 3/5 | 1/5 |
| C | 5/5 | 0/5 | 0/5 | 5/5 | 1/5 |
| D | 5/5 | 0/5 | 4/5 | 3/5 | 1/5 |

## Failure Summary

| Condition | Failure reason | Count |
| --- | --- | ---: |
| A | Action, arguments, and answer are inconsistent. (3) | 10 |
| A | Response does not match the response schema. (4) | 5 |
| A | Useful tool evidence existed, but the final answer was missing or incorrect. | 4 |
| B | No successful supported recovery. | 9 |
| B | Response does not match the response schema. (4) | 5 |
| B | Useful tool evidence existed, but the final answer was missing or incorrect. | 3 |
| C | Action, arguments, and answer are inconsistent. (3) | 10 |
| C | Useful tool evidence existed, but the final answer was missing or incorrect. | 4 |
| D | No successful supported recovery. | 9 |
| D | Useful tool evidence existed, but the final answer was missing or incorrect. | 3 |

## Interpretation

The strongest current result is that strict response schemas reduced invalid response behavior and increased task success for this local model. The model still struggled with recovery reasoning in persistent unavailability and stale-output cases, where it often failed to switch to the authoritative backup source. These results should be treated as a development pilot because they use one model, one seed, and a synthetic inventory domain.

## Files

- `analysis_by_condition.csv`
- `analysis_by_scenario_type.csv`
- `analysis_failures.csv`
- `analysis_episodes.csv`
