# cronwatch

A lightweight CLI tool to monitor, log, and alert on cron job failures with email and Slack notifications.

---

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/cronwatch.git && cd cronwatch && pip install .
```

---

## Usage

Wrap any cron job command with `cronwatch` to enable monitoring and alerts:

```bash
cronwatch --name "nightly-backup" --notify slack,email -- /usr/local/bin/backup.sh
```

Configure your notification settings in `~/.cronwatch/config.yaml`:

```yaml
slack:
  webhook_url: "https://hooks.slack.com/services/your/webhook/url"

email:
  smtp_host: "smtp.example.com"
  from: "alerts@example.com"
  to: "ops@example.com"
```

Then add it to your crontab:

```
0 2 * * * cronwatch --name "nightly-backup" -- /usr/local/bin/backup.sh
```

Logs are written to `~/.cronwatch/logs/` by default. Use `cronwatch logs` to view recent job history:

```bash
cronwatch logs --tail 20
```

---

## Options

| Flag | Description |
|------|-------------|
| `--name` | Identifier for the job |
| `--notify` | Comma-separated list of channels (`slack`, `email`) |
| `--on-failure` | Only alert on non-zero exit codes (default) |
| `--always` | Alert on every run regardless of outcome |
| `--timeout` | Kill job and alert if it exceeds N seconds |

---

## License

MIT © 2024 cronwatch contributors