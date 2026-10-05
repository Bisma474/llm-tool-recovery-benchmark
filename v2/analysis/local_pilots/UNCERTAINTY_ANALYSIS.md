# Uncertainty Analysis for Local Pilots

Runs analyzed: 4; bootstrap iterations: 10000.
Wilson intervals describe aggregate success proportions. Contrast intervals use a scenario-cluster bootstrap: each of the 25 scenario IDs is one resampling unit, with seed results averaged within scenario.

## Success Rates

| Model | Condition | Successes | Rate | Wilson 95% interval |
| --- | --- | ---: | ---: | ---: |
| `llama3.2:3b` | A | 12/50 | 24.00% | [14.30%, 37.41%] |
| `llama3.2:3b` | B | 16/50 | 32.00% | [20.76%, 45.81%] |
| `llama3.2:3b` | C | 22/50 | 44.00% | [31.16%, 57.69%] |
| `llama3.2:3b` | D | 26/50 | 52.00% | [38.51%, 65.20%] |
| `qwen3:4b` | A | 0/50 | 0.00% | [0.00%, 7.13%] |
| `qwen3:4b` | B | 4/50 | 8.00% | [3.15%, 18.84%] |
| `qwen3:4b` | C | 30/50 | 60.00% | [46.18%, 72.39%] |
| `qwen3:4b` | D | 30/50 | 60.00% | [46.18%, 72.39%] |

## Paired Contrasts

| Model | Contrast | Estimate | Bootstrap 95% interval |
| --- | --- | ---: | ---: |
| `llama3.2:3b` | schema_minus_json | 20.00 points | [4.00, 36.00] |
| `llama3.2:3b` | structured_minus_plain | 8.00 points | [-12.00, 28.00] |
| `llama3.2:3b` | interaction | 0.00 points | [0.00, 0.00] |
| `qwen3:4b` | schema_minus_json | 56.00 points | [36.00, 74.00] |
| `qwen3:4b` | structured_minus_plain | 4.00 points | [0.00, 10.00] |
| `qwen3:4b` | interaction | -8.00 points | [-20.00, 0.00] |

These intervals quantify uncertainty for this controlled pilot. They do not justify broad population-level claims beyond the tested models and scenario family.
