# Revised research path: execution-history representation and recovery

Status: proposed protocol, 26 September 2026. Freeze the final version before held-out evaluation. This document does not report new experimental results.

## Decision and scope

Continue with a narrow controlled empirical study. Working title: **Execution-History Format and Output Constraints in LLM Tool-Failure Recovery**.

Research question: When agents receive equivalent evidence about a failed execution, how does the representation of that history affect verified recovery, and does enforcing the action-output schema change that effect?

Treat input-record reproduction as a candidate mechanism, not an established explanation. Existing experiments are development evidence only. The new study concerns recovery from a supplied failed attempt; it does not claim autonomous failure detection, full provenance graphs, or general production reliability.

## Position relative to related work

Schema First Tool APIs (https://arxiv.org/abs/2603.13404) studies interface contracts and diagnostics. Hold the tool documentation fixed here and vary execution history plus output constraints. ToolMaze (https://arxiv.org/abs/2606.05806) studies replanning under tool perturbations; use it as a reference for fault realism and potential external replication. These distinctions are proposed scope boundaries, not proof of novelty. Before the main run, complete a comparison matrix for the closest work: manipulated variables, fixed information, failure persistence, output constraints, models, outcome verification, and overlap with our contribution.

## Main experiment

Use a 2 x 2 design to keep the initial study interpretable and affordable:

| Condition | History evidence | Response generation |
|---|---|---|
| A | Plain key-value log | JSON mode with a prompted schema |
| B | Structured JSON record | JSON mode with the same prompted schema |
| C | Plain key-value log | Enforced response JSON schema |
| D | Structured JSON record | Enforced same response JSON schema |

Use the exact same model-visible output-schema instructions in all four conditions; change only the backend schema constraint between the two response-generation settings. Tool names, argument schemas, task facts, failure observations, budgets, sampling configuration, and environment state remain identical within a paired scenario. Do not call condition A unconstrained natural language: JSON mode still constrains syntax.

Generate history renderings from one canonical observation record and verify field coverage automatically and by a small manual review. Do not insert hidden failure labels or preferred recovery actions. Use neutral condition wording rather than labeling one representation as superior. Keep message roles and instruction placement fixed. Render subsequent tool observations consistently within the assigned condition. Log prompt lengths and prevent truncation; natural token-length differences are part of the format intervention, not proof of a pure syntax effect.

Primary estimand: interaction in success-rate differences, (D - C) - (B - A). This asks whether the effect of history format changes under schema enforcement. Also report all four success rates and the two format contrasts with intervals, including null and negative effects. Prespecify these comparisons without assuming a winner.

Optional later ablations: narrative history, absent history, alternative field names/order, and native tool calling. Do not add them to the first experiment unless the literature review shows they are essential. Missing history tests information availability, a separate question.

## Environment and faults

Build a small local sandbox with fixture-backed files, a SQLite database, deterministic computation, and a primary/fallback retrieval service. At least two task families should require combining tool outputs rather than reading off a known answer. Expose a stable tool catalog in every condition. Keep expected answers and state oracles outside the model context.

| Fault | Required environment behavior | Valid recovery example |
|---|---|---|
| Invalid arguments | Original malformed arguments continue to fail | Correct the type, key, or permitted value |
| Transient timeout | A documented simulated state rule allows a later retry | Retry within budget |
| Persistent unavailability | Original service remains unavailable throughout episode | Use a documented fallback |
| Malformed output | Actual schema violation; blindly repeating the same call need not fix it | Change a supported option or use an alternate source |
| Plausible wrong output | Schema-valid but incorrect/stale content; a verification route exists | Cross-check and use supported evidence |

For the recovery-conditioned study, tell every condition that the initial attempt did not complete the task reliably, including content-quality failures. Do not claim that the agent discovered the initial fault. For every scenario, record what evidence makes recovery possible. Avoid cases requiring access to hidden information unavailable through the catalog.

State persists across actions and is reset between episodes. Faults do not disappear merely because the model selected the original tool. All legal proposed actions execute; correctness is determined from outcomes, not equality to a single gold action. Support multiple valid recovery paths.

Use a maximum of three recovery tool calls followed by one final-answer turn. Specify how invalid JSON and invalid calls consume turns before running; apply the rule identically. A recommended simple rule is three action opportunities, with invalid responses consuming an opportunity, then one final-answer turn. Actual calls can therefore be fewer than three. No extra model-driven repair loop is granted only to one condition.

Add healthy and irrecoverable control suites separately. Correct abstention is reported separately from successful recovery and requires an observable basis; do not reward blind refusal. Keep all tools local and all side effects confined to per-episode state.

## Outcomes and evaluation

Primary outcome: correct task result, supported by required executed tool evidence, within the recovery budget on the recoverable set. Define deterministic per-task oracles before model runs; validate output content and relevant final environment state. Include nontrivial retrieval tasks so memorized/mental answers cannot dominate.

Secondary outcomes: JSON parsing, schema compliance, executable action rate, recovery attempts, futile repeated calls, final-answer correctness, unsupported success claims, tokens, and time. Keep success and schema compliance separate: a valid action object may still be semantically wrong.

Define input-record reproduction using an explicit structural detector, and manually audit a blinded sample including detector positives and negatives. Do not infer intent from the detector or silently convert copied records into successful actions. Investigate whether constraints reduce reproduction and improve success, but do not label that association a proven mediation mechanism.

Avoid requiring a diagnosis before every action in the primary experiment; that can alter the behavior being studied. If diagnosis is included as a secondary study, provide an enum with unknown/insufficient-evidence and adjudicate evidence quality separately.

## Validation gates and run sizes

1. **Literature and specification:** finish the closest-work comparison, fixed tool contracts, canonical history renderer, and scoring specification. Gate: a clearly stated contribution beyond repeating prior results.
2. **Harness validation:** create development fixtures covering all five faults. A known recovery policy must pass each recoverable fixture; deliberately wrong actions must fail. Always-retry must fail persistent-fault cases; changing arguments must matter in argument-error cases. Healthy and impossible controls must behave as specified.
3. **Diagnostic model pilot:** proposed 20 development scenarios x 4 conditions x 2 models x 3 recorded sampling seeds = 480 episodes, plus controls. This is a debugging/design pilot, not a powered confirmatory sample. Include at least one different model family; select exact models after checking available hardware and schema support. Keep per-model decoding settings fixed and record actual runtime configuration. Seed replay is useful metadata, not a guarantee of hardware-level determinism.
4. **Freeze:** remove leakage and floor/ceiling problems using development data only; finalize the protocol, analysis, prompt templates, model versions, and exclusions. Choose a minimum meaningful effect and estimate sample needs using base-task clustering and pilot discordance. Precision requirements and resources determine held-out sample size.
5. **Held-out evaluation:** split by task template/family so close paraphrases and injected-failure variants do not cross from development into test. Use fresh scenarios, multiple model families, and repeated runs. Randomize/counterbalance conditions. Never tune prompts on these outcomes. For budgeting only, 100 scenario instances x 4 conditions x 3 models x 3 seeds would be 3,600 episodes; this is not a power justification and does not mean 3,600 independent tasks. At four model turns per episode the ceiling would be 14,400 requests before controls.
6. **Replication and writing:** if the effect is informative, replicate on a second task environment or suitable external benchmark subset. Present every condition, uncertainty, negative results, costs, and limits.

Use paired comparisons on matched scenarios. Aggregate repeated runs appropriately and use a cluster-aware bootstrap or hierarchical model that respects base-task/template dependence; do not bootstrap trial rows independently. For a small number of tested models, report model-specific estimates rather than implying representativeness of all LLMs. Preregister treatment of infrastructure failures, budget exhaustion, and missing runs. Output failures count as outcomes, not exclusions. Correct multiplicity for additional exploratory contrasts.

## Baselines and reproducibility

Run always-retry and a simple observable-error rule policy. A privileged oracle policy validates feasibility and is not a fair model competitor. A schema-constrained model is part of the factorial design, not evidence by itself of superior reasoning.

Store immutable per-run JSONL records with the rendered prompt, raw and parsed response, validation results, every state transition and tool output, oracle verdict, model digest, runtime/library versions, sampling parameters and seeds, finish reason, tokens, warm-up policy, and separate loading/inference/end-to-end timing. Avoid comparing one-call and two-call timing. Use append-only checkpoints and unique run IDs; preserve original pilot files.

## Decision after the pilot

Proceed if the benchmark works, the novelty review supports the question, and the study can give a useful estimate or explain a reproducible failure. A positive effect is not a requirement. If the phenomenon is limited to one prompt/model, characterize it as such or pivot. If existing work already answers the question, narrow or change the contribution before increasing the run budget. A null conclusion requires informative uncertainty; lack of significance alone is not evidence of equivalence.

## Immediate implementation order

Create a separate v2 directory with scenario/state definitions, a tool registry, canonical evidence renderers, response validators, deterministic task oracles, an episode runner, and paired analysis. First implement one invalid-argument scenario and one persistent-unavailability scenario end to end with scripted policies. Extend to the remaining fault types only after those tests pass. Then run the small model pilot. Do not launch another 500-trial version of the original runner.
