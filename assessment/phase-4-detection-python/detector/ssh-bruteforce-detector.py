#!/usr/bin/env python3

"""
SSH brute-force detector

- Reads an auth.log style file
- Find "Failed password" attempts
- Extracts timestamp, IP, and user
"""

import argparse, re
from datetime import datetime
from pathlib import Path

FAILED_RE = re.compile(r'^(?P<ts>\S+)\s+\S+\s+sshd\[\d+\]: Failed password for\s+(?P<user>\S+)\s+from\s+(?P<ip>\d+.\d+.\d+.\d+)')


DEFAULT_THRESHOLD = 5
DEFAULT_WINDOW_SECONDS = 60

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


def main():
    parser = argparse.ArgumentParser(description="SSH brute-force detector")
    parser.add_argument("-i", "--input", default="/var/log/auth.log", help="Path to auth.log file")
    parser.add_argument("-t", "--threshold", type=int, default=DEFAULT_THRESHOLD, help="Number of failed attempts to trigger alert")
    parser.add_argument("-w", "--window", type=int, default=DEFAULT_WINDOW_SECONDS, help="Time window in seconds to check for brute-force attempts")

    args = parser.parse_args()
    log_path = Path(args.input)

    if not log_path.exists():
        parser.error(f"Input file {log_path} does not exist")

    if args.threshold <= 0:
        parser.error("Threshold must be a positive integer")

    if args.window <= 0:
        parser.error("Window must be a positive integer")

    lines = log_path.read_text(errors="replace").splitlines()
    attempts = parse_failed_attempts(lines)

    print(f"[INFO] Parsed {len(attempts)} failed login attempts from {log_path}")

    alerts = detect_bruteforce(attempts, args.threshold, args.window)

    if not alerts:
        print("[INFO] No brute-force patterns detected.")

    else:
        print(f"[ALERT] Detected {len(alerts)} brute-force source(s):")

    for alert in alerts:
        print(
            f"  - IP {alert['ip']} had {alert['count']} failures "
            f"between {alert['first_seen']} and {alert['last_seen']}"
        )


    return 0

if __name__ == "__main__":
    exit(main())
