# Development and device synchronization

## Roles and paths

Use GitHub to synchronize source, configurations, trace specifications, docs, and reviewed summaries. Each machine keeps its own environment, models, runtime image, and raw experiment directories.

| Checkout | Suggested path | Role |
|---|---|---|
| Workstation | `ISP/S1-Chunked-Prefill` | Client/analysis development and review |
| Orin-1 | `/media/ssd/saisandesh/projects/S1-Chunked-Prefill` | Primary pilot and experiment execution |
| Orin-2 | `/media/ssd/saisandesh/projects/S1-Chunked-Prefill` | Replication and optional development |

These are deployment conventions, not paths to hardcode in Python imports. Device availability and checkout creation have not been verified in this step.

## Repository and Orin clones

The workstation repository is initialized on `main`, with `origin` set to `https://github.com/saisandeshk/s1-chunked-prefill.git`. See `PLAN.md` for push and deployment status. No license has been selected for the research code; choose one with the authors before distributing it under an explicit license.

On each Orin, once the first push is complete and access is configured:

```bash
cd /media/ssd/saisandesh/projects
git clone https://github.com/saisandeshk/s1-chunked-prefill.git S1-Chunked-Prefill
cd S1-Chunked-Prefill
git rev-parse HEAD
```

Cloning the source does not install SGLang, transfer its image/model, or establish runtime permission.

## Day-to-day sync

1. Inspect `git status --short` before pulling. Preserve and commit in-progress device edits on a named branch before switching revisions.
2. Use `git pull --ff-only` on a clean shared branch. Fast-forward failure means histories differ and need deliberate reconciliation.
3. Give each active implementation a branch, such as `feat/stream-client` or `feat/mixed-arrivals`. Avoid simultaneous edits to the same shared branch on multiple machines.
4. Push reviewed changes, then update the other checkouts. Before a comparative campaign, verify that both Orins use the intended commit and identical experiment/trace hashes.
5. Record the commit in every run manifest. A dirty diagnostic run must retain its patch; use a clean commit for the frozen campaign.

Run directories include the device ID plus a unique run ID. Git is not a raw-data synchronization mechanism. Transfer raw data through an explicit, checksummed artifact copy when needed, retaining provenance. Put only reviewed summaries/figures and their manifest references in `results/`.

## Local configuration and Python

Copy `config/local.example.json` to the ignored `config/local.json` and fill in machine-specific values when configuring a device. It is a configuration convention for the forthcoming adapter; no loader or environment bootstrap is implemented yet.

The package uses the standard `src/` layout and Python 3.10+. Create virtual environments on the workstation or Orin NVMe workspace. Once client implementation starts, install this package in editable mode in that local environment; add dependencies only when the implementation needs them. Keep the large serving stack in its existing container.

## Integrate with the existing Orin deployment

The local JouleServe checkout remains the owner of image/model validation, guarded server launch, and telemetry primitives. Locate it through `jouleserve_root` in local configuration and read its `AGENTS.md`/handoff before use. This workspace does not copy its build system, alter its wrapper, or replace its sealed evidence.

The forthcoming adapter must explicitly pass the image identity from `config/runtime-reference.json`; the existing server controller's historical default may select a different runtime. It must also use a unique owned server name, an unused loopback port, and the shared pilot parameters. Validate the resulting server specification before running it.

The restricted wrapper currently accepts server specifications only inside approved JouleServe run/evidence paths. Its S1 launch records may therefore live there with a unique `srs-s1` identifier; cross-reference them from this repository's local run manifest. This is an operational boundary, not a reason to intermingle the two research codebases.

Keep raw data, caches, temporary files, and build output on the NVMe workspace. Live device checks must establish headroom, endpoint ownership, model identity, and stable operating conditions before experiments. The existing device policy governs Docker and power actions; GitHub synchronization grants no additional privileges.
