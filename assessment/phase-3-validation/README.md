# Phase 3: Validation (Attack Blocked)

## Objective
Validate that the SSH defenses implemented in Phase 2 successfully detect and block a real attack attempt.

This phase confirms that:
- Unauthorized access is prevented
- Attacker behavior is logged
- Automated defenses respond correctly
- The system enforces access control without manual intervention

---

## Validation Scenario

After applying:
- UFW rules restricting SSH access
- Fail2Ban monitoring SSH authentication failures

The attacker (Kali Linux) attempts to reconnect to the Ubuntu server using SSH.

---

## Observed Behavior

### Attacker Side (Kali)
- SSH authentication fails
- Multiple failed attempts trigger a ban
- Subsequent SSH connections are refused

This confirms the attacker is actively blocked.

---

### Defender Side (Ubuntu)

#### SSH Logs
- Failed authentication attempts are recorded in `/var/log/auth.log`
- Repeated failures originate from the attacker IP

#### Fail2Ban Status
- SSH jail detects multiple failures
- Attacker IP is added to the banned list
- Ban is enforced automatically

### Trusted Access Preserved

SSH access from the trusted host system remained functional after defenses were applied.

This confirms that:
- SSH service availability was maintained
- Firewall rules were not overly restrictive
- Defensive controls selectively blocked only the attacker

See screenshot: `host-ssh-access-still-allowed.png`

---

## Evidence

Screenshots in the `screenshots/` directory show:
- SSH connection attempts from Kali
- Authentication failures on Ubuntu
- Fail2Ban banning the attacker IP
- SSH connections being refused after the ban

---

## Outcome

The attack → observe → defend → validate workflow is complete.

The Ubuntu server:
- Detected malicious behavior
- Logged the attack
- Automatically blocked the attacker
- Maintained service availability and integrity

This confirms the effectiveness of layered SSH defenses using UFW and Fail2Ban.
