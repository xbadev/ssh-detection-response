# Phase 03: Defense Hardening

This phase implements **layered defensive controls** to protect Ubuntu Server from the SSH brute-force attacks demonstrated in Phase 02.  
The objective is to enforce network-level access restrictions and deploy automated intrusion prevention to reduce attack surface and block malicious authentication attempts.

All defensive measures are validated through controlled testing to confirm proper enforcement and minimal impact on legitimate access.

---

## Objective

Implement defense-in-depth controls to mitigate SSH brute-force attacks while preserving legitimate administrative access.

This phase demonstrates:
- Network-level access control using UFW firewall
- Automated intrusion prevention using Fail2Ban
- Validation that defenses block attacks without disrupting authorized access
- Defense-in-depth security architecture

---

## Defensive Strategy

Two complementary defensive layers are deployed:

**Layer 1: Network Perimeter Control (UFW)**  
Restrict SSH access to trusted internal network only, blocking all external SSH attempts at the firewall level before authentication is attempted.

**Layer 2: Intrusion Prevention (Fail2Ban)**  
Monitor authentication logs in real-time and automatically ban IPs after repeated failed login attempts, providing time-based blocking for detected brute-force behavior.

Together, these controls implement **defense-in-depth**: if network controls are bypassed, intrusion prevention provides a second line of defense.

---

## Defense Implementation

### UFW Firewall Configuration

Ubuntu's Uncomplicated Firewall (UFW) was configured to restrict SSH access to the internal host-only network (`192.168.56.0/24`).

**Firewall Rule:**
```bash
sudo ufw allow from 192.168.56.0/24 to any port 22
```

**Configuration Details:** [`ufw/rules.txt`](ufw/rules.txt)

**Impact:**
- SSH is only accessible from the trusted internal network
- External networks (including the NAT adapter) cannot reach SSH
- Attack surface is reduced at the network layer

**Evidence:**
- 📸 [UFW Rules and Status](ufw/ufw-rules-and-status.png) - Firewall configuration and active enforcement

---

### Fail2Ban Intrusion Prevention

Fail2Ban was deployed to monitor `/var/log/auth.log` and automatically ban IPs exhibiting brute-force behavior.

**Configuration:** [`fail2ban/jail.local`](fail2ban/jail.local)

**Key Settings:**
- **Service:** SSH (sshd)
- **Log Path:** `/var/log/auth.log`
- **Max Retries:** 3 failed attempts
- **Find Time:** 60 seconds
- **Ban Time:** 300 seconds (5 minutes)

**Behavior:**
- Monitors authentication logs continuously
- Detects patterns of repeated failed login attempts
- Automatically adds offending IPs to firewall ban list
- Releases bans after configured time period

**Evidence:**
- 📸 [Fail2Ban Status](fail2ban/fail2ban-status.png) - Service active and monitoring

---

## Validation

Defensive controls were validated through controlled SSH connection tests from multiple sources:

✅ **UFW firewall enforced** - SSH accessible from host-only network, blocked from external sources  
✅ **Fail2Ban service active** - Monitoring authentication logs and banning offending IPs  
✅ **Legitimate access preserved** - Authorized connections from internal network still function  
✅ **Attack traffic blocked** - Brute-force attempts successfully prevented

**Validation Evidence:**

- 📸 [Host SSH Access Still Allowed](evidence/host-ssh-access-still-allowed.png) - Confirms authorized access from internal network preserved
- 📸 [Kali SSH Refused](evidence/kali-ssh-refused.png) - Confirms unauthorized access blocked by firewall
- 📸 [Fail2Ban Client Banned](evidence/fail2ban-client-banned-kali-ip.png) - Confirms Fail2Ban detecting and banning attack sources
- 📸 [Ubuntu Auth Log Validation](evidence/ubuntu-auth-log-validation.png) - Confirms logs show firewall denials and Fail2Ban actions

---

## Design Rationale

These defensive controls were selected to:

- **Enforce network segmentation** - Limit SSH to trusted internal networks only
- **Automate threat response** - Reduce manual intervention through automated banning
- **Preserve usability** - Maintain legitimate administrative access from authorized sources
- **Demonstrate layered security** - Show defense-in-depth with multiple control types
- **Mirror production practices** - Reflect real-world SSH hardening strategies

By combining network-level restrictions (UFW) with application-level monitoring (Fail2Ban), the defense posture is significantly strengthened while maintaining operational flexibility.

---

## Outcome

At the conclusion of this phase:

- SSH access is restricted to the internal trusted network
- Automated intrusion prevention is monitoring and blocking brute-force attempts
- Defensive controls are validated and enforcing as designed
- The attack surface has been significantly reduced

This hardened baseline enables Phase 04 (Detection & Monitoring) to focus on observing and alerting on attack attempts with additional monitoring capabilities.

---

## Documentation Structure

```
03-defense-hardening/
├── README.md                                      # This document
├── fail2ban/
│   ├── jail.local                                 # Fail2Ban configuration
│   └── fail2ban-status.png                        # Service status verification
├── ufw/
│   ├── rules.txt                                  # UFW rule documentation
│   └── ufw-rules-and-status.png                   # Firewall configuration verification
└── evidence/
    ├── fail2ban-client-banned-kali-ip.png        # Fail2Ban ban validation
    ├── host-ssh-access-still-allowed.png          # Authorized access validation
    ├── kali-ssh-refused.png                       # Unauthorized access blocked
    └── ubuntu-auth-log-validation.png             # Log-level enforcement validation
```

---

## Next Phase

**→ [Phase 04: Detection & Monitoring](../04-detection-monitoring/)**

With defensive controls in place, the next phase develops Python-based detection logic and monitoring capabilities to identify, alert on, and track security events in real-time.
