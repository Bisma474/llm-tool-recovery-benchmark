# Research audit and proposed restart

Date: 26 September 2026. Scope: files supplied in F:/research.

## Assessment

This is an exploratory prototype studying whether execution history, especially structured provenance, helps an LLM recover from tool failures. There is substantial implementation and pilot work, but the current experiments do not establish that structured provenance improves genuine recovery. The central problems are experimental controls, simulated failure semantics, output compliance, and evaluation validity.

“Unsupported” is more accurate than “false” for the broad research hypothesis. The checked saved scores reproduce; this audit found no scoring discrepancies in those checks. That is not independent authentication of how model responses were generated. No manuscript, research proposal, literature review, preregistration, or run manifest was present in the inspected project files, so claims outside these files remain unaudited.

## Work already present

| Component | Evidence | Status |
|---|---|---|
| Deterministic tool harness | Five tools in experiment_harness.py | Reusable prototype; mostly dictionary lookups, not external tools |
| Scenario collection | 125 scenarios: 5 tools x 5 failure types x 5 examples | Only 25 distinct underlying tasks |
| Normal tool validation | 25 saved checks | Smoke checks, not a complete semantic oracle |
| Failure validation | 125 saved checks | Checks flags/non-null output; weak evidence of realistic failure behavior |
| Early pilots | Native tool and JSON recovery pilots, plus main pilot | Development evidence; main pilot contains 100 records despite printing “Expected: 20” |
| Main experiment | 500 records, four conditions | Complete saved grid; serious answer leakage and unequal evidence |
| Blinded experiment | 500 records, four conditions | Complete saved grid; partial redesign, residual leakage and output-shape failure |
| Analysis | Original figures, corrected figures, experiment comparison | Useful descriptive work; corrections do not fix data-generation confounds |

Both main logs have exactly one record for each of 125 scenarios under each of four conditions. There are no missing or duplicate scenario-condition pairs. Current scripts specify qwen3:4b; saved main logs do not independently capture model digest, runtime version, or full request configuration.

There is no defensible percentage of “research completed” without a target protocol or thesis scope. The accurate milestone is: prototype and exploratory experiments completed; confirmatory evidence and publication claims not yet established.

## Recomputed results

Each row below contains 125 trials. “Action” is exact equality with the original tool and arguments. “Diagnosis” is the existing substring scorer. Neither is independently validated end-to-end recovery.

| Experiment | Condition | Exact action | Diagnosis | Mean score / 2 |
|---|---|---:|---:|---:|
| Original | No history | 9.6% | 0.0% | 0.096 |
| Original | Raw history | 4.8% | 0.0% | 0.048 |
| Original | Plain log | 16.8% | 0.0% | 0.168 |
| Original | Structured provenance | 29.6% | 42.4% | 0.720 |
| Blinded | No history | 0.0% | 0.0% | 0.000 |
| Blinded | Raw history | 5.6% | 6.4% | 0.120 |
| Blinded | Plain log | 8.0% | 13.6% | 0.216 |
| Blinded | Structured provenance | 0.8% | 4.0% | 0.048 |

These values reproduce the corresponding existing corrected/combined tables. The blinded result does not support a general structured-provenance advantage. It also does not establish that structured provenance is inherently worse: several aspects of the prompt changed simultaneously, and schema compliance differs dramatically.

## Findings that invalidate or limit the current interpretation

### 1. Original conditions do not isolate representation

In main_experiment.py, raw history and plain log are generic statements without the actual submitted arguments or returned evidence. Structured provenance alone receives those details and explicit error metadata. The comparison therefore mixes information availability with representation format.

The first-stage prompt explicitly supplies the correct tool (line 117). The second-stage prompt supplies the correct failure type (line 170). That second request is a fresh conversation without the original task, recovery action, or recovered output. A nonempty final answer cannot establish task completion.

Action: retain this run as a confounded exploratory pilot. Do not use it to claim a causal format advantage.

### 2. The blinded run is not fully label-blind

Removing error_type did not remove the message generated in experiment_harness.py: `simulated invalid_parameter`, `simulated timeout`, and `simulated unavailable_tool`. These leak the exact scored label in 75 of the 125 scenarios to all three history-bearing conditions. No-history receives no corresponding diagnostic evidence.

Natural error messages are legitimate observations. The problem here is treating literal benchmark category names as independent diagnostic evidence while describing the experiment as label-blind. Replace synthetic taxonomy strings with realistic observable symptoms and define exactly what “blind” means.

### 3. Recovery is guaranteed by the evaluator once a response matches

Both runners accept only the original tool and original arguments, then call the tool with FailureType.NONE. I replayed all 125 scenarios locally: every original argument set succeeds unchanged when the fault is removed.

Invalid-parameter trials do not actually contain invalid arguments. Unavailable tools become available automatically. The model neither fixes the inputs nor restores availability. Even persistent faults are effectively treated as transient. Thus the outcome is largely exact action reproduction under an automatically repaired environment.

The blinded prompt permits alternative tools or stating recovery is impossible, but the scorer rejects both. This is an instruction/evaluation mismatch.

Action: replace this mechanism before a main rerun. Execute proposed actions against a persistent scenario state and judge their actual effects.

### 4. Structured inputs frequently displace the requested output schema

In the blinded structured condition, 119/125 responses parse as JSON objects, but only 18/125 contain all three requested top-level keys. A transparent heuristic identifies 101/125 objects with `task` and `attempt` or `input_arguments`, i.e. provenance-shaped responses. This is evidence of input-record reproduction, not a semantic diagnosis of every response. The corresponding count in the original structured condition is 46/125.

For example, blinded scenario_001 returns the task, attempt, observed_result, and failed status rather than action/arguments/diagnosis. Its failure is therefore not simply a poor recovery decision.

The runners request format="json", not an output JSON schema. Ollama supports passing a JSON schema and validating the result. Apply the same constraints to every condition, and separately measure JSON parsing, schema compliance, valid tool invocation, and successful task completion. See [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

### 5. Diagnosis scoring measures label spelling as well as understanding

The scorer checks whether the literal snake_case failure name appears in free text. A diagnosis saying “invalid parameter” can be rejected for not saying “invalid_parameter”. Conversely, a negated label or list of possible labels can pass.

The audit found seven rejected responses across the main logs containing the label after simple underscore/hyphen normalization. These are surface-form sensitivity examples, not seven adjudicated correct diagnoses. The saved examples should be reviewed with a rubric.

Action: request a diagnosis enum including unknown/insufficient_evidence, plus a rationale. Score category separately from evidence quality. Permit uncertainty when observations cannot identify the underlying cause.

### 6. The original four-point score double counts and leaks credit

Exact action validity and non-null recovery output are effectively two credits for the same event. A further credit comes from reproducing a supplied diagnosis and producing any nonempty final answer. The corrected two-point score removes that contaminated final-stage credit but still combines diagnosis and action with arbitrary equal weight; it does not resolve the experiment's causal confounds.

Action: use actual task success as the primary endpoint. Keep diagnosis and action metrics separate and secondary.

### 7. Statistical analysis ignores the repeated design

make_figures.py uses independent-sample Mann–Whitney tests and chi-square comparisons despite each scenario appearing under all four conditions. test.py similarly compares the two runs as independent samples. The same 25 underlying tasks also recur across five injected failures. Pooling three controls further mixes conditions and dependencies.

Action: predefine a primary paired contrast. For binary outcomes, paired scenario analysis is a starting point, but account for shared base-task clusters using cluster-aware resampling or an appropriate hierarchical model. Report paired effect sizes and uncertainty; correct exploratory multiple comparisons. Reanalysis cannot repair unequal evidence or unrealistic faults. Neither statistical significance nor resampling establishes generalization from these 25 hand-authored tasks.

### 8. Fault detection and fault recovery are conflated

Malformed and misleading outputs are returned with success=True and no error_type by the harness, yet the blinded context announces status=failed. That is acceptable for a study explicitly conditioned on a detected failure, but it cannot demonstrate autonomous failure detection. The misleading output is always an overtly irrelevant sentence, and malformed output always uses the same wrapper. Neither covers realistic variation well.

Action: separate detection from recovery experiments. Include normal outputs as controls in any detection study; define expected output schemas and task correctness checks.

### 9. Timing and reproducibility need redesign

The original runner times two model calls, while the blinded runner times one. Both set keep_alive=0, which requests immediate model unloading, so latency can include repeated model loading. These are not comparable clean measures of recovery-decision speed. The Ollama API exposes load duration, token counts, evaluation duration, and completion reason; record them. See [Ollama chat API](https://docs.ollama.com/api/chat).

Conditions always run in a fixed order. Seeds and temperature are not explicitly controlled. The logs omit full prompts, token counts, finish reasons, model digest, and runtime metadata. Existing evidence cannot establish whether malformed responses were truncated by num_predict=256.

Several paths are hardcoded to G:/research although this workspace is F:/research. Logs are written only at the end of a run, risking loss after an interruption. There is no supplied dependency lockfile or conventional test suite; test.py is an analysis script.

## What to keep, revise, and rerun

Keep original logs and figures as immutable pilot evidence, the scenario inventory as seed material, raw model responses, the deterministic-tool approach, and the work distinguishing first-stage metrics from the contaminated final score.

Revise the scientific question, equal-information controls, tool catalog, stateful failure implementation, outcome oracle, schema handling, and reproducibility records. Replace conclusion-shaped chart titles such as “Structured provenance improves direct recovery” with neutral descriptions in future figures.

Rerun the substantive experiment after those changes. Replotting or rescoring existing runs cannot recover a clean test. New runs should use fresh tasks held out from prompt development. Historical logs can support an explicitly exploratory error analysis.

## Proposed next experiment

Primary question: Does structured execution evidence improve verified task completion compared with the same evidence represented as a plain log?

1. Give every condition the same available-tool catalog, argument schemas, user task, and action budget. Keep task-specific correct answers out of prompts.
2. Construct one canonical observation record per scenario. Render its same facts as narrative history, key-value log, or structured JSON. Treat missing history as a separate information-ablation condition, not the sole evidence for a formatting claim.
3. Implement genuine faults: incorrect argument keys/types requiring correction; a timeout that resolves after a defined state transition; persistent tool unavailability requiring a documented fallback or justified stop; malformed output requiring validation/requery; plausible wrong output requiring an independent check. Do not require every fault to be recoverable.
4. Execute actions against isolated persistent state for a fixed budget, e.g. three recovery actions. Verify terminal state or answer against a hidden deterministic oracle. Report successful completion and justified non-completion separately.
5. Use identical output schema enforcement in all primary conditions. Add unconstrained JSON as a separate ablation to investigate the observed record-copying failure.
6. Include always-retry and simple rule-based recovery baselines. Include healthy-tool and impossible-recovery controls. A useful benchmark must distinguish correct adaptation from retrying everything.
7. Split by base task/template, not individual failure row. Develop prompts on a pilot split and freeze them before held-out evaluation. Randomize/counterbalance condition order and use repeated runs. Choose sample size from pilot variance, base-task clustering, and a prespecified minimum meaningful effect; do not call 500 records 500 independent tasks.
8. Start with the current model for continuity and a second model for a limited replication if resources allow. Log model digest, runtime, hardware, seeds, sampling settings, actual prompts, raw responses, state transitions, tokens, completion reason, and timing components. Save append-only trial records and resume safely.

First implementation milestone: a small balanced harness validation set covering every fault type, with a known successful policy and deliberately incorrect policies. Require the oracle to accept correct recovery and reject unchanged retries for persistent faults before spending time on a model experiment.

Second milestone: a small model pilot to verify schema compliance, observability, realistic difficulty, and absence of ceiling/floor effects. Freeze the protocol only after this diagnostic pilot. Do not tune using the eventual held-out set.

Third milestone: run the preregistered comparison, report all conditions and failures, then consider external tasks. The outcome may favor structured evidence, plain logs, or neither; all are legitimate findings.

## Brainstorming the contribution

Best immediate direction: **When does execution-record structure help or interfere with recovery?** The 101/125 provenance-shaped outputs provide a concrete lead. Test the interaction between evidence representation and output-schema enforcement while holding evidence fixed.

Second direction: **Which evidence fields matter?** Ablate arguments, observed output, timing, and prior attempts from otherwise identical records. This can identify useful information without attributing its benefit to formatting.

Third direction: **Recovery under persistent faults.** Compare transient versus persistent failures, justified stopping, fallback use, and recovery cost. This is more demanding and needs the stateful harness first.

These are candidate contributions, not verified novelty claims. A focused literature review remains necessary. As methodological starting points, [tau-bench](https://arxiv.org/abs/2406.12045) evaluates tool-agent interactions through task outcomes and repeated-trial reliability, while [ToolEmu](https://arxiv.org/abs/2309.15817) illustrates the need to validate simulated environments and evaluators. Neither paper by itself establishes novelty for this project.

## Audit artifacts and limits

Run `python audit/reproduce_audit.py` from the project root. It makes no model calls, imports only the guarded deterministic harness, and writes only audit/outputs.

- recomputed_summary.csv: counts, schema-key coverage, provenance-shape heuristic, and original metrics.
- integrity_checks.json: pair completeness, score/output consistency, and fault/retry diagnostics.
- diagnosis_surface_form_examples.json: seven examples for manual review.
- source_sha256.json: hashes of top-level Python, JSON, and JSONL sources examined by the reproducibility script; not a signature or historical provenance record.

Original research files were not edited. This audit reran deterministic checks and recomputed saved metrics; it did not rerun the LLM experiments or complete a systematic literature review. A manuscript or supervisor-approved research question, if stored elsewhere, could change the scope of the next phase.
