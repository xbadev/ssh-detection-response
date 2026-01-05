# VirtualBox Network Adapter Configuration

This lab uses two VirtualBox network adapters per virtual machine to separate internal and external traffic.

---

## Adapter 1: Host-Only Adapter

**Type:** Host-only Adapter  
**Purpose:** Internal communication between host and VMs  
**Visibility:** Host ↔ VMs only

This adapter enables:
- SSH access from host to VMs
- ICMP testing between VMs
- Isolated internal traffic with no internet exposure

Host-only networking was chosen to simulate a private internal network similar to a corporate LAN.

---

## Adapter 2: NAT Adapter

**Type:** NAT  
**Purpose:** External internet access  
**Visibility:** VM ↔ Internet only

This adapter enables:
- System updates
- Package installation
- External connectivity without exposing internal services

Using NAT prevents direct inbound connections from the external network while still allowing outbound access.

---

## Design Rationale

Using both adapters together allows the lab to:
- Maintain a secure internal network
- Provide controlled internet access
- Mirror real-world segmented environments
- Reduce attack surface while preserving usability
