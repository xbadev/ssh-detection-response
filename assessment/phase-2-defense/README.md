# Phase 2: Defense (UFW + Fail2ban)

## Objective
Apply practical SSH defenses on the Ubuntu server after observing a controlled brute-force attempt from Kali in Phase 1.

This phase hardens SSH by adding:
- **UFW** firewall rules to restrict/limit exposure
- **Fail2ban** to automatically detect repeated failures and **ban** the attacker IP

---

## Environment
- **Ubuntu Server (target):** `192.168.56.20` (host-only)
- **Kali Linux (attacker):** `192.168.56.30` (host-only)
- **Host (Windows):** `192.168.56.1` (host-only gateway)

---

## Defense Controls Implemented

### 1) UFW (Firewall)
UFW is used as the host firewall policy layer. The intent here is:
- Keep SSH available for lab access
- Ensure rules are explicit and auditable
- Record current firewall state and rules for validation later

Evidence saved:
- `ufw/rules.txt`
- `ufw/status.txt`

> Note: `ufw status` can show **inactive** while `systemctl status ufw` shows the service is enabled/active (exited).  
> UFW’s systemd unit can be enabled to load rules at boot, but the firewall policy itself is considered “inactive” until `ufw enable` is applied.

---

### 2) Fail2ban (SSH brute-force protection)
Fail2ban monitors authentication logs and triggers bans when repeated failures occur.

The intent here is:
- Detect repeated SSH failures in `/var/log/auth.log`
- Ban the attacking IP automatically after N retries
- Provide visible proof of bans + enforcement in Phase 3

Configuration saved:
- `fail2ban/jail.local`

Evidence saved:
- `fail2ban/status.txt`

---

## What “Success” Looks Like (handoff to Phase 3)
Phase 2 is complete when:
- UFW rules + status are captured (files in `ufw/`)
- Fail2ban is installed, running, and configured for `sshd` (files in `fail2ban/`)
- We are ready to validate that Kali’s brute-force attempts trigger a ban and are blocked

Next phase:
➡️ **Phase 3: Validation**  
Re-run the controlled attack and capture proof that Fail2ban bans Kali and SSH attempts are blocked (with logs + fail2ban status output).

---
