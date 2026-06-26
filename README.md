# GitShodanKey v2

Fast async tool to find leaked API keys in public GitHub/GitLab repositories.

Supports **11 API key types**, concurrent async search, live Rich terminal UI, HTML reports, and Telegram/Discord notifications.

## Supported Services

| Service | Key Pattern | Validator |
|---------|------------|-----------|
| Shodan | 32 alphanumeric chars | API info endpoint |
| VirusTotal | 64 hex chars | API quota check |
| Censys | UUID format | Account endpoint |
| AWS | `AKIA[A-Z0-9]{16}` | Format validation |
| Stripe | `sk_live_...` | Account endpoint |
| OpenAI | `sk-[A-Za-z0-9]{48}` | Models endpoint |
| Slack | `xoxb-...` | auth.test |
| Twilio | `SK[a-f0-9]{32}` | Format validation |
| SendGrid | `SG....` | User profile |
| Telegram Bot | `\d+:AA...` | getMe |
| GitHub Token | `ghp_...` | User endpoint |

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Scan all services, output HTML report
gitshodankey scan --token <github_token> --output report --format html

# Scan specific services only
gitshodankey scan --token <github_token> --services shodan,virustotal,aws

# Include GitLab
gitshodankey scan --token <github_token> --gitlab-token <gitlab_token>

# With Telegram notifications
gitshodankey scan --token <github_token> --notify-telegram <bot_token> <chat_id>

# With Discord notifications
gitshodankey scan --token <github_token> --notify-discord <webhook_url>

# Resume interrupted scan
gitshodankey scan --token <github_token> --resume

# Skip validation (faster)
gitshodankey scan --token <github_token> --no-validate

# Use config file
gitshodankey scan --config config.yaml

# List supported services
gitshodankey list-services
```

## Config File

Copy `config.example.yaml` and fill in your tokens:

```yaml
github_token: "ghp_..."
gitlab_token: "glpat-..."
services:
  - shodan
  - virustotal
  - aws
concurrency: 10
output_file: results
output_format: html
telegram_token: ""
telegram_chat_id: ""
discord_webhook_url: ""
```

## Output Formats

- `html` — Dark-themed interactive report (default)
- `json` — Machine-readable JSON
- `csv` — Spreadsheet-compatible
- `txt` — Plain text

## Environment Variables

```bash
export GITHUB_TOKEN=ghp_...
export GITLAB_TOKEN=glpat-...
export TELEGRAM_TOKEN=...
export TELEGRAM_CHAT_ID=...
export DISCORD_WEBHOOK_URL=...
```

## Running Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Disclaimer

This tool is for security research and educational purposes only. Use responsibly and only on repositories you have permission to analyze. Do not use discovered keys for unauthorized access.
