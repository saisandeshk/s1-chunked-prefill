#!/usr/bin/env python3
"""Export measured block points; use report.py for paired uncertainty."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.35), layout="constrained")
    devices = [("orin64-ref-01", "Orin-1", "#0072B2", "o"),
               ("orin64-build-01", "Orin-2", "#D55E00", "s")]
    for axis, metric, title in zip(axes, ("interference_max_gap_ms", "injected_ttft_ms"),
                                    ("(a) Peak active-stream delivery stall", "(b) Arriving-request TTFT")):
        for device_index, (device, label, color, marker) in enumerate(devices):
            means = []
            positions = []
            for i, chunk in enumerate((256, 1024, 4096)):
                values = [c[metric] for c in report["cell_means"] if c["device"] == device
                          and c["workload"] == "mixed" and c["chunk"] == chunk and c[metric] is not None]
                if not values:
                    continue
                x = i + (-.09 if device_index == 0 else .09)
                jitter = np.linspace(-.035, .035, len(values)) if len(values) > 1 else [0]
                axis.scatter(x + np.asarray(jitter), values, s=18, marker=marker, color=color,
                             alpha=.65, edgecolors="none", zorder=3)
                means.append(statistics.mean(values))
                positions.append(x)
            axis.plot(positions, means, color=color, linewidth=1, label=label, zorder=2)
        axis.set_xticks(range(3), ["256", "1,024", "4,096"])
        axis.set_xlabel("Prefill chunk size (tokens)")
        axis.set_ylabel("Milliseconds")
        axis.set_title(title, fontsize=9, loc="left")
        axis.set_ylim(bottom=0)
        axis.grid(axis="y", color="0.9", linewidth=.5)
        axis.legend(frameon=False, fontsize=7)
    fig.savefig(args.output / "mixed-latency.pdf", metadata={"Title": "S1 mixed-workload block means"})
    fig.savefig(args.output / "mixed-latency.png", dpi=220)
    plt.close(fig)
    provenance = {"report_sha256": hashlib.sha256(args.report.read_bytes()).hexdigest(),
                  "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "matplotlib_version": matplotlib.__version__, "numpy_version": np.__version__,
                  "point_definition": "Mean of valid measured traces in one independent treatment block",
                  "line_definition": "Arithmetic mean across displayed blocks; not a fitted trend or confidence interval",
                  "sources": report["sources"]}
    (args.output / "figure-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


if __name__ == "__main__":
    main()
