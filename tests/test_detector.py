"""Unit tests for the Phase 04 detector: log parsing and sliding-window logic."""

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from _load import DETECTOR, load

T0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def at(seconds: float) -> datetime:
    return T0 + timedelta(seconds=seconds)


class ParseFailureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = load(DETECTOR, "detector_parse", {
            "LAB_STATE_DIR": cls.tmp.name, "LAB_LOG_DIR": cls.tmp.name,
        })

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_failed_password_valid_user(self):
        msg = "Failed password for bader from 10.10.10.30 port 51234 ssh2"
        self.assertEqual(self.d.parse_failure(msg), ("10.10.10.30", "bader"))

    def test_failed_password_invalid_user(self):
        msg = "Failed password for invalid user admin from 10.10.10.30 port 40000 ssh2"
        self.assertEqual(self.d.parse_failure(msg), ("10.10.10.30", "admin"))

    def test_invalid_user_line_is_ignored(self):
        # sshd writes this IN ADDITION to the "Failed password ... invalid user"
        # line for the same attempt. Counting it would double-count.
        msg = "Invalid user admin from 10.10.10.30 port 40000"
        self.assertIsNone(self.d.parse_failure(msg))

    def test_successful_login_is_ignored(self):
        msg = "Accepted password for bader from 10.10.10.1 port 50000 ssh2"
        self.assertIsNone(self.d.parse_failure(msg))

    def test_ipv6_source(self):
        msg = "Failed password for bader from fe80::1 port 22222 ssh2"
        self.assertEqual(self.d.parse_failure(msg), ("fe80::1", "bader"))


class SlidingDetectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = load(DETECTOR, "detector_window", {
            "LAB_STATE_DIR": self.tmp.name, "LAB_LOG_DIR": self.tmp.name,
            "DETECT_WINDOW_SECONDS": 60,
        })

    def tearDown(self):
        self.tmp.cleanup()

    def new(self, threshold=3):
        return self.d.SlidingDetector(threshold=threshold, window_s=60, retention_s=600)

    def test_below_threshold_no_alert(self):
        det = self.new()
        self.assertIsNone(det.record_failure("10.10.10.30", "bader", at(0)))
        self.assertIsNone(det.record_failure("10.10.10.30", "bader", at(5)))

    def test_alert_at_threshold(self):
        det = self.new()
        det.record_failure("10.10.10.30", "bader", at(0))
        det.record_failure("10.10.10.30", "bader", at(5))
        alert = det.record_failure("10.10.10.30", "bader", at(10))
        self.assertIsNotNone(alert)
        self.assertEqual(alert["source_ip"], "10.10.10.30")
        self.assertEqual(alert["failure_count"], 3)
        self.assertEqual(alert["users_targeted"], ["bader"])

    def test_cooldown_suppresses_repeat_alert(self):
        det = self.new()
        for s in (0, 1, 2):
            det.record_failure("10.10.10.30", "bader", at(s))
        self.assertIsNone(det.record_failure("10.10.10.30", "bader", at(3)))
        self.assertIsNone(det.record_failure("10.10.10.30", "bader", at(30)))

    def test_alerts_again_after_cooldown(self):
        det = self.new()
        for s in (0, 1, 2):
            det.record_failure("10.10.10.30", "bader", at(s))
        # Cooldown = window = 60s after the alert at t=2.
        for s in (70, 71):
            self.assertIsNone(det.record_failure("10.10.10.30", "bader", at(s)))
        self.assertIsNotNone(det.record_failure("10.10.10.30", "bader", at(72)))

    def test_ips_are_tracked_independently(self):
        det = self.new()
        det.record_failure("10.10.10.30", "bader", at(0))
        det.record_failure("10.10.10.30", "bader", at(1))
        for s in (2, 3):
            self.assertIsNone(det.record_failure("10.10.10.99", "bader", at(s)))
        self.assertIsNotNone(det.record_failure("10.10.10.99", "bader", at(4)))

    def test_slow_attack_outside_window_no_alert(self):
        det = self.new()
        for i in range(5):
            self.assertIsNone(det.record_failure("10.10.10.50", "bob", at(i * 120)))

    def test_cooldown_survives_restart(self):
        det = self.new()
        for s in (0, 1, 2):
            det.record_failure("10.10.10.30", "bader", at(s))
        saved = json.loads((Path(self.tmp.name) / "detector-cooldowns.json").read_text())
        self.assertIn("10.10.10.30", saved)
        # Fresh instance (simulated service restart) is still in cooldown.
        det2 = self.new()
        for s in (5, 6, 7):
            self.assertIsNone(det2.record_failure("10.10.10.30", "bader", at(s)))


class EndToEndParsingTests(unittest.TestCase):
    """Real sshd message sequences through parse_failure + SlidingDetector."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = load(DETECTOR, "detector_e2e", {
            "LAB_STATE_DIR": self.tmp.name, "LAB_LOG_DIR": self.tmp.name,
        })

    def tearDown(self):
        self.tmp.cleanup()

    def feed(self, det, messages):
        alerts = []
        for i, msg in enumerate(messages):
            parsed = self.d.parse_failure(msg)
            if parsed:
                a = det.record_failure(parsed[0], parsed[1], at(i))
                if a:
                    alerts.append(a)
        return alerts

    def test_two_invalid_user_attempts_count_as_two_not_four(self):
        # Regression: 2 attempts used to produce 4 counted failures.
        det = self.d.SlidingDetector(threshold=3, window_s=60, retention_s=600)
        msgs = [
            "Invalid user admin from 10.10.10.30 port 40000",
            "Failed password for invalid user admin from 10.10.10.30 port 40000 ssh2",
            "Invalid user root from 10.10.10.30 port 40001",
            "Failed password for invalid user root from 10.10.10.30 port 40001 ssh2",
        ]
        self.assertEqual(self.feed(det, msgs), [])

    def test_demo_wordlist_trips_detector_once(self):
        # run-attack.sh sends 6 passwords; threshold 3 -> exactly one alert
        # (attempts 4-6 fall inside the cooldown).
        det = self.d.SlidingDetector(threshold=3, window_s=60, retention_s=600)
        msgs = [f"Failed password for bader from 10.10.10.30 port {50000 + i} ssh2"
                for i in range(6)]
        alerts = self.feed(det, msgs)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["failure_count"], 3)


if __name__ == "__main__":
    unittest.main()
