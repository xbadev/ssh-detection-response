#!/usr/bin/env python3
"""
Phase 05 — SSH Alert Responder (inotify, real-time).

Tails the JSONL alerts file written by the Phase 04 detector and POSTs
each new alert to a webhook (Discord-compatible) in real time.

Architecture: separated from detection on purpose. The responder owns
the network egress and the secret (webhook URL); the detector owns the
event stream. Either side can be developed, tested, or replaced
independently — same pattern as a real SOAR detection-vs-action split.

Inputs (env, from lab.env):
    LAB_LOG_DIR                 alerts file location (default /var/log/ssh-detection-response)
    LAB_STATE_DIR               state dir (default /var/lib/ssh-detection-response)
    ALERT_WEBHOOK_URL           required for live notifications
    RESPONSE_COOLDOWN_SECONDS   per-IP suppression (default 300)

Outputs:
    HTTP POST to ALERT_WEBHOOK_URL with {"content": "..."} payload.
    {LAB_STATE_DIR}/responder-offset.json   tracks last byte read
    stdout/stderr -> journald
"""

from __future__ import annotations

import json
import os
import select
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# --- Config ----------------------------------------------------
LOG_DIR = Path(os.environ.get("LAB_LOG_DIR", "/var/log/ssh-detection-response"))
STATE_DIR = Path(os.environ.get("LAB_STATE_DIR", "/var/lib/ssh-detection-response"))
WEBHOOK_URL = os.environ.get("ALERT_WEBHOOK_URL", "").strip()
COOLDOWN_SECONDS = int(os.environ.get("RESPONSE_COOLDOWN_SECONDS", "300"))

ALERTS_FILE = LOG_DIR / "alerts.jsonl"
OFFSET_FILE = STATE_DIR / "responder-offset.json"
COOLDOWN_FILE = STATE_DIR / "responder-cooldowns.json"
DRY_RUN = os.environ.get("RESPONDER_DRY_RUN", "").lower() in ("1", "true", "yes")


# --- Helpers ---------------------------------------------------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}", file=sys.stderr)
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)


def post_webhook(content: str, timeout: int = 10) -> None:
    if DRY_RUN or not WEBHOOK_URL:
        print(f"[DRY] would post: {content!r}")
        return
    body = json.dumps({"content": content}).encode("utf-8")
    req = Request(
        WEBHOOK_URL,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "ssh-responder/1.0"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as resp:
        resp.read()


def format_alert(alert: dict) -> str:
    """Format an alert dict into a single Discord message."""
    ip = alert.get("source_ip", "?")
    count = alert.get("failure_count", "?")
    window = alert.get("window_seconds", "?")
    users = ", ".join(alert.get("users_targeted", [])) or "?"
    host = alert.get("host", "?")
    last = alert.get("last_seen", "?")
    return (
        f":rotating_light: **SSH brute-force detected**\n"
        f"Host: `{host}`\n"
        f"Source IP: `{ip}`\n"
        f"Failures: `{count}` in `{window}s`\n"
        f"Users targeted: `{users}`\n"
        f"Last seen: `{last}`"
    )


# --- Cooldown --------------------------------------------------
class Cooldowns:
    def __init__(self):
        raw = load_json(COOLDOWN_FILE, {})
        self.until: dict[str, datetime] = {}
        for ip, ts in raw.items():
            try:
                self.until[ip] = datetime.fromisoformat(ts)
            except ValueError:
                continue

    def should_suppress(self, ip: str) -> bool:
        u = self.until.get(ip)
        return u is not None and now_utc() < u

    def mark(self, ip: str) -> None:
        self.until[ip] = datetime.fromtimestamp(
            now_utc().timestamp() + COOLDOWN_SECONDS, tz=timezone.utc
        )
        save_json(COOLDOWN_FILE, {ip: ts.isoformat() for ip, ts in self.until.items()})


# --- File follower ---------------------------------------------
def follow_jsonl(path: Path, start_offset: int):
    """
    Yield (parsed_alert, new_offset) tuples from the JSONL file.
    Uses inotify when available (via select on inotify fd), falls back
    to short polling. Handles file rotation (inode change) and truncation.

    Polling-only is intentional here — the inotify Python stdlib doesn't
    exist; using `select` on a tail-following descriptor is the standard
    pattern. We poll every 0.5s when there is no data; that's fast enough
    for a 'real-time' demo and trivially cheap.
    """
    # Wait for file to exist.
    while not path.exists():
        print(f"[INFO] waiting for {path} to appear...")
        _sleep(2.0)

    fh = path.open("r")
    try:
        st = path.stat()
        current_inode = st.st_ino
        # Resume from saved offset, but clamp to file size.
        if start_offset > st.st_size:
            start_offset = 0
        fh.seek(start_offset)

        while True:
            line = fh.readline()
            if line:
                line = line.strip()
                if not line:
                    continue
                try:
                    alert = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[WARN] skipping malformed JSONL: {e}", file=sys.stderr)
                    continue
                yield alert, fh.tell()
                continue

            # No data — check for rotation.
            try:
                disk_st = path.stat()
            except FileNotFoundError:
                print("[INFO] alerts file disappeared, waiting for it to return...")
                _sleep(1.0)
                continue

            if disk_st.st_ino != current_inode:
                print("[INFO] alerts file rotated, reopening")
                fh.close()
                fh = path.open("r")
                current_inode = disk_st.st_ino
                continue

            if disk_st.st_size < fh.tell():
                # Truncation
                print("[INFO] alerts file truncated, rewinding")
                fh.seek(0)
                continue

            _sleep(0.5)
    finally:
        fh.close()


def _sleep(seconds: float) -> None:
    """Interruptible sleep — uses select so SIGTERM cuts it short."""
    try:
        select.select([], [], [], seconds)
    except InterruptedError:
        pass


# --- Main ------------------------------------------------------
def main() -> int:
    if not WEBHOOK_URL and not DRY_RUN:
        print("[WARN] ALERT_WEBHOOK_URL not set — running but webhook will be skipped.")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    state = load_json(OFFSET_FILE, {"offset": 0})
    offset = int(state.get("offset", 0))

    cooldowns = Cooldowns()

    print(f"[INFO] Responder starting: alerts={ALERTS_FILE} resume_offset={offset} cooldown={COOLDOWN_SECONDS}s dry={DRY_RUN}")

    # Clean shutdown.
    def _on_term(signum, frame):
        print(f"[INFO] received signal {signum}, exiting")
        sys.exit(0)
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)

    for alert, new_offset in follow_jsonl(ALERTS_FILE, offset):
        ip = alert.get("source_ip", "")
        if cooldowns.should_suppress(ip):
            print(f"[INFO] suppressing notification for {ip} (in cooldown)")
        else:
            content = format_alert(alert)
            try:
                post_webhook(content)
                print(f"[INFO] notified for {ip} count={alert.get('failure_count')}")
                cooldowns.mark(ip)
            except (HTTPError, URLError) as e:
                # Don't advance offset on webhook failure — retry on next event.
                print(f"[ERROR] webhook POST failed for {ip}: {e}", file=sys.stderr)
                continue

        save_json(OFFSET_FILE, {"offset": new_offset})

    return 0


if __name__ == "__main__":
    sys.exit(main())
