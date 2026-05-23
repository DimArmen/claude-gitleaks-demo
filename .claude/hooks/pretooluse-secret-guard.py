#!/usr/bin/env python3
import sys, json, re
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
cmd = (data.get("tool_input") or {}).get("command", "")
if "secret-guard " in cmd:
    sys.exit(0)
DANGER = re.compile(
    r'(?:(?:^|[;&|]|\s)(?:docker\s+inspect|env|printenv|set)(?:\s|$))'
    r'|kubectl\s+get\s+secret'
    r'|cat\s+[^|]*\.env'
    r'|helm\s+get\s+values', re.I)
if DANGER.search(cmd):
    sys.stderr.write(
        f"secret-guard: `{cmd}` can leak secrets into the model context.\n"
        f"Re-run it wrapped:\n    secret-guard {cmd}\n"
        "Do NOT grep or inspect the output yourself - that IS the leak.\n")
    sys.exit(2)
sys.exit(0)
