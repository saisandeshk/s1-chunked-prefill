# S1 measurement protocol v1

Frozen September 7, 2026 after the two-device diagnostic pilot and before the repeated campaign. The pilot (`pilot-block0-v2`, one block per board) informed feasibility and is excluded from confirmatory estimates. [Experiment scope](EXPERIMENT.md) and [runtime source semantics](RESEARCH.md) remain applicable.

## Question, primary comparison, and limits

Primary comparison: 256 versus 4,096 fixed prefill tokens, with mixed prefill/decode batches disabled. Primary outcome: the largest client-observed content-delivery gap across the four active requests whose gap interval intersects the injected request's actual-dispatch-to-first-content window. This measures a delivery stall, not an engine per-token latency distribution.

The 1,024-token treatment, injected-request TTFT, output-token throughput, and decode-only/prefill-only controls provide secondary characterization. A ten-percent relative change is the prespecified practical-effect threshold. Report observed directions honestly; smaller chunks need not improve any outcome. Do not claim a new scheduler, general Orin optimum, task-quality benefit, or architectural causality against discrete GPUs.

No application deadline is assigned to this synthetic trace. SLO attainment is therefore outside the final comparison; it must not be inferred from the latency results.

## Artifacts and operating conditions

`config/campaign-v1.json` fixes common launch parameters and required live runtime fields. The exact source-built image and pinned model are identified by `config/runtime-reference.json`. Each cell records the controller's validated server specification, image identity, launch/stop evidence, complete live server configuration, and code/config/trace hashes. S1 uses immutable local image ID plus source/build/model and canonical archive-content provenance as its reproducibility contract. This does not relabel JouleServe's historical diagnostic measurements or claim that the image was published in a registry.

Use the three committed traces under `data/traces/`: mixed-v1, decode-only-v1, and prefill-only-v1. Exact token IDs and output budgets remain identical across treatments. The mixed trace dispatches four 256-token requests at the epoch and one 3,072-token request at +500 ms, each with 128 forced output tokens. Greedy synthetic completions are load controls, not a quality evaluation.

The two AGX Orin 64GB boards are separate replications. Retain their existing power modes, dynamic-clock behavior, and background services. Record service state, process names/usage, memory/swap, power-mode query, thermals, and 500 ms host/rail telemetry. Do not change services or power policy between treatments. Admission requires at least 8 GiB available memory and 10 GiB free SSD, no other running Docker container, and readable CPU/GPU temperatures no higher than 75 C. Capture the actual service and power-mode values in the report; do not describe the boards as service-identical or clock-locked.

## Schedule and repetitions

Run 12 independent treatment blocks on each board. Each block visits all three chunk sizes in a seeded random permutation (seed 20260908). Restart the owned server for each treatment cell. Warm each of the three workload shapes twice, then measure it twice. Within a repeat, randomize workload order using the campaign's deterministic block/repeat schedule, common across treatments. Flush the idle owned endpoint before every trace, allow 200 ms for the asynchronous request, and validate zero cached tokens in actual generation metadata. Retain warmup observations but exclude them from estimates.

This produces 36 treatment cells and 216 measured traces per board, plus 216 warmup traces. The independent inferential unit is the paired block, not the two traces within a cell, individual requests, tokens, or telemetry samples. The single pilot block is not part of these 12 blocks. No optional stopping based on a favorable effect is permitted.

## Validity, failures, and resume

A trace is invalid for estimates if any request fails, exact input/output accounting fails, cached tokens are nonzero or absent, actual dispatch exceeds the target by more than 20 ms, any of the four active streams fails to span injection, swap I/O or OOM counters change, required CPU/GPU temperatures are missing/over 75 C at before/after snapshots, or service state changes. Controls do not require injection overlap. Inspect telemetry for within-trace thermal excursions and inspect scheduler logs for ongoing requests at injected prefill; retain these checks with the final analysis. A failed collector, wrong live runtime setting, or incomplete server cleanup prevents accepting the cell as complete.

Keep all failed/invalid trials and reasons. Abort for unsafe admission or broken runtime/collector; resume only after checking the authoritative process/container state. Never restart from a stale PID or a status file alone. New attempts receive new paths. Do not overwrite incomplete evidence or append new measurements to a sealed run. If a material implementation or protocol change is needed, version it and start a separate campaign; do not pool it silently.

## Analysis and reporting

Verify raw request hashes, request inventory/IDs, trace hashes, committed code identity, common configuration, and live treatment settings before deriving metrics. Recompute summaries from events. Report counts of warmup, measured, invalid and paired blocks. For each board and metric, average the two valid measured traces within each cell and pair the treatment/control cell means within blocks. Show all block points.

Report paired mean differences and geometric mean ratios with percentile 95% bootstrap intervals from 10,000 resamples of paired blocks (seed 20260907). These are pointwise descriptive intervals, not simultaneous coverage for all secondary comparisons. Do not produce intervals with fewer than eight valid independent pairs. If exclusions leave too few pairs, state that limitation rather than treating requests as extra replicates. A bounded equivalence claim would require the entire relevant ratio interval inside [0.9, 1.1]; a noisy null is inconclusive. An adverse, replicated effect is a valid result.

Energy is secondary diagnostic context and is not a primary paper claim: monitored rail sums exclude double-counted DDR, are not wall-plug energy, and are too coarse for per-token energy. Preserve telemetry and report operating temperatures/service state even if energy is omitted from the two-page paper.

Final deliverables: verified raw-data inventory and curated analysis, reproducible figures/tables, two-page source and PDF, explicit limits, authentic author details, accurate AI disclosure, and a checklist for advisor undertaking and submission. Completion of a campaign alone does not complete the project.
