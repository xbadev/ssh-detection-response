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


