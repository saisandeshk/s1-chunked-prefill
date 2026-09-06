import argparse
import json
from pathlib import Path

from .analysis import summarize_run
from .runner import run_trace, write_json
from .trace import make_trace


def main():
    parser = argparse.ArgumentParser(description="S1 chunked-prefill experiment client")
    commands = parser.add_subparsers(dest="command", required=True)
    trace = commands.add_parser("make-trace")
    trace.add_argument("--endpoint", default="http://127.0.0.1:30001")
    trace.add_argument("--output", type=Path, required=True)
    trace.add_argument("--active", type=int, default=4)
    trace.add_argument("--short-tokens", type=int, default=256)
    trace.add_argument("--long-tokens", type=int, default=3072)
    trace.add_argument("--output-tokens", type=int, default=128)
    trace.add_argument("--injection-ms", type=float, default=500)
    trace.add_argument("--trace-id", default="pilot-v1")
    run = commands.add_parser("run")
    run.add_argument("--endpoint", default="http://127.0.0.1:30001")
    run.add_argument("--trace", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--device-id", required=True)
    run.add_argument("--timeout", type=float, default=120)
    run.add_argument("--allow-dirty", action="store_true")
    summary = commands.add_parser("summarize")
    summary.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "make-trace":
        if args.output.exists():
            parser.error("Trace already exists; choose a new path")
        value = make_trace(args.endpoint, active=args.active, short_tokens=args.short_tokens,
                           long_tokens=args.long_tokens, output_tokens=args.output_tokens,
                           injection_ms=args.injection_ms, trace_id=args.trace_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        write_json(args.output, value)
        print(f"Wrote {len(value['requests'])} requests to {args.output}")
    elif args.command == "run":
        value = run_trace(args.endpoint, args.trace, args.output_dir, device_id=args.device_id,
                          timeout=args.timeout, allow_dirty=args.allow_dirty)
        write_json(args.output_dir / "summary.json", summarize_run(args.output_dir))
        print(json.dumps(value, indent=2))
        return 0 if value["status"] == "complete" else 1
    else:
        print(json.dumps(summarize_run(args.directory), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
