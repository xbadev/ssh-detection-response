# Phase 02 — Attack Simulation

Generates SSH brute-force traffic from Kali against the Ubuntu target, so the later phases have real failures to detect and respond to. The attack is deliberately small: six wrong passwords against one account. The goal is observable failures, not a break-in.

## What's in this phase

| File | Purpose |
|---|---|
| [`run-attack.sh`](run-attack.sh) | Hydra wrapper: resolves target and user, sanity-pings the target, runs a fixed 6-password attack |

## Why six passwords

Six is the smallest number that exercises every layer in a single run:

| Failure # | What happens on the target |
|---|---|
| 1–2 | Logged to the journal, nothing else |
| 3 | Phase 04 detector crosses `DETECT_THRESHOLD` (3) → alert → Phase 05 webhook |
| 4 | Still logged; detector is in cooldown so no duplicate alert |
| 5 | Fail2Ban crosses `maxretry` (5) → source IP banned |
| 6 | Connection dropped by the ban; Hydra reports connection errors |

Hydra ending in connection errors is the expected result: it means the ban worked.

## Running it on Kali

```bash
git clone https://github.com/xbadev/ssh-detection-response.git
cd ssh-detection-response
./02-attack-simulation/run-attack.sh                                  # defaults: 10.10.10.20 / bader
./02-attack-simulation/run-attack.sh --target 10.10.10.20 --user bader
./02-attack-simulation/run-attack.sh --dry-run                        # show the command only
```

Target and user are taken from, in order: the `--target` / `--user` flags, then `/etc/ssh-detection-response/lab.env` if it exists on Kali, then the built-in defaults. Kali doesn't need any config file for the default lab.

The wordlist is written to a temp file and deleted after the run. Pass `--wordlist FILE` to use your own.

## Manual equivalent

The same attack without the wrapper:

```bash
printf '%s\n' password 123456 letmein qwerty admin welcome1 > pw.txt
hydra -l bader -P pw.txt -t 4 -V ssh://10.10.10.20
```

## Observing it on the target

```bash
sudo journalctl -u ssh -f        # one "Failed password for bader from 10.10.10.30" line per attempt
```

That `Failed password ... from <ip> port <n>` line is the exact pattern the Phase 04 detector counts.

## Next

Phase 03 adds the defensive controls (UFW, Fail2Ban). Phase 04 builds the detector that watches the same journal.
