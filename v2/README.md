# Validate five recovery scenarios without an LLM

## Real local-model development pilot

`python F:\research\v2\run_local_pilot.py` runs five existing development scenarios under A/B/C/D using local `qwen3:4b`. This is a real model run, unlike the offline scripts. It uses temperature 0, seed 42, 4096 context tokens, 256 output tokens, `think=false`, and the same prompts/schema already checked. No cloud service or pip package is needed. Do not run a second copy while a pilot is active.

Each run creates a unique `outputs/local_pilot_*` directory containing a source-hashed manifest, requests checkpointed before generation, raw responses checkpointed after each call, completed episode logs, and a summary CSV. It does not strip thinking, repair malformed output, or retry infrastructure failures. An infrastructure error stops the run and retains partial data; restarting creates a new run rather than silently replacing old outcomes. There is no automatic resume. A 300-second client timeout does not guarantee the server stopped generating.

`COMPLETED` means the schedule finished, not that every task succeeded. Success, invalid responses, observable thinking fields/tags, truncation, timing, tokens, and tool results remain available for diagnosis. All timing includes the backend call and may include cold loading or cache effects. Five easy development fixtures, one model, and one seed cannot establish a general format advantage. A known reliable backup makes these fixtures particularly limited. This is an integration/difficulty pilot only.

## Check the installed local model through the API

```powershell
python F:\research\v2\check_ollama_api.py
```

Requires running Ollama and the already-downloaded `qwen3:4b`; no pip packages or API key. It makes five short real local model requests, each with `think=false`, a 4096-token context, temperature 0, seed 42, and a 256-token output limit. Each request has a 180-second client timeout. Models remain loaded for five minutes. A client timeout does not guarantee server-side generation has stopped; check Ollama before rerunning if a timeout occurs.

The probes check plain READY compliance, the same action prompt under JSON mode and the experiment schema, and a conflicting prompt under JSON mode versus a small enforced schema. The latter is a diagnostic of whether the backend respects a schema when the prompt requests something else; it is not a research task. A five-request check cannot guarantee universal enforcement. The shared local validator rejects floating-point representations for integer fields, matching this harness's stricter contract.

The script records raw responses without removing thinking, tags, or malformed text. It distinguishes returned `message.thinking` from `message.content`, checks explicit thinking tags, and records finish reason, timing and tokens returned by Ollama. Plain text that differs from READY requires inspection; this is not a claim about internal model reasoning. `/api/show`, model digest, Ollama version, and loaded-model metadata are recorded too.

Each run saves `outputs/ollama_check_*/report.json`, checkpointed before and after every request. `SMOKE_CHECK_PASSED` means these probes passed; `NEEDS_REVIEW` lists failures for investigation, and `API_ERROR` retains partial results. Do not label either failure state as a successful research run. The optional `--timeout 300` changes only the client timeout. The script never switches models, repairs responses, downloads anything, or uses a cloud service.

## Validate the four-condition runner (latest step)

```powershell
python F:\research\v2\run_offline_experiment.py
```

This runs all 42 tests and 20 scripted episodes (five scenarios times four conditions). Expected final message: `PASS: 42 tests; all 20 scripted episodes completed across A/B/C/D.` No dependencies or model installation are required.

Conditions A/B use plain/structured history and request JSON mode; C/D use the corresponding histories and request the shared response schema. The prompted instructions are identical between A/C and B/D. **The offline backend is a script: it does not implement constrained decoding.** This step checks request construction, validation, action execution, budgets, and outcome logging. It cannot compare LLM performance or establish the effect of schema enforcement. A real backend must implement and verify the requested modes before experiments.

Responses have exactly `action`, `arguments`, and `answer`. A tool action uses a documented tool name, an integer record_id argument, and a null answer. A finish response uses null arguments and a final record (or null if unsuccessful). Shared post-response validation checks every condition equally, including cross-field consistency. The small local validator supports only the schema keywords used here, not arbitrary JSON Schema. Tool integers reject booleans and floats.

Each episode has three action opportunities (invalid responses consume one), then one finish-only turn; early finish is allowed. Tool calls are forbidden on the final turn. The runner logs opportunities separately from executed calls. Each request contains the current complete public execution history rather than a growing chat transcript; it includes the previous response error, but no private oracle. Use this same policy for all later model conditions.

Logs are saved under a new `outputs/offline_runner_*` directory: `response_schema.json`, append-only `scripted_episodes.jsonl` with exact requests/responses, `scripted_summary.csv`, and `validation_report.json`. The 100% scripted success is a wiring check, not a research finding. A seeded shuffled order exercises all cases; it is not a complete statistical counterbalancing design. The runner accepts a backend callable but this milestone adds no real model integration or model-run metadata/resume handling.

## Validate equivalent evidence formats

Run only:

```powershell
python F:\research\v2\run_evidence_validation.py
```

This runs all 31 harness and evidence tests, then exports five pairs into a new timestamped `outputs/evidence_*` directory. Each `case_*` folder contains `plain_evidence.txt` and `structured_evidence.txt` for inspection, plus the separate history and shared-context files. The final message is `PASS: 31 tests; all 5 evidence pairs preserve identical information.`

Only the execution-history representation changes. Task, tool catalog, recovery notice, and remaining budget are identical in both evidence blocks. The plain log uses key=value lines with JSON-encoded values so strings, integers, nested outputs, and newlines remain intact. The structured version uses a nested JSON array. These are not natural-language prose versus JSON conditions.

Validation decodes both histories and compares them with the canonical public history, including value types. Tests reject missing/duplicated fields and unexpected private metadata. This checks the implementation's information preservation; it does not establish equal token length, equal model understanding, or general absence of experimental confounds. Scenario names occur only in filenames/report metadata, not the evidence blocks. These exported files are evidence blocks, not complete model prompts. No LLM is called.

## Validate the recovery harness alone

This is a local Python simulation. It uses no Ollama, model, API key, internet connection, or third-party Python packages. Python 3.10 or later is sufficient. Python 3.11.9 was available when this was created.

Open PowerShell and run:

```powershell
cd F:\research
python .\v2\run_validation.py
```

If Windows cannot find `python`, try `py -3 .\v2\run_validation.py` instead. You can also run the script using its full path from another directory.

The command first runs 20 automated checks, then shows ten scripted episodes:

| Scenario | Scripted policy | Expected outcome |
|---|---|---|
| Invalid arguments | Keep retrying the string `"101"` | Failure |
| Invalid arguments | Change the argument to integer `101` | Success |
| Persistent primary-service outage | Keep retrying the primary | Failure |
| Persistent primary-service outage | Read from the documented backup | Success |
| Temporary timeout | Retry after the first timed-out request | Success for both policies |
| Malformed output | Repeat and accept the malformed record | Failure |
| Malformed output | Obtain a valid record from the backup | Success |
| Plausible incorrect output | Repeat and accept stale inventory | Failure |
| Plausible incorrect output | Consult the authoritative backup | Success |

`Task outcome: FAILURE` for the always-retry baseline is a successful validation of the environment: a bad strategy must not magically work. The final line reports `PASS: 20 tests` when the automated checks all pass.

Each episode allows three recovery attempts. The initial failed call is supplied separately. The unavailable primary remains offline even after using the backup; correcting an argument does not change environment availability. Every episode starts with fresh state.

Task success requires both a correct final inventory record and a successful recovery tool call that actually returned that record. Merely calling a tool, reading the wrong record, or inventing a correct answer without tool evidence does not count. Different legal recovery paths can succeed.

Files:

- `recovery_harness.py`: tools, persistent episode state, scripted policies, and outcome checker.
- `test_recovery_harness.py`: meaningful positive and negative behavioral checks.
- `run_validation.py`: one command to validate and demonstrate everything.
- `outputs/validation_*.json`: timestamped local logs; previous logs are retained.

The primary/backup inventory tools are deterministic in-memory fixtures, not real network services. This step verifies research infrastructure only. It does not measure intelligence, demonstrate a model advantage, or establish that the benchmark is representative. The scripted recovery rule is intentionally tailored to these five development cases.

Original experiment files are untouched. No model installation is necessary for this milestone.

The timeout is simulated without sleeping: the first valid primary request times out; later requests succeed. New episodes reset that counter. Malformed and stale primary responses persist for the entire episode. `OK` describes tool execution only, not answer correctness. Stale quantities satisfy the output schema but fail the hidden task check. The simple policy consults the documented authoritative replica when the initial result is unreliable. The always-retry baseline stops on tool-reported success, even if the returned content is bad.

All scenarios receive the same public notice that the initial attempt did not reliably complete the task. This tests recovery after a supplied failure; it does not test autonomous detection. The backup is deliberately reliable in these development fixtures, so these five cases alone are not a diverse research benchmark.
