# Kali–Ubuntu Dual-NIC Homelab

## Overview
This lab documents a hands-on cybersecurity homelab built using VirtualBox with Kali Linux and Ubuntu Server. The environment is designed to simulate a segmented network using dual network interfaces, enabling controlled internal communication while maintaining external internet access.

The lab focuses on practical networking concepts, SSH access, and foundational system hardening techniques commonly used in real-world environments.

---

## Lab Goals
- Design a segmented virtual network using VirtualBox
- Configure dual-NIC virtual machines with distinct roles
- Assign static IP addresses on an internal network
- Enable external internet access via NAT
- Validate connectivity and SSH access between host and VMs
- Document configuration, validation, and troubleshooting steps

---

## Environment
- Host OS: Windows 11 (Surface Pro 9)
- Hypervisor: Oracle VirtualBox
- Attacker VM: Kali Linux
- Server VM: Ubuntu Server

---

## Network Topology
Each virtual machine uses two network adapters:

### Adapter 1: Host-Only Network (Internal)
- Purpose: Isolated internal communication between host and VMs
- Subnet: `192.168.56.0/24`

| Device | Interface | IP Address |
|------|----------|-----------|
| Host (Windows) | VirtualBox Host-Only | 192.168.56.1 |
| Kali Linux | eth0 | 192.168.56.30 |
| Ubuntu Server | enp0s3 | 192.168.56.20 |

### Adapter 2: NAT (External)
- Purpose: Internet access for updates and package installation
- IP assignment: DHCP

---

## Network Configuration Summary
- Kali Linux:
  - `eth0`: Static IP on host-only network
  - `eth1`: DHCP via NAT

- Ubuntu Server:
  - `enp0s3`: Static IP configured via Netplan
  - `enp0s8`: DHCP via NAT

This design mirrors real-world segmented environments where internal services are isolated while maintaining controlled external connectivity.

---

## Validation
Connectivity and access were validated using:
- ICMP ping between host and VMs
- ICMP ping between Kali and Ubuntu
- SSH access from host to both VMs
- SSH access from Kali to Ubuntu

Evidence of successful validation is documented in the `evidence/` directory.

---

## Security Considerations
- Internal traffic is isolated to the host-only network
- External exposure is limited to NAT-controlled access
- SSH is used for secure remote administration
- Firewall rules and access controls are documented separately

---

## Troubleshooting
Several issues were encountered and resolved during setup, including:
- Netplan configuration persistence
- Interface naming inconsistencies
- cloud-init network overrides
- Initial connectivity failures due to adapter ordering

Detailed resolutions are documented in `troubleshooting.md`.

---

## What I Learned
- How to design and implement segmented virtual networks
- Practical differences between host-only and NAT networking
- Static vs dynamic IP addressing in Linux environments
- Debugging real network configuration issues
- Importance of documenting reproducible infrastructure

---

## Next Steps
- Harden SSH configuration
- Implement firewall rules (UFW)
- Add logging and monitoring
- Expand lab with IDS/IPS or firewall appliance
