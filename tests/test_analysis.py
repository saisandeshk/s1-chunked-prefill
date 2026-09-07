import unittest
import errno
from pathlib import Path
import tempfile
from unittest.mock import patch

from s1_chunked_prefill.analysis import quantile, request_metrics
from s1_chunked_prefill.campaign import check_admission, quality, thermal_snapshot, treatment_order


class AnalysisTests(unittest.TestCase):
    def test_frozen_admission_requires_readable_cool_gpu_and_idle_container_inventory(self):
        config = {'measurement': {'quality_limits': {'maximum_temperature_millicelsius': {'gpu-thermal': 75000}}}}
        pre = {'available_memory_kib': 16 * 1024**2, 'free_disk_bytes': 20 * 1024**3,
               'thermal_millicelsius': {'gpu-thermal': 50000},
               'containers': {'exit_code': 0, 'stdout': 'CONTAINER ID IMAGE\n'}}
        check_admission(pre, config)
        for value in (None, 76000):
            pre['thermal_millicelsius']['gpu-thermal'] = value
            with self.assertRaisesRegex(RuntimeError, 'Thermal admission'):
                check_admission(pre, config)
        pre['thermal_millicelsius']['gpu-thermal'] = 50000
        pre['containers']['stdout'] += 'foreign runtime\n'
        with self.assertRaisesRegex(RuntimeError, 'another container'):
            check_admission(pre, config)

    def test_temporarily_unavailable_sensor_preserves_other_temperatures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i, name in enumerate(('cpu-thermal', 'offline-zone')):
                zone = root / f'thermal_zone{i}'
                zone.mkdir()
                (zone / 'type').write_text(name)
                (zone / 'temp').write_text('51000')
            with patch('s1_chunked_prefill.campaign.os.read',
                       side_effect=[b'51000\n', BlockingIOError(errno.EAGAIN, 'temporarily unavailable')]):
                values, errors = thermal_snapshot(root)
            self.assertEqual(values, {'cpu-thermal': 51000})
            self.assertEqual(errors['offline-zone']['errno'], errno.EAGAIN)

    def test_delivery_events_are_not_counted_as_tokens(self):
        record = {"id": "a", "role": "active", "status": "ok", "dispatch_ns": 1_000_000,
                  "intended_dispatch_ns": 0, "completed_ns": 21_000_000,
                  "content_times_ns": [3_000_000, 7_000_000, 19_000_000],
                  "meta_info": {"prompt_tokens": 20, "completion_tokens": 5, "cached_tokens": 0}}
        value = request_metrics(record)
        self.assertEqual(value["ttft_ms"], 2)
        self.assertEqual(value["aggregate_tpot_ms"], 4)
        self.assertEqual(value["content_gap_max_ms"], 12)
        self.assertEqual(value["content_events"], 3)
        self.assertEqual(value["completion_tokens"], 5)
        self.assertAlmostEqual(value["content_gap_p95_ms"], 11.6)

    def test_missing_content_is_missing_measurement(self):
        self.assertIsNone(quantile([], .95))

    def test_each_randomized_block_contains_each_treatment_once(self):
        cells = treatment_order([256, 1024, 4096], 7, 42)
        self.assertEqual(cells, treatment_order([256, 1024, 4096], 7, 42))
        for block in range(7):
            self.assertCountEqual([c['chunk'] for c in cells if c['block'] == block], [256, 1024, 4096])

    def test_failed_overlap_cache_reuse_and_swap_are_not_valid_measurements(self):
        summary = {"manifest_status": "complete", "active_requests_spanning_injection": [],
                   "request_metrics": [{"id": "a", "completion_tokens": 8, "cached_tokens": 2,
                                        "dispatch_lateness_ms": 1}]}
        trace = {"requests": [{"id": "a", "role": "active", "payload": {"sampling_params": {"max_new_tokens": 8}}},
                              {"id": "b", "role": "injected"}]}
        before = {"vmstat": "pswpin 0\npswpout 0\noom_kill 0\n", "services": {}}
        after = {"vmstat": "pswpin 1\npswpout 0\noom_kill 0\n", "services": {}}
        result = quality(summary, trace, before, after)
        self.assertFalse(result['diagnostic_valid'])
        self.assertIn('missing_active_decode_overlap', result['issues'])
        self.assertIn('host_pswpin_changed', result['issues'])
        self.assertIn('cached_input_or_missing_cache_accounting:a', result['issues'])
