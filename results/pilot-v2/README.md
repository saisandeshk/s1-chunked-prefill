# Two-device diagnostic pilot

These are feasibility observations from one randomized treatment block on each board, with two measured repeats and two warmups per workload/cell. They are excluded from the subsequent frozen repeated campaign. No inferential interval is reported for one independent block.

All 72 traces (36 warmup, 36 measured) passed the diagnostic checks. Request inventories, individual request hashes, trace hashes, common configuration, live server settings, code identity, and recomputed metrics were verified before generating `report.json`. Both full raw inventories contain 417 files, including controller evidence; their SHA256SUMS passed on-device and after workstation transfer.

| Board | Chunk | Peak active-stream stall (ms) | Injected TTFT (ms) |
|---|---:|---:|---:|
| Orin-1 | 256 | 276.67 | 298.63 |
| Orin-1 | 1,024 | 125.91 | 145.94 |
| Orin-1 | 4,096 | 115.78 | 135.04 |
| Orin-2 | 256 | 272.34 | 295.80 |
| Orin-2 | 1,024 | 127.91 | 149.49 |
| Orin-2 | 4,096 | 113.13 | 136.31 |

Each table entry is the mean of the two measured mixed traces in one block. Peak stall is the largest active-request content-delivery gap intersecting the arriving request's dispatch-to-first-content interval. It is not an engine per-token latency percentile. See `trials.csv` for every warmup/measured observation and validity flags, and `figures/` for the exported visualization with provenance.

The 256-token setting produces about 2.4 times the control's peak stall on each board. At this pilot scale that is a repeatable diagnostic direction, not a claim of population precision. The 1,024 setting is much closer to the control. The 4,096 setting fits the 3,072-token prompt in one chunk; it is not global chunking disablement.

The retained 256-token server log shows the long input processed as twelve successive 256-token prefill batches with four running requests. The corresponding delivery records show the active-stream interruption. This agrees with the pinned source's prefill precedence and disabled mixed-chunk setting. The coarse periodic decode log alone cannot establish every individual engine step; source semantics, live settings, and delivery evidence must be interpreted together. The KV allocation log records BF16 and the common 8,192-token pool.

Telemetry maxima across these pilot cells were below 59 C for both CPUs/GPUs. CV thermal zones can return EAGAIN and are recorded as unavailable. No energy or thermal-efficiency benefit is claimed.

Raw locations on the workstation:

- `runs/imported/orin1/pilot-block0-v2/`
- `runs/imported/orin2/pilot-block0-v2/`

Each source Orin retains the corresponding `runs/pilot-block0-v2/` under its S1 checkout. Runtime/controller records are additionally retained by JouleServe. These ignored raw directories are not included in a fresh Git clone; the curated report records hashes and code provenance.
