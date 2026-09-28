# LLM Tool-Failure Recovery Research

This repository contains an ongoing research project on how LLM agents recover from failed or unreliable tool calls.

The current revised study uses a controlled Python harness with inventory-retrieval tasks. It compares:

- plain key-value execution history vs structured JSON execution history,
- prompted JSON output vs schema-constrained output,
- verified task success supported by executed tool evidence.

Current development runs include local Ollama experiments with `qwen3:4b` and `llama3.2:3b` across seeds 42 and 43, for 400 completed real model episodes.

## Current Status

This is ongoing research, not a final publication release.

Completed so far:

- stateful recovery harness,
- 25 controlled scenarios across five failure types,
- four-condition A/B/C/D runner,
- local Ollama integration,
- analysis script,
- first paper draft,
- two local model families tested across two seeds each.

## Key Files

```text
v2/recovery_harness.py          Scenario state, tools, and scoring oracle.
v2/experiment_runner.py         Four-condition episode runner.
v2/run_local_pilot.py           Real Ollama model runner.
v2/analyze_local_pilot.py       Analysis report generator.
v2/PAPER_DRAFT.md               Current paper draft.
audit/RESEARCH_AUDIT.md         Audit of the original prototype.
audit/REVISED_RESEARCH_PROTOCOL.md
REPO_PLAN.md                    Planned professional repo structure and branch workflow.
```

## Validation

Run:

```powershell
cd F:\research
python .\v2\run_offline_experiment.py
```

Expected result:

```text
PASS: 43 tests; all 100 scripted episodes completed across A/B/C/D.
```

## Running a Local Pilot

Example:

```powershell
cd F:\research
python .\v2\run_local_pilot.py --model llama3.2:3b --seed 43
```

Use `--max-episodes 4` for a short shakedown.

## Data Policy

Raw model requests and responses are not committed by default. They can be large and may contain full prompts and outputs. Keep raw `v2/outputs/` folders local unless intentionally packaging a public artifact.

