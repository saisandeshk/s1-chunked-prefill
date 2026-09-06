"""Descriptive delivery metrics; repeated-run inference is a separate step."""

import json
from pathlib import Path


def quantile(values, q):
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * q
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def request_metrics(record):
    times = record["content_times_ns"]
    dispatch = record.get("dispatch_ns")
    tokens = record.get("meta_info", {}).get("completion_tokens", 0)
    gaps = [(b - a) / 1e6 for a, b in zip(times, times[1:])]
    return {"id": record["id"], "role": record["role"], "status": record["status"],
            "ttft_ms": (times[0] - dispatch) / 1e6 if times and dispatch is not None else None,
            "response_ms": (record["completed_ns"] - dispatch) / 1e6 if dispatch is not None else None,
            "dispatch_lateness_ms": (dispatch - record["intended_dispatch_ns"]) / 1e6 if dispatch is not None else None,
            "content_events": len(times), "content_gap_p95_ms": quantile(gaps, .95),
            "content_gap_max_ms": max(gaps) if gaps else None,
            "aggregate_tpot_ms": (times[-1] - times[0]) / 1e6 / (tokens - 1) if times and tokens > 1 else None,
            "prompt_tokens": record.get("meta_info", {}).get("prompt_tokens"),
            "completion_tokens": tokens, "cached_tokens": record.get("meta_info", {}).get("cached_tokens")}


def summarize_run(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    records = [json.loads(p.read_text()) for p in sorted(directory.glob("request-*.json"))]
    metrics = [request_metrics(r) for r in records]
    injected = [r for r in records if r["role"] == "injected"]
    overlap = []
    interference_gaps = []
    if len(injected) == 1 and injected[0]["content_times_ns"]:
        start = injected[0]["dispatch_ns"]
        end = injected[0]["content_times_ns"][0]
        for record in records:
            times = record["content_times_ns"]
            if record["role"] != "active":
                continue
            if times and times[0] < start < times[-1]:
                overlap.append(record["id"])
            interference_gaps.extend((b - a) / 1e6 for a, b in zip(times, times[1:]) if a <= end and b >= start)
    dispatched = [r["dispatch_ns"] for r in records if "dispatch_ns" in r]
    elapsed = (max(r["completed_ns"] for r in records) - min(dispatched)) / 1e9 if dispatched else None
    return {"schema_version": 1, "classification": manifest["classification"],
            "manifest_status": manifest["status"], "request_metrics": metrics,
            "active_requests_spanning_injection": overlap,
            "overlap_definition": "Active content delivery both before and after injected dispatch; engine logs still needed for scheduling claims",
            "interference_content_gap_max_ms": max(interference_gaps) if interference_gaps else None,
            "completed_requests_per_second": sum(r["status"] == "ok" for r in records) / elapsed if elapsed else None,
            "completion_tokens_per_second": sum(r["meta_info"].get("completion_tokens", 0) for r in records if r["status"] == "ok") / elapsed if elapsed else None}
