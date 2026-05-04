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
        └─ not in cooldown → format + POST → record cooldown → advance offset
```

The follower handles three corner cases that bite naive `tail -f`-style code:

1. **File rotation** — detected via inode change. Reopens.
2. **Truncation** — detected via size shrinking below current offset. Rewinds to 0.
3. **Network failure** — webhook POST raises `URLError`. The responder logs the error and **does not advance the offset**, so the next attempt retries the same alert.

## Configuration

Sourced from `/etc/ssh-detection-response/lab.env`:

| Variable | Default | Effect |
|---|---|---|
| `ALERT_WEBHOOK_URL` | _(required)_ | Discord-compatible webhook URL — accepts `{"content": "..."}` |
| `RESPONSE_COOLDOWN_SECONDS` | 300 | Per-IP suppression after one notification |
| `LAB_LOG_DIR` | `/var/log/ssh-detection-response` | Reads `alerts.jsonl` from here |
| `LAB_STATE_DIR` | `/var/lib/ssh-detection-response` | Persists offset and cooldown state here |
| `RESPONDER_DRY_RUN` | _(unset)_ | Set to `1` to log instead of posting |

## Webhook message format

Default Discord-friendly Markdown:

```
🚨 **SSH brute-force detected**
Host: `ubuntu-target`
Source IP: `10.10.10.30`
Failures: `5` in `60s`
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

Dry-run for testing without spamming a real webhook:

```bash
sudo systemctl set-environment RESPONDER_DRY_RUN=1
sudo systemctl restart ssh-responder
```

## Testing

The responder is verified by an end-to-end harness that spins up a local HTTP server, writes alerts into `alerts.jsonl`, and asserts the responder posts the right payloads (and respects cooldown). The harness lives in the repo's CI scripts; the manual equivalent is:

```bash
# Terminal 1 — fake webhook
python3 -m http.server 8080

# Terminal 2 — point responder at it
sudo systemctl set-environment ALERT_WEBHOOK_URL=http://127.0.0.1:8080
sudo systemctl restart ssh-responder

# Terminal 3 — drop a test alert
echo '{"timestamp":"2026-05-02T22:00:00+00:00","source_ip":"1.2.3.4","failure_count":5,"window_seconds":60,"first_seen":"2026-05-02T21:59:00+00:00","last_seen":"2026-05-02T22:00:00+00:00","users_targeted":["bader"],"host":"test"}' | sudo tee -a /var/log/ssh-detection-response/alerts.jsonl

# Terminal 1 should see a POST.
```

## Pipeline closure

This phase closes the automation loop:

```
Hydra → sshd → journald → ssh-detector → alerts.jsonl → ssh-responder → webhook → Discord
                                                  └─ Fail2Ban (parallel) → IP ban
```

Detection and response are decoupled, observable end-to-end via `journalctl -u ssh-detector -u ssh-responder -f`, and re-runnable in seconds via `sudo make demo`.
