# SSH Detection & Response — Home Lab

Built an end-to-end security automation pipeline on a Linux environment: from network segmentation and SSH hardening, through brute-force simulation, layered defense with UFW and Fail2Ban, Python-based detection, to automated webhook alerting — using native Linux tooling, Python, and systemd.

## Environment

| Component | Detail |
|-----------|--------|
| Attacker | Kali Linux VM |
| Target | Ubuntu Server 24.04 LTS |
| Network | VirtualBox Host-Only + NAT (dual-NIC) |
| Attack Surface | SSH (port 22) |
| Defense | UFW + Fail2Ban |
| Detection | Python script monitoring `/var/log/auth.log` |
| Alerting | Discord webhook via systemd service |

## Phases

| # | Phase | Description |
|---|-------|-------------|
| 01 | [Environment Setup](./01-environment-setup/) | Configured dual-NIC network segmentation, static internal addressing, and hardened SSH access. |
| 02 | [Attack Simulation](./02-attack-simulation/) | Simulated SSH brute-force from Kali using Hydra and observed authentication failures in system logs. |
| 03 | [Defense Hardening](./03-defense-hardening/) | Deployed UFW to restrict SSH to the internal network and Fail2Ban to auto-ban brute-force sources. |
| 04 | [Detection & Monitoring](./04-detection-monitoring/) | Built a Python detection script for SSH brute-force patterns with state tracking, running continuously via systemd. |
| 05 | [Automated Response](./05-automated-response/) | Automated Discord webhook notifications triggered by detection alerts, completing the automation pipeline. |

Each phase has its own README with step-by-step documentation and inline evidence screenshots. Start at Phase 01 and progress sequentially.
