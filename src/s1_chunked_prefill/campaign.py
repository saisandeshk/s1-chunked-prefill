"""Guarded, restart-aware diagnostic treatment blocks on one Orin.

Each cell owns one server, warms the trace shapes, records telemetry and all
outcomes, then finalizes controller evidence even when a request fails.
"""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time

from .analysis import summarize_run
from .client import connection, json_request
from .runner import digest, run_trace, write_json

ROOT = Path(__file__).resolve().parents[2]
WRAPPER = "/usr/local/sbin/jouleserve-docker"
COMMON_KEYS = ("context_length", "mem_fraction_static", "kv_cache_dtype", "attention_backend",
               "max_running_requests", "max_total_tokens", "cuda_graph_max_bs",
               "max_prefill_tokens", "random_seed")


def treatment_order(chunks, blocks, seed):
    rng = random.Random(seed)
    cells = []
    for block in range(blocks):
        order = list(chunks)
        rng.shuffle(order)
        cells.extend({"block": block, "chunk": chunk} for chunk in order)
    return cells


def server_command(joule, action, name, evidence, config, reference, chunk, port):
    command = ["bash", str(joule / "scripts/sglang-server-control.sh"), action,
               "--name", name, "--evidence-dir", str(evidence)]
    if action == "start":
        command += ["--image", reference["runtime"]["local_image_id"],
                    "--model", reference["model"]["id"], "--revision", reference["model"]["revision"],
                    "--port", str(port), "--chunked-prefill-size", str(chunk)]
        for key in COMMON_KEYS:
            command.extend(["--" + key.replace("_", "-"), str(config["common_server"][key])])
    return command


def verify_server(info, config, reference, chunk):
    expected = {key: config["common_server"][key] for key in COMMON_KEYS if key != "cuda_graph_max_bs"}
    expected.update(chunked_prefill_size=chunk, enable_mixed_chunk=False,
                    enable_dynamic_chunking=False, version=reference["runtime"]["version"],
                    served_model_name=reference["model"]["id"],
                    max_total_num_tokens=config["common_server"]["max_total_tokens"])
    expected.update(config.get("runtime_requirements", {}))
    # New SGLang spelling of the compatibility launch flag.
    graph = info.get("cuda_graph_max_bs_decode", info.get("cuda_graph_max_bs"))
    if graph != config["common_server"]["cuda_graph_max_bs"]:
        raise ValueError(f"Graph batch limit differs: {graph}")
    mismatches = {key: {"expected": value, "actual": info.get(key)}
                  for key, value in expected.items() if info.get(key) != value}
    if mismatches:
        raise ValueError(f"Live treatment differs from requested configuration: {mismatches}")


def flush_cache(endpoint):
    conn, prefix = connection(endpoint, 30)
    try:
        conn.request("GET", prefix + "/flush_cache")
        response = conn.getresponse()
        body = response.read().decode()
        if response.status != 200 or "Cache flushed" not in body:
            raise RuntimeError(f"Cache flush failed: {response.status} {body}")
    finally:
        conn.close()
    # The endpoint acknowledges asynchronously. Logs and actual cached-token
    # counts, not this delay, provide the evidence that the flush took effect.
    time.sleep(.2)


def thermal_snapshot(root=Path("/sys/class/thermal")):
    values, errors = {}, {}
    for path in sorted(root.glob("thermal_zone*/temp")):
        name = path.parent.name
        try:
            name = (path.parent / "type").read_text().strip()
            # Some powered-down Jetson zones return EAGAIN. TextIOWrapper on
            # Python 3.10 turns that into an opaque None/bytes TypeError;
            # os.read preserves the actual errno for the evidence record.
            fd = os.open(path, os.O_RDONLY)
            try:
                values[name] = int(os.read(fd, 4096))
            finally:
                os.close(fd)
        except (OSError, ValueError) as exc:
            errors[name] = {"type": type(exc).__name__, "errno": getattr(exc, "errno", None),
                            "message": str(exc)}
    return values, errors


def snapshot():
    mem = Path("/proc/meminfo").read_text()
    available = int(next(line.split()[1] for line in mem.splitlines() if line.startswith("MemAvailable:")))
    stats = {"wall_time_ns": time.time_ns(), "monotonic_ns": time.monotonic_ns(),
             "meminfo": mem, "vmstat": Path("/proc/vmstat").read_text(),
             "loadavg": os.getloadavg(), "free_disk_bytes": shutil.disk_usage(ROOT).free,
             "available_memory_kib": available}
    commands = {"processes": ["ps", "-eo", "pid,uid,comm,pcpu,pmem"],
                "services": ["systemctl", "is-active", "k3s", "k3s-agent", "jtop", "ollama"],
                "power_mode": ["nvpmodel", "-q"],
                "containers": ["sudo", "-n", WRAPPER, "observe", "ps"]}
    for key, command in commands.items():
        result = subprocess.run(command, text=True, capture_output=True, timeout=30)
        stats[key] = {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    stats["thermal_millicelsius"], stats["thermal_read_errors"] = thermal_snapshot()
    return stats


def quality(summary, trace, before, after, limits=None):
    limits = limits or {}
    issues = []
    if summary["manifest_status"] != "complete":
        issues.append("request_failure")
    expectations = {r["id"]: r for r in trace["requests"]}
    for metric in summary["request_metrics"]:
        expected = expectations[metric["id"]]
        if limits.get("require_exact_prompt_tokens") and metric["prompt_tokens"] != len(expected["payload"]["input_ids"]):
            issues.append("prompt_count_mismatch:" + metric["id"])
        if metric["completion_tokens"] != expected["payload"]["sampling_params"]["max_new_tokens"]:
            issues.append("output_count_mismatch:" + metric["id"])
        if metric["cached_tokens"] != 0:
            issues.append("cached_input_or_missing_cache_accounting:" + metric["id"])
        if metric["dispatch_lateness_ms"] is None or metric["dispatch_lateness_ms"] > 20:
            issues.append("dispatch_lateness:" + metric["id"])
    if any(r["role"] == "injected" for r in trace["requests"]):
        wanted = {r["id"] for r in trace["requests"] if r["role"] == "active"}
        if set(summary["active_requests_spanning_injection"]) != wanted:
            issues.append("missing_active_decode_overlap")
    def vm(data):
        return {k: int(v) for k, v in (line.split() for line in data["vmstat"].splitlines())}
    prior, current = vm(before), vm(after)
    for key in ("pswpin", "pswpout", "oom_kill"):
        if current.get(key, 0) != prior.get(key, 0):
            issues.append("host_" + key + "_changed")
    if before["services"] != after["services"]:
        issues.append("service_state_changed")
    for name, maximum in limits.get("maximum_temperature_millicelsius", {}).items():
        values = [host.get("thermal_millicelsius", {}).get(name) for host in (before, after)]
        if any(value is None for value in values):
            issues.append("required_temperature_missing:" + name)
        elif max(values) > maximum:
            issues.append("temperature_limit_exceeded:" + name)
    return {"diagnostic_valid": not issues, "issues": issues}


def execute(args):
    config = json.loads(args.config.read_text())
    reference_path = args.config.parent / config["runtime_reference"]
    reference = json.loads(reference_path.read_text())
    measurement = config.get("measurement", {})
    classification = measurement.get("classification", "diagnostic")
    if measurement.get("publication_protocol_frozen"):
        for actual, key in ((args.blocks, "repeated_blocks"), (args.repeats, "measured_repeats_per_cell_workload"),
                            (args.warmups, "warmup_repeats_per_cell_workload"), (args.seed, "order_seed")):
            if actual != measurement[key]:
                raise ValueError(f"Campaign arguments differ from frozen {key}")
    if args.blocks <= 0 or args.repeats <= 0 or args.warmups <= 0:
        raise ValueError("Blocks, repeats and warmups must be positive")
    if not str(ROOT).startswith("/media/ssd/saisandesh/projects/"):
        raise ValueError("Campaign runs only from the Orin SSD project checkout")
    if subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True):
        raise ValueError("Campaign requires a clean committed checkout")
    traces = [path.resolve() for path in args.traces]
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "runs"):
        raise ValueError("Campaign output must be inside this checkout's runs directory")
    output.mkdir(parents=True, exist_ok=False)
    lock_path = ROOT / "runs" / f"port-{args.port}.lock"
    with lock_path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock.seek(0)
        lock.truncate()
        lock.write(str(os.getpid()))
        lock.flush()
        state = {"schema_version": 1, "classification": classification, "pid": os.getpid(),
                 "status": "running", "device_id": args.device_id,
                 "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                 "config_sha256": digest(args.config), "runtime_reference_sha256": digest(reference_path),
                 "traces": {str(p.relative_to(ROOT)): digest(p) for p in traces},
                 "seed": args.seed, "warmups": args.warmups, "repeats": args.repeats,
                 "cells": treatment_order(config["treatments"]["chunked_prefill_size"], args.blocks, args.seed)}
        write_json(output / "campaign.json", state)
        shutil.copy(args.config, output / "config.json")
        shutil.copy(reference_path, output / "runtime-reference.json")
        endpoint = f"http://127.0.0.1:{args.port}"
        try:
            for index, cell in enumerate(state["cells"]):
                cell_dir = output / f"cell-{index:03d}-b{cell['block']}-c{cell['chunk']}"
                cell_dir.mkdir()
                name = "jouleserve-srs-s1-" + hashlib.sha256(str(output).encode()).hexdigest()[:8] + f"-{index:03d}"
                evidence = args.jouleserve_root / "runs" / name
                cell.update(status="starting", name=name, evidence_dir=str(evidence), output=str(cell_dir))
                write_json(output / "campaign.json", state)
                pre = snapshot()
                write_json(cell_dir / "admission.json", pre)
                if pre["available_memory_kib"] < 8 * 1024**2 or pre["free_disk_bytes"] < 10 * 1024**3:
                    raise RuntimeError("Insufficient memory or SSD headroom")
                for name, maximum in config.get("measurement", {}).get("quality_limits", {}).get("maximum_temperature_millicelsius", {}).items():
                    value = pre["thermal_millicelsius"].get(name)
                    if value is None or value > maximum:
                        raise RuntimeError(f"Thermal admission failed for {name}: {value}")
                # Refuse contention with any existing Docker container. Never stop it.
                if pre["containers"]["exit_code"] != 0 or len(pre["containers"]["stdout"].strip().splitlines()) > 1:
                    raise RuntimeError("Container inventory unavailable or another container is running")
                collector = None
                collector_log = None
                started = False
                try:
                    started = True  # A failed launch may still need owned cleanup.
                    with (cell_dir / "launch.log").open("w") as log:
                        subprocess.run(server_command(args.jouleserve_root, "start", name, evidence, config,
                                                      reference, cell["chunk"], args.port),
                                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=900)
                    info = json_request(endpoint, "/server_info")
                    write_json(cell_dir / "server-info.json", info)
                    verify_server(info, config, reference, cell["chunk"])
                    collector_log = (cell_dir / "collector.log").open("w")
                    collector = subprocess.Popen([sys.executable, str(args.jouleserve_root / "scripts/collect-telemetry.py"),
                                                  "--run-id", name, "--output-dir", str(cell_dir / "telemetry"),
                                                  "--interval-ms", "500"], stdout=collector_log, stderr=subprocess.STDOUT)
                    deadline = time.monotonic() + 15
                    while not (cell_dir / "telemetry/READY").exists():
                        if collector.poll() is not None or time.monotonic() > deadline:
                            raise RuntimeError("Telemetry collector failed readiness")
                        time.sleep(.1)
                    cell["runs"] = []
                    for repeat in range(-args.warmups, args.repeats):
                        order = list(traces)
                        random.Random(args.seed + cell["block"] * 1000 + repeat).shuffle(order)
                        for trace_path in order:
                            flush_cache(endpoint)
                            before = snapshot()
                            run_id = f"{'warmup' if repeat < 0 else 'repeat'}-{abs(repeat):02d}-{trace_path.stem}"
                            run_dir = cell_dir / run_id
                            run_trace(endpoint, trace_path, run_dir, device_id=args.device_id, classification=classification)
                            after = snapshot()
                            summary = summarize_run(run_dir)
                            summary["quality"] = quality(summary, json.loads(trace_path.read_text()), before, after,
                                                         config.get("measurement", {}).get("quality_limits"))
                            write_json(run_dir / "summary.json", summary)
                            write_json(run_dir / "host-before.json", before)
                            write_json(run_dir / "host-after.json", after)
                            cell["runs"].append({"path": run_id, "warmup": repeat < 0, "quality": summary["quality"]})
                            write_json(output / "campaign.json", state)
                            if collector.poll() is not None:
                                raise RuntimeError("Telemetry collector stopped during cell")
                            time.sleep(.5)
                    cell["status"] = "complete"
                finally:
                    try:
                        if collector is not None:
                            collector.terminate()
                            try:
                                collector.wait(timeout=15)
                            except subprocess.TimeoutExpired:
                                collector.kill()
                                collector.wait(timeout=5)
                            cell["collector_exit_code"] = collector.returncode
                    finally:
                        if collector_log is not None:
                            collector_log.close()
                        try:
                            if started:
                                with (cell_dir / "stop.log").open("w") as log:
                                    subprocess.run(server_command(args.jouleserve_root, "stop", name, evidence, config,
                                                                  reference, cell["chunk"], args.port),
                                                   stdout=log, stderr=subprocess.STDOUT, check=True, timeout=90)
                        finally:
                            write_json(output / "campaign.json", state)
                print(f"Completed block {cell['block']} chunk {cell['chunk']}", flush=True)
            state["status"] = "complete"
        except BaseException as exc:
            state.update(status="failed", error={"type": type(exc).__name__, "message": str(exc)})
            raise
        finally:
            write_json(output / "campaign.json", state)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/pilot.json")
    parser.add_argument("--jouleserve-root", type=Path, default=ROOT.parent / "JouleServe")
    parser.add_argument("--traces", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--port", type=int, default=30001)
    parser.add_argument("--blocks", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--seed", type=int, default=20260907)
    args = parser.parse_args()
    def terminate(signum, frame):
        raise KeyboardInterrupt(f"Received signal {signum}")
    signal.signal(signal.SIGTERM, terminate)
    execute(args)


if __name__ == "__main__":
    main()
