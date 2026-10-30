#!/usr/bin/env bash
# Shared helper: read the hook JSON payload from stdin and print tool_input.file_path.
# Works with jq if installed, otherwise python3, otherwise a sed fallback.
payload="$(cat)"

if command -v jq >/dev/null 2>&1; then
  printf '%s' "$payload" | jq -r '.tool_input.file_path // empty'
elif command -v python3 >/dev/null 2>&1; then
  printf '%s' "$payload" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))'
else
  printf '%s' "$payload" | sed -nE 's/.*"file_path"[[:space:]]*:[[:space:]]*"([^"]*)".*/\1/p' | head -1
fi
