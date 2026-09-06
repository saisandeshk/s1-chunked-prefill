"""Incremental SSE framing and SGLang native stream accounting."""

import codecs
import json


class ProtocolError(ValueError):
    pass


class SSEDecoder:
    """Accept arbitrary byte fragments, including split UTF-8 and CRLF."""

    def __init__(self):
        self.decoder = codecs.getincrementaldecoder("utf-8-sig")()
        self.line = ""
        self.data = []
        self.after_cr = False

    def feed(self, chunk):
        events = []
        for char in self.decoder.decode(chunk):
            if char == "\n" and self.after_cr:
                self.after_cr = False
                continue
            self.after_cr = char == "\r"
            if char in "\r\n":
                if self.line == "":
                    if self.data:
                        events.append("\n".join(self.data))
                        self.data = []
                elif self.line.startswith("data:"):
                    value = self.line[5:]
                    self.data.append(value[1:] if value.startswith(" ") else value)
                elif self.line == "data":
                    self.data.append("")
                self.line = ""
            else:
                self.line += char
                if len(self.line) > 8 * 1024 * 1024:
                    raise ProtocolError("SSE line exceeds 8 MiB")
        return events

    def finish(self):
        self.decoder.decode(b"", final=True)
        if self.line or self.data:
            raise ProtocolError("EOF inside an SSE event")


class NativeStream:
    """Preserve delivery events; cumulative text is not a token clock."""

    def __init__(self):
        self.events = []
        self.content_times_ns = []
        self.text = ""
        self.meta = {}
        self.done = False
        self.finish_reason = None

    def accept(self, data, received_ns):
        if self.done:
            raise ProtocolError("Event after [DONE]")
        if data == "[DONE]":
            self.done = True
            self.events.append({"received_ns": received_ns, "done": True})
            return
        payload = json.loads(data)
        self.events.append({"received_ns": received_ns, "payload": payload})
        if not isinstance(payload, dict):
            raise ProtocolError("Expected one native generation object")
        if payload.get("error") or payload.get("object") == "error":
            raise ProtocolError(f"Application error: {payload}")
        current = payload.get("text", self.text)
        if not isinstance(current, str):
            raise ProtocolError("Native text must be a string")
        if current and current != self.text:
            self.content_times_ns.append(received_ns)
        self.text = current
        meta = payload.get("meta_info", {})
        if not isinstance(meta, dict):
            raise ProtocolError("Invalid native metadata")
        self.meta.update(meta)
        if meta.get("finish_reason") is not None:
            self.finish_reason = meta["finish_reason"]
            if isinstance(self.finish_reason, dict) and self.finish_reason.get("type") == "abort":
                raise ProtocolError(f"Generation aborted: {self.finish_reason}")

    def validate(self, expected_prompt_tokens=None):
        if not self.done or self.finish_reason is None:
            raise ProtocolError("Missing terminal marker or finish reason")
        if not self.content_times_ns:
            raise ProtocolError("No nonempty streamed content")
        for key in ("prompt_tokens", "completion_tokens"):
            if type(self.meta.get(key)) is not int or self.meta[key] <= 0:
                raise ProtocolError(f"Missing or invalid {key}")
        if expected_prompt_tokens is not None and self.meta["prompt_tokens"] != expected_prompt_tokens:
            raise ProtocolError("Server prompt count differs from input IDs")
