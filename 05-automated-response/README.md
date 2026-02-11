# Phase 05: Automated Response

This phase implements **automated incident response** that triggers automated notifications when SSH brute-force attacks are detected. 
The objective is to close the security automation loop by enabling real-time, automated responses to detection alerts without manual intervention.

The response system monitors detection alerts and sends notifications to external systems (Discord webhook) for security event visibility and potential orchestration.

---

## Objective

Implement automated response capabilities that execute when brute-force attacks are detected by the Phase 04 monitoring system.

This phase demonstrates:
- Event-driven response automation
- Webhook-based notification integration
- Systemd service integration for continuous response monitoring
- Configuration-driven response behavior
- Complete security automation workflow (detect → alert → respond)

---

## Response Strategy

The automated response system monitors detection alerts and triggers configured actions when new security events occur.

**Response Architecture:**
- Monitor detection alert log (`alerts.log` from Phase 04)
- Track processed alerts to avoid duplicate notifications
- Send webhook notifications to Discord when new attacks detected
- Maintain persistent state across service restarts
- Execute continuously via systemd timer

**Why Discord Webhook:**
- Demonstrates external integration capability
- Provides real-time visibility into security events
- Can be extended to trigger additional orchestration
- Simple, reliable notification mechanism
- Proof of concept for SIEM/SOAR integration

---

## Implementation

### Response Script

The core response logic is implemented in Python and monitors detection alerts for automated action.

**Script:** [`responder/ssh-alert-webhook.py`](responder/ssh-alert-webhook.py)

**Key Functionality:**
- Monitors Phase 04 detection `alerts.log` for new entries
- Parses alert format to extract IP, count, and timestamp information
- Sends formatted notifications to Discord webhook
- Tracks processed alerts in persistent state file
- Prevents duplicate notifications for same alert

---

### Response Configuration

Response behavior is configured via environment file loaded by systemd service.

**Configuration:** [`config/responder.env.example`](config/responder.env.example)

Configuration Parameters:
- ALERT_WEBHOOK_URL – Discord webhook endpoint for notifications (primary variable)
- WEBHOOK_URL – Optional fallback variable name accepted by the script


Usage:
- Copy responder.env.example to a secure location (e.g., /etc/ssh-bruteforce-responder.env)
- Set the actual Discord webhook URL
- Ensure proper file permissions (e.g., chmod 600)

---

### Systemd Service Integration

The response script runs continuously via systemd service and timer units, monitoring for new alerts and triggering responses automatically.

**Service Unit:** [`systemd/ssh-alert-webhook.service`](systemd/ssh-alert-webhook.service)  
Defines script execution environment, working directory, and environment file loading.

**Timer Unit:** [`systemd/ssh-alert-webhook.timer`](systemd/ssh-alert-webhook.timer)  
Schedules periodic execution to check for new alerts.

**Why Service + Timer:**
- **Service** defines execution environment and loads configuration
- **Timer** schedules periodic alert checking
- Together they enable continuous response automation
- System automatically resumes monitoring after reboot

This completes the end-to-end automation pipeline:
```
Attack occurs → Detection alerts → Response triggers → Notification sent
```

---

### Response Output

The response script generates runtime state files for tracking processed alerts.

**Output Directory:** `output/`

**Files:**
- **`notify_state.json`** - Tracks which alerts have been processed to prevent duplicates
- **`notifications.log`** - Records all sent notifications with timestamps

Both files are excluded from version control via `.gitignore` as they contain runtime state specific to each environment.

📂 **[Output Documentation](output/)** - See output folder README for state file format and gitignore rationale

---

## Validation

Automated response capabilities were validated through controlled testing:

✅ **Script monitors alerts.log correctly** - Detects new alert entries  
✅ **Webhook notifications sent** - Discord receives formatted security alerts  
✅ **State tracking prevents duplicates** - Same alert not notified multiple times  
✅ **Systemd integration works** - Service executes on schedule via timer  
✅ **End-to-end automation functions** - Detection triggers response automatically  

**Validation Evidence:**

- 📸 [Discord SSH Alert](screenshots/discord-ssh-alert.png) - Webhook notification received in Discord
- 📸 [Responder Environment Permissions](screenshots/responder.env-permission.png) - Configuration file permissions validated
- 📸 [Systemd Webhook Timer Active](screenshots/systemd-webhook-timer-active.png) - Timer scheduling confirmed active
- 📸 [Webhook Journal Success](screenshots/webhook-journal-success.png) - Systemd logs showing successful notification delivery

---

## Design Rationale

This response automation was designed to:

- **Close the automation loop** - Detect → Alert → Respond without manual steps
- **Enable external integration** - Webhook demonstrates extensibility to other systems
- **Maintain operational visibility** - Notifications provide security event awareness
- **Support orchestration** - Webhook can trigger additional defensive actions
- **Demonstrate production patterns** - Systemd integration mirrors real-world deployment

By implementing automated response, the lab demonstrates a complete security automation workflow from attack simulation through defensive action.

---

## Outcome

At the conclusion of this phase:

- Automated response system monitors detection alerts continuously
- Webhook notifications sent to Discord when attacks detected
- Systemd integration ensures persistent response monitoring
- Complete security automation pipeline operational (attack → detect → respond)

This final phase completes the security lab demonstrating end-to-end automation from controlled attack through automated defensive response.

---

## Documentation Structure

```
05-automated-response/
├── README.md                                      # This document
├── config/
│   └── responder.env.example                     # Configuration template
├── responder/
│   └── ssh-alert-webhook.py                      # Response automation script
├── systemd/
│   ├── ssh-alert-webhook.service                 # Systemd service unit
│   └── ssh-alert-webhook.timer                   # Systemd timer unit
├── output/
│   ├── README.md                                  # Output files documentation
│   └── .gitignore                                 # Excludes runtime state files
└── screenshots/
    ├── discord-ssh-alert.png
    ├── responder.env-permission.png
    ├── systemd-webhook-timer-active.png
    └── webhook-journal-success.png
```

---

## Lab Completion

Phase 05 completes the **Kali-Ubuntu Dual-NIC Security Lab** with a full security automation workflow:

1. **[Phase 01 – Segmented, Hardened Environment](../01-environment-setup/)**
2. **[Phase 02 – Controlled Attack Simulation](../02-attack-simulation/)**
3. **[Phase 03 – Layered Defensive Controls](../03-defense-hardening/)**
4. **[Phase 04 – Automated Detection and Monitoring](../04-detection-monitoring/)**
5. **[Phase 05 – Automated Incident Response](../05-automated-response/)**


The lab demonstrates complete security engineering capabilities from infrastructure setup through automated threat response.
