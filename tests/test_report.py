import json
from pathlib import Path
import tempfile
import unittest

from s1_chunked_prefill.report import aggregate, paired_estimate, verify_run
from s1_chunked_prefill.runner import digest


class ReportTests(unittest.TestCase):
    def test_modified_request_fails_integrity_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'request-000.json').write_text('{"id":"a"}')
            (root / 'trace.json').write_text('{"requests":[{"id":"a"}]}')
            manifest = {'request_count': 1, 'files_sha256': {'request-000.json': digest(root / 'request-000.json')},
                        'trace_sha256': digest(root / 'trace.json')}
            (root / 'manifest.json').write_text(json.dumps(manifest))
            verify_run(root)
            (root / 'request-000.json').write_text('{"id":"changed"}')
            with self.assertRaisesRegex(ValueError, 'integrity failure'):
                verify_run(root)

    def test_repeated_trials_are_averaged_before_pairing(self):
        rows = []
        for chunk, values in ((256, [100, 180]), (4096, [100, 100])):
            for value in values:
                rows.append({'device': 'orin', 'campaign': 'c', 'block': 0, 'chunk': chunk,
                             'workload': 'mixed', 'included': True, 'injected_ttft_ms': value,
                             'active_max_gap_ms': None, 'interference_max_gap_ms': None,
                             'output_tokens_per_second': None})
        result = aggregate(rows)['paired_comparisons'][0]
        self.assertEqual(result['blocks'], 1)
        self.assertAlmostEqual(result['geometric_mean_ratio'], 1.4)
        self.assertEqual(result['mean_difference'], 40)
        self.assertIsNone(result['ratio_ci95'])

    def test_constant_paired_effect_and_uncertainty(self):
        result = paired_estimate([(20, 10)] * 8)
        self.assertEqual(result['blocks'], 8)
        self.assertEqual(result['difference_ci95'], [10, 10])
        for value in result['ratio_ci95']:
            self.assertAlmostEqual(value, 2)
