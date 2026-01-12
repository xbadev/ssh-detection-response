## Phase 4.2.1 – SSH Log Parsing (Detection Foundation)

### Objective
Extract failed SSH authentication attempts from an auth.log-style file using Python.

This step validates that:
- Authentication logs are readable programmatically
- Failed login attempts can be reliably identified
- Key fields (timestamp, IP, user) can be extracted for detection logic

### Log Source
Ubuntu authentication log format (`/var/log/auth.log`).

Example log entry:
2026-01-08T01:32:23.181726+00:00 ubuntuserver1 sshd[969]: Failed password for bader from 192.168.56.30 port 38562 ssh2

### Fields Extracted
- Timestamp (ISO format)
- Source IP address
- Username attempted

### Detection Method
- Regular expression matching on `"Failed password"` SSH events
- Non-matching lines are ignored
- Matching entries are parsed into structured Python dictionaries

### Validation
The detector was tested against a real sample authentication log file:

Command:
python3 detector/ssh-bruteforce-detector.py --input logs/sample-auth.log

Result:
[INFO] Parsed 10 failed login attempts from logs/sample-auth.log

This confirms the parser correctly identifies real failed SSH attempts from prior attack activity.
