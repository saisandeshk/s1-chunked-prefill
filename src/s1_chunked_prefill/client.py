"""Dependency-free HTTP client for a device-local SGLang endpoint."""

import http.client
import json
import time
from urllib.parse import urlsplit

from .protocol import NativeStream, ProtocolError, SSEDecoder


def connection(endpoint, timeout):
    url = urlsplit(endpoint)
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
        raise ValueError("Expected an HTTP(S) endpoint without credentials")
    cls = http.client.HTTPSConnection if url.scheme == "https" else http.client.HTTPConnection
    return cls(url.hostname, url.port, timeout=timeout), url.path.rstrip("/")


def json_request(endpoint, path, payload=None, timeout=60):
    conn, prefix = connection(endpoint, timeout)
    try:
        body = json.dumps(payload).encode() if payload is not None else None
        conn.request("POST" if body is not None else "GET", prefix + path, body,
                     {"Content-Type": "application/json"})
        response = conn.getresponse()
        data = response.read()
        if response.status != 200:
            raise ProtocolError(f"HTTP {response.status}: {data[:2048]!r}")
        return json.loads(data) if data else None
    finally:
        conn.close()


def stream_request(endpoint, request, epoch_ns, timeout=120):
    """One connection per request; no retry that could alter offered load."""
    intended_ns = epoch_ns + round(request["offset_ms"] * 1_000_000)
    stream = NativeStream()
    decoder = SSEDecoder()
    record = {"id": request["id"], "role": request["role"],
              "intended_dispatch_ns": intended_ns, "status": "error"}
    conn = None
    try:
        conn, prefix = connection(endpoint, timeout)
        body = json.dumps(request["payload"], separators=(",", ":")).encode()
        delay = (intended_ns - time.monotonic_ns()) / 1e9
        if delay > 0:
            time.sleep(delay)
        record["dispatch_ns"] = time.monotonic_ns()
        conn.request("POST", prefix + "/generate", body,
                     {"Content-Type": "application/json", "Accept": "text/event-stream"})
        record["request_sent_ns"] = time.monotonic_ns()
        response = conn.getresponse()
        record["headers_ns"] = time.monotonic_ns()
        record["http_status"] = response.status
        if response.status != 200:
            raise ProtocolError(f"HTTP {response.status}: {response.read(2048)!r}")
        if "text/event-stream" not in response.getheader("Content-Type", ""):
            raise ProtocolError(f"Expected SSE response: {response.read(2048)!r}")
        while True:
            if time.monotonic_ns() - record["dispatch_ns"] > timeout * 1e9:
                raise TimeoutError("Total stream deadline exceeded")
            chunk = response.read1(65536)
            received_ns = time.monotonic_ns()
            if not chunk:
                break
            for data in decoder.feed(chunk):
                stream.accept(data, received_ns)
        decoder.finish()
        ids = request["payload"].get("input_ids")
        stream.validate(len(ids) if ids is not None else None)
        record["status"] = "ok"
    except Exception as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        record["completed_ns"] = time.monotonic_ns()
        if conn is not None:
            conn.close()
    record.update(events=stream.events, content_times_ns=stream.content_times_ns,
                  text=stream.text, meta_info=stream.meta, finish_reason=stream.finish_reason,
                  done=stream.done)
    return record
