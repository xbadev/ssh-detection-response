# Phase 03 — Defense Hardening

Two complementary defensive controls on the Ubuntu target. UFW limits *who* can reach SSH at all; Fail2Ban watches the journal and bans IPs that keep failing once they're past UFW.

These are deliberately overlapping. UFW alone does not stop an attacker who is already inside the allowed subnet — the lab attacker is. Fail2Ban catches that case at the host. In production the two layers protect against different threat models; in the lab they demonstrate defense-in-depth.

## What's in this phase

| File | Purpose |
|---|---|
| [`install-ufw.sh`](install-ufw.sh) | Resets and configures UFW, allowing SSH only from `INTERNAL_SUBNET` |
| [`jail.local`](jail.local) | Fail2Ban SSH jail with `backend=systemd` |

## UFW — network firewall

```bash
sudo ./install-ufw.sh
```

The script reads `INTERNAL_SUBNET` from `/etc/ssh-detection-response/lab.env`, resets UFW, sets `default deny incoming`, then opens TCP/22 only from that subnet. After it runs, port 22 is unreachable from any other source, including the host's external NIC.

Manual equivalent:

```bash
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.10.10.0/24 to any port 22 proto tcp
sudo ufw --force enable
```

## Fail2Ban — log-driven IP bans

Install:

```bash
sudo apt-get install -y fail2ban
sudo install -m 0644 jail.local /etc/fail2ban/jail.local
sudo systemctl enable --now fail2ban
sudo systemctl restart fail2ban
```

Configuration:

| Setting | Value | Reason |
|---|---|---|
| `backend` | `systemd` | Reads journald directly, matching the Phase 04 detector |
| `maxretry` | 3 | Sensitive enough to catch a real attack |
| `findtime` | 60s | Three failures within a minute is the trigger window |
| `bantime` | 600s | 10-minute IP ban — long enough to be obviously effective in a demo, short enough for repeat runs |

The `backend = systemd` line is the important one on modern Ubuntu — newer images often ship without `/var/log/auth.log` because the default logger is journald. Older Fail2Ban tutorials still reference the auth.log file path and silently fail on those systems.

## Validation

```bash
sudo ufw status verbose             # rule on 22 from internal subnet only
sudo fail2ban-client status sshd    # active jail, current banned IPs
```

After Hydra runs from Kali a few times, expect to see `Currently banned: 1` and `10.10.10.30` in the banned list.

To unban during testing:

```bash
sudo fail2ban-client set sshd unbanip 10.10.10.30
```

## Next

Phase 04 adds a detection layer that observes the *same* journal Fail2Ban is reading, and emits structured alerts. The two run side-by-side: Fail2Ban enforces, the detector reports.
