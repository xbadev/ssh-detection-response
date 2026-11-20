# Phase 03 — Defense Hardening

Two defensive controls on the Ubuntu target. UFW limits *who* can reach SSH at all; Fail2Ban watches the journal and bans IPs that keep failing after they get past UFW.

The overlap is deliberate. UFW alone doesn't stop an attacker who is already inside an allowed subnet, and the lab attacker is. Fail2Ban catches that case at the host. In production the two layers cover different threat models (internet vs. inside); in the lab they show defense in depth.

## What's in this phase

| File | Purpose |
|---|---|
| [`install-ufw.sh`](install-ufw.sh) | Default-deny inbound; allow SSH only from the lab subnet and your management subnet; refuses to run if it would cut off your current SSH session |
| [`jail.local`](jail.local) | Fail2Ban SSH jail reading the systemd journal |

## UFW — network firewall

```bash
sudo ./03-defense-hardening/install-ufw.sh
```

The script reads two subnets from `/etc/ssh-detection-response/lab.env`:

| Variable | Default | Why SSH is allowed from it |
|---|---|---|
| `INTERNAL_SUBNET` | `10.10.10.0/24` | The lab subnet on `vmbr1`, where Kali attacks from |
| `MGMT_SUBNET` | `192.168.1.0/24` | Where *you* SSH in from to administer the VM (usually your home LAN on `vmbr0`) |

**Set `MGMT_SUBNET` to your real home LAN before running.** Without it, enabling UFW drops your own SSH session.

### Lockout guard

Before changing anything, the script lists every established SSH session on the box (`ss`) and checks each source IP against both subnets. If any session would be cut off, it stops with exit code 3 and prints the offending IPs. `--force` overrides the guard (use it from the Proxmox console, where SSH sessions don't matter).

Manual equivalent of what it applies:

```bash
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.10.10.0/24  to any port 22 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw --force enable
```

## Fail2Ban — log-driven IP bans

```bash
sudo apt-get install -y fail2ban
sudo install -m 0644 03-defense-hardening/jail.local /etc/fail2ban/jail.local
sudo systemctl enable --now fail2ban
sudo systemctl restart fail2ban
```

| Setting | Value | Reason |
|---|---|---|
| `backend` | `systemd` | Reads the journal directly, same source as the Phase 04 detector; works with no `/var/log/auth.log` |
| `maxretry` | 5 | Deliberately above the detector's threshold (3), see below |
| `findtime` | 60s | Five failures within a minute triggers the ban |
| `bantime` | 600s | 10 minutes: obvious in a demo, short enough to recover from |

### Why Fail2Ban bans at 5 and the detector alerts at 3

Both components read the same journal. If Fail2Ban banned at 3 (or anything at or below the detector's threshold), it would cut the attacker off before the detector saw enough failures to alert, so the notification half of the pipeline would never fire. With the detector at 3 and Fail2Ban at 5, one attack produces an alert first and then a ban: **notify, then enforce**.

## Validation

```bash
sudo ufw status verbose             # 22/tcp allowed only from the two subnets
sudo fail2ban-client status sshd    # jail active; banned list after an attack
```

After one run of `run-attack.sh` from Kali, expect `Currently banned: 1` with `10.10.10.30` listed.

`sudo make reset` (and `make demo`) clears all Fail2Ban bans so you can run the attack again immediately. To unban by hand:

```bash
sudo fail2ban-client set sshd unbanip 10.10.10.30
```

## Next

Phase 04 adds the detector, which watches the same journal Fail2Ban reads and emits structured alerts.
