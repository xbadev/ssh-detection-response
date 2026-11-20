# Phase 05 — Automated Response

A second long-running Python daemon that tails `alerts.jsonl` (written by Phase 04) and posts each new alert to a webhook in real time. It owns the network egress and the webhook secret; the detector owns the event stream. Either side can change without affecting the other.

## What's in this phase

| File | Purpose |
|---|---|
| [`responder/ssh-responder.py`](responder/ssh-responder.py) | The responder daemon |
| [`systemd/ssh-responder.service`](systemd/ssh-responder.service) | Long-running systemd unit, hardened, runs as `ssh-dr` |

## How it works

```
alerts.jsonl  (written by ssh-detector)
        │
        ▼  open + seek to last persisted byte offset
  follow loop: readline → JSON → check inode/size
        │
        ▼  for each new alert
  cooldown check (per source IP, RESPONSE_COOLDOWN_SECONDS)
        │
        ├─ in cooldown → skip, advance offset
        └─ not in cooldown → format + POST (with retries) → record cooldown → advance offset
```

The follower handles three corner cases that bite naive `tail -f`-style code:

1. **File rotation**: detected via inode change. Reopens.
2. **Truncation**: detected via the file shrinking below the current offset. Rewinds to 0.
3. **Webhook failure**: any network error (refused, timeout, HTTP error) is retried in place with exponential backoff (1s, 2s, ...) up to `RESPONSE_WEBHOOK_RETRIES` attempts. If every attempt fails, the responder logs `giving up on notification`, advances the offset, and moves on, so one dead webhook can't stall every alert queued behind it. The alert itself is never lost: it stays in `alerts.jsonl` and in the detector's journal output.

## Configuration

Sourced from `/etc/ssh-detection-response/lab.env`:

| Variable | Default | Effect |
|---|---|---|
| `ALERT_WEBHOOK_URL` | _(required)_ | Discord-compatible webhook URL that accepts `{"content": "..."}`. The shipped `REPLACE_ME` placeholder is treated as unset |
| `RESPONSE_COOLDOWN_SECONDS` | 300 | Per-IP suppression after one notification |
| `RESPONSE_WEBHOOK_RETRIES` | 3 | Delivery attempts per alert before giving up |
| `LAB_LOG_DIR` | `/var/log/ssh-detection-response` | Reads `alerts.jsonl` from here |
| `LAB_STATE_DIR` | `/var/lib/ssh-detection-response` | Persists offset and cooldown state here |
| `RESPONDER_DRY_RUN` | _(unset)_ | Set to `1` to log instead of posting |

## Webhook message format

Default Discord-friendly Markdown:

```
🚨 **SSH brute-force detected**
Host: `ubuntu-target`
Source IP: `10.10.10.30`
Failures: `3` in `60s`
Users targeted: `bader`
Last seen: `2026-05-02T22:00:00+00:00`
```

Slack accepts the same `{"content": "..."}` shape if its incoming-webhook is configured for plain content; for richer formatting, swap `format_alert()` for a Slack Block Kit payload.

## Cooldown

Independent from the detector's cooldown — the detector throttles event-to-alert, the responder throttles alert-to-notification. Both are necessary. The responder cooldown defaults to 5 minutes per source IP so a sustained attack does not spam the webhook channel.

State persists across restarts in `responder-cooldowns.json` and `responder-offset.json` in `LAB_STATE_DIR`.

## Secret handling

`ALERT_WEBHOOK_URL` is set in `/etc/ssh-detection-response/lab.env` (mode `0640`, group `ssh-dr`). The systemd unit sources that file via `EnvironmentFile=`, so the secret reaches the process as an environment variable but is never written to disk by the service or committed to the repo.

The committed file is [`lab.env.example`](../lab.env.example) at the repo root with the placeholder URL — `lab.env` itself is gitignored.

## Running it

After `sudo make install` and `sudo make enable`:

```bash
sudo systemctl status ssh-responder
sudo journalctl -u ssh-responder -f
```

Dry-run (log the message instead of posting it): add `RESPONDER_DRY_RUN=1` to `/etc/ssh-detection-response/lab.env`, then `sudo systemctl restart ssh-responder`. Remove the line to go live again.

## Testing

Tests live in [`tests/test_responder.py`](../tests/test_responder.py) and run with `make test` (no root, standard library only):

- **Unit**: message formatting, the `REPLACE_ME` placeholder being treated as unset, retry-then-succeed, and give-up-after-N-attempts.
- **End to end**: the real responder runs as a subprocess against a local fake webhook server; the test writes alerts into `alerts.jsonl` and asserts the right POSTs arrive, that a repeat IP is suppressed by cooldown, and that a restart doesn't re-send alerts already delivered (offset persistence).

To check the live service on the target without waiting for an attack, append a fake alert and watch the responder pick it up:

```bash
echo '{"timestamp":"2026-01-01T12:00:00+00:00","source_ip":"203.0.113.7","failure_count":3,"window_seconds":60,"first_seen":"2026-01-01T11:59:58+00:00","last_seen":"2026-01-01T12:00:00+00:00","users_targeted":["test"],"host":"manual-test"}' \
  | sudo tee -a /var/log/ssh-detection-response/alerts.jsonl
sudo journalctl -u ssh-responder -n 5
```

`203.0.113.7` is a reserved documentation address, so the test alert can't be mistaken for real traffic.

## Pipeline closure

This phase closes the automation loop:

```
Hydra → sshd → journald → ssh-detector → alerts.jsonl → ssh-responder → webhook → Discord
                                                  └─ Fail2Ban (parallel) → IP ban
```

Detection and response are decoupled, observable end-to-end via `journalctl -u ssh-detector -u ssh-responder -f`, and re-runnable in seconds via `sudo make demo`.
