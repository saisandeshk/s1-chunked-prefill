from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
import unittest

from s1_chunked_prefill.client import stream_request


class FakeServer(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    arrivals = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.arrivals.append(time.monotonic_ns())
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Connection', 'close')
        self.end_headers()
        for text in ('', 'one two', 'one two three'):
            event = 'data: ' + json.dumps({'text': text, 'meta_info': {}}) + '\n\n'
            # Deliberate wire fragmentation; content events still span multiple tokens.
            for part in (event[:7].encode(), event[7:].encode()):
                self.wfile.write(part)
                self.wfile.flush()
            time.sleep(.04)
        terminal = {'text': 'one two three', 'meta_info': {'prompt_tokens': len(payload['input_ids']),
                    'completion_tokens': 3, 'finish_reason': {'type': 'length'}}}
        self.wfile.write(('data: ' + json.dumps(terminal) + '\n\ndata: [DONE]\n\n').encode())
        self.wfile.flush()
        self.close_connection = True


class ClientTests(unittest.TestCase):
    def test_stream_timing_and_open_loop_arrivals_use_real_http(self):
        FakeServer.arrivals = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), FakeServer)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            endpoint = f'http://127.0.0.1:{server.server_port}'
            epoch = time.monotonic_ns() + 100_000_000
            requests = [{'id': str(i), 'role': 'active' if i == 0 else 'injected',
                         'offset_ms': i * 20, 'payload': {'input_ids': [1, 2], 'stream': True}}
                        for i in range(2)]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(stream_request, endpoint, req, epoch, 5) for req in requests]
                records = [future.result() for future in futures]
            self.assertTrue(all(r['status'] == 'ok' for r in records), records)
            self.assertLess(records[1]['dispatch_ns'], records[0]['completed_ns'])
            self.assertLess(FakeServer.arrivals[1], records[0]['completed_ns'])
            self.assertEqual(len(records[0]['content_times_ns']), 2)
            self.assertEqual(records[0]['meta_info']['completion_tokens'], 3)
            self.assertLess(records[0]['content_times_ns'][0], records[0]['content_times_ns'][1])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
