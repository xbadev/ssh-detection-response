#!/usr/bin/env python3

"""
Script: ssh-bruteforce-detector.py

Purpose:
Detect SSH brute-force attempts by analyzing authentication logs and identifying
repeated failed login attempts within a configurable time window.

High-level behavior:
- Parses an auth.log style file for "Failed password" SSH events
- Extracts timestamp, source IP address, and username
- Groups failed attempts by source IP
- Uses a sliding time window to detect brute-force patterns
- Generates alerts when a configurable threshold is exceeded
- Maintains state to prevent duplicate alerts for the same activity

Key features:
- Time-based detection using a sliding window algorithm
- Configurable threshold, time window, and lookback period
- Deduplication using a persistent JSON state file
- Append-only alert logging for auditability
- Designed for scheduled execution via systemd timer or cron

Inputs:
- SSH authentication log (default: /var/log/auth.log)

Outputs:
- Alert log file documenting detected brute-force sources
- JSON state file tracking last alert per IP for deduplication

Intended use:
This script is designed for detection and monitoring only.
It does not block traffic or modify firewall rules.
Automated response actions are handled in a different script.
"""


import argparse, re, json
from datetime import datetime, timedelta, timezone
from pathlib import Path

FAILED_RE = re.compile(r'^(?P<ts>\S+)\s+\S+\s+sshd\[\d+\]: Failed password for\s+(?P<user>\S+)\s+from\s+(?P<ip>\d+\.\d+\.\d+\.\d+)')


DEFAULT_THRESHOLD = 5 # 5 retries
DEFAULT_WINDOW_SECONDS = 60 # 1 minute
DEFAULT_LOOKBACK_SECONDS = 600  # 10 minutes
DEFAULT_OUTPUT_PATH = Path("output/alerts.log")
DEFAULT_STATE_PATH = Path("output/state.json")

def parse_timestamp(ts: str) -> datetime:
    """ Convert ISO timestamp string into datetime """
    return datetime.fromisoformat(ts)

def parse_failed_attempts(lines):
    """
    parse a auth.log and returns a list of failed attempts.
    each attempt is a dict with timestamp, user, and ip.
    """
    attempts = []

    for line in lines:
        match = FAILED_RE.match(line.strip())

        if not match:
            continue

        attempts.append({
            "timestamp": parse_timestamp(match.group("ts")),
            "ip": match.group("ip"),
            "user": match.group("user")
        })

    return attempts


def detect_bruteforce(attempts, threshold: int, window_seconds: int):
    """
    Detect brute-force attempts.

    Returns a list of alert dictionaries like:
    {
      "ip": "192.168.56.30",
      "count": 6,
      "first_seen": datetime(...),
      "last_seen": datetime(...)
    }
    """

    attempts = sorted(attempts, key=lambda a: a["timestamp"])

    # Group by ip
    attempts_by_ip = {}
    for a in attempts:
        attempts_by_ip.setdefault(a["ip"], []).append(a)

    alerts = []

    # Sliding window per ip
    for ip, ip_attempts in attempts_by_ip.items():
        left = 0
        for right in range(len(ip_attempts)):
            while (ip_attempts[right]["timestamp"] - ip_attempts[left]["timestamp"]).total_seconds() > window_seconds:
                left += 1

            count_in_window = right - left + 1
            if count_in_window >= threshold:
                alerts.append({
                    "ip": ip,
                    "count": count_in_window,
                    "first_seen": ip_attempts[left]["timestamp"],
                    "last_seen": ip_attempts[right]["timestamp"],
                })
                break

    return alerts

def write_alerts(alerts, output_path: Path):
    """
    Append detected alerts to an output log file.
    """
    if not alerts:
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a") as f:
        for alert in alerts:
            f.write(
                f"[ALERT] {alert['ip']} | "
                f"count={alert['count']} | "
                f"from={alert['first_seen']} | "
                f"to={alert['last_seen']}\n"
            )


def load_state(state_path: Path) -> dict:
    """
    Loads JSON state that tracks last alert per IP.
    Format:
      {"ips": {"1.2.3.4": {"last_alert_end": "ISO_TIMESTAMP"}}}
    """
    if not state_path.exists():
        return {"ips": {}}

    try:
        data = json.loads(state_path.read_text())
        if "ips" not in data or not isinstance(data["ips"], dict):
            return {"ips": {}}
        return data
    except Exception:
        # If state file is corrupted or invalid, start fresh
        return {"ips": {}}


def save_state(state_path: Path, state: dict) -> None:
    """
    Writes state safely (temp file then replace).
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(state_path)


def filter_new_alerts(alerts, state: dict):
    """
    Dedup logic:
    For each IP, if we've already alerted up to last_alert_end,
    skip alerts whose last_seen is <= that stored time.
    """
    new_alerts = []
    ips_state = state.setdefault("ips", {})

    for alert in alerts:
        ip = alert["ip"]
        last_seen = alert["last_seen"]

        prev_iso = ips_state.get(ip, {}).get("last_alert_end")
        if prev_iso:
            try:
                prev_dt = datetime.fromisoformat(prev_iso)
                if last_seen <= prev_dt:
                    continue
            except ValueError:
                # if previous timestamp is weird, ignore it
                pass

        new_alerts.append(alert)

    return new_alerts


def update_state_with_alerts(state: dict, alerts) -> None:
    """
    After writing alerts, update state so we don't alert again on the same event.
    """
    ips_state = state.setdefault("ips", {})
    for alert in alerts:
        ip = alert["ip"]
        ips_state.setdefault(ip, {})
        ips_state[ip]["last_alert_end"] = alert["last_seen"].isoformat()



def main():
    parser = argparse.ArgumentParser(description="SSH brute-force detector")
    parser.add_argument("-i", "--input", default="/var/log/auth.log", help="Path to auth.log file. DEFAULT = /var/log/auth.log")
    parser.add_argument("-t", "--threshold", type=int, default=DEFAULT_THRESHOLD, help="Number of failed attempts to trigger alert. DEFAULT = 5")
    parser.add_argument("-w", "--window", type=int, default=DEFAULT_WINDOW_SECONDS, help="Time window in seconds to check for brute-force attempts. DEFAULT = 60")
    parser.add_argument("--lookback", type=int, default=DEFAULT_LOOKBACK_SECONDS, help="Only analyze events from the last N seconds. DEFAULT = 600")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="Where to append alerts. DEFAULT = output/alerts.log")
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH), help="State file (json) used to dedupe alerts. DEFAULT = output/state.json")


    args = parser.parse_args()
    log_path = Path(args.input)

    if not log_path.exists():
        parser.error(f"Input file {log_path} does not exist")

    if args.threshold <= 0:
        parser.error("Threshold must be a positive integer")

    if args.window <= 0:
        parser.error("Window must be a positive integer")

    if args.lookback <= 0:
        parser.error("Lookback must be a positive integer")

    if args.lookback < args.window:
        parser.error("Lookback must be >= window so the detector can see a full window")


    lines = log_path.read_text(errors="replace").splitlines()
    attempts = parse_failed_attempts(lines)

    # Lookback filter (prevents old history from triggering forever)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=args.lookback)
    recent_attempts = [a for a in attempts if a["timestamp"] >= cutoff]

    print(f"[INFO] Parsed {len(attempts)} failed login attempts from {log_path}")
    print(f"[INFO] Lookback={args.lookback}s, analyzing {len(recent_attempts)} attempts since {cutoff.isoformat()}")

    alerts = detect_bruteforce(recent_attempts, args.threshold, args.window)

    output_file = Path(args.output)
    state_file = Path(args.state)

    if not alerts:
        print("[INFO] No brute-force patterns detected.")
    else:
        # Deduplicate using state
        state = load_state(state_file)
        new_alerts = filter_new_alerts(alerts, state)

        if not new_alerts:
            print("[INFO] Brute-force detected but already alerted (deduped by state).")
            return 0

        print(f"[ALERT] Detected {len(new_alerts)} new brute-force source(s):")

        for alert in new_alerts:
            print(
                f"  - IP {alert['ip']} had {alert['count']} failures "
                f"between {alert['first_seen']} and {alert['last_seen']}"
            )

        write_alerts(new_alerts, output_file)
        update_state_with_alerts(state, new_alerts)
        save_state(state_file, state)


    return 0

if __name__ == "__main__":
    exit(main())
