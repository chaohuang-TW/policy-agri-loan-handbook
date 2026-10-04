#!/usr/bin/env python3
"""Offline tests for the isolated inline diagnostic; no network or file writes."""
import ast
import contextlib
import io
import json
from pathlib import Path
import types
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/source-network-diagnostics.yml'
TEXT = WORKFLOW.read_text(encoding='utf-8')
BEGIN = '          # BEGIN_NETWORK_DIAGNOSTICS\n'
END = '          # END_NETWORK_DIAGNOSTICS\n'
assert TEXT.count(BEGIN) == TEXT.count(END) == 1
BLOCK = TEXT.split(BEGIN)[1].split(END)[0]
assert all(not line.strip() or line.startswith('          ') for line in BLOCK.splitlines())
SOURCE = '\n'.join(line[10:] for line in BLOCK.splitlines())
ast.parse(SOURCE)
DIAG = types.ModuleType('offline_network_diagnostics')
exec(compile(SOURCE, str(WORKFLOW), 'exec'), DIAG.__dict__)


class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()

    def tearDown(self):
        self.capture.__exit__(None, None, None)

    def run_result(self, stdout='', code=0):
        return types.SimpleNamespace(stdout=stdout, stderr='PRIVATE_PROXY_SECRET', returncode=code)

    def test_workflow_is_isolated_and_never_deploys(self):
        prefix = TEXT.split(BEGIN)[0]
        self.assertIn('branches: [codex/official-source-network-diagnosis]', prefix)
        self.assertIn("if: github.ref == 'refs/heads/codex/official-source-network-diagnosis'", prefix)
        self.assertIn('runs-on: ubuntu-24.04', prefix)
        self.assertIn('timeout-minutes: 10', prefix)
        self.assertIn("python3.12 -B - <<'PY'", prefix)
        for forbidden in ('uses:', 'permissions:', 'secrets.', 'workflow_dispatch:',
                          'continue-on-error:', 'deploy:', 'contents: write', '|| true'):
            self.assertNotIn(forbidden, prefix)
        self.assertEqual(prefix.count('      - name:'), 1)

    def test_fixed_targets_and_no_credentials_or_body_logging(self):
        self.assertEqual(DIAG.URLS, (
            'https://law.afna.gov.tw/', 'https://law.afna.gov.tw/view.php?id=50',
            'https://law.afna.gov.tw/view.php?id=1551',
            'https://law.afna.gov.tw/files/boaf/law/50/A01_7.pdf', 'https://www.afna.gov.tw/'))
        self.assertEqual(DIAG.USER_AGENT, 'policy-agri-loan-handbook-source-audit/1.0')
        self.assertEqual((DIAG.CONNECT_TIMEOUT, DIAG.REQUEST_TIMEOUT), (8, 25))
        DIAG.failure('test', RuntimeError('PRIVATE_PROXY_SECRET'))
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())

    def test_dns_a_and_absent_aaaa_are_distinct(self):
        a = ';; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1\nlaw.afna.gov.tw. 300 IN A 210.241.95.231\n'
        empty = ';; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 1\n'
        with patch.object(DIAG.subprocess, 'run', side_effect=[self.run_result(a), self.run_result(empty)]) as call:
            self.assertEqual(DIAG.dns_probe(DIAG.HOSTS[0], 'A')['addresses'], ['210.241.95.231'])
            self.assertTrue(DIAG.dns_probe(DIAG.HOSTS[0], 'AAAA')['ok'])
            self.assertEqual(call.call_args.kwargs['timeout'], 5)
        with patch.object(DIAG.subprocess, 'run', return_value=self.run_result(empty)):
            self.assertFalse(DIAG.dns_probe(DIAG.HOSTS[0], 'A')['ok'])

    def test_dns_failure_and_timeout_fail(self):
        with patch.object(DIAG.subprocess, 'run', return_value=self.run_result('status: SERVFAIL,', 0)):
            self.assertFalse(DIAG.dns_probe(DIAG.HOSTS[0], 'A')['ok'])
        with patch.object(DIAG.subprocess, 'run', side_effect=TimeoutError('PRIVATE_PROXY_SECRET')):
            record = DIAG.dns_probe(DIAG.HOSTS[0], 'A')
            self.assertFalse(record['ok'])
            self.assertEqual(record['errorType'], 'TimeoutError')
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())

    def test_tcp_and_tls_failures_are_localized(self):
        raw = MagicMock()
        raw.__enter__.return_value = raw
        raw.connect.side_effect = TimeoutError()
        with patch.object(DIAG.socket, 'socket', return_value=raw):
            records = DIAG.transport_probe(DIAG.HOSTS[0], ['210.241.95.231'])
            self.assertEqual(records[-1]['stage'], 'tcp')
            self.assertFalse(records[-1]['ok'])
        raw.connect.side_effect = None
        tls = MagicMock()
        tls.wrap_socket.side_effect = DIAG.ssl.SSLError()
        with patch.object(DIAG.socket, 'socket', return_value=raw), patch.object(DIAG.ssl, 'create_default_context', return_value=tls):
            records = DIAG.transport_probe(DIAG.HOSTS[0], ['210.241.95.231'])
            self.assertTrue(records[0]['ok'])
            self.assertEqual(records[-1]['stage'], 'tls')
            self.assertFalse(records[-1]['ok'])
            tls.wrap_socket.assert_called_once_with(raw, server_hostname=DIAG.HOSTS[0])

    def test_missing_a_answer_does_not_guess_or_connect(self):
        with patch.object(DIAG.socket, 'socket') as call:
            self.assertFalse(DIAG.transport_probe(DIAG.HOSTS[0], [])[0]['ok'])
            call.assert_not_called()

    def curl_metrics(self, **overrides):
        return {'http_code': 200, 'ssl_verify_result': 0, 'time_appconnect': 0.1,
                'PRIVATE_PROXY_SECRET': 'PRIVATE_PROXY_SECRET', **overrides}

    def test_curl_success_limits_and_redaction(self):
        with patch.object(DIAG.subprocess, 'run', return_value=self.run_result(json.dumps(self.curl_metrics()))) as call:
            self.assertTrue(DIAG.curl_probe(DIAG.URLS[0])['ok'])
            args = call.call_args.args[0]
            self.assertIn('/dev/null', args)
            self.assertNotIn('--location', args)
            self.assertNotIn('--retry', args)
            self.assertNotIn('--insecure', args)
            self.assertNotIn('--noproxy', args)
            self.assertEqual(args[args.index('--max-time') + 1], '25')
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())

    def test_curl_timeout_http_error_and_redirect_do_not_pass(self):
        for code, metrics in ((28, self.curl_metrics(http_code=0)),
                              (0, self.curl_metrics(http_code=500)),
                              (0, self.curl_metrics(http_code=302, redirect_url='https://user:PRIVATE_PROXY_SECRET@law.afna.gov.tw/private?q=PRIVATE_PROXY_SECRET'))):
            with patch.object(DIAG.subprocess, 'run', return_value=self.run_result(json.dumps(metrics), code)):
                self.assertFalse(DIAG.curl_probe(DIAG.URLS[0])['ok'])
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())

    def test_curl_phase_does_not_guess_dns_from_timeout(self):
        self.assertEqual(DIAG.curl_phase(28, {}), 'before-tcp-completion-not-localized')
        self.assertEqual(DIAG.curl_phase(28, {'time_connect': 1}), 'before-tls-completion')
        self.assertEqual(DIAG.curl_phase(28, {'time_appconnect': 1}), 'waiting-for-http-headers')
        self.assertEqual(DIAG.curl_phase(28, {'http_code': 200}), 'body')
        self.assertEqual(DIAG.curl_phase(6, {}), 'dns')
        self.assertEqual(DIAG.curl_phase(7, {}), 'tcp')
        self.assertEqual(DIAG.curl_phase(60, {}), 'tls')

    def test_urllib_headers_and_body_are_separate(self):
        response = MagicMock(status=200)
        response.__enter__.return_value = response
        response.read.side_effect = [b'PRIVATE_RESPONSE_BODY', b'']
        opener = MagicMock()
        opener.open.return_value = response
        with patch.object(DIAG.urllib.request, 'build_opener', return_value=opener), patch.object(DIAG, 'request_deadline', contextlib.nullcontext):
            records = DIAG.urllib_probe(DIAG.URLS[0])
            self.assertEqual([record['stage'] for record in records], ['urllib-headers', 'urllib-body'])
            self.assertTrue(all(record['ok'] for record in records))
            self.assertEqual(opener.open.call_args.kwargs['timeout'], 25)
        self.assertNotIn('PRIVATE_RESPONSE_BODY', self.output.getvalue())

    def test_urllib_body_timeout_keeps_header_evidence(self):
        response = MagicMock(status=200)
        response.__enter__.return_value = response
        response.read.side_effect = TimeoutError()
        opener = MagicMock()
        opener.open.return_value = response
        with patch.object(DIAG.urllib.request, 'build_opener', return_value=opener), patch.object(DIAG, 'request_deadline', contextlib.nullcontext):
            records = DIAG.urllib_probe(DIAG.URLS[0])
            self.assertTrue(records[0]['ok'])
            self.assertEqual(records[-1]['stage'], 'urllib-body')
            self.assertFalse(records[-1]['ok'])

    def test_urllib_open_timeout_is_not_assumed_to_be_dns(self):
        opener = MagicMock()
        opener.open.side_effect = DIAG.urllib.error.URLError(TimeoutError('PRIVATE_PROXY_SECRET'))
        with patch.object(DIAG.urllib.request, 'build_opener', return_value=opener), patch.object(DIAG, 'request_deadline', contextlib.nullcontext):
            records = DIAG.urllib_probe(DIAG.URLS[0])
            self.assertEqual(records[0]['stage'], 'urllib-open-before-headers-not-localized')
            self.assertFalse(records[0]['ok'])
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())

    def test_urllib_redirect_is_not_followed_or_passed(self):
        self.assertIsNone(DIAG.FirstResponseOnly().redirect_request(None, None, 302, '', {}, 'https://law.afna.gov.tw/other'))
        error = DIAG.urllib.error.HTTPError(DIAG.URLS[0], 302, '', {'Location': 'https://user:PRIVATE_PROXY_SECRET@law.afna.gov.tw/private?q=PRIVATE_PROXY_SECRET'}, io.BytesIO())
        opener = MagicMock()
        opener.open.side_effect = error
        with patch.object(DIAG.urllib.request, 'build_opener', return_value=opener), patch.object(DIAG, 'request_deadline', contextlib.nullcontext):
            record = DIAG.urllib_probe(DIAG.URLS[0])[0]
            self.assertEqual(record['httpCode'], 302)
            self.assertFalse(record['ok'])
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())

    def test_deadline_restores_process_handler(self):
        with patch.object(DIAG.signal, 'getsignal', return_value='previous'), patch.object(DIAG.signal, 'signal') as handler, patch.object(DIAG.signal, 'setitimer') as timer:
            with self.assertRaises(TimeoutError):
                with DIAG.request_deadline():
                    handler.call_args.args[1](0, None)
            self.assertEqual(timer.call_args_list[0].args, (DIAG.signal.ITIMER_REAL, 25))
            self.assertEqual(timer.call_args_list[-1].args, (DIAG.signal.ITIMER_REAL, 0))
            self.assertEqual(handler.call_args.args[1], 'previous')

    def test_proxy_values_never_appear_and_request_budget_is_fixed(self):
        dns_ok = {'ok': True, 'addresses': ['210.241.95.231']}
        with patch.object(DIAG.os, 'environ', {'HTTPS_PROXY': 'PRIVATE_PROXY_SECRET'}), patch.object(DIAG.urllib.request, 'getproxies', return_value={'https': 'PRIVATE_PROXY_SECRET'}), patch.object(DIAG.subprocess, 'run', return_value=self.run_result('curl 8 test\n')), patch.object(DIAG, 'dns_probe', return_value=dns_ok) as dns, patch.object(DIAG, 'transport_probe', return_value=[{'ok': True}]) as transport, patch.object(DIAG, 'curl_probe', return_value={'ok': True}) as curl, patch.object(DIAG, 'urllib_probe', return_value=[{'ok': True}]) as urllib:
            self.assertEqual(DIAG.main(), 0)
            self.assertEqual((dns.call_count, transport.call_count, curl.call_count, urllib.call_count), (4, 2, 5, 5))
        self.assertNotIn('PRIVATE_PROXY_SECRET', self.output.getvalue())
        self.assertIn('NOT-a-release-gate', self.output.getvalue())

    def test_any_probe_failure_makes_diagnostic_fail(self):
        with patch.object(DIAG.subprocess, 'run', return_value=self.run_result('curl test\n')), patch.object(DIAG, 'dns_probe', return_value={'ok': True, 'addresses': ['210.241.95.231']}), patch.object(DIAG, 'transport_probe', return_value=[{'ok': True}]), patch.object(DIAG, 'curl_probe', return_value={'ok': False}), patch.object(DIAG, 'urllib_probe', return_value=[{'ok': True}]):
            self.assertEqual(DIAG.main(), 1)
        self.assertIn('unchanged-and-still-unpassed', self.output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
