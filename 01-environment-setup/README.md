# Phase 01 — Environment Setup

Built the network and host baseline for the lab on Proxmox: dual-NIC Ubuntu target on `10.10.10.0/24`, hardened SSH daemon, MAC-based interface matching for stability across reboots and Ubuntu releases.

## Topology

| VM | Role | Internal IP (vmbr1) | External (vmbr0) |
|---|---|---|---|
| Ubuntu Server 24.04 | Target | `10.10.10.20` | DHCP |
| Kali Linux | Attacker | `10.10.10.30` | DHCP |

Both VMs run on Proxmox with two virtual NICs each, one bridged to `vmbr0` (internet egress, DHCP) and one to `vmbr1` (internal lab subnet, static).

`vmbr1` has no uplink — the internal subnet is isolated from the home network. All attack traffic stays within the hypervisor.

## What's in this phase

| File | Purpose |
|---|---|
| [`configs/ubuntu-netplan.yaml`](configs/ubuntu-netplan.yaml) | Netplan for the Ubuntu target — interfaces matched by MAC |
| [`configs/sshd_config.snippet`](configs/sshd_config.snippet) | SSH daemon hardening drop-in |
| [`network/`](network/) | Network architecture and IP plan |

## Network — interface matching by MAC

Earlier iterations of this lab pinned configuration to specific kernel-assigned interface names (`ens18`, `enp0s3`). Those names drift between Ubuntu releases and between virtualization platforms. The new netplan matches each interface by MAC address (set in the Proxmox VM hardware tab) and renames them to semantic aliases (`ext0`, `int0`):

```yaml
ethernets:
  ext0:
    match: { macaddress: "BC:24:11:AA:AA:AA" }
    set-name: ext0
    dhcp4: true
  int0:
    match: { macaddress: "BC:24:11:BB:BB:BB" }
    set-name: int0
    addresses: [10.10.10.20/24]
```

This survives kernel updates and works the same on a fresh VM clone. Fill in the actual MACs from `ip -br link` before applying.

## SSH — hardened baseline

The drop-in at [`configs/sshd_config.snippet`](configs/sshd_config.snippet) is installed as `/etc/ssh/sshd_config.d/10-lab.conf` so it overrides the distro defaults without editing `sshd_config` directly:

- `PermitRootLogin no` — root cannot log in via SSH
- `MaxAuthTries 3` — fewer attempts per connection
- `LoginGraceTime 20` — short window to authenticate
- `AllowUsers <LAB_USER>` — only one named user permitted
- Password authentication is **intentionally left enabled** because the lab's purpose is to simulate password brute-force; production would disable it.

Reload the daemon to apply: `sudo systemctl reload ssh`.

## Validation

```bash
ip -br addr           # confirm ext0 has DHCP, int0 has 10.10.10.20/24
ping -c1 10.10.10.30  # reach attacker on internal subnet
ssh -o ConnectTimeout=3 bader@10.10.10.20  # SSH works, root login refused
sshd -T | grep -E 'permitrootlogin|maxauthtries'
```

## Next

Phase 02 introduces the attack — running Hydra from Kali against the hardened-but-still-reachable SSH daemon to generate the failure events that downstream phases will detect and respond to.
