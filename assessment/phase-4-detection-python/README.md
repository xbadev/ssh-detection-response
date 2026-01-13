# Phase 4: Detection (Python) - SSH Brute-Force Detector + systemd Timer

This phase builds a lightweight blue-team detector that monitors SSH authentication failures on the Ubuntu server and alerts when a brute-force pattern is detected. The detector runs automatically every minute using a `systemd` service + timer, and it avoids repeating the same alert over and over by tracking state.

## Goal

- Parse `/var/log/auth.log` for SSH failures (`Failed password`)
- Detect brute-force behavior using a threshold + time window
- Write alerts to a log file
- Run automatically every minute using `systemd`
- Prevent duplicate alerts across repeated runs (stateful dedupe)
- Keep GitHub clean (runtime output ignored, but evidence preserved in `logs/` and `screenshots/`)

## What We Built

### 1) Python detector script
Location:
- `detector/ssh-bruteforce-detector.py`

What it does:
- Reads an auth.log style file (default: `/var/log/auth.log`)
- Extracts failed SSH attempts with timestamp, username, and source IP
- Detects brute-force per IP using a sliding time window
- Filters analysis to only the last `N` seconds (lookback)
- Deduplicates alerts using a JSON state file (per-IP last alert timestamp)
- Appends new alerts to an output file

Key flags (all have defaults):
- `--input` (default: `/var/log/auth.log`)
- `--threshold` (default: 5)
- `--window` (default: 60 seconds)
- `--lookback` (default: 600 seconds)
- `--output` (default: `output/alerts.log`)
- `--state` (default: `output/state.json`)

### 2) systemd service + timer (automation)
Location:
- `systemd/ssh-bruteforce-detector.service`
- `systemd/ssh-bruteforce-detector.timer`

What it does:
- Runs the detector every minute
- Uses `WorkingDirectory=.../phase-4-detection-python` so relative paths like `output/alerts.log` work correctly

Important fix we made:
- The timer was running but output was not being written because the script was being executed from a different working directory. Adding `WorkingDirectory` to the `.service` fixed this.

### 3) Output + evidence handling
Folders:
- `output/` = runtime output directory (ignored by git)
- `logs/` = saved evidence files + sample logs (tracked in git)
- `screenshots/` = screenshots of detection and automation proof

We ignore live runtime files:
- `output/alerts.log`
- `output/state.json`

These are generated on the VM and change constantly, so they should not be committed. Instead, we store proof outputs in `logs/` and screenshots.

## Folder Structure
phase-4-detection-python/
├── detector/
│ ├── ssh-bruteforce-detector.py
│ └── notes.md
├── logs/
│ ├── sample-auth.log
│ ├── 01-detector-first-run.txt
│ ├── 02-detector-second-run-dedup.txt
│ └── 03-systemd-journal-snippet.txt
├── output/
│ ├── .gitignore
│ └── .keep
├── screenshots/
│ └── python-detection-dry-run.png
└── systemd/
├── ssh-bruteforce-detector.service
└── ssh-bruteforce-detector.timer

## How Detection Works

### Pattern matching
The script detects lines like:
- `Failed password for <user> from <ip> ...`

It extracts:
- timestamp
- username
- source IP

### Brute-force logic
For each IP:
- Sort attempts by time
- Use a sliding window of `--window` seconds
- Trigger an alert if `count >= --threshold`

### Lookback filter
To prevent old history from causing constant alerts, the detector only analyzes attempts within the last:
- `--lookback` seconds

Default:
- 600 seconds (10 minutes)

### State-based dedupe (no repeated alerts)
To avoid alerting the same brute-force event every minute, the script writes a state file:
- `output/state.json`

It stores:
- per IP: `last_alert_end`

If a future run sees the same IP but the latest event timestamp is not newer than what we already alerted, it prints:
- “already alerted (deduped by state)”  
and does not write a new alert.

## How To Run Manually

From inside `phase-4-detection-python/`:

Run against the live server log:
python3 detector/ssh-bruteforce-detector.py

Run against the sample log:
python3 detector/ssh-bruteforce-detector.py --input logs/sample-auth.log --threshold 3 --window 20 --lookback 600

Check the output:
cat output/alerts.log
cat output/state.json

systemd Automation
Install service + timer (on the Ubuntu server)

Copy the unit files into:
/etc/systemd/system/

Then reload + enable:
sudo systemctl daemon-reload
sudo systemctl enable --now ssh-bruteforce-detector.timer

Verify:
sudo systemctl status ssh-bruteforce-detector.timer
systemctl list-timers | grep brute

View logs:
journalctl -u ssh-bruteforce-detector.service --no-pager

Evidence (Proof This Works)
Saved run outputs: logs/01-*.txt, logs/02-*.txt
systemd proof: logs/03-systemd-journal-snippet.txt
screenshots: screenshots/
