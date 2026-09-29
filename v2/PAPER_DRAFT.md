# Schema-Constrained Recovery from Tool Failures in a Controlled LLM Agent Harness

## Abstract

Large language model agents often need to recover from failed or unreliable tool calls, but it is unclear how much recovery depends on the representation of execution history and how much depends on the model being forced to produce executable responses. This project studies tool-failure recovery in a controlled local harness where each episode supplies a task, a tool catalog, an initial unreliable attempt, and a fixed recovery budget. We compare four conditions in a 2 x 2 design: plain key-value execution history versus structured JSON history, and prompted JSON output versus enforced response-schema output. In four 100-episode development pilots using local `qwen3:4b` and `llama3.2:3b` across two seeds each, schema-constrained generation generally improved verified task success, but the pattern varied by model. For `qwen3:4b`, success increased from 0/25 and 2/25 in JSON mode to 15/25 and 15/25 in schema mode on both seeds. For `llama3.2:3b`, success increased from 6/25 and 8/25 in JSON mode to 11/25 and 13/25 in schema mode on both seeds. Structured JSON history did not consistently improve recovery, though it helped `llama3.2:3b` modestly. The study remains preliminary because it uses two small local models, two seeds per model, and a synthetic inventory environment.

## Introduction

Tool-using LLM agents are commonly evaluated on whether they can call the right tool and produce the right final answer. In real use, however, a first tool call may fail, return malformed data, use stale cached data, or require a fallback source. A useful agent must not only call tools, but also recover from evidence that the previous action did not reliably complete the task.

Earlier exploratory experiments in this project suggested that structured execution records might help recovery. A later audit showed that those experiments were not sufficient to support that claim. Some conditions received unequal information, some error messages leaked benchmark labels, retries could succeed because faults disappeared rather than because the model recovered, and scoring sometimes rewarded exact action reproduction instead of verified task completion. The revised work restarts the study with a narrower question and a stateful recovery harness.

The current research question is:

> When LLM agents receive equivalent evidence about a failed or unreliable tool execution, how do execution-history representation and output-schema enforcement affect verified recovery?

This separates two issues that are often mixed together. The first is evidence representation: whether the same execution history is shown as a plain key-value log or as structured JSON. The second is response control: whether the model is merely prompted to return a JSON action object or whether the backend enforces the exact response schema.

## Method

The experiment uses a deterministic inventory-retrieval harness. Each episode asks the model to retrieve an inventory record and report `record_id`, `item`, and `quantity`. The model sees a fixed public tool catalog with two tools:

- `lookup_primary`, a primary service that may be unavailable, cached, malformed, or temporarily timed out.
- `lookup_backup`, an independently available authoritative replica.

The hidden oracle knows the correct inventory record. The model does not see the oracle answer. Task success requires a correct final answer and supporting evidence from an executed recovery tool call. A correct answer invented without tool evidence does not count.

Each episode begins with an initial tool attempt already present in the execution history. The model receives the task, tool catalog, public recovery notice, current execution history, and remaining recovery budget. It then receives up to three recovery action opportunities. Invalid responses consume an opportunity. After those opportunities, the model gets one final-answer-only turn.

## Failure Types

The development benchmark contains 25 scenarios, five variants for each of five failure types:

| Failure type | Required recovery behavior |
| --- | --- |
| Invalid arguments | Correct a malformed argument, such as changing a string record id to an integer. |
| Persistent unavailability | Stop retrying an offline primary service and use the backup source. |
| Temporary timeout | Retry a valid primary request after the simulated timeout clears. |
| Malformed output | Extract or recover a valid record when the primary returns a wrapper that violates the public return schema. |
| Plausible incorrect output | Detect stale but schema-valid primary data and use the authoritative backup. |

Faults persist according to explicit state rules. For example, a persistently unavailable primary service remains unavailable for the whole episode, and stale primary data remains stale. This avoids rewarding repeated calls that work only because the environment silently repaired itself.

## Experimental Design

The experiment uses a 2 x 2 design:

| Condition | History evidence | Response generation |
| --- | --- | --- |
| A | Plain key-value log | JSON mode with prompted schema |
| B | Structured JSON record | JSON mode with prompted schema |
| C | Plain key-value log | Enforced response schema |
| D | Structured JSON record | Enforced response schema |

The same canonical observation record is rendered into both history formats. The same task facts, tool catalog, failure observations, budgets, and scoring rules are used across paired conditions. In all conditions, the system prompt describes the same response schema. Conditions C and D additionally pass the schema to the backend for constrained generation.

The pilots used local Ollama with `qwen3:4b` and `llama3.2:3b`, temperature 0, seeds 42 and 43, 4096 context tokens, 256 output tokens, and `think=false`. Each model-seed pair completed 100 episodes: 25 scenarios under each of the four conditions.

## Results

The main result is that schema-constrained generation improved verified task success for both models, and the success counts were stable across seeds 42 and 43. Figure artifacts for these aggregated results are saved as `v2/figures/success_by_condition.svg` and `v2/figures/success_heatmap_by_failure_type.svg`.

| Model | Seeds | Condition | History | Output mode | Successes | Success rate |
| --- | --- | --- | --- | --- | ---: | ---: |
| `qwen3:4b` | 42, 43 | A | plain | json | 0/50 | 0.0% |
| `qwen3:4b` | 42, 43 | B | structured | json | 4/50 | 8.0% |
| `qwen3:4b` | 42, 43 | C | plain | schema | 30/50 | 60.0% |
| `qwen3:4b` | 42, 43 | D | structured | schema | 30/50 | 60.0% |
| `llama3.2:3b` | 42, 43 | A | plain | json | 12/50 | 24.0% |
| `llama3.2:3b` | 42, 43 | B | structured | json | 16/50 | 32.0% |
| `llama3.2:3b` | 42, 43 | C | plain | schema | 22/50 | 44.0% |
| `llama3.2:3b` | 42, 43 | D | structured | schema | 26/50 | 52.0% |

Aggregated contrasts make the pattern clearer:

| Model | Schema minus JSON | Structured minus plain | Interaction `(D - C) - (B - A)` |
| --- | ---: | ---: | ---: |
| `qwen3:4b` | +56.0 points | +4.0 points | -8.0 points |
| `llama3.2:3b` | +20.0 points | +8.0 points | 0.0 points |

The failure-type breakdown shows that schema enforcement mostly helped cases where valid executable actions were the main bottleneck. For `qwen3:4b`, schema mode solved invalid-argument, temporary-timeout, and malformed-output cases, but not persistent unavailability or stale output:

| Condition | Invalid args | Offline primary | Timeout | Malformed | Stale output |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| B | 2/10 | 0/10 | 2/10 | 0/10 | 0/10 |
| C | 10/10 | 0/10 | 10/10 | 10/10 | 0/10 |
| D | 10/10 | 0/10 | 10/10 | 10/10 | 0/10 |

For `llama3.2:3b`, structured history gave modest gains in both JSON and schema settings. Condition D reached 26/50 compared with 22/50 for condition C, and it had no response errors. However, the model still failed all persistent-unavailability cases and most stale-output cases.

Across both models, schema enforcement helped more reliably than changing the execution-history format. Structured history was not harmful, and it helped `llama3.2:3b` slightly, but it was not the dominant effect.

## Interpretation

The strongest current finding is that output-schema enforcement mattered more than history format for this local model. Plain JSON mode often produced parseable JSON, but not the required action object. The model sometimes copied the surrounding task and tool context instead of returning `{action, arguments, answer}`. These responses were syntactically JSON but unusable as agent actions.

Schema-constrained generation largely removed that failure mode. It made the interaction cleaner and allowed the model to complete easier recovery cases. However, valid action formatting did not guarantee recovery reasoning. The model still struggled when the correct behavior required abandoning the primary service and using the backup source, especially for persistent outages and stale but plausible primary data.

The result does not support a broad claim that structured execution history alone improves recovery. The better statement is:

> In this controlled tool-recovery harness, enforcing the response schema improved verified recovery across two small local models. Structured JSON history had no effect for `qwen3:4b` under schema enforcement and a modest positive effect for `llama3.2:3b`, but the main bottleneck remained valid, supported recovery behavior rather than history representation alone.

## Limitations

This is a development pilot, not final paper evidence. It uses two small local models, two seeds per model, and one synthetic inventory domain. The 25 scenarios are controlled and useful for debugging, but they are not a broad benchmark of real-world tool use. The repeated scenario templates also mean the 100 episodes per model-seed pair should not be treated as 100 fully independent tasks.

The harness supplies a notice that the initial attempt did not reliably complete the task. Therefore, this study evaluates recovery after a supplied unreliable attempt; it does not evaluate autonomous failure detection. The current environment also has a reliable backup source, which simplifies some recovery paths.

The runs do not yet include held-out scenario templates, cluster-aware uncertainty estimates, a larger model with reliable schema enforcement, or a systematic related-work comparison. These are necessary before making a strong publication claim.

Free-tier Ollama cloud candidates were also screened after the local pilots. `gemma4:cloud`, `gemma4:31b-cloud`, `gpt-oss:20b-cloud`, `gpt-oss:120b-cloud`, and `nemotron-3-nano:30b-cloud` were accessible through the local Ollama path, but did not satisfy the strict schema-conflict probe required for comparable C/D conditions. Several other cloud aliases registered but returned HTTP 402 on this account. These checks are eligibility diagnostics, not main benchmark trials, and the corresponding models are excluded from the primary result table.

## Future Work

The next step is to add a stronger model with reliable schema enforcement or expand the benchmark with held-out scenario templates. Cloud models tested through the current Ollama path were accessible, but did not pass the strict schema-enforcement probe, so they should not be used for the main A/B/C/D comparison until that issue is resolved.

The benchmark should also be expanded beyond inventory lookup. At least one second task family should require combining outputs from multiple tools or updating state, so success cannot be achieved by simple record retrieval alone. Persistent unavailability and stale-output cases should receive special attention because they remained difficult even with schema enforcement.

For a final study, the protocol should be frozen before held-out evaluation. The analysis should use paired scenario comparisons and cluster-aware uncertainty estimates, because scenario variants share templates and records. Output failures should remain counted as outcomes rather than excluded.

## Current Status

The revised project has moved from a confounded exploratory prototype to a working controlled development benchmark with four completed local model runs: two models across two seeds each. The code now includes a stateful recovery harness, equivalent evidence renderers, strict response validation, real local-model integration, append-only run logs, and an analysis script. The current evidence is stronger than the first pilot, but the paper still needs held-out scenarios, a stronger model or external replication, and uncertainty estimates before its claims are ready to submit.

