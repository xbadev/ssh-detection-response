# Phase 5 – Response Automation (Alerting)

## Overview

Phase 5 adds **automated incident response** to the SSH brute-force detection pipeline built in Phase 4.

At this stage, the system no longer only *detects* suspicious activity — it **reacts automatically** by delivering real-time alerts to an external communication platform (Discord) using a secure webhook mechanism.

This phase demonstrates how detection systems integrate into real operational workflows, similar to alerting pipelines used in SOC, SRE, and production security environments.

---

## Architecture Summary

**Pipeline flow:**

SSH auth.log
↓
Phase 4 – Detection (Python log parser)
↓
alerts.log (append-only)
↓
Phase 5 – Responder (Webhook sender)
↓
External alert (Discord)

---

Key design principle:

> **Detection and response are intentionally decoupled.**

---

## Why logs instead of sockets or live streams?

This project uses **log-based communication** rather than sockets, pipes, or IPC.

### Reasons:
- Logs are **durable** and survive restarts
- Logs are **inspectable** and auditable
- Logs enable **loose coupling** between components
- Logs mirror real security workflows (SIEMs, SOC tooling)

This allows detection and response to:
- Run independently
- Fail independently
- Be replaced or extended independently

This design reflects real-world production environments.

---

## Why Fail2Ban handles blocking (not Python)

Fail2Ban is already active on the system and is responsible for **blocking malicious IPs**.

### Why blocking is not duplicated in Python:
- Fail2Ban operates at the firewall level
- It is battle-tested and efficient
- It enforces bans consistently across restarts
- Reimplementing blocking logic increases risk

### Python’s role instead:
- Visibility
- Alerting
- Context
- Auditability

This mirrors real security architectures where enforcement and detection are separate layers.

---

## Why the responder is separate from detection

Detection (Phase 4) and response (Phase 5) are intentionally split.

### Benefits:
- Clear separation of responsibilities
- Easier debugging
- Easier testing
- Easier future expansion (Slack, email, SIEM)

If detection fails, response does not crash.  
If response fails, detection continues collecting evidence.

This is **modular security design**, not a monolithic script.

---

## Responder Component

**Location:**
responder/ssh-alert-webhook.py

---

### Responsibilities:
- Read new alert entries from Phase 4 output
- Deduplicate alerts using persistent state
- Format human-readable messages
- Send alerts via webhook
- Exit cleanly

### Key features:
- Supports `--dry-run` for safe testing
- Uses persistent state (`notify_state.json`)
- Prevents duplicate alerts
- Fails safely without spamming

---

## Configuration and Secrets Management

**Environment file:**
/etc/ssh-bruteforce-responder.env

---

Secrets are **never committed** to Git.

### Why this matters:
- Prevents credential leaks
- Follows security best practices
- Matches production deployment patterns

A sanitized example file is included:
config/responder.env.example

---

## Why systemd timers (not cron)

systemd timers are used instead of cron jobs.

### Advantages:
- Native service supervision
- Structured logging via `journalctl`
- Dependency awareness (`network-online.target`)
- Persistent scheduling after reboot
- Easier debugging and monitoring

Timers used:
- `ssh-alert-webhook.timer`
- Executes once per minute
- Paired with a oneshot service

This reflects modern Linux automation practices.

---

## Automation Behavior

### Normal operation:
- Timer triggers responder
- Responder checks for new alerts
- If alerts exist, sends notifications
- Updates state to prevent duplicates

### No-alert scenario:
The responder logs:
[INFO] No new alert lines to notify.

This confirms:
- Automation is functioning
- No alert spam
- State tracking works correctly

---

## Evidence and Validation

Screenshots in the `screenshots/` directory demonstrate:
- Secure environment file permissions
- Active systemd timers
- Successful webhook delivery
- Clean responder execution
- Correct “no new alerts” behavior

These screenshots serve as **verifiable proof** of automation.

---

## Skills Demonstrated

This phase demonstrates experience with:
- Linux system administration
- Python automation
- Secure secrets handling
- systemd services and timers
- Log-based security detection
- Incident response workflows
- Production-style architecture

---

## Final Outcome

At the end of Phase 5, the system provides:
- Automated detection
- Automated response
- Real-time alerting
- Zero manual intervention
- Modular and resilient design

This completes the **Attack → Detect → Respond** security workflow.

---

## Next Steps

Possible future extensions:
- Multiple alert destinations
- Severity classification
- Alert aggregation
- SIEM integration
- Metrics and dashboards
