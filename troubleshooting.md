# Troubleshooting and Issue Resolution

This section documents issues encountered during the setup of the Kali–Ubuntu dual-NIC homelab and how they were resolved.

---

## Issue 1: Network Configuration Not Persisting on Ubuntu Server

### Symptoms
- Static IP configuration would not persist after reboot
- Interface reverted to DHCP behavior unexpectedly

### Cause
Ubuntu Server uses `cloud-init` by default, which can override or regenerate network configuration files during boot.

### Resolution
- Identified cloud-init as the source of configuration overrides
- Disabled cloud-init networking behavior
- Moved static IP configuration fully into Netplan
- Verified persistence across reboots

### Outcome
Static IP configuration on the host-only interface persisted correctly after reboot.

---

## Issue 2: Interface Naming Confusion Between Adapters

### Symptoms
- Uncertainty over which interface corresponded to host-only vs NAT
- Initial misconfiguration attempts using incorrect interface names

### Cause
Predictable network interface naming (`enp0s3`, `enp0s8`, `eth0`, `eth1`) depends on adapter order and PCI mapping in VirtualBox.

### Resolution
- Used `ip a` to map interfaces to active IP addresses
- Correlated interface behavior with VirtualBox adapter order
- Confirmed correct mapping before applying static configuration

### Outcome
Correct interfaces were identified and configured without further conflicts.

---

## Issue 3: SSH Connectivity Failing Initially

### Symptoms
- SSH connection attempts timing out or being refused
- Ping working but SSH unavailable

### Cause
- SSH service not running by default on Ubuntu Server
- Firewall rules not yet allowing SSH traffic

### Resolution
- Installed and enabled OpenSSH server
- Verified SSH service status
- Adjusted firewall rules to allow SSH traffic

### Outcome
SSH access was successfully established from host and Kali Linux.

---

## Issue 4: NAT vs Host-Only Routing Expectations

### Symptoms
- Confusion over duplicate NAT IP addresses across VMs
- Initial assumption that NAT IPs should be unique across VMs

### Cause
VirtualBox NAT assigns IP addresses per-VM in isolated namespaces, allowing identical private IPs without conflict.

### Resolution
- Confirmed routing behavior using `ip route`
- Verified outbound internet access independently on each VM
- Validated that internal traffic correctly used the host-only network

### Outcome
Correct understanding of NAT isolation and routing behavior.

---

## Lessons Learned
- Always identify interface mappings before applying static configuration
- cloud-init can override network settings and must be accounted for
- Successful ICMP does not guarantee service availability
- Understanding virtualization networking behavior is critical for debugging

This troubleshooting process reinforced the importance of methodical validation and documentation.

