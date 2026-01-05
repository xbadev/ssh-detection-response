# IP Addressing Plan

This document outlines the IP addressing scheme used in the Kali–Ubuntu dual-NIC homelab.

---

## Host-Only Network (Internal)

**Subnet:** `192.168.56.0/24`  
**Purpose:** Isolated internal communication between host and virtual machines.

| Device | Interface | IP Address |
|------|----------|-----------|
| Windows Host | VirtualBox Host-Only Adapter | 192.168.56.1 |
| Kali Linux | eth0 | 192.168.56.30 |
| Ubuntu Server | enp0s3 | 192.168.56.20 |

All internal IP addresses are statically assigned to ensure predictable addressing and reliable SSH connectivity.

---

## NAT Network (External)

**Purpose:** Internet access for system updates and package installation.  
**IP Assignment:** DHCP (VirtualBox-managed).

| Device | Interface |
|------|----------|
| Kali Linux | eth1 |
| Ubuntu Server | enp0s8 |

The NAT network is intentionally separated from the internal host-only network to simulate controlled external access.
