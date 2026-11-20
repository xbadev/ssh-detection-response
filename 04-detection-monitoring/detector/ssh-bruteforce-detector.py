#!/usr/bin/env python3
"""
Phase 04 — SSH Brute-Force Detector (journald, real-time).

Follows the systemd journal for sshd, parses authentication failures
in real time, and emits structured alerts to a JSONL file when a
source IP exceeds the configured failure threshold within a sliding
time window.

Architecture choice: this daemon is intentionally narrow. It detects
and emits — it does NOT block IPs or send notifications. Response is
handled by Phase 05, which tails the JSONL output. Separating detection
from response mirrors how real SOAR platforms are built and lets either
side be developed, tested, or scaled independently.

Configuration is read from lab.env (sourced by the systemd unit) via
environment variables. See lab.env.example at the repo root.

Inputs (env):
    DETECT_THRESHOLD            int, default 5
    DETECT_WINDOW_SECONDS       int, default 60
    DETECT_RETENTION_SECONDS    int, default 600
    LAB_LOG_DIR                 str, default /var/log/ssh-detection-response
    LAB_STATE_DIR               str, default /var/lib/ssh-detection-response

Outputs:
    {LAB_LOG_DIR}/alerts.jsonl   one JSON object per detected event
    stdout/stderr                progress + warnings (captured by journald)
"""

from __future__ import annotations

import json
import os
import re
import signal
import socket
import subprocess
import sys
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

# --- Config from environment -----------------------------------

THRESHOLD = int(os.environ.get("DETECT_THRESHOLD", "5"))
WINDOW_SECONDS = int(os.environ.get("DETECT_WINDOW_SECONDS", "60"))
RETENTION_SECONDS = int(os.environ.get("DETECT_RETENTION_SECONDS", "600"))
LOG_DIR = Path(os.environ.get("LAB_LOG_DIR", "/var/log/ssh-detection-response"))
STATE_DIR = Path(os.environ.get("LAB_STATE_DIR", "/var/lib/ssh-detection-response"))

ALERTS_FILE = LOG_DIR / "alerts.jsonl"
COOLDOWN_FILE = STATE_DIR / "detector-cooldowns.json"

# Suppress repeat alerts for the same IP for this many seconds after firing.
# Prevents one sustained attack from generating one alert per second.
ALERT_COOLDOWN_SECONDS = WINDOW_SECONDS

# --- Patterns --------------------------------------------------
# journalctl -o json gives us the MESSAGE field. Exactly ONE line per failed
# password attempt is counted: "Failed password for [invalid user ]X from IP".
#
# sshd also logs "Invalid user X from IP" for nonexistent accounts, but that
# line is written IN ADDITION to the "Failed password ... invalid user ..."
# line for the same attempt. Matching both would count one attempt twice,
# so "Invalid user" lines are deliberately ignored.
#
# The IP group accepts IPv4 and IPv6 literals.
FAILED_PATTERNS = [
    re.compile(
        r"Failed password for (?:invalid user )?(?P<user>\S+) "
        r"from (?P<ip>[0-9A-Fa-f:.]+) port \d+"
    ),
]


def parse_failure(message: str):
    for pat in FAILED_PATTERNS:
        m = pat.search(message)
        if m:
            return m.group("ip"), m.group("user")
    return None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# --- State management ------------------------------------------
# Per-IP deque of (timestamp, user) tuples within the retention window.
# Old entries are evicted lazily as new ones arrive.
class SlidingDetector:
    def __init__(self, threshold: int, window_s: int, retention_s: int):
        self.threshold = threshold
        self.window_s = window_s
        self.retention_s = retention_s
        self.events: dict[str, deque] = defaultdict(deque)
        self.cooldowns: dict[str, datetime] = self._load_cooldowns()

    def _load_cooldowns(self) -> dict[str, datetime]:
        if not COOLDOWN_FILE.exists():
            return {}
        try:
            data = json.loads(COOLDOWN_FILE.read_text())
            return {ip: datetime.fromisoformat(ts) for ip, ts in data.items()}
        except Exception as e:
            print(f"[WARN] Could not load cooldowns: {e}", file=sys.stderr)
            return {}

    def _save_cooldowns(self) -> None:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = COOLDOWN_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps({ip: ts.isoformat() for ip, ts in self.cooldowns.items()}))
        tmp.replace(COOLDOWN_FILE)

    def record_failure(self, ip: str, user: str, ts: datetime):
        # Evict events outside retention window.
        bucket = self.events[ip]
        cutoff_retention = ts.timestamp() - self.retention_s
        while bucket and bucket[0][0].timestamp() < cutoff_retention:
            bucket.popleft()
        bucket.append((ts, user))

        # Check cooldown — suppress if we already alerted recently.
        cooldown_until = self.cooldowns.get(ip)
        if cooldown_until and ts < cooldown_until:
            return None

        # Count events within the detection window.
        cutoff_window = ts.timestamp() - self.window_s
        in_window = [(t, u) for (t, u) in bucket if t.timestamp() >= cutoff_window]
        if len(in_window) >= self.threshold:
            users = sorted({u for (_, u) in in_window})
            alert = {
                "timestamp": ts.isoformat(),
                "source_ip": ip,
                "failure_count": len(in_window),
                "window_seconds": self.window_s,
                "first_seen": in_window[0][0].isoformat(),
                "last_seen": in_window[-1][0].isoformat(),
                "users_targeted": users,
                "host": socket.gethostname(),
            }
            self.cooldowns[ip] = datetime.fromtimestamp(ts.timestamp() + ALERT_COOLDOWN_SECONDS, tz=timezone.utc)
            self._save_cooldowns()
            return alert
        return None


# --- Alert sink ------------------------------------------------
def emit_alert(alert: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = json.dumps(alert, separators=(",", ":")) + "\n"
    # Open/close per write. Slower than a held handle, but safer
    # against log rotation and crash recovery.
    with ALERTS_FILE.open("a") as f:
        f.write(line)
        f.flush()
        os.fsync(f.fileno())
    print(f"[ALERT] {alert['source_ip']} count={alert['failure_count']} users={alert['users_targeted']}")


# --- journald follower -----------------------------------------
def follow_journal():
    """
    Yield parsed events from `journalctl -u ssh -f -o json`.
    Each yielded item is (datetime, message_string).
    """
    cmd = [
        "journalctl",
        "-u", "ssh.service",
        "-u", "sshd.service",     # both unit names exist depending on distro
        "-o", "json",
        "-f",                      # follow
        "--no-pager",
        "-n", "0",                 # start from now, ignore history on restart
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Forward signals to child so systemd stop is clean.
    def _handle_sig(signum, frame):
        proc.terminate()
        sys.exit(0)
    signal.signal(signal.SIGTERM, _handle_sig)
    signal.signal(signal.SIGINT, _handle_sig)

    if proc.stdout is None:
        raise RuntimeError("journalctl produced no stdout")

    for raw in proc.stdout:
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        message = entry.get("MESSAGE", "")
        if not message:
            continue
        # journald gives us __REALTIME_TIMESTAMP in microseconds since epoch.
        ts_raw = entry.get("__REALTIME_TIMESTAMP")
        if ts_raw:
            try:
                ts = datetime.fromtimestamp(int(ts_raw) / 1_000_000, tz=timezone.utc)
            except (ValueError, TypeError):
                ts = now_utc()
        else:
            ts = now_utc()
        yield ts, message


# --- Main loop -------------------------------------------------
def main() -> int:
    print(f"[INFO] Detector starting: threshold={THRESHOLD} window={WINDOW_SECONDS}s retention={RETENTION_SECONDS}s")
    print(f"[INFO] Alerts file: {ALERTS_FILE}")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    detector = SlidingDetector(THRESHOLD, WINDOW_SECONDS, RETENTION_SECONDS)

    for ts, message in follow_journal():
        parsed = parse_failure(message)
        if not parsed:
            continue
        ip, user = parsed
        alert = detector.record_failure(ip, user, ts)
        if alert:
            emit_alert(alert)

    return 0


if __name__ == "__main__":
    sys.exit(main())
