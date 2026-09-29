# Aggregated Local Pilot Results

Aggregated runs: 4

| Run | Model | Seed |
| --- | --- | ---: |
| `local_pilot_20260927T140515_796428Z` | `qwen3:4b` | 42 |
| `local_pilot_20260928T141812_603243Z` | `qwen3:4b` | 43 |
| `local_pilot_20260928T124701_310525Z` | `llama3.2:3b` | 42 |
| `local_pilot_20260928T134617_595431Z` | `llama3.2:3b` | 43 |

## Main Table

| Model | Condition | History | Output mode | Successes | Success rate | Response errors |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `llama3.2:3b` | A | plain | json | 12/50 | 24.0% | 100 |
| `llama3.2:3b` | B | structured | json | 16/50 | 32.0% | 40 |
| `llama3.2:3b` | C | plain | schema | 22/50 | 44.0% | 80 |
| `llama3.2:3b` | D | structured | schema | 26/50 | 52.0% | 0 |
| `qwen3:4b` | A | plain | json | 0/50 | 0.0% | 72 |
| `qwen3:4b` | B | structured | json | 4/50 | 8.0% | 76 |
| `qwen3:4b` | C | plain | schema | 30/50 | 60.0% | 2 |
| `qwen3:4b` | D | structured | schema | 30/50 | 60.0% | 0 |

## Contrasts

| Model | Schema minus JSON | Structured minus plain | Interaction |
| --- | ---: | ---: | ---: |
| `llama3.2:3b` | 20.0 pts | 8.0 pts | 0.0 pts |
| `qwen3:4b` | 56.0 pts | 4.0 pts | -8.0 pts |

## Figures

- `success_by_condition.svg`
- `success_heatmap_by_failure_type.svg`
