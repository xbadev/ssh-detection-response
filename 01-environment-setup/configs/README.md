# System Configuration

This section documents the **core system configuration choices** applied during the environment setup phase.  
These configurations establish a secure, predictable baseline for networking and remote access before any attack simulation or defensive tooling is introduced.

The focus here is **configuration intent and enforcement**, not step-by-step installation.

---

## Configuration Overview

Two primary configuration areas are defined in this phase:

- **Network interface configuration**
  - Static internal addressing
  - DHCP-managed external access
- **SSH daemon configuration**
  - Controlled remote access
  - Reduced authentication and privilege risk

These configurations ensure the environment behaves consistently and supports later security testing phases.

---

## Network Interface Configuration (Netplan)

Ubuntu Server networking is configured using Netplan to enforce **dual-NIC separation**:

- Internal interface uses a **static IP**
- External interface uses **DHCP**
- Internal traffic remains predictable and isolated
- External traffic is limited to outbound connectivity

### Configuration File

- 📄 **[`ubuntu-netplan.yaml`](./ubuntu-netplan.yaml)**

This file defines:
- Static addressing for the host-only interface
- DHCP for the NAT-facing interface
- Clear separation between internal and external traffic paths

### Evidence: Active Network State

The following screenshots confirm that the configuration is **actively applied on the system**:

- 📸 **[`netplan-active-interfaces-and-routing.png`](./evidence/netplan-active-interfaces-and-routing.png)**  
  Confirms:
  - Static IP on internal interface
  - DHCP assignment on external interface
  - Default route via external adapter

- 📸 **[`netplan-static-yaml.png`](./evidence/netplan-static-yaml.png)**  
  Confirms:
  - Netplan configuration as applied under `/etc/netplan/`

---

## SSH Daemon Configuration

SSH access is intentionally restricted to reduce unnecessary exposure while preserving administrative access for management and testing.

### Configuration Snippet

- 📄 **[`sshd_config.snippet`](./sshd_config.snippet)**

This snippet highlights key security-relevant directives, including:
- Root login disabled
- Explicit protocol version
- Controlled authentication methods
- User-level access restriction

The snippet is provided as a **focused excerpt** rather than a full configuration dump to emphasize intent over noise.

### Evidence: SSH Service Enforcement

- 📸 **[`sshd-service-status.png`](./evidence/sshd-service-status.png)**

This confirms:
- SSH daemon is running
- Service is successfully loaded and active
- Configuration is syntactically valid and enforced

---

## Design Rationale

These configurations were selected to:

- Ensure **predictable internal networking**
- Limit exposure of management services
- Reduce authentication and privilege risk
- Provide a clean baseline for attack and defense phases
- Mirror real-world infrastructure hardening practices

By enforcing these controls early, later phases can focus on **security behavior** rather than environmental instability.

---

## Outcome

At the conclusion of this section:

- Network interfaces behave as designed
- SSH access is available but constrained
- Core services are stable and verifiable
- The environment is ready for controlled attack simulation
