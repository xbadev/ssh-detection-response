# Network Architecture

This section documents the network design used in the Kali–Ubuntu dual-NIC homelab.  
The goal of this architecture is to **intentionally separate internal communication from external access** in order to support realistic attack simulation, observation, and defensive validation.

The network design is a foundational component of the security assessment workflow used throughout later phases.

---

## Network Overview

Each virtual machine is configured with **two VirtualBox network adapters**:

- **Host-Only Adapter (Internal Network)**
  - Isolated communication between the host and virtual machines
  - Used for management, SSH access, and controlled lateral testing

- **NAT Adapter (External Network)**
  - Provides outbound internet access only
  - Prevents direct inbound exposure from external networks

This dual-NIC approach mirrors segmented enterprise environments and reduces unnecessary attack surface while preserving usability.

---

## IP Addressing Scheme

The internal network uses a **static IP addressing model** to ensure predictable communication and reliable SSH connectivity between systems.

Detailed IP assignments and subnet layout are documented in:

- 📄 **[`ip-plan.md`](./ip-plan.md)**

This document defines:
- Internal subnet selection
- Interface-to-IP mappings
- Static vs DHCP assignment decisions
- Separation between internal and external traffic paths

### Evidence: Interface Addressing

Screenshots verifying interface configuration and IP assignment are available here:

- 📸 **[`evidence/kali-ip-a.png`](./evidence/kali-ip-a.png)**
- 📸 **[`evidence/ubuntu-ip-a.png`](./evidence/ubuntu-ip-a.png)**

These artifacts confirm that internal addressing aligns with the documented IP plan.

---

## VirtualBox Adapter Configuration

Each VM is configured with two distinct VirtualBox adapters to enforce traffic separation at the hypervisor level.

Full adapter configuration details and design rationale are documented in:

- 📄 **[`virtualbox-adapters.md`](./virtualbox-adapters.md)**

This document explains:
- Adapter types and visibility scope
- Traffic purpose per adapter
- Security implications of each configuration choice
- Why host-only and NAT were selected together

---

## Design Rationale

This network architecture was intentionally chosen to:

- Maintain a **secure internal network** for management and observation
- Allow **controlled external access** for updates and tooling
- Prevent unintended exposure of internal services
- Support realistic security testing scenarios
- Mirror segmented environments commonly found in production networks

By separating internal and external traffic paths, the lab provides a stable foundation for later attack simulation, detection, and defense phases.

---

## Outcome

At the conclusion of this section, the network environment is fully configured to:

- Support controlled attack activity
- Preserve clear visibility into traffic flow
- Enable reliable validation of defensive controls in subsequent phases
