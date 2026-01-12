#! usr/bin/env python3

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
    return 0

if __name__ == "__main__":
    exit(main())
