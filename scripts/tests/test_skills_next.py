"""Failure paths for the local Skills/MCP block; no services or user data."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / 'scripts/skills'))
import local_tools as local
import design_mcp as mcp
from mcp_probe import probe


class LocalTests(unittest.TestCase):
    def setUp(self):
        self.brief = json.loads((local.ROOT / 'fixtures/design-brief.json').read_text())

    def test_valid_brief(self):
        self.assertTrue(local.validate_brief(self.brief)['valid'])

    def test_bad_brief_types(self):
        for value in [None, [], {}, self.brief | {'purpose': ' '}, self.brief | {'preserve': 'tokens'},
                      self.brief | {'acceptance': []}, self.brief | {'references': [4]},
                      self.brief | {'secret': 'synthetic-unexpected-field'}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                local.validate_brief(value)

    def test_html_detects_missing_semantics(self):
        lint = local.StructuralLint(); lint.feed('<html><img src="fixture.png"><input><p id="x"><p id="x">')
        self.assertEqual(set(lint.result()['findings']), {'missing_lang', 'missing_title', 'missing_main',
                         'image_missing_alt', 'image_missing_dimensions', 'input_missing_id', 'duplicate_id'})

    def test_html_valid_fixture(self):
        lint = local.StructuralLint(); lint.feed((local.ROOT / 'fixtures/browser.html').read_text())
        self.assertEqual(lint.result()['findings'], [])

    def test_find_offline_and_deterministic(self):
        self.assertEqual(local.find('browser'), local.find('browser'))
        self.assertTrue(any(e['name'] == 'Agent Browser' for e in local.find('browser')))
        self.assertEqual(local.find('no-such-synthetic-capability'), [])

    def test_media_no_video_rejected(self):
        for payload in [{}, {'streams': [{'codec_type': 'audio'}], 'format': {'duration': '1'}},
                        {'streams': [{'codec_type': 'video', 'width': 0, 'height': 10}], 'format': {'duration': '1'}}]:
            with patch('local_tools.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps(payload))), self.assertRaises(ValueError):
                local.media(Path('/tmp/synthetic'), 'ffprobe')

    def test_media_failure_redacted(self):
        with patch('local_tools.subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'synthetic-user-tags')):
            with self.assertRaisesRegex(ValueError, '^ffprobe_failed$'):
                local.media(Path('/tmp/synthetic'), 'ffprobe')

    def test_measurement_zero_is_data(self):
        output='lavfi.signalstats.YAVG=0\n'+'lavfi.signalstats.UAVG=0\n'+'lavfi.signalstats.VAVG=0\n'
        with patch('local_tools.media',return_value={'duration_seconds':1}), patch('local_tools.subprocess.run',return_value=subprocess.CompletedProcess([],0,output)):
            value=local.measure_video(local.ROOT/'fixtures/design-brief.json','synthetic','ffmpeg','ffprobe')
        self.assertEqual(value['signalstats']['YAVG']['mean'],0)

    def test_measurement_missing_is_failure(self):
        with patch('local_tools.media',return_value={'duration_seconds':1}), patch('local_tools.subprocess.run',return_value=subprocess.CompletedProcess([],0,'')), self.assertRaisesRegex(ValueError,'missing_samples'):
            local.measure_video(local.ROOT/'fixtures/design-brief.json','synthetic','ffmpeg','ffprobe')

    def test_export_refuses_existing_output(self):
        with self.assertRaisesRegex(ValueError, 'output_exists'):
            local.export_video(Path('/tmp/synthetic'), local.ROOT / 'PROFILE.json', 640, 640, 'ffmpeg', 'ffprobe')

    def test_export_rejects_invalid_dimensions(self):
        for width,height in [(0,640),(639,640),(4000,640)]:
            with self.assertRaises(ValueError):
                local.export_video(Path('/tmp/synthetic'), Path('/tmp/choms-unused-output.mp4'), width, height, 'ffmpeg', 'ffprobe')

    def test_mcp_notifications_silent(self):
        self.assertIsNone(mcp.dispatch({'jsonrpc': '2.0', 'method': 'notifications/initialized'}))

    def test_mcp_wrong_params_type(self):
        reply=mcp.dispatch({'id':1,'method':'tools/call','params':[]})
        self.assertEqual(reply['error']['code'],-32602)

    def test_mcp_unknown_tool(self):
        reply = mcp.dispatch({'id': 1, 'method': 'tools/call', 'params': {'name': 'not-a-tool'}})
        self.assertEqual(reply['error']['code'], -32602)

    def test_mcp_real_subprocess(self):
        result = probe([sys.executable, '-B', str(BASE / 'scripts/skills/design_mcp.py')])
        self.assertEqual(result['status'], 'PASS')

    def test_mcp_malformed_json_recovers(self):
        p = subprocess.run([sys.executable, '-B', str(BASE / 'scripts/skills/design_mcp.py')],
                           input='invalid\n{"id":7,"method":"ping"}\n', capture_output=True, text=True, timeout=10)
        first, second = map(json.loads, p.stdout.splitlines())
        self.assertEqual(first['error']['code'], -32700)
        self.assertEqual(second['result'], {})
        self.assertEqual(p.stderr, '')


if __name__ == '__main__':
    unittest.main()
