# S1 development plan

Updated: September 6, 2026.

State: **workspace ready; prototype authorized by Sai; professor review pending.** The remaining review concerns the eventual research contribution/publication, not whether to prepare this workspace.

## Completed

- [x] Create a dedicated, portable workspace separate from JouleServe and the proposal portfolio.
- [x] Bring the S1 question and experimental boundaries into self-contained documentation.
- [x] Record the proposed pilot matrix and the existing runtime/model identity separately.
- [x] Prepare Git exclusions, Python package layout, and workstation/Orin synchronization guidance.

Scaffold verification: all three JSON configs and package metadata parse; the package imports; all seven local Markdown links resolve within this workspace; Git ignore checks preserve shared configs/curated results while excluding local settings and raw runs. Git is initialized on `main` with the user-provided GitHub remote. Device execution remains pending.

## Next: repository and development setup

- [x] Initialize the local repository and connect `origin` to `https://github.com/saisandeshk/s1-chunked-prefill.git`, supplied by Sai.
- [ ] Make the initial commit and push; record the resulting commit in future device handoffs.
- [ ] Clone onto each Orin's NVMe workspace and verify that all three checkouts share the intended commit.
- [ ] Probe live Python/runtime/model/endpoint access and device availability without changing operating state.

## Then: implement the smallest useful pilot

- [ ] Implement streamed response recording: request dispatch, first content, subsequent content events, completion, usage, and errors.
- [ ] Add meaningful local tests using fragmented SSE fixtures, empty/role-only events, interrupted streams, and multi-token content chunks.
- [ ] Implement a reproducible mixed-arrival trace: active decodes followed by an injected long prompt; record intended and actual dispatch times.
- [ ] Implement an explicit adapter to the existing runtime controller with fixed common launch parameters and per-treatment chunk sizes.
- [ ] Establish actual token lengths, comparable prefix-cache behavior, common token-pool feasibility, and real prefill/decode overlap on one Orin.
- [ ] Run the three-treatment diagnostic pilot and inspect whether an interpretable effect exists.

## Before a claim-bearing campaign

- [ ] Freeze workload, offered loads, measurement boundaries, repetitions, thermal/service state, and practical effect margin.
- [ ] Resolve publication/provenance gates with the professor and the deployment owners as applicable.
- [ ] Run paired treatment blocks, retain invalid/failed runs, and repeat a representative subset on the second Orin.
- [ ] Produce traceable plots and a bounded result; record professor feedback before final paper submission.

No benchmark client, launch adapter, automated campaign, or new Orin result is marked complete at this stage.
