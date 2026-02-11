# Kali-Ubuntu Dual-NIC Security Lab

A complete security automation workflow demonstrating attack simulation, detection, defense, and automated response in a segmented homelab environment.

This lab builds a **defense-in-depth security architecture** from scratch, progressing from controlled attack scenarios to fully automated incident response with reproducible infrastructure and documented evidence.

---

## Lab Overview

This project simulates a real-world security operations workflow using VirtualBox virtual machines:

- **Kali Linux (192.168.56.30)** – Attacker  
- **Ubuntu Server (192.168.56.20)** – Target with layered defenses  
- **Dual-NIC Architecture** – Isolated internal network + controlled external access  

The lab demonstrates infrastructure hardening, attack observation, threat detection, defensive controls, and automated incident response.

---

## Workflow Phases

### [Phase 01: Environment Setup](01-environment-setup/)
Establish a segmented, hardened network environment with predictable IP addressing and restricted SSH access.

**Key Outcomes:**
- Dual-NIC network architecture (host-only + NAT)
- Static internal IP addressing
- SSH configuration hardening
- Validated baseline connectivity

---

### [Phase 02: Attack Simulation](02-attack-simulation/)
Generate controlled SSH brute-force attack traffic to create observable security events.

**Key Outcomes:**
- Hydra SSH brute-force execution
- Authentication log generation
- Attack traffic correlation
- Evidence collection

---

### [Phase 03: Defense Hardening](03-defense-hardening/)
Implement layered defensive controls to reduce attack surface and block malicious traffic.

**Key Outcomes:**
- UFW firewall network segmentation
- Fail2Ban intrusion prevention
- Defense validation and testing
- Attack surface reduction

---

### [Phase 04: Detection & Monitoring](04-detection-monitoring/)
Develop Python-based detection logic to identify and alert on SSH brute-force patterns.

**Key Outcomes:**
- Automated log analysis
- Stateful attack tracking
- Alert generation
- Systemd service integration

---

### [Phase 05: Automated Response](05-automated-response/)
Close the security automation loop with event-driven response actions.

**Key Outcomes:**
- Webhook-based notifications
- External system integration (Discord)
- Automated incident response
- Complete automation pipeline

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Workflow                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Attack         Detection        Defense        Response    │
│  Occurs    →    Identifies  →    Blocks    →    Notifies    │
│                                                             │
│  Phase 02       Phase 04         Phase 03       Phase 05    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Network Segmentation (Phase 01):
  Internal: 192.168.56.0/24 (Host-Only)
  External: NAT (DHCP)

Defensive Layers (Phase 03):
  Layer 1: UFW Firewall (Network)
  Layer 2: Fail2Ban (Application)

Detection & Response (Phases 04-05):
  Monitor → Detect → Alert → Notify
```

---

## Technical Stack

### Infrastructure

- VirtualBox 7.x
- Kali Linux 2024.x
- Ubuntu Server 24.04 LTS

### Security Tools

- Hydra
- UFW
- Fail2Ban

### Automation

- Python 3
- Systemd
- Discord Webhooks

---

## Key Demonstrations

- Network segmentation with dual-NIC architecture
- Defense-in-depth (firewall + IPS)
- Python-based attack detection
- Automated response without manual intervention
- Systemd-managed continuous monitoring
- Webhook-based external integration

---

## Use Cases

- Security engineering portfolio
- SOC analyst training
- DevSecOps learning
- Interview discussion material
- Expandable homelab foundation

---

## Getting Started

1. Review Phase 01 to understand the architecture.
2. Follow phases sequentially.
3. Examine evidence for validation.
4. Adapt configurations as needed.

Each phase README contains full implementation details and validation steps.

---

## Project Highlights

- Complete automation pipeline from attack through response
- Production-style systemd orchestration
- Structured validation workflow
- Professional documentation and evidence collection
- Extensible security architecture
