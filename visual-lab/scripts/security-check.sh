#!/bin/bash
# Static security checks for a lab (or any compose project) before it is tested, committed,
# pushed or deployed. test-isolated.sh runs it before `up`. Exits 1 on any FAIL.
#
#   security-check.sh <project dir>
#
# FAIL: a host port not bound to 127.0.0.1 / ::1 (Docker's iptables rules bypass ufw, so the
#       app would be reachable on the server's public IP, skipping Cloudflare); a password,
#       secret, token or key with a non-empty fallback in compose or app config, or a value
#       in .env.example (placeholders like your_..._here are fine); a literal password in
#       compose (KEY: value, user:pass@ URLs); .env, pipeline-run.sh (when present) or
#       claude_logs/ tracked or not ignored by git, now or in history.
# warn: a service other than rixus-frontend / cloudflared on tunnel-net; an image-based service (database, broker, …) sharing a network with the public
#       frontend; admin / reset / flush style routes, which must need a token and be off by
#       default; `curl -X POST|DELETE` examples for such routes in docs.
set -uo pipefail

DIR="$(cd "${1:?project directory}" && pwd)"
cd "$DIR"
failed=0
ok() { echo "ok   $*"; }
fail() { echo "FAIL $*"; failed=1; }
warn() { echo "warn $*"; }

SECRET='[A-Z0-9_]*(PASSWORD|PASSWD|SECRET|TOKEN|API_KEY|PRIVATE_KEY|ACCESS_KEY)[A-Z0-9_]*'

# Compose: resolved ports and networks. The test override is merged in when present.
files=(-f docker-compose.yml)
[ -f docker-compose.test.yml ] && files+=(-f docker-compose.test.yml)
for set in "main:-f docker-compose.yml" "test:${files[*]}"; do
  label="${set%%:*}"; args="${set#*:}"
  [ "$label" = test ] && [ ! -f docker-compose.test.yml ] && continue
  # shellcheck disable=SC2086
  if ! json="$(docker compose $args config --format json 2>&1)"; then
    fail "docker compose config ($label) failed: $(printf '%s' "$json" | tail -n1)"
    continue
  fi
  printf '%s' "$json" | python3 -I -c '
import json, sys
label = sys.argv[1]
cfg = json.load(sys.stdin)
public = lambda s: s.get("container_name") == "rixus-frontend"
tunnel = lambda s: s.get("container_name") == "cloudflared-tunnel" or (s.get("image") or "").startswith("cloudflare/cloudflared")
services = cfg.get("services", {})
bad = 0
for name, svc in services.items():
    for p in svc.get("ports") or []:
        host_ip = p.get("host_ip", "")
        published, target = p.get("published"), p.get("target")
        where = host_ip or "all interfaces"
        if published and host_ip not in ("127.0.0.1", "::1"):
            print(f"FAIL {label}: {name} publishes {published}->{target} on {where}: bind it to 127.0.0.1")
            bad = 1
    nets = svc.get("networks") or {}
    if "tunnel-net" in nets and not public(svc) and not tunnel(svc):
        print(f"warn {label}: {name} joins tunnel-net; only rixus-frontend should, unless the tunnel routes to it on purpose")
front = next((s for s in services.values() if s.get("container_name") == "rixus-frontend"), None)
if front is None and label == "main":
    front = services.get("frontend") or services.get("web")
if front is not None:
    fnets = set(front.get("networks") or {})
    for name, svc in services.items():
        if svc is front or "build" in svc or tunnel(svc):
            continue
        shared = fnets & set(svc.get("networks") or {})
        if shared:
            image = svc.get("image")
            print(f"warn {label}: {name} ({image}) shares {sorted(shared)} with the public frontend; put it on an internal backend network")
if not bad:
    print(f"ok   {label}: host ports bound to loopback")
sys.exit(bad)
' "$label" || failed=1
done

# Fallback values for secrets: ${VAR:-value} / ${VAR-value} in compose, ${VAR:value} in Spring
# config, and real values in the committed .env.example.
sfail=0
hits="$(grep -nHE "\\\$\\{${SECRET}:?-[^}]+\\}" docker-compose*.yml 2>/dev/null)"
[ -n "$hits" ] && sfail=1 && fail "secret with a fallback value in compose (use \${VAR:?Set VAR in .env}):" && sed 's/^/      /' <<< "$hits"
hits="$(grep -nHE "^[^#]*(^|[[:space:]-])${SECRET}(:|=) *[\"']?[^\$\"' {][^ ]*|://[^:/@ ]+:[^\$@/ ]+@" docker-compose*.yml 2>/dev/null)"
[ -n "$hits" ] && sfail=1 && fail "literal password, secret or token in compose (move it to .env):" && sed 's/^/      /' <<< "$hits"
hits="$(find . \( -name node_modules -o -name .git -o -name target -o -name dist -o -name build \) -prune -o \
          \( -name 'application*.yml' -o -name 'application*.yaml' -o -name 'application*.properties' \) -print 2>/dev/null \
        | xargs -r grep -nHE "\\\$\\{${SECRET}:[^}]+\\}")"
[ -n "$hits" ] && sfail=1 && fail "secret with a default value in app config:" && sed 's/^/      /' <<< "$hits"
if [ -f .env.example ]; then
  hits="$(grep -nE "^${SECRET}=[[:space:]]*[^[:space:]#]" .env.example | grep -viE "=[[:space:]]*[\"']?(your[_-]|<|changeme|change-me|replace)")"
  [ -n "$hits" ] && sfail=1 && fail ".env.example holds a value for a secret (it is committed):" && sed 's/^/      /' <<< "$hits"
fi
[ "$sfail" = 0 ] && ok "no fallback or example values for passwords, secrets, tokens or keys"

# Git: secrets and logs must be ignored and never tracked, now or in history
if git rev-parse --git-dir >/dev/null 2>&1; then
  gfail=0
  paths=(.env claude_logs/x)
  [ -e pipeline-run.sh ] && paths+=(pipeline-run.sh)
  for path in "${paths[@]}"; do
    git check-ignore -q "$path" || { fail "git does not ignore ${path%/x}"; gfail=1; }
  done
  tracked="$(git ls-files | grep -E '(^|/)\.env$|(^|/)\.env\.[^e]|(^|/)pipeline-run\.sh$|(^|/)claude_logs/')"
  [ -n "$tracked" ] && { fail "tracked by git: $(echo $tracked)"; gfail=1; }
  if git rev-parse -q --verify HEAD >/dev/null; then
    hist="$(git log --all --format= --name-only | sort -u | grep -E '(^|/)\.env$|(^|/)\.env\.[^e]|(^|/)pipeline-run\.sh$|(^|/)claude_logs/')"
    [ -n "$hist" ] && { fail "in git history (remove with git filter-repo --invert-paths --path <path>): $(echo $hist)"; gfail=1; }
  fi
  [ "$gfail" = 0 ] && ok "git ignores .env, pipeline-run.sh and claude_logs/; none tracked or in history"
fi

# Destructive endpoints: cannot be proven safe statically, so flag them for a manual check
routes="$(grep -rnIE "['\"\`]/(api/)?(admin|reset|flush|wipe|drop|truncate|purge)(/|['\"\`])|/api/[a-z0-9/_-]*/(reset|flush|wipe|purge)\b" \
            --include=*.py --include=*.js --include=*.mjs --include=*.ts --include=*.java --include=*.go --include=*.kt \
            --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=dist --exclude-dir=target --exclude-dir=test --exclude-dir=tests \
            --exclude='*_test.go' --exclude='*.test.*' --exclude='*.spec.*' --exclude='test_*.py' . 2>/dev/null | head -n 10)"
if [ -n "$routes" ]; then
  warn "admin/reset-style routes found. Each must need a token (e.g. X-Admin-Token == ADMIN_TOKEN, constant-time) and be off while the token is empty:"
  sed 's/^/      /' <<< "$routes"
fi
docs="$(grep -nHIE 'curl[^|]*-X *(POST|DELETE|PUT)[^|]*/(admin|reset|flush|wipe|purge)' README.md docker-compose*.yml 2>/dev/null)"
[ -n "$docs" ] && warn "docs show calling a destructive endpoint; make sure the example sends the token:" && sed 's/^/      /' <<< "$docs"

[ "$failed" = 0 ] && echo "Security check passed: $DIR" || echo "Security check FAILED: $DIR"
exit "$failed"
