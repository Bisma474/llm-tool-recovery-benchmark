# Repository Plan

## Goal

Turn this research folder into a professional, reproducible repository without losing the old exploratory work. The repo should clearly separate:

- old prototype experiments,
- the revised v2 harness,
- raw experiment outputs,
- paper drafts,
- audit notes,
- future held-out evaluation work.

## Recommended Repository Layout

```text
research/
  README.md
  LICENSE
  .gitignore
  docs/
    RESEARCH_AUDIT.md
    REVISED_RESEARCH_PROTOCOL.md
    PAPER_DRAFT.md
    RESULTS_SUMMARY.md
  src/
    recovery_harness.py
    evidence_formats.py
    experiment_runner.py
    analyze_local_pilot.py
    check_ollama_api.py
  scripts/
    run_validation.py
    run_evidence_validation.py
    run_offline_experiment.py
    run_local_pilot.py
  tests/
    test_recovery_harness.py
    test_evidence_formats.py
    test_experiment_runner.py
  experiments/
    manifests/
    summaries/
    selected_results/
  archive/
    original_prototype/
  outputs/
    .gitkeep
```

## What Should Be Versioned

Commit these:

- source code,
- tests,
- small CSV summaries,
- selected final result reports,
- paper drafts,
- protocol and audit documents,
- environment notes,
- reproducibility instructions.

Do not commit these by default:

- `.venv/`,
- `__pycache__/`,
- raw `requests.jsonl` and `responses.jsonl` logs,
- huge model output folders,
- secrets such as `key.txt`,
- temporary plots or duplicate old logs unless intentionally archived.

Raw outputs should stay local, or be released separately as an artifact later.

## Branch Plan

Use branches for purpose, not for every small task.

| Branch | Purpose |
| --- | --- |
| `main` | Stable, professional repo: clean code, tests pass, current draft, selected results. |
| `dev` | Active working branch for new scripts, refactors, and analysis changes. |
| `paper-draft` | Paper text, figures, result tables, writing changes. |
| `experiment-runs` | Run manifests, selected summaries, and analysis outputs. Avoid huge raw logs. |
| `heldout-eval` | Future frozen held-out scenarios and confirmatory runs. |
| `archive-original` | Old prototype code preserved for history, not used for main claims. |

Suggested flow:

```text
dev -> main
paper-draft -> main
experiment-runs -> main
heldout-eval -> main only after protocol freeze
```

## First Cleanup Milestone

1. Create `.gitignore`.
2. Move v2 code into `src/`, `scripts/`, and `tests/`.
3. Move paper/protocol docs into `docs/`.
4. Move old prototype files into `archive/original_prototype/`.
5. Keep only selected result summaries in `experiments/`.
6. Run all tests.
7. Initialize Git.
8. Commit as `initial structured research repo`.

## Important Safety Rule

Do not push this repository anywhere until `key.txt` and other secrets are removed from version control and confirmed ignored.

## Near-Term Research Branch Workflow

After cleanup:

1. `dev`: add seed aggregation script.
2. `experiment-runs`: add summaries for Qwen seed 42, Llama seed 42, Llama seed 43, and Qwen seed 43 after it completes.
3. `paper-draft`: update the paper with multi-seed tables.
4. `main`: merge only after tests pass and docs are coherent.

