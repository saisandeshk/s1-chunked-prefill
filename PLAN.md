# S1 development plan

Updated: September 7, 2026.

State: **end-to-end project authorized; client implemented; diagnostic device bring-up underway.** The deliverable remains an evidence-backed initial/submission-ready SRS paper. Professor review does not block work; authentic submission paperwork remains required.

## Completed

- [x] Create a dedicated, portable workspace separate from JouleServe and the proposal portfolio.
- [x] Bring the S1 question and experimental boundaries into self-contained documentation.
- [x] Record the proposed pilot matrix and the existing runtime/model identity separately.
- [x] Prepare Git exclusions, Python package layout, and workstation/Orin synchronization guidance.

Scaffold verification: all three JSON configs and package metadata parse; the package imports; all seven local Markdown links resolve within this workspace; Git ignore checks preserve shared configs/curated results while excluding local settings and raw runs. Git is initialized on `main` with the user-provided GitHub remote. Device execution remains pending.

## Next: repository and development setup

- [x] Initialize the local repository and connect `origin` to `https://github.com/saisandeshk/s1-chunked-prefill.git`, supplied by Sai.
- [x] Create and push initial scaffold commit `473b78d` to `origin/main`; `main` tracks that remote branch. Record the current commit in future device handoffs.
- [x] Clone onto both Orins' NVMe workspaces at initial revision `e4e5ab0`; synchronize each implementation checkpoint.
- [ ] Probe live Python/runtime/model/endpoint access and device availability without changing operating state.

## Then: implement the smallest useful pilot

- [x] Implement streamed response recording: request dispatch, first content, subsequent content events, completion, usage, and errors.
- [x] Add meaningful local tests using fragmented SSE fixtures, empty/role-only events, interrupted streams, and multi-token content chunks.
- [x] Implement a reproducible mixed-arrival trace: active decodes followed by an injected long prompt; record intended and actual dispatch times.
- [x] Implement an explicit adapter to the existing runtime controller with fixed common launch parameters and per-treatment chunk sizes.
- [ ] Establish actual token lengths, comparable prefix-cache behavior, common token-pool feasibility, and real prefill/decode overlap on one Orin.
- [ ] Run the three-treatment diagnostic pilot and inspect whether an interpretable effect exists.

## Before a claim-bearing campaign

- [ ] Freeze workload, offered loads, measurement boundaries, repetitions, thermal/service state, and practical effect margin.
- [ ] Freeze the S1 measurement and reproducibility contract using verified artifacts; distinguish its evidence from historical JouleServe functional diagnostics.
- [ ] Run paired treatment blocks, retain invalid/failed runs, and repeat a representative subset on the second Orin.
- [ ] Produce traceable plots, a bounded result, source/PDF paper, and submission checklist (including authentic author details, advisor undertaking, and AI disclosure).

## Current checkpoint and next actions

- Twelve local tests pass, including a real fragmented HTTP/SSE server and overlapping arrivals. Use `PYTHONPATH=src python3 -B -m unittest discover -s tests -v`.
- Both Orins have Python 3.10.12. Orin-1 has ~58 GiB available RAM and Orin-2 ~49 GiB; both had no running Docker containers at admission. Orin-2 reports active K3s/jtop; preserve and record service state.
- Orin-1's exact runtime image was absent despite historical records. Its ten-file model manifest passed on September 7 local time. The exact-image deployment finished and image identity was verified; serving bring-up also passed on the restored image. Import evidence: `/media/ssd/saisandesh/telemetry/sglang-0.5.16-deployment/orin64-ref-01/import/20260906T184409Z`.
- Orin-2 diagnostic container `jouleserve-srs-s1-c4096` is running on loopback port 30001. Its controller evidence is in the JouleServe checkout at `runs/srs-s1-bringup-20260907-c4096`; S1 bring-up log/config are in `runs/bringup-20260907/`. Live server has `enable_mixed_chunk=false`, context 4096 and token pool 8192.
- Orin-2 first diagnostic (`runs/pilot-orin2-c4096-first`) passed 5/5 requests, exact 256/3072 input and 128 output counts, zero cached tokens, four active decodes spanning injection. Scheduler log corroborates 4 running requests during the injected prefill. Curated summary: `results/bringup/orin2-first-trace.json`; imported raw hashes verified locally.
- Versioned traces: `data/traces/mixed-v1.json` (500 ms injection), `decode-only-v1.json`, `prefill-only-v1.json`. Native synthetic workload; no chat quality claims.
- Guarded diagnostic campaign implemented: randomized treatment blocks, live config checks, shape warmups, cache flush plus cached-token validation, telemetry, host snapshots, durable per-run/cell status, owned cleanup, port lock. Next: sync and exercise it on both devices, starting with one block before larger campaigns.
- Bring-up containers currently use `jouleserve-srs-s1-c4096` on port 30001 on both boards. Stop through the controller before a campaign; Orin-1 evidence is `JouleServe/runs/srs-s1-restored-20260907-c4096`, Orin-2 evidence is `JouleServe/runs/srs-s1-bringup-20260907-c4096`.
- No claim-bearing campaign or measured scientific result is complete. The goal remains active through paper generation and verification.
