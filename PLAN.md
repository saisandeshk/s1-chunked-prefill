# S1 development plan

Updated: September 7, 2026.

State: **two-device diagnostic pilot complete; repeated protocol frozen; paper source compiles.** The deliverable remains an evidence-backed initial/submission-ready SRS paper. Professor review does not block work; authentic submission paperwork remains required.

## Completed

- [x] Create a dedicated, portable workspace separate from JouleServe and the proposal portfolio.
- [x] Bring the S1 question and experimental boundaries into self-contained documentation.
- [x] Record the proposed pilot matrix and the existing runtime/model identity separately.
- [x] Prepare Git exclusions, Python package layout, and workstation/Orin synchronization guidance.

Scaffold verification: all three JSON configs and package metadata parse; the package imports; all seven local Markdown links resolve within this workspace; Git ignore checks preserve shared configs/curated results while excluding local settings and raw runs. Git is initialized on `main` with the user-provided GitHub remote. Device execution is underway; see current checkpoint below.

## Next: repository and development setup

- [x] Initialize the local repository and connect `origin` to `https://github.com/saisandeshk/s1-chunked-prefill.git`, supplied by Sai.
- [x] Create and push initial scaffold commit `473b78d` to `origin/main`; `main` tracks that remote branch. Record the current commit in future device handoffs.
- [x] Clone onto both Orins' NVMe workspaces at initial revision `e4e5ab0`; synchronize each implementation checkpoint.
- [x] Probe live Python/runtime/model/endpoint access and device availability; restored the missing exact Orin-1 runtime through the existing deployment workflow.

## Then: implement the smallest useful pilot

- [x] Implement streamed response recording: request dispatch, first content, subsequent content events, completion, usage, and errors.
- [x] Add meaningful local tests using fragmented SSE fixtures, empty/role-only events, interrupted streams, and multi-token content chunks.
- [x] Implement a reproducible mixed-arrival trace: active decodes followed by an injected long prompt; record intended and actual dispatch times.
- [x] Implement an explicit adapter to the existing runtime controller with fixed common launch parameters and per-treatment chunk sizes.
- [x] Establish exact token lengths, zero cached-token reuse, common token-pool feasibility, and active decoding spanning injection for all three treatments on both Orins.
- [x] Complete the three-treatment diagnostic pilot on both boards: 72 traces including warmup, 36 measured, zero validity exclusions.

## Before a claim-bearing campaign

- [x] Freeze workload, measurement, 12 paired blocks per board, operating-state policy, and 10% practical-effect margin in `docs/PROTOCOL.md` and `config/campaign-v1.json`.
- [x] Freeze the S1 measurement and reproducibility contract using exact artifacts; retain historical and pilot diagnostics separately.
- [ ] Run paired treatment blocks, retain invalid/failed runs, and repeat a representative subset on the second Orin.
- [ ] Produce traceable plots, a bounded result, source/PDF paper, and submission checklist (including authentic author details, advisor undertaking, and AI disclosure).

## Current checkpoint and next actions

- Seventeen tests pass locally and on both Orins at campaign code commit `eb2805424e54bf8897e6526c177d0d2c13c6668e`. A new test covers frozen thermal/container admission.
- Both pilot drivers (`pilot-block0-v2`, Orin-1 PID 70301, Orin-2 PID 145767) are terminal, all cells complete, and both boards have no running Docker containers. Each campaign was sealed with 417 files, including copied controller evidence. Raw state lives in each S1 checkout at `runs/pilot-block0-v2`; imports are under workstation `runs/imported/orin1/` and `orin2/`. Both workstation imports now include controller records; all 417-file SHA256SUMS inventories passed locally.
- Curated verified pilot analysis: `results/pilot-v2/report.json` and `trials.csv`. One independent block per board, two measured repeats per workload/cell; no bootstrap intervals. Smallest chunks show roughly 2.4x peak active-stream stalls versus 4096, but this is a pilot, excluded from the repeated estimates.
- The first attempt (`pilot-block0-v1`) failed before launching cells on unavailable CV thermal sensors. The fixed code records EAGAIN while preserving CPU/GPU temperatures; failed evidence is retained. Orin-1's missing runtime image was restored and identity/model/serving verified. Neither condition remains a blocker.
- The first repeated-campaign attempt (`runs/campaign-v1`, Orin-1 PID 88519, Orin-2 PID 163946) failed before data collection: the thermal loop shadowed the container-name variable. The wrapper rejected the invalid name. Both driver PIDs are absent. Admission is now isolated in a function, preventing that scope error; original attempt evidence remains.
- **Repeated campaigns are LIVE** at `runs/campaign-v1-r2` on both boards, using committed code `eb2805424e54bf8897e6526c177d0d2c13c6668e` and `config/campaign-v1.json`. Orin-1 driver PID **89859**; Orin-2 driver PID **165360**. Each S1 checkout has `runs/campaign-v1-r2-driver.json` (command/commit/PID), `runs/campaign-v1-r2-driver.log`, and `runs/campaign-v1-r2/campaign.json` (durable cell/trial state). Last verified: both drivers alive, first cell at chunk 1024 had completed six warmup traces with no validity exclusions; first owned container name is `jouleserve-srs-s1-56f2a016-000` on port 30001.
- **Resume by inspecting those exact PIDs, `/proc/<pid>/cmdline`, driver log and campaign JSON first.** Target: 12 blocks / 36 cells per board, 216 measured traces plus 216 warmups per board. Do not pull or edit either running checkout. Workstation documentation/analysis commits may advance separately. If a process disappears, inspect its manifest, logs, and owned container before any restart; preserve failed paths.
- After terminal success, seal each campaign with copied controller evidence (per-cell `evidence_dir`) and recursive SHA256SUMS, transfer to workstation ignored runs, verify every hash, then run `s1_chunked_prefill.report` against the two campaign directories. Inspect telemetry and scheduler logs as required by `docs/PROTOCOL.md` before accepting comparisons. Plot with `scripts/plot-results.py`, replace paper progress text with measured results and uncertainty, and verify the final PDF.
- `paper/main.tex` and `results.tex` form a methods/validation working draft. `bash scripts/build-paper.sh` succeeds with pinned Tectonic 0.17.0; current PDF has 2 US-letter pages. It is not yet the final manuscript. Replace progress text with verified repeated results, add figures, inspect rendering/fonts/margins and citations, then retain the reviewed PDF outside `paper/build/`.
- Author name/program/affiliation/coauthors were requested asynchronously and remain pending. Advisor undertaking is an authentic submission artifact, not a blocker to experiments or drafting. Never generate a signature or claim student review occurred.
- The full goal remains active through repeated-data verification, final analysis/figures, and the evidence-backed initial/submission-ready paper. A running campaign or compiling draft is not completion.
