# claude-gitleaks-demo

A minimal demo of **tool-boundary secret redaction for AI agents**: secrets are intercepted and withheld from the model context *before* they can be read, not after.

## The problem

When an AI agent runs `docker inspect`, `cat .env`, or similar commands, the raw output — including plaintext secrets — lands directly in the model's context window. Secrets that enter the context can be logged, cached, or leaked in subsequent tool calls.

## The solution

Two complementary layers:

| Layer | File | What it does |
|---|---|---|
| **PreToolUse hook** | `.claude/hooks/pretooluse-secret-guard.py` | Blocks known secret-exposing commands before they run; instructs the agent to wrap them in `secret-guard` instead |
| **Output wrapper** | `secret-guard` | Runs the command, scans stdout with gitleaks, and withholds the full output if secrets are found — returning only redacted rule/finding summaries |

## Files

```
.
├── docker_inspect_dirty.json        # Fake container config with test secrets
├── gitleaks-custom.toml             # Extends default rules; adds connection-string rule
├── secret-guard                     # Bash wrapper — redacts at the tool boundary
└── .claude/
    ├── settings.json                # Wires PreToolUse hook into Claude Code
    └── hooks/
        └── pretooluse-secret-guard.py   # Hook: blocks raw secret-exposing commands
```

## Requirements

- [gitleaks](https://github.com/gitleaks/gitleaks) on `$PATH`
- Claude Code (for the hook)

## Demo

**Baseline — direct gitleaks scan (redacted output):**
```bash
cat docker_inspect_dirty.json | gitleaks detect --pipe -c gitleaks-custom.toml --no-banner -v --redact
```

**Guarded — wrapper withholds output if secrets are found:**
```bash
SECRET_GUARD_CONFIG=$PWD/gitleaks-custom.toml ./secret-guard cat docker_inspect_dirty.json
```

Expected output:
```
⛔ secret-guard blocked output of: cat docker_inspect_dirty.json
   gitleaks flagged 5 secret(s). Raw output WITHHELD from model context.
   ─────────────────────────────────────────────────────────────
    stripe-access-token               "STRIPE_SECRET_KEY=REDACTED...
    connection-string-credentials     "DATABASE_URL=REDACTEDdb.internal...
    generic-api-key                   "STRIPE_SECRET_KEY=REDACTED"
    generic-api-key                   "STRIPE_WEBHOOK_SECRET=REDACTED"
    generic-api-key                   "PAYLOAD_SECRET=REDACTED"
   ─────────────────────────────────────────────────────────────
   override (audited):  SECRET_GUARD_ALLOW=1 secret-guard cat docker_inspect_dirty.json
```

**Override (audited escape hatch):**
```bash
SECRET_GUARD_ALLOW=1 SECRET_GUARD_CONFIG=$PWD/gitleaks-custom.toml ./secret-guard cat docker_inspect_dirty.json
```

## Secret types caught

| Rule ID | Matched env var |
|---|---|
| `stripe-access-token` | `STRIPE_SECRET_KEY` |
| `generic-api-key` | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `PAYLOAD_SECRET` |
| `connection-string-credentials` | `DATABASE_URL` (postgres password) |

> **Note:** All secrets in this repo are fake test values. Do not use real credentials.
