# Detection Testing and Logs

This directory contains sample authentication logs and test execution output documenting the development and validation of the SSH brute-force detection script.

The files capture the iterative testing workflow used to validate detection logic before deploying as a systemd service.

---

## Testing Workflow

The detection script was validated through a staged testing approach:

### Stage 0: Dry Run Testing
Initial script development and testing against sample logs in a controlled environment.

### Stage 1: First Live Detection
First execution against real authentication logs from Phase 02 attack traffic.

### Stage 2: State Persistence Validation
Second execution to verify state tracking and deduplication logic across runs.

### Stage 3: Systemd Integration
Verification of script execution via systemd service and timer units.

---

## Log Files

### `sample-auth.log`

**Purpose:** Sample authentication log file containing realistic SSH brute-force patterns for development testing.

**Contents:**
- Failed SSH authentication attempts from multiple source IPs
- Realistic auth.log format from actual Ubuntu system logs
- Multiple attack patterns for threshold testing

**Usage:**
- Used during dry-run testing with `--input` flag
- Enables script development without requiring live attack traffic
- Provides repeatable test data for validation

---

### `00-dry-run-detection.txt`

**Purpose:** Output from initial dry-run testing against sample logs.

**Command:**
```bash
python3 detector/ssh-bruteforce-detector.py --input logs/sample-auth.log -t 3 -w 20
```

**Key Observations:**
- Script successfully parsed 10 failed login attempts from sample log
- Detected 2 brute-force sources exceeding threshold (3 failures)
- Alert format and output validated
- Notes on threshold tuning and window sensitivity

**Validation:**
- ✅ Log parsing works correctly
- ✅ Threshold detection functions as designed
- ✅ Alert generation produces expected output

---

### `01-detector-first-run.txt`

**Purpose:** First execution against real authentication logs from Phase 02 attack.

**Execution Context:**
- Ran against `/var/log/auth.log` containing live Hydra attack traffic
- Lookback window: 600 seconds
- Analyzed 14 failed login attempts

**Key Observations:**
- Detected 1 new brute-force source (192.168.56.30 - Kali attacker)
- 5 failures detected within attack window
- Alert generated with correct timestamp range

**Validation:**
- ✅ Script processes real auth.log format correctly
- ✅ Detects actual attack traffic from Phase 02
- ✅ State file created for tracking

---

### `02-detector-second-run.txt`

**Purpose:** Second execution to validate state persistence and deduplication.

**Execution Context:**
- Ran against same `/var/log/auth.log` as first run
- Same lookback window (600 seconds)
- Same 14 failed attempts analyzed

**Key Observations:**
- Script detected brute-force pattern again
- **Deduplication worked:** "Brute-force detected but already alerted (deduped by state)"
- No duplicate alert generated
- State tracking prevents alert spam

**Validation:**
- ✅ State persistence works across executions
- ✅ Deduplication logic functions correctly
- ✅ No duplicate alerts for same attack window

---

### `03-systemd-journal-snippet.txt`

**Purpose:** Systemd journal output showing script execution via service and timer units.

**Execution Context:**
- Detection script running as systemd service
- Timer triggering execution every minute (for testing)
- Journal logs captured via `journalctl`

**Key Observations:**
- Timer triggers service execution successfully
- Script runs with correct permissions and environment
- Detection logic executes and produces expected output
- Deduplication continues to work in systemd context

**Validation:**
- ✅ Systemd service configuration correct
- ✅ Timer scheduling functions as designed
- ✅ Script executes reliably via systemd
- ✅ State persists across service-managed runs

**Sample Output:**
- Shows service start messages
- Displays detection script INFO and ALERT logs
- Confirms automated execution without manual intervention

---

## Testing Progression Summary

```
00-dry-run          → Validates logic against sample data
01-first-run        → Detects real attack from Phase 02
02-second-run       → Confirms state persistence and deduplication
03-systemd-journal  → Proves automated execution via systemd
```

This staged approach ensures the detection script is thoroughly validated before continuous deployment in Phase 05.

---

## Relationship to `sample-auth.log`

The `sample-auth.log` file contains the authentication log entries used during dry-run testing. These logs are referenced in the root phase README as demonstration data showing what SSH brute-force patterns look like in `/var/log/auth.log`.

By maintaining both sample logs and test output, the testing methodology is fully documented and reproducible.
