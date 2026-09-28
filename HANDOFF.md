# Handoff: LLM Tool-Failure Recovery Benchmark

This document is for continuing the project in a new chat. Do not push this file unless explicitly requested.

## Repository

GitHub repo:

```text
https://github.com/Bisma474/llm-tool-recovery-benchmark
```

Local path:

```text
F:\research
```

Current local branch at handoff:

```text
paper-draft
```

Local uncommitted docs at handoff:

```text
README.md
v2/PAPER_DRAFT.md
HANDOFF.md
```

Important rule from user:

```text
Do not use "Codex" in branch names, commit messages, PR titles, PR bodies, or repo-facing text.
```

The repository has already been initialized and pushed with purpose branches.

## Branches

| Branch | Purpose |
| --- | --- |
| `main` | Stable root documentation only. |
| `dev` | Active v2 research code. |
| `paper-draft` | Paper draft text. |
| `experiment-runs` | Selected result summaries only, not raw logs. |
| `archive-original` | Old exploratory prototype and audit materials. |
| `heldout-eval` | Reserved future branch for frozen held-out evaluation. |

Commits already pushed:

```text
main:
  Add repository documentation

dev:
  Add recovery harness validation
  Add evidence format checks
  Add four condition experiment runner
  Add local model pilot runner
  Add pilot analysis script

paper-draft:
  Add initial paper draft

experiment-runs:
  Add selected pilot result summaries

archive-original:
  Add research audit documents
  Archive original prototype experiments
  Archive blinded analysis summary
```

## Files To Know

Root:

```text
README.md
REPO_PLAN.md
.gitignore
HANDOFF.md
```

v2 code:

```text
v2/recovery_harness.py
v2/evidence_formats.py
v2/experiment_runner.py
v2/run_validation.py
v2/run_evidence_validation.py
v2/run_offline_experiment.py
v2/check_ollama_api.py
v2/run_local_pilot.py
v2/analyze_local_pilot.py
v2/PAPER_DRAFT.md
```

Audit/protocol:

```text
audit/RESEARCH_AUDIT.md
audit/REVISED_RESEARCH_PROTOCOL.md
```

## Data Policy

Do not commit or push these by default:

```text
key.txt
.venv/
__pycache__/
v2/outputs/
*.jsonl
requests.jsonl
responses.jsonl
generated figures
```

The `.gitignore` already excludes these.

Raw `v2/outputs/` remain local. The `experiment-runs` branch contains only selected `RESULTS.md` and analysis CSV summaries.

## Current Research State

Research question:

```text
When LLM agents receive equivalent evidence about a failed or unreliable tool execution,
how do execution-history representation and output-schema enforcement affect verified recovery?
```

Experiment design:

| Condition | History evidence | Response generation |
| --- | --- | --- |
| A | Plain key-value log | JSON mode with prompted schema |
| B | Structured JSON record | JSON mode with prompted schema |
| C | Plain key-value log | Enforced response schema |
| D | Structured JSON record | Enforced response schema |

Scenarios:

```text
25 scenarios total
5 failure types x 5 variants
```

Failure types:

```text
invalid_arguments
persistent_unavailability
temporary_timeout
malformed_output
plausible_incorrect_output
```

Each full model run:

```text
100 episodes = 25 scenarios x 4 conditions
```

## Completed Model Runs

### qwen3:4b seed 42

Output folder:

```text
F:\research\v2\outputs\local_pilot_20260927T140515_796428Z
```

Result:

| Condition | Setup | Success |
| --- | --- | ---: |
| A | plain + JSON | 0/25 |
| B | structured + JSON | 2/25 |
| C | plain + schema | 15/25 |
| D | structured + schema | 15/25 |

### qwen3:4b seed 43

Output folder:

```text
F:\research\v2\outputs\local_pilot_20260928T141812_603243Z
```

Result:

| Condition | Setup | Success |
| --- | --- | ---: |
| A | plain + JSON | 0/25 |
| B | structured + JSON | 2/25 |
| C | plain + schema | 15/25 |
| D | structured + schema | 15/25 |

The Qwen seed 43 run matched seed 42 success counts exactly.

### llama3.2:3b seed 42

Output folder:

```text
F:\research\v2\outputs\local_pilot_20260928T124701_310525Z
```

Result:

| Condition | Setup | Success |
| --- | --- | ---: |
| A | plain + JSON | 6/25 |
| B | structured + JSON | 8/25 |
| C | plain + schema | 11/25 |
| D | structured + schema | 13/25 |

### llama3.2:3b seed 43

Output folder:

```text
F:\research\v2\outputs\local_pilot_20260928T134617_595431Z
```

Result:

| Condition | Setup | Success |
| --- | --- | ---: |
| A | plain + JSON | 6/25 |
| B | structured + JSON | 8/25 |
| C | plain + schema | 11/25 |
| D | structured + schema | 13/25 |

The Llama seed 43 run matched seed 42 success counts exactly.

Both local models now have two completed seeds. Total completed real model episodes:

```text
400 episodes = 2 models x 2 seeds x 25 scenarios x 4 conditions
```

The user also stopped the local Ollama models after the Qwen seed 43 run:

```powershell
ollama stop llama3.2:3b
ollama stop qwen3:4b
```

## Cloud Model Findings

Ollama Cloud access worked after sign-in.

Tested:

```text
gpt-oss:20b-cloud
gemma4:cloud
```

Both could run, but both failed the strict schema-enforcement probe through the current Ollama API path. Therefore, do not use them for the main A/B/C/D experiment until schema enforcement is verified.

Smoke check command:

```powershell
cd F:\research
python .\v2\check_ollama_api.py --model MODEL_NAME --timeout 300
```

Known passing local schema check:

```text
qwen3:4b
llama3.2:3b
```

## Commands

Offline validation:

```powershell
cd F:\research
python .\v2\run_offline_experiment.py
```

Expected:

```text
PASS: 43 tests; all 100 scripted episodes completed across A/B/C/D.
```

Model smoke check:

```powershell
cd F:\research
python .\v2\check_ollama_api.py --model llama3.2:3b --timeout 300
```

Short shakedown:

```powershell
cd F:\research
python .\v2\run_local_pilot.py --model llama3.2:3b --max-episodes 4
```

Full run:

```powershell
cd F:\research
python .\v2\run_local_pilot.py --model qwen3:4b --seed 43
```

Analyze run:

```powershell
cd F:\research
python .\v2\analyze_local_pilot.py F:\research\v2\outputs\LOCAL_PILOT_FOLDER
```

## Immediate Next Step

Aggregate the four completed runs:

1. Add or run a multi-run aggregation script.
2. Summarize both seeds per model in one table.
3. Update `v2/PAPER_DRAFT.md` on the `paper-draft` branch.
4. Add selected summaries to `experiment-runs` only if the user asks.
5. Keep `HANDOFF.md` local unless the user explicitly asks to commit it.

## Repo Work Next

The repo is pushed, but not fully restructured into `src/`, `scripts/`, `tests/`, and `docs/` yet. `REPO_PLAN.md` describes the intended professional structure.

Recommended cleanup branch:

```text
dev
```

Potential future commits:

```text
Move v2 code into package structure
Move scripts into scripts directory
Move tests into tests directory
Move draft and protocol docs into docs
Add result aggregation script
Add multi-seed summary table
```

Keep commits small and meaningful.

## Current Paper Claim

Safe current claim:

```text
In a controlled tool-recovery harness, schema-constrained generation improved verified recovery
across two small local models and was stable across seeds 42 and 43. Structured JSON history had
no effect for qwen3:4b under schema enforcement and a modest positive effect for llama3.2:3b,
but the main bottleneck remained valid, supported recovery behavior rather than history
representation alone.
```

Do not claim final publication-level evidence yet. The project still needs:

```text
multi-seed aggregation
possibly one stronger schema-reliable model
held-out scenario templates
cluster-aware uncertainty estimates
literature comparison
```

