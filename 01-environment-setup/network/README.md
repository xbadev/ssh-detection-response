# Network Configuration

The lab uses a dual-NIC design per VM, with one NIC on each Proxmox bridge.

## Proxmox bridges

| Bridge | Purpose | Notes |
|---|---|---|
| `vmbr0` | Internet egress | DHCP from the home router |
| `vmbr1` | Internal lab traffic | No uplink — isolated from home network |

Bridge configuration lives on the Proxmox host (see [proxmox-homelab](https://github.com/xbadev/proxmox-homelab)). VMs receive two virtual NICs each in the VM hardware tab.

## VM NIC layout

| VM | NIC 1 (vmbr0) | NIC 2 (vmbr1) |
|---|---|---|
| Ubuntu | DHCP, internet only | Static `10.10.10.20/24` |
| Kali | DHCP, internet only | Static `10.10.10.30/24` |

## IP plan

| Host | Internal IP | Role |
|---|---|---|
| Ubuntu Server | `10.10.10.20` | Detection / response target |
| Kali Linux | `10.10.10.30` | Attacker |
| (reserved) | `10.10.10.1` | Gateway slot — unused, no router on vmbr1 |

`10.10.10.0/24` is set aside for this lab. Adding a Windows VM later (for the [rdp-detection-response](https://github.com/xbadev/rdp-detection-response) lab) keeps the same subnet and assigns from `10.10.10.40` onward.

## Why match interfaces by MAC

Kernel-assigned interface names (`ens18`, `enp0s3`, `eth0`) change between distributions and even between kernel versions. Pinning configuration to those names breaks on the next reboot or VM clone. The netplan in [`../configs/ubuntu-netplan.yaml`](../configs/ubuntu-netplan.yaml) matches each interface by its MAC address (visible in the Proxmox VM hardware tab) and renames it to a semantic alias.

## Verification

```bash
ip -br link            # MAC addresses of each NIC
ip -br addr            # final names + IPs
ip route               # default route via ext0 (vmbr0), no route on int0
ping -c1 10.10.10.30   # reach Kali across vmbr1
```
