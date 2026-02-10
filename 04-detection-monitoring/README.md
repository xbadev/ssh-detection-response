# Phase 04: Detection & Monitoring

This phase develops **Python-based detection logic** to identify SSH brute-force attacks in real-time by monitoring authentication logs.  
The objective is to implement automated detection capabilities that analyze log patterns, generate security alerts, and maintain persistent state tracking across monitoring sessions.

The detection script runs as a systemd service with timer-based execution, enabling continuous monitoring without manual intervention.

---

## Objective

Implement automated detection and alerting for SSH brute-force attacks through real-time log analysis.

This phase demonstrates:
- Python-based log parsing and pattern matching
- Stateful detection tracking failed authentication attempts
- Automated alert generation for security events
- Systemd service integration for continuous monitoring
- Persistent state management across service restarts

---

## Detection Strategy

The detection system monitors `/var/log/auth.log` for SSH authentication failures and tracks repeated failed attempts from the same source IP.

**Detection Logic:**
- Parse authentication logs for failed SSH login attempts
- Track failed attempt count per source IP
- Generate alerts when threshold is exceeded (3+ failures)
- Maintain persistent state between monitoring runs
- Output alerts to structured log file

**Continuous Monitoring:**
- Systemd service executes detection script periodically
- Timer-based scheduling (every 5 minutes)
- Persistent state tracking across restarts
- Automated alert generation without manual intervention

---

## Implementation

### Detection Script

The core detection logic is implemented in Python and monitors authentication logs for brute-force patterns.

**Script:** [`detector/ssh-bruteforce-detector.py`](detector/ssh-bruteforce-detector.py)

**Key Functionality:**
- Parses `/var/log/auth.log` for failed SSH authentication attempts
- Extracts source IP addresses from failed login entries
- Tracks failure count per IP using persistent state file
- Generates alerts when IP exceeds threshold (3 failures)
- Outputs alerts to `alerts.log` with timestamp and IP details

---

### Sample Logs for Testing

Sample authentication logs are provided to demonstrate detection logic during development and testing.

**Sample Log:** [`logs/sample-auth.log`](logs/sample-auth.log)

This log contains realistic SSH authentication failure patterns for script validation.

📂 **[Logs Documentation](logs/)** - See logs folder README for testing workflow details

---

### Detection Output

The detection script generates two types of output files:

**Alert Log:** `output/alerts.log`  
Records all detected brute-force attempts with timestamp and source IP information.

**State File:** `output/state.json`  
Maintains persistent tracking of failed attempt counts per IP across script executions.

📂 **[Output Documentation](output/)** - See output folder README for file format details and gitignore rationale

---

### Systemd Service Integration

The detection script runs continuously via systemd service and timer units, enabling automated monitoring without manual execution.

**Service Unit:** [`systemd/ssh-bruteforce-detector.service`](systemd/ssh-bruteforce-detector.service)  
Defines how the detection script executes (user, working directory, execution command)

**Timer Unit:** [`systemd/ssh-bruteforce-detector.timer`](systemd/ssh-bruteforce-detector.timer)  
Schedules periodic execution (every 5 minutes)

**Why Service + Timer:**
- **Service** defines *what* to run and *how* to run it
- **Timer** defines *when* to run it (scheduling)
- Together they enable continuous, automated monitoring
- Script runs periodically without manual intervention
- System automatically restarts monitoring after reboot

This architecture enables **Phase 05 (Automated Response)** to trigger defensive actions based on detection alerts.

---

## Validation

Detection capabilities were validated through controlled testing:

✅ **Script parses logs correctly** - Extracts failed SSH attempts from auth.log  
✅ **State tracking persists** - Failure counts maintained across script runs  
✅ **Alerts generated accurately** - Threshold-based alerting functions as designed  
✅ **Systemd integration works** - Service executes on schedule via timer  
✅ **Detection observes real attacks** - Captures brute-force attempts from Phase 02  

**Validation Evidence:**

- 📸 [Python Detection Dry Run](screenshots/00-python-detection-dry-run.png) - Initial script testing against sample logs
- 📸 [Kali Hydra Attack](screenshots/01-kali-hydra-attack.png) - Live attack traffic for detection validation
- 📸 [Ubuntu Auth Log Failures](screenshots/02-ubuntu-authlog-failures.png) - Authentication log showing detected failures
- 📸 [Manual Test and Deduplication Check](screenshots/03-manual-test-and-dedup-check.png) - Verification of state persistence and deduplication logic

---

## Design Rationale

This detection system was designed to:

- **Enable automated monitoring** - Continuous log analysis without manual oversight
- **Maintain persistent state** - Track attack patterns across monitoring intervals
- **Generate actionable alerts** - Provide structured output for response automation
- **Integrate with systemd** - Leverage native Linux service management
- **Support response automation** - Provide foundation for Phase 05 automated blocking

By implementing detection as a systemd service, the monitoring infrastructure runs continuously and survives system restarts, providing reliable security event visibility.

---

## Outcome

At the conclusion of this phase:

- Automated detection script monitors SSH authentication logs continuously
- Failed login attempts are tracked and alerted based on threshold rules
- Systemd integration ensures persistent monitoring across reboots
- Alert output is structured and ready for automated response integration

This detection foundation enables Phase 05 (Automated Response) to implement defensive actions triggered by detection alerts.

---

## Documentation Structure

```
04-detection-monitoring/
├── README.md                                      # This document
├── detector/
│   └── ssh-bruteforce-detector.py                # Detection script
├── logs/
│   ├── README.md                                  # Testing workflow documentation
│   ├── sample-auth.log                            # Sample logs for testing
│   ├── 00-dry-run-detection.txt                   # Initial test run output
│   ├── 01-detector-first-run.txt                  # First live detection output
│   ├── 02-detector-second-run.txt                 # Second run showing persistence
│   └── 03-systemd-journal-snippet.txt             # Systemd execution logs
├── output/
│   ├── README.md                                  # Output files documentation
│   └── .gitignore                                 # Excludes state.json and alerts.log
├── systemd/
│   ├── ssh-bruteforce-detector.service           # Systemd service unit
│   └── ssh-bruteforce-detector.timer             # Systemd timer unit
└── screenshots/
    ├── 00-python-detection-dry-run.png
    ├── 01-kali-hydra-attack.png
    ├── 02-ubuntu-authlog-failures.png
    └── 03-manual-test-and-dedup-check.png
```

---

## Next Phase

**→ [Phase 05: Automated Response](../05-automated-response/)**

With detection capabilities in place, the next phase implements automated response actions that execute when brute-force attacks are detected, closing the security automation loop.
