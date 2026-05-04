# Host Configuration

System configuration applied to the Ubuntu target to establish a hardened baseline before any attack simulation.

## Network — `ubuntu-netplan.yaml`

Path on target: `/etc/netplan/01-lab.yaml` (mode `0600` per netplan requirements).

Apply with:

```bash
sudo install -m 0600 ubuntu-netplan.yaml /etc/netplan/01-lab.yaml
sudo netplan generate
sudo netplan apply
```

Two NICs, each matched by MAC, renamed to `ext0` (vmbr0, DHCP) and `int0` (vmbr1, static `10.10.10.20/24`). Replace the placeholder MAC addresses with the actual values from `ip -br link` before applying.

## SSH daemon — `sshd_config.snippet`

Path on target: `/etc/ssh/sshd_config.d/10-lab.conf`.

Apply with:

```bash
sudo install -m 0644 sshd_config.snippet /etc/ssh/sshd_config.d/10-lab.conf
sudo sshd -t                        # validate before reloading
sudo systemctl reload ssh
```

Drop-in files in `/etc/ssh/sshd_config.d/` are loaded after `sshd_config` and override matching directives. This pattern survives distribution upgrades because the package-managed `sshd_config` is left untouched.
