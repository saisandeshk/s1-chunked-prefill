import json
import unittest

from s1_chunked_prefill.protocol import NativeStream, ProtocolError, SSEDecoder


class SSETests(unittest.TestCase):
    def test_every_fragment_size_preserves_utf8_crlf_comments_and_multiline(self):
        raw = '\ufeff: heartbeat\r\nevent: message\r\ndata: {"text":\r\ndata: "हैलो"}\r\n\r\ndata: [DONE]\r\n\r\n'.encode()
        for size in range(1, len(raw) + 1):
            parser = SSEDecoder()
            events = []
            for offset in range(0, len(raw), size):
                events.extend(parser.feed(raw[offset:offset + size]))
            parser.finish()
            self.assertEqual(events, ['{"text":\n"हैलो"}', '[DONE]'])

    def test_incomplete_event_is_not_silently_accepted(self):
        parser = SSEDecoder()
        self.assertEqual(parser.feed(b'data: {"text":"partial"}\n'), [])
        with self.assertRaises(ProtocolError):
            parser.finish()

    def test_incomplete_utf8_fails(self):
        parser = SSEDecoder()
        parser.feed(b'data: \xe2')
        with self.assertRaises(UnicodeDecodeError):
            parser.finish()

    def test_native_cumulative_text_metadata_and_delivery_clock(self):
        stream = NativeStream()
        stream.accept(json.dumps({"text": "", "meta_info": {}}), 1)
        stream.accept(json.dumps({"text": "one two", "meta_info": {"completion_tokens": 2}}), 10)
        stream.accept(json.dumps({"text": "one two three"}), 20)
        stream.accept(json.dumps({"text": "one two three", "meta_info": {
            "prompt_tokens": 5, "completion_tokens": 3, "cached_tokens": 0,
            "finish_reason": {"type": "length", "length": 3}}}), 30)
        stream.accept("[DONE]", 40)
        stream.validate(5)
        self.assertEqual(stream.content_times_ns, [10, 20])
        self.assertEqual(stream.meta["completion_tokens"], 3)

    def test_http_200_application_error_and_abort_fail(self):
        for payload in ({"error": {"message": "context overflow"}},
                        {"object": "error", "message": "bad input"},
                        {"meta_info": {"finish_reason": {"type": "abort"}}}):
            with self.assertRaises(ProtocolError):
                NativeStream().accept(json.dumps(payload), 1)

    def test_truncated_success_looking_stream_fails(self):
        stream = NativeStream()
        stream.accept('{"text":"hello","meta_info":{"prompt_tokens":5,"completion_tokens":1}}', 1)
        with self.assertRaises(ProtocolError):
            stream.validate(5)

    def test_wrong_prompt_accounting_fails(self):
        stream = NativeStream()
        stream.accept('{"text":"hello","meta_info":{"prompt_tokens":5,"completion_tokens":1,"finish_reason":{"type":"length"}}}', 1)
        stream.accept('[DONE]', 2)
        with self.assertRaises(ProtocolError):
            stream.validate(6)
