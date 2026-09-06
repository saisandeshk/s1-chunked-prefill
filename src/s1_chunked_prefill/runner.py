"""Open-loop trace execution with durable per-request records."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

from .client import stream_request
from .trace import validate_trace


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def run_trace(endpoint, trace_path, output_dir, *, device_id, timeout=120, allow_dirty=False):
    trace_path = Path(trace_path)
    trace = json.loads(trace_path.read_text())
    validate_trace(trace)
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True)
    if dirty and not allow_dirty:
        raise ValueError("Commit changes first, or explicitly allow a diagnostic dirty run")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    if dirty:
        patch = subprocess.check_output(["git", "-C", str(root), "diff", "HEAD", "--binary"])
        (output_dir / "dirty.patch").write_bytes(patch)
        (output_dir / "dirty-status.txt").write_text(dirty)
        # Also preserve source files, including untracked implementation files.
        import tarfile
        with tarfile.open(output_dir / "diagnostic-source.tar.gz", "w:gz") as archive:
            for directory in ("src", "scripts", "config"):
                archive.add(root / directory, arcname=directory, filter=lambda info: None if info.name.endswith("local.json") or "__pycache__" in info.name else info)
    (output_dir / "trace.json").write_bytes(trace_path.read_bytes())
    manifest = {"schema_version": 1, "classification": "diagnostic",
                "status": "running", "device_id": device_id, "code_commit": revision,
                "dirty": bool(dirty), "trace_sha256": digest(trace_path),
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "endpoint": endpoint, "request_count": len(trace["requests"])}
    write_json(output_dir / "manifest.json", manifest)
    results = []
    # One waiting worker per request: arrivals never wait for earlier completion.
    with ThreadPoolExecutor(max_workers=len(trace["requests"])) as pool:
        epoch_ns = time.monotonic_ns() + 200_000_000
        manifest["epoch_ns"] = epoch_ns
        write_json(output_dir / "manifest.json", manifest)
        futures = {pool.submit(stream_request, endpoint, req, epoch_ns, timeout): req["id"]
                   for req in trace["requests"]}
        for future in as_completed(futures):
            record = future.result()
            # Use an index, never a trace-supplied ID as a filesystem path.
            path = output_dir / f"request-{len(results):03d}.json"
            write_json(path, record)
            results.append(record)
    manifest.update(status="complete" if all(r["status"] == "ok" for r in results) else "failed",
                    completed_utc=datetime.now(timezone.utc).isoformat(),
                    successful_requests=sum(r["status"] == "ok" for r in results),
                    files_sha256={p.name: digest(p) for p in sorted(output_dir.glob("request-*.json"))})
    write_json(output_dir / "manifest.json", manifest)
    return manifest
