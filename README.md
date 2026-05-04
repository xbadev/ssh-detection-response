# SSH Detection & Response — Home Lab

End-to-end SSH brute-force detection and response pipeline on Linux. A real-time journald-following detector emits structured alerts, a separate responder posts them to a webhook, and Fail2Ban + UFW provide defense-in-depth. Everything is driven from one config file and brought up with one `make` command.

The lab runs on a Proxmox VE hypervisor with two VMs on an isolated internal subnet — Ubuntu Server as the target, Kali Linux as the attacker.

## Environment

| Component | Detail |
|-----------|--------|
| Hypervisor | Proxmox VE 9.x (see [proxmox-homelab](https://github.com/xbadev/proxmox-homelab)) |
| Target | Ubuntu Server 24.04 LTS — `10.10.10.20` |
| Attacker | Kali Linux — `10.10.10.30` |
| Internal network | `10.10.10.0/24` on Proxmox bridge `vmbr1` (no internet exposure) |
| External network | Proxmox bridge `vmbr0` (DHCP, internet egress only) |
| Attack surface | SSH (port 22) |
| Defense layer | UFW (network) + Fail2Ban (host, journald backend) |
| Detection | Python daemon following `journalctl -u ssh -f -o json` |
| Response | Python daemon tailing JSONL alerts → webhook POST |
| Latency | Attack to webhook delivery: ~2 seconds |

## Quick demo

On the Ubuntu target:

```bash
git clone https://github.com/xbadev/ssh-detection-response.git
cd ssh-detection-response
sudo make install
sudo make config       # set ALERT_WEBHOOK_URL and verify IPs
sudo make enable
```

On the Kali attacker (after copying `lab.env` to `/etc/ssh-detection-response/lab.env`):

```bash
cd ssh-detection-response
./02-attack-simulation/run-attack.sh
```

Within ~2 seconds, the alert lands on the webhook. To watch the pipeline live on the target:

```bash
sudo journalctl -u ssh-detector -u ssh-responder -f
```

## Phases

| # | Phase | What it does |
|---|-------|---|
| 01 | [Environment Setup](./01-environment-setup/) | Proxmox dual-NIC layout, netplan config matched by MAC, SSH daemon hardening |
| 02 | [Attack Simulation](./02-attack-simulation/) | `run-attack.sh` Hydra runner that reads target IP and user from `lab.env` |
| 03 | [Defense Hardening](./03-defense-hardening/) | UFW restricting SSH to internal subnet, Fail2Ban with systemd-journal backend |
| 04 | [Detection & Monitoring](./04-detection-monitoring/) | Real-time detector daemon following the journal, sliding-window threshold, JSONL output |
| 05 | [Automated Response](./05-automated-response/) | Real-time responder daemon tailing JSONL, webhook POST, per-IP cooldown |

## Architecture

```
┌──────────────┐   SSH brute-force    ┌────────────────────────────────────────┐
│  Kali        │ ───────────────────► │  Ubuntu target                          │
│ 10.10.10.30  │                      │  10.10.10.20                            │
└──────────────┘                      │                                         │
                                      │  ┌─────────────┐                        │
                                      │  │ sshd        │                        │
                                      │  └──────┬──────┘                        │
                                      │         │ writes failures               │
                                      │         ▼                               │
                                      │  ┌─────────────┐                        │
                                      │  │ journald    │ ◄── Fail2Ban also reads│
                                      │  └──────┬──────┘     and bans           │
                                      │         │ -f                            │
                                      │         ▼                               │
                                      │  ┌─────────────┐                        │
                                      │  │ ssh-detector│ ──► alerts.jsonl       │
                                      │  └─────────────┘                        │
                                      │                          │              │
                                      │                          ▼              │
                                      │  ┌─────────────┐                        │
                                      │  │ ssh-responder │ ──► webhook ────► Discord
                                      │  └─────────────┘                        │
                                      └─────────────────────────────────────────┘
```

Detection and response are intentionally split: detector owns the event stream, responder owns the secret (webhook URL) and the network egress. Either side can be developed, tested, or replaced independently — same pattern as a SOAR detection-vs-action split.

## Configuration

All settings live in `/etc/ssh-detection-response/lab.env` (mode `0640`, sourced by both systemd units). See [`lab.env.example`](./lab.env.example) for every supported variable.

```bash
sudo make config       # opens lab.env in $EDITOR
```

Change subnet, IPs, threshold, or webhook URL there and restart with `sudo systemctl restart ssh-detector ssh-responder`.

## Make targets

| Command | Purpose |
|---|---|
| `sudo make install` | First-time install: service user, directories, units |
| `sudo make config` | Open `/etc/ssh-detection-response/lab.env` in `$EDITOR` |
| `sudo make enable` | Enable and start both services |
| `sudo make disable` | Stop and disable both services |
| `make status` | Service status + last 5 alerts |
| `sudo make demo` | Reset state and print attacker-side instructions |
| `sudo make reset` | Wipe runtime state and alert history |
| `sudo make uninstall` | Remove services and runtime files (keeps logs) |

## Notes for reviewers

- The detector is pinned to read only from sshd via `journalctl -u ssh.service -u sshd.service`. There is no log file parsing.
- All file output goes under `/var/log/ssh-detection-response/` and `/var/lib/ssh-detection-response/` — standard FHS locations, owned by an unprivileged service account `ssh-dr`, never the developer's user.
- The systemd units use modern hardening directives (`ProtectSystem=strict`, `NoNewPrivileges`, `ReadWritePaths`). Run `systemd-analyze security ssh-detector` to verify.
- Fail2Ban uses `backend=systemd` so it reads the same data source as the detector — no `/var/log/auth.log` dependency.
- The detector and responder are intentionally idempotent on restart and handle log rotation / file truncation correctly.
