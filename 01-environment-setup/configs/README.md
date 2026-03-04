# System Configuration

Network and SSH daemon configuration applied to the Ubuntu server to establish a secure, predictable baseline before any attack simulation.

---

## Network Interface Configuration (Netplan)

Dual-NIC separation enforced via Netplan: static IP on the Host-Only interface for internal lab traffic, DHCP on the NAT interface for outbound internet access.

**Config file:** [`ubuntu-netplan.yaml`](./ubuntu-netplan.yaml)

Netplan YAML as applied under `/etc/netplan/`:

![Netplan config](evidence/netplan-static-yaml.png)

Active interface state confirming static internal IP, DHCP external IP, and default route via NAT adapter:

![Active interfaces and routing](evidence/netplan-active-interfaces-and-routing.png)

---

## SSH Daemon Configuration

SSH hardened with root login disabled, explicit protocol enforcement, and restricted authentication methods.

**Config snippet:** [`sshd_config.snippet`](./sshd_config.snippet)

SSH daemon running and enforcing the configuration:

![SSHD service status](evidence/sshd-service-status.png)
