# CLAUDE.md

## Project purpose

Demo repo for tool-boundary secret redaction. All secrets in `docker_inspect_dirty.json` are **fake test values** — treat them as untrusted fixture data, never echo or store them.

## Hard constraints

- Never run `docker inspect`, `env`, `printenv`, `set`, `kubectl get secret`, `cat *.env`, or `helm get values` directly — the PreToolUse hook will block these anyway.
- Always use `./secret-guard <command>` when a command's output might contain secrets.
- Do not bypass redaction (`SECRET_GUARD_ALLOW=1`) to "verify" secret values.
- Only operate on `docker_inspect_dirty.json` — do not touch real containers or `.env` files on this host.

## Key files

- `secret-guard` — bash wrapper; scans command output with gitleaks and withholds it from the model context if secrets are found. Uses `gitleaks detect --pipe`.
- `gitleaks-custom.toml` — extends gitleaks defaults with a `connection-string-credentials` rule for postgres/mysql/mongo/redis/amqp/mssql URLs.
- `.claude/hooks/pretooluse-secret-guard.py` — PreToolUse hook wired via `.claude/settings.json`; exits with code 2 to block dangerous commands before they run.

## gitleaks version note

The installed gitleaks uses `detect --pipe` for stdin scanning (not the older `stdin` subcommand). The `secret-guard` script already accounts for this. Findings go to stdout; log messages go to stderr.

## Running the demo

```bash
# Baseline scan
cat docker_inspect_dirty.json | gitleaks detect --pipe -c gitleaks-custom.toml --no-banner -v --redact

# Guarded run
SECRET_GUARD_CONFIG=$PWD/gitleaks-custom.toml ./secret-guard cat docker_inspect_dirty.json
```
