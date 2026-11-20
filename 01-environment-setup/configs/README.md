# Host Configuration

System configuration applied to the Ubuntu target to establish a hardened baseline before any attack simulation. Commands below are run from this directory.

## Network — `ubuntu-netplan.yaml`

Path on target: `/etc/netplan/01-lab.yaml` (mode `0600`; netplan warns about anything looser).

Two NICs, each matched by MAC and renamed to `ext0` (vmbr0, DHCP) and `int0` (vmbr1, static `10.10.10.20/24`). Replace the placeholder MACs with the real ones from `ip -br link` first.

Optional if networking already works. Read the cloud-init caveat in the [Phase 01 README](../README.md) before applying, and do it from the Proxmox console:

```bash
sudo install -m 0600 ubuntu-netplan.yaml /etc/netplan/01-lab.yaml
sudo netplan try        # rolls back automatically after 120s unless you confirm
```

## SSH daemon — `sshd_config.snippet`

Path on target: `/etc/ssh/sshd_config.d/10-lab.conf`. Edit `AllowUsers` to your login account first.

```bash
sudo install -m 0644 sshd_config.snippet /etc/ssh/sshd_config.d/10-lab.conf
sudo sshd -t            # validate; fix any error before reloading
sudo systemctl reload ssh
```

How the override works: Ubuntu's `sshd_config` starts with `Include /etc/ssh/sshd_config.d/*.conf`, and for most options sshd keeps the **first** value it reads. Drop-ins are therefore read before the main file and win; among drop-ins, lexical order decides, which is why this one is named `10-` (it beats e.g. `50-cloud-init.conf`). The package-managed `sshd_config` is never edited, so upgrades don't conflict with it.
