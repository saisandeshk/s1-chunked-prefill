# S1 — Chunked Prefill on Orin

A standalone HiPC SRS study of how **fixed prefill chunk size** affects ongoing decoding when long prompts arrive on a Jetson AGX Orin.

**Current state:** streaming client and synthetic workload generator implemented; device bring-up and diagnostic pilot in progress. Sai authorized the full project through an initial/submission-ready SRS paper on September 7, 2026, without waiting for professor review. See `PLAN.md` for current evidence and continuation steps.

## Start here

- [Experiment specification](docs/EXPERIMENT.md): question, treatments, measurements, and boundaries.
- [Development plan](PLAN.md): completed work and next tasks.
- [Development and device sync](docs/DEVELOPMENT.md): GitHub setup, workstation/Orin roles, and runtime integration.
- [Pilot configuration](config/pilot.json): proposed experiment values, subject to feasibility checks.
- [Runtime reference](config/runtime-reference.json): identity of the existing serving artifact; not a new S1 validation result.

## Workspace layout

```text
config/                  Shared experiment configuration; ignored local overrides
docs/                    Experiment and development guidance
src/s1_chunked_prefill/   Python package for the forthcoming client and analysis
scripts/                 Future command-line entry points
tests/                   Future protocol, timing, and correctness tests
data/traces/             Small, versioned input traces and generation specifications
runs/                    Ignored device-local raw logs, telemetry, and results
results/                 Reviewed summaries and figures selected for Git
```

The client/analysis package targets Python 3.10+ and currently has no third-party dependencies. No GPU or SGLang installation is needed to inspect this scaffold. SGLang remains in the existing Orin container; it is not a dependency to install in the workstation's client environment.

This workspace is initialized on `main` with `origin` set to [saisandeshk/s1-chunked-prefill](https://github.com/saisandeshk/s1-chunked-prefill). See the development plan for push/deployment status and the development guide for cloning onto the Orins' NVMe workspaces.

Research documents and configs are self-contained within this repository. Running the eventual Orin launch adapter will additionally require the existing local JouleServe deployment tools and approved runtime. Model weights, images, credentials, and raw runs stay outside Git.
