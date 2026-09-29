# Local Pilot Results

Run directory: `F:\research\v2\outputs\local_pilot_20260928T141812_603243Z`
Model: `qwen3:4b`
Episodes: 100
Completed episodes in manifest: 100

## Main Result

| Condition | History | Output mode | Successes | Success rate | Response errors |
| --- | --- | --- | ---: | ---: | ---: |
| A | plain | json | 0/25 | 0.0% | 36 |
| B | structured | json | 2/25 | 8.0% | 38 |
| C | plain | schema | 15/25 | 60.0% | 1 |
| D | structured | schema | 15/25 | 60.0% | 0 |

Schema-constrained generation produced much higher task success than plain JSON mode in this run. Structured evidence did not improve success over plain evidence when the same output mode was used.

## Scenario-Type Breakdown

| Condition | Invalid args | Offline primary | Temporary timeout | Malformed output | Stale output |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| B | 1/5 | 0/5 | 1/5 | 0/5 | 0/5 |
| C | 5/5 | 0/5 | 5/5 | 5/5 | 0/5 |
| D | 5/5 | 0/5 | 5/5 | 5/5 | 0/5 |

## Failure Summary

| Condition | Failure reason | Count |
| --- | --- | ---: |
| A | Response does not match the response schema. (1) | 14 |
| A | Response does not match the response schema. (2) | 11 |
| B | Response does not match the response schema. (2) | 15 |
| B | Response does not match the response schema. (1) | 8 |
| C | No successful supported recovery. | 9 |
| C | Tool calls are forbidden on the final-answer-only turn. (1) | 1 |
| D | No successful supported recovery. | 10 |

## Interpretation

The strongest current result is that strict response schemas reduced invalid response behavior and increased task success for this local model. The model still struggled with recovery reasoning in persistent unavailability and stale-output cases, where it often failed to switch to the authoritative backup source. These results should be treated as a development pilot because they use one model, one seed, and a synthetic inventory domain.

## Files

- `analysis_by_condition.csv`
- `analysis_by_scenario_type.csv`
- `analysis_failures.csv`
- `analysis_episodes.csv`
