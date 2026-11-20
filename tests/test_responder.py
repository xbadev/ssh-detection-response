"""Tests for the Phase 05 responder: formatting, retry, and an end-to-end run
against a local fake webhook server."""

import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from _load import RESPONDER, load

ALERT = {
    "timestamp": "2026-01-01T12:00:00+00:00",
    "source_ip": "10.10.10.30",
    "failure_count": 3,
    "window_seconds": 60,
    "first_seen": "2026-01-01T11:59:58+00:00",
    "last_seen": "2026-01-01T12:00:00+00:00",
    "users_targeted": ["bader"],
    "host": "ubuntu-target",
}


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def mod(self, **env):
        base = {"LAB_STATE_DIR": self.tmp.name, "LAB_LOG_DIR": self.tmp.name}
        base.update(env)
        return load(RESPONDER, "responder_unit", base)

    def test_format_alert_contains_key_fields(self):
        r = self.mod(ALERT_WEBHOOK_URL="http://example.invalid")
        text = r.format_alert(ALERT)
        for needle in ("10.10.10.30", "bader", "ubuntu-target", "`3`"):
            self.assertIn(needle, text)

    def test_placeholder_url_counts_as_unset(self):
        r = self.mod(ALERT_WEBHOOK_URL="https://discord.com/api/webhooks/REPLACE_ME")
        self.assertEqual(r.WEBHOOK_URL, "")

    def test_deliver_retries_then_succeeds(self):
        r = self.mod(ALERT_WEBHOOK_URL="http://example.invalid", RESPONSE_WEBHOOK_RETRIES=3)
        calls = []

        def flaky(_content):
            calls.append(1)
            if len(calls) < 3:
                raise OSError("connection refused")

        r.post_webhook = flaky
        r._sleep = lambda _s: None
        self.assertTrue(r.deliver(ALERT))
        self.assertEqual(len(calls), 3)

    def test_deliver_gives_up_after_retries(self):
        r = self.mod(ALERT_WEBHOOK_URL="http://example.invalid", RESPONSE_WEBHOOK_RETRIES=2)
        calls = []

        def down(_content):
            calls.append(1)
            raise OSError("timed out")

        r.post_webhook = down
        r._sleep = lambda _s: None
        self.assertFalse(r.deliver(ALERT))
        self.assertEqual(len(calls), 2)


class _Recorder(http.server.BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        type(self).received.append(json.loads(body))
        self.send_response(204)
        self.end_headers()

    def log_message(self, *_):
        pass


class EndToEndTests(unittest.TestCase):
    """Run the real responder process against a fake webhook server."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        _Recorder.received = []
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        self.server = http.server.HTTPServer(("127.0.0.1", port), _Recorder)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.env = {
            **os.environ,
            "LAB_LOG_DIR": self.tmp.name,
            "LAB_STATE_DIR": self.tmp.name,
            "ALERT_WEBHOOK_URL": f"http://127.0.0.1:{port}",
            "RESPONSE_COOLDOWN_SECONDS": "300",
        }
        self.alerts = Path(self.tmp.name) / "alerts.jsonl"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def run_responder(self, lines, settle=2.5):
        proc = subprocess.Popen([sys.executable, str(RESPONDER)], env=self.env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            time.sleep(1.0)
            with self.alerts.open("a") as f:
                for line in lines:
                    f.write(json.dumps(line) + "\n")
                    f.flush()
                    time.sleep(0.6)
            time.sleep(settle)
        finally:
            proc.terminate()
            out, _ = proc.communicate(timeout=5)
        return out

    def test_posts_alerts_and_respects_cooldown(self):
        other = {**ALERT, "source_ip": "10.10.10.99"}
        repeat = {**ALERT}  # same IP as the first -> suppressed by cooldown
        out = self.run_responder([ALERT, other, repeat])
        posted = [r["content"] for r in _Recorder.received]
        self.assertEqual(len(posted), 2, msg=out)
        self.assertIn("10.10.10.30", posted[0])
        self.assertIn("10.10.10.99", posted[1])
        self.assertIn("suppressing notification for 10.10.10.30", out)

    def test_offset_persisted_so_restart_does_not_resend(self):
        self.run_responder([ALERT])
        self.assertEqual(len(_Recorder.received), 1)
        offset = json.loads((Path(self.tmp.name) / "responder-offset.json").read_text())
        self.assertEqual(offset["offset"], self.alerts.stat().st_size)
        # Second run with no new alerts must not re-post the old one.
        self.run_responder([], settle=1.5)
        self.assertEqual(len(_Recorder.received), 1)


if __name__ == "__main__":
    unittest.main()
