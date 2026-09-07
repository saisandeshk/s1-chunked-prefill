"""Verify campaign records and aggregate at the independent-block level."""

import argparse
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
import random
import statistics

from .analysis import quantile, summarize_run
from .campaign import quality, verify_server
from .runner import digest, write_json


def verify_run(directory):
    manifest = json.loads((directory / "manifest.json").read_text())
    files = manifest["files_sha256"]
    actual = {p.name for p in directory.glob("request-*.json")}
    if actual != set(files) or len(actual) != manifest["request_count"]:
        raise ValueError(f"Request inventory mismatch: {directory}")
    for name, expected in files.items():
        if Path(name).name != name or digest(directory / name) != expected:
            raise ValueError(f"Request integrity failure: {directory / name}")
    if digest(directory / "trace.json") != manifest["trace_sha256"]:
        raise ValueError(f"Trace integrity failure: {directory}")
    trace = json.loads((directory / "trace.json").read_text())
    ids = [json.loads((directory / name).read_text())["id"] for name in files]
    if len(set(ids)) != len(ids) or set(ids) != {r["id"] for r in trace["requests"]}:
        raise ValueError(f"Request identity mismatch: {directory}")
    return manifest, trace


def read_campaign(directory):
    directory = Path(directory)
    state = json.loads((directory / "campaign.json").read_text())
    if state["status"] != "complete":
        raise ValueError(f"Campaign is not terminal and complete: {directory}")
    config = json.loads((directory / "config.json").read_text())
    reference = json.loads((directory / "runtime-reference.json").read_text())
    if digest(directory / "config.json") != state["config_sha256"] or digest(directory / "runtime-reference.json") != state["runtime_reference_sha256"]:
        raise ValueError("Campaign configuration integrity failure")
    rows = []
    for cell in state["cells"]:
        cell_dir = directory / Path(cell["output"]).name
        if cell["status"] != "complete" or cell.get("collector_exit_code") != 0:
            raise ValueError(f"Incomplete cell or failed telemetry: {cell_dir}")
        verify_server(json.loads((cell_dir / "server-info.json").read_text()), config, reference, cell["chunk"])
        for run in cell["runs"]:
            if Path(run["path"]).name != run["path"]:
                raise ValueError("Invalid run path")
            path = cell_dir / run["path"]
            manifest, trace = verify_run(path)
            if manifest["code_commit"] != state["code_commit"] or manifest["dirty"]:
                raise ValueError("Run code differs from campaign code")
            if manifest["trace_sha256"] not in state["traces"].values():
                raise ValueError("Run trace was not declared by the campaign")
            summary = summarize_run(path)
            before = json.loads((path / "host-before.json").read_text())
            after = json.loads((path / "host-after.json").read_text())
            checks = quality(summary, trace, before, after, config.get("measurement", {}).get("quality_limits"))
            metrics = summary["request_metrics"]
            active = [m for m in metrics if m["role"] == "active"]
            injected = [m for m in metrics if m["role"] in ("injected", "control")]
            kind = "mixed" if active and injected else "decode-only" if active else "prefill-only"
            row = {"device": state["device_id"], "campaign": directory.name,
                   "block": cell["block"], "chunk": cell["chunk"], "workload": kind,
                   "run": str(path.relative_to(directory)), "warmup": run["warmup"],
                   "included": checks["diagnostic_valid"] and not run["warmup"],
                   "issues": ";".join(checks["issues"]),
                   "injected_ttft_ms": injected[0]["ttft_ms"] if injected else None,
                   "active_max_gap_ms": max((m["content_gap_max_ms"] for m in active if m["content_gap_max_ms"] is not None), default=None),
                   "interference_max_gap_ms": summary["interference_content_gap_max_ms"],
                   "output_tokens_per_second": summary["completion_tokens_per_second"],
                   "max_dispatch_lateness_ms": max((m["dispatch_lateness_ms"] for m in metrics if m["dispatch_lateness_ms"] is not None), default=None),
                   "request_count": manifest["request_count"],
                   "run_manifest_sha256": digest(path / "manifest.json")}
            rows.append(row)
    return state, rows


def paired_estimate(pairs, seed=20260907):
    """Bootstrap independent paired blocks, never individual token events."""
    if not pairs:
        return {"blocks": 0, "mean_difference": None, "geometric_mean_ratio": None,
                "difference_ci95": None, "ratio_ci95": None}
    differences = [t - c for t, c in pairs]
    logs = [math.log(t / c) for t, c in pairs] if all(t > 0 and c > 0 for t, c in pairs) else None
    result = {"blocks": len(pairs), "mean_difference": statistics.mean(differences),
              "geometric_mean_ratio": math.exp(statistics.mean(logs)) if logs else None,
              "difference_ci95": None, "ratio_ci95": None}
    if len(pairs) < 8:
        result["uncertainty_note"] = "Fewer than eight independent blocks; no bootstrap interval reported"
        return result
    rng = random.Random(seed)
    diff_samples, ratio_samples = [], []
    for _ in range(10000):
        indices = rng.choices(range(len(pairs)), k=len(pairs))
        diff_samples.append(statistics.mean(differences[i] for i in indices))
        if logs:
            ratio_samples.append(math.exp(statistics.mean(logs[i] for i in indices)))
    result["difference_ci95"] = [quantile(diff_samples, .025), quantile(diff_samples, .975)]
    if logs:
        result["ratio_ci95"] = [quantile(ratio_samples, .025), quantile(ratio_samples, .975)]
    return result


def aggregate(rows):
    metrics = ("injected_ttft_ms", "active_max_gap_ms", "interference_max_gap_ms", "output_tokens_per_second")
    groups = defaultdict(list)
    for row in rows:
        if row["included"]:
            groups[(row["device"], row["campaign"], row["block"], row["chunk"], row["workload"])].append(row)
    cells = []
    for key, group in sorted(groups.items()):
        cell = dict(zip(("device", "campaign", "block", "chunk", "workload"), key))
        cell["trials"] = len(group)
        for metric in metrics:
            values = [r[metric] for r in group if r[metric] is not None]
            cell[metric] = statistics.mean(values) if values else None
        cells.append(cell)
    comparisons = []
    for device in sorted({r["device"] for r in rows}):
        for workload in ("mixed", "decode-only", "prefill-only"):
            for metric in metrics:
                by_chunk = defaultdict(dict)
                for cell in cells:
                    if cell["device"] == device and cell["workload"] == workload and cell[metric] is not None:
                        by_chunk[cell["chunk"]][(cell["campaign"], cell["block"])] = cell[metric]
                for chunk in (256, 1024):
                    keys = sorted(set(by_chunk[chunk]) & set(by_chunk[4096]))
                    if keys:
                        result = paired_estimate([(by_chunk[chunk][key], by_chunk[4096][key]) for key in keys])
                        comparisons.append({"device": device, "workload": workload, "metric": metric,
                                            "treatment": chunk, "control": 4096, **result})
    return {"cell_means": cells, "paired_comparisons": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaigns", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, sources = [], []
    for directory in args.campaigns:
        state, new_rows = read_campaign(directory)
        rows.extend(new_rows)
        sources.append({"device": state["device_id"], "campaign": directory.name,
                        "campaign_sha256": digest(directory / "campaign.json"), "code_commit": state["code_commit"],
                        "classification": state["classification"]})
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "trials.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {"schema_version": 1, "sources": sources,
              "total_trials_including_warmup": len(rows),
              "included_trials": sum(r["included"] for r in rows),
              "invalid_trials_including_warmup": sum(bool(r["issues"]) for r in rows),
              "unit_of_inference": "Within-device paired block; repeated traces are averaged within each cell",
              **aggregate(rows)}
    write_json(args.output / "report.json", report)
    print(json.dumps({key: report[key] for key in ("total_trials_including_warmup", "included_trials", "invalid_trials_including_warmup")}, indent=2))


if __name__ == "__main__":
    main()
