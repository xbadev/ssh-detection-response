# Phase 04 — Detection & Monitoring

A long-running Python daemon that follows the systemd journal in real time, applies a per-IP sliding-window threshold, and emits structured JSONL alerts when SSH brute-force activity is detected. There's no polling interval: an alert is written as soon as the failure that crosses the threshold reaches the journal.

## What's in this phase

| File | Purpose |
|---|---|
| [`detector/ssh-bruteforce-detector.py`](detector/ssh-bruteforce-detector.py) | The detector daemon |
| [`systemd/ssh-detector.service`](systemd/ssh-detector.service) | Long-running systemd unit, hardened, runs as `ssh-dr` |

## How it works

```
journalctl -u ssh -f -o json
        │
        ▼  one JSON message per journald event
  parse_failure(MESSAGE)
        │
        ▼  matches "Failed password for [invalid user ]X from <ip> port <n>"
  SlidingDetector.record_failure(ip, user, ts)
        │
        ▼  per-IP deque, evict outside retention, count within window
  threshold reached?
        │
        ├─ no  → continue
        └─ yes → emit JSON to alerts.jsonl + start cooldown for that IP
```

The detector subprocesses `journalctl -u ssh.service -u sshd.service -o json -f -n 0`. Each line is a complete journald entry with `MESSAGE` and `__REALTIME_TIMESTAMP`, so we get authoritative timestamps without parsing date strings.

Per-IP state lives in memory as a `deque` of `(timestamp, user)` tuples, retained for `DETECT_RETENTION_SECONDS`. Each new event triggers eviction of expired entries and a count of events in the inner detection window.

### One attempt, one count

For a nonexistent account, sshd logs two lines per attempt: `Invalid user admin from <ip> port <n>` and then `Failed password for invalid user admin from <ip> port <n> ssh2`. An earlier version matched both, so every attempt against a fake username counted twice and the detector fired at half the intended threshold. It now counts only the `Failed password` line, which sshd writes exactly once per attempt for real and fake users alike. The regression is pinned by `test_two_invalid_user_attempts_count_as_two_not_four` in [`tests/test_detector.py`](../tests/test_detector.py).

## Configuration

All tunables come from `/etc/ssh-detection-response/lab.env` (sourced by the systemd unit):

| Variable | Default | Effect |
|---|---|---|
| `DETECT_THRESHOLD` | 3 | Failures required to trigger an alert. Kept below Fail2Ban's `maxretry` (5) so the alert fires before the ban cuts the attacker off |
| `DETECT_WINDOW_SECONDS` | 60 | Sliding window for the threshold check |
| `DETECT_RETENTION_SECONDS` | 600 | How long to keep per-IP state in memory |
| `LAB_LOG_DIR` | `/var/log/ssh-detection-response` | Where `alerts.jsonl` is written |
| `LAB_STATE_DIR` | `/var/lib/ssh-detection-response` | Where cooldown state is persisted |

## Alert format

One JSON object per line in `alerts.jsonl`:

```json
{
  "timestamp": "2026-05-02T22:00:00+00:00",
  "source_ip": "10.10.10.30",
  "failure_count": 3,
  "window_seconds": 60,
  "first_seen": "2026-05-02T21:59:00+00:00",
  "last_seen": "2026-05-02T22:00:00+00:00",
  "users_targeted": ["bader"],
  "host": "ubuntu-target"
}
```

## Cooldown

Once an IP triggers an alert, further events from that IP are suppressed for `DETECT_WINDOW_SECONDS`. Without this, a sustained Hydra run would generate one alert per second. Cooldowns persist across restarts via `detector-cooldowns.json` in `LAB_STATE_DIR`.

## Systemd unit

The service runs as `Type=simple` (no timer — it's a real-time follower, not a poller). It runs as the unprivileged `ssh-dr` system user, which is a member of `systemd-journal` so it can read the journal without root.

Hardening directives applied (run `systemd-analyze security ssh-detector` to verify):

- `NoNewPrivileges=yes`
- `ProtectSystem=strict` with explicit `ReadWritePaths`
- `ProtectHome=yes`, `PrivateTmp=yes`
- `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6`
- `MemoryDenyWriteExecute=yes`
- `LockPersonality=yes`

On crash, `Restart=on-failure` brings the service back, with `StartLimitBurst=5` so a parse bug cannot spin.

## Running it

After `sudo make install` and `sudo make enable` from the repo root:

```bash
sudo systemctl status ssh-detector
sudo journalctl -u ssh-detector -f      # see live detector log
tail -f /var/log/ssh-detection-response/alerts.jsonl
```

## Testing

Unit tests live in [`tests/test_detector.py`](../tests/test_detector.py) and need no root, no services, and no packages beyond Python's standard library:

```bash
make test
```

They cover message parsing (valid user, invalid user, IPv6, lines that must be ignored), the sliding window (below / at threshold, slow attacks outside the window, independent IPs), cooldown (suppression, expiry, persistence across a restart), and two end-to-end sequences of real sshd messages: the invalid-user double-count regression, and the 6-password demo attack producing exactly one alert.

For a live test, run `sudo make demo` on the target, then `run-attack.sh` on Kali, and watch `sudo journalctl -u ssh-detector -f`.

## Next

Phase 05's responder tails `alerts.jsonl` and posts each new alert to a webhook. Detection ends here.
