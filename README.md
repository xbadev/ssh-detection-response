# SSH Detection & Response — Home Lab

End-to-end SSH brute-force detection and response on Linux. A detector daemon follows the systemd journal in real time and emits structured alerts; a separate responder daemon posts them to a webhook; Fail2Ban and UFW enforce. One config file drives everything, `make` installs and runs it, and `make test` checks the logic without a VM.

The lab runs on a Proxmox VE hypervisor with two VMs on an isolated internal subnet: Ubuntu Server as the target, Kali Linux as the attacker. Companion repo: [rdp-detection-response](https://github.com/xbadev/rdp-detection-response) (same pattern on Windows).

## Environment

| Component | Detail |
|-----------|--------|
| Hypervisor | Proxmox VE (see [proxmox-homelab](https://github.com/xbadev/proxmox-homelab)) |
| Target | Ubuntu Server 24.04 LTS — `10.10.10.20` |
| Attacker | Kali Linux — `10.10.10.30` |
| Internal network | `10.10.10.0/24` on Proxmox bridge `vmbr1` (no uplink) |
| External network | Proxmox bridge `vmbr0` (DHCP, internet egress + management) |
| Attack surface | SSH (port 22) |
| Enforcement | UFW (network) + Fail2Ban (host, journal backend) |
| Detection | Python daemon following `journalctl -u ssh -f -o json` |
| Response | Python daemon tailing JSONL alerts → webhook POST with retries |
| Latency | Event-driven, no polling interval: the alert fires on the failure that crosses the threshold |

## Quick demo

On the Ubuntu target:

```bash
sudo apt-get install -y git python3 rsync fail2ban
git clone https://github.com/xbadev/ssh-detection-response.git
cd ssh-detection-response
make test              # 20 unit + end-to-end tests, no root needed
sudo make install
sudo make config       # set ALERT_WEBHOOK_URL, MGMT_SUBNET, LAB_USER
sudo ./03-defense-hardening/install-ufw.sh
sudo install -m 0644 03-defense-hardening/jail.local /etc/fail2ban/jail.local && sudo systemctl restart fail2ban
sudo make enable
sudo make demo
```

On Kali:

```bash
git clone https://github.com/xbadev/ssh-detection-response.git
cd ssh-detection-response
./02-attack-simulation/run-attack.sh
```

One run sends six wrong passwords. On the target you should see, in order:

1. Failure 3: `ssh-detector` writes an alert, `ssh-responder` posts it to the webhook
2. Failure 5: Fail2Ban bans `10.10.10.30`
3. Failure 6: Hydra reports connection errors (the ban is working)

Watch it live with `sudo journalctl -u ssh-detector -u ssh-responder -f`; confirm the ban with `sudo fail2ban-client status sshd`. `sudo make demo` resets everything, including the Fail2Ban ban, for the next run.

## Phases

| # | Phase | What it does |
|---|-------|---|
| 01 | [Environment Setup](./01-environment-setup/) | Proxmox dual-NIC layout, netplan matched by MAC, sshd hardening drop-in |
| 02 | [Attack Simulation](./02-attack-simulation/) | `run-attack.sh`: 6-password Hydra run sized to trip both the detector and Fail2Ban |
| 03 | [Defense Hardening](./03-defense-hardening/) | UFW with a lockout guard, Fail2Ban on the journal; thresholds ordered so alerting happens before banning |
| 04 | [Detection & Monitoring](./04-detection-monitoring/) | Real-time journal follower, per-IP sliding window, JSONL alerts, hardened systemd unit |
| 05 | [Automated Response](./05-automated-response/) | Real-time responder: tails JSONL, retries webhook delivery, per-IP cooldown |

## Architecture

```
┌──────────────┐  SSH brute-force   ┌──────────────────────────────────────────────┐
│ Kali         │ ─────────────────► │ Ubuntu target  10.10.10.20                   │
│ 10.10.10.30  │                    │                                              │
└──────────────┘                    │   sshd ──writes failures──► journald         │
       ▲                            │                               │    │         │
       │   ban (failure 5)          │            ┌──────────────────┘    │         │
       └────────────────────────────┼─ Fail2Ban ◄┘                       │ -f      │
                                    │                                    ▼         │
                                    │                             ssh-detector     │
                                    │                       (alert at failure 3)   │
                                    │                                    │         │
                                    │                                    ▼         │
                                    │                              alerts.jsonl    │
                                    │                                    │         │
                                    │                                    ▼         │
                                    │                             ssh-responder ───┼──► webhook ──► Discord
                                    └──────────────────────────────────────────────┘
```

Detection and response are split on purpose: the detector owns the event stream, the responder owns the secret (webhook URL) and network egress. Either side can be developed, tested, or replaced on its own, the same split SOAR platforms make between detection and action.

## Configuration

All settings live in `/etc/ssh-detection-response/lab.env` (mode `0640`, root:ssh-dr), loaded by both systemd units via `EnvironmentFile=`. See [`lab.env.example`](./lab.env.example) for every variable and why each default is what it is.

```bash
sudo make config       # edit lab.env, then restart the services as prompted
```

## Make targets

| Command | Purpose |
|---|---|
| `make test` | Run the test suite (no root, standard library only) |
| `sudo make install` | Service user, directories, runtime files in `/opt`, systemd units |
| `sudo make config` | Edit `/etc/ssh-detection-response/lab.env` |
| `sudo make enable` | Enable and start both services (warns if the webhook is still the placeholder) |
| `sudo make disable` | Stop and disable both services |
| `make status` | Service status + last 5 alerts |
| `sudo make reset` | Wipe alert history and state, clear Fail2Ban bans |
| `sudo make demo` | `reset`, then print the attacker-side command |
| `sudo make uninstall` | Remove services and runtime files (keeps logs, config, and the `ssh-dr` user) |

## Tests

`make test` runs [`tests/`](./tests/): 20 tests covering log parsing, the sliding window, cooldowns and their persistence, webhook retry behavior, and an end-to-end run of the real responder against a local fake webhook server. Details are in the Phase 04 and Phase 05 READMEs.

## Notes for reviewers

- The detector reads only sshd's journal entries (`journalctl -u ssh.service -u sshd.service`); there's no log-file parsing and no dependency on `/var/log/auth.log`.
- It counts exactly one line per failed attempt. sshd logs two lines for a nonexistent username; counting both would double-count, and a regression test pins that.
- Runtime output goes to `/var/log/ssh-detection-response/` and `/var/lib/ssh-detection-response/`, owned by the unprivileged `ssh-dr` service account, which reads the journal through `systemd-journal` group membership rather than root.
- The units use systemd sandboxing (`ProtectSystem=strict`, `NoNewPrivileges`, `MemoryDenyWriteExecute`, restricted address families). `systemd-analyze security ssh-detector` scores them.
- The responder survives log rotation and truncation, persists its read offset so a restart doesn't re-send alerts, and retries failed webhook POSTs with backoff instead of silently dropping them.
