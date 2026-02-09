# Phase 01: Environment Setup

This phase establishes the **foundational infrastructure** for the Kali–Ubuntu dual-NIC security lab.  
The objective is to configure a **segmented, stable, and reproducible environment** that supports controlled attack simulation, detection observation, and defensive validation in later phases.

All configuration decisions prioritize **security, predictability, and isolation** to mirror real-world enterprise network architecture.

---

## Objectives

This phase accomplishes the following:

✅ **Network Segmentation** - Dual-NIC architecture separating internal and external traffic  
✅ **Static Internal Addressing** - Predictable IP assignments for reliable SSH connectivity  
✅ **Controlled External Access** - NAT-based internet access without inbound exposure  
✅ **Hardened Remote Access** - SSH configuration with reduced privilege and authentication risk  
✅ **Validated Baseline** - Verified network connectivity and service enforcement  

---

## Environment Components

### 1. Network Architecture
The lab uses a **dual-NIC design** with VirtualBox network adapters to enforce traffic separation:

- **Host-Only Network** (`192.168.56.0/24`) - Internal communication only
- **NAT Network** (DHCP) - External internet access only

This design prevents unnecessary exposure while maintaining usability for system updates and security tooling.

📂 **[Full Network Documentation](network/)**

**Evidence:**
- 📸 [SSH from Host to Kali](evidence/ssh-host-to-kali.png) - Confirms internal network connectivity to Kali
- 📸 [SSH from Host to Ubuntu](evidence/ssh-host-to-ubuntu.png) - Confirms internal network connectivity to Ubuntu Server

---

### 2. System Configuration
Core system configurations establish a secure and predictable baseline before introducing attack or defensive tooling:

- **Netplan (Ubuntu)** - Static internal IP, DHCP external IP, enforced dual-NIC separation
- **SSH Daemon** - Root login disabled, explicit protocol enforcement, restricted authentication

These configurations reduce attack surface and ensure consistent behavior across all testing phases.

📂 **[Full Configuration Documentation](configs/)**

---

## Design Rationale

This environment setup was intentionally designed to:

- **Simulate segmented enterprise networks** - Separate internal management from external access
- **Enable realistic attack scenarios** - Isolated internal network for lateral movement testing
- **Reduce unintended exposure** - NAT prevents direct inbound connections from external networks
- **Provide stable testing foundation** - Static addressing ensures predictable SSH and service connectivity
- **Mirror production hardening practices** - SSH restrictions and network segmentation reflect real-world security controls

By establishing this baseline, subsequent phases can focus on **security behavior and detection logic** rather than environmental troubleshooting.

---

## Validation

Environment readiness was validated through:

- ✅ **Network connectivity tests** - ICMP and SSH verification between host and VMs
- ✅ **Interface configuration review** - Static and DHCP assignments confirmed via `ip a`
- ✅ **Service status verification** - SSH daemon active and configuration enforced
- ✅ **Traffic segmentation confirmation** - Internal and external paths properly isolated

All validation artifacts are documented within the [network](network/) and [configs](configs/) subdirectories.

---

## Outcome

At the conclusion of this phase:

- The network environment is **fully segmented and operational**
- Remote access is **available but hardened**
- IP addressing is **static, documented, and predictable**
- The environment is **ready for controlled attack simulation**

This foundation enables Phase 2 (Attack Simulation) to introduce realistic security testing without environmental instability.

---

## Documentation Structure

```
01-environment-setup/
├── README.md                          # This document
├── network/                           # Network architecture documentation
│   ├── README.md
│   ├── ip-plan.md
│   ├── virtualbox-adapters.md
│   └── evidence/
├── configs/                           # System configuration documentation
│   ├── README.md
│   ├── ubuntu-netplan.yaml
│   ├── sshd_config.snippet
│   └── evidence/
└── evidence/                          # Phase-level validation artifacts
    ├── ssh-host-to-kali.png
    └── ssh-host-to-ubuntu.png
```

---

## Next Phase

**→ [Phase 2: Attack Simulation](../02-attack-simulation/)**

This foundation enables Phase 2 (Attack Simulation) to introduce realistic security testing without environmental instability or configuration drift.
