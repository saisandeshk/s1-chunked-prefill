"""Versioned synthetic load traces with exact, server-tokenized inputs."""

import math

from .client import json_request

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
PASSAGE = (
    "The field team records temperature, rainfall, wind and soil moisture each morning. "
    "The measurements help compare conditions across farms and plan the next inspection. "
    "Engineers verify the sensors and retain each observation with its timestamp. "
)


def make_trace(endpoint, *, active=4, short_tokens=256, long_tokens=3072,
               output_tokens=128, injection_ms=500, trace_id="pilot-v1"):
    if not 1 <= active <= 7 or min(short_tokens, long_tokens, output_tokens) <= 0:
        raise ValueError("Invalid request or token counts")
    if not math.isfinite(injection_ms) or injection_ms < 0:
        raise ValueError("Injection offset must be finite and nonnegative")
    if max(short_tokens, long_tokens) + output_tokens > 4096:
        raise ValueError("Input plus output exceeds the pilot context")
    requests = []
    for index in range(active + 1):
        role = "injected" if index == active else "active"
        length = long_tokens if role == "injected" else short_tokens
        # The leading differing number bounds inter-request prefix reuse.
        prompt = f"{index + 1} {trace_id}: Continue the field report in detail.\n" + PASSAGE * (length // 20 + 2)
        result = json_request(endpoint, "/v1/tokenize", {
            "model": MODEL, "prompt": prompt, "add_special_tokens": False})
        tokens = result["tokens"][:length]
        if len(tokens) != length or any(type(t) is not int or t < 0 for t in tokens):
            raise ValueError("Tokenizer did not return enough valid token IDs")
        requests.append({"id": f"{role}-{index}", "role": role,
                         "offset_ms": injection_ms if role == "injected" else 0,
                         "payload": {"input_ids": tokens, "stream": True,
                                     "sampling_params": {"temperature": 0,
                                                         "max_new_tokens": output_tokens,
                                                         "ignore_eos": True}}})
    trace = {"schema_version": 1, "trace_id": trace_id, "model": MODEL,
             "workload_kind": "synthetic_native_completion_fixed_token_budget",
             "generation": {"active": active, "short_tokens": short_tokens,
                            "long_tokens": long_tokens, "output_tokens": output_tokens,
                            "injection_ms": injection_ms, "passage": PASSAGE},
             "requests": requests}
    validate_trace(trace)
    return trace


def validate_trace(trace):
    requests = trace["requests"]
    if not requests or len(requests) > 8:
        raise ValueError("Trace must contain 1–8 requests")
    if len({r["id"] for r in requests}) != len(requests):
        raise ValueError("Request IDs must be unique")
    for req in requests:
        if req["role"] not in ("active", "injected", "control"):
            raise ValueError("Unknown request role")
        if not math.isfinite(req["offset_ms"]) or req["offset_ms"] < 0:
            raise ValueError("Invalid arrival offset")
        payload = req["payload"]
        ids = payload["input_ids"]
        cap = payload["sampling_params"]["max_new_tokens"]
        if not ids or any(type(t) is not int or t < 0 for t in ids):
            raise ValueError("Invalid input IDs")
        if type(cap) is not int or cap <= 0 or len(ids) + cap > 4096:
            raise ValueError("Invalid output cap or context overflow")
        if payload.get("stream") is not True:
            raise ValueError("Trace must use streaming")
