#!/bin/bash
# Builds and starts a lab's compose stack as a separate, throw-away compose project so the app
# that is live in the Cloudflare tunnel keeps running. Never runs pipeline-run.sh.
#
#   test-isolated.sh <lab dir> [up|smoke|down]     (default: up, then smoke)
#
# up:    security-check.sh, then docker compose -p <slug>-test with docker-compose.test.yml (renamed containers, no
#        tunnel-net, UI on the test port)
# smoke: waits for the UI, then checks /, /api/health and every self-test path in
#        frontend/src/demos/catalog.js through nginx
# down:  removes the test project's containers, networks and volumes
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIR="$(cd "${1:?lab directory}" && pwd)"
ACTION="${2:-all}"
cd "$DIR"
[ -f docker-compose.test.yml ] || { echo "No docker-compose.test.yml in $DIR" >&2; exit 1; }

PROJECT="$(basename "$DIR" | tr '[:upper:]_' '[:lower:]-' | tr -cd 'a-z0-9-')-test"
# The UI port from `- "127.0.0.1:3900:80"` (or a bare `"3900:80"`)
PORT="$(grep -oE '[0-9]+:80"' docker-compose.test.yml | head -n1 | cut -d: -f1)"
PORT="${PORT:-3900}"
# The classic builder: a buildx bake build hung once here with no output
export COMPOSE_BAKE=false
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.yml -f docker-compose.test.yml)

# docker-compose.yml declares tunnel-net as external; it must exist even though the test
# frontend does not join it. Creating it is harmless to the live app.
docker network inspect tunnel-net >/dev/null 2>&1 || docker network create tunnel-net >/dev/null

up() {
  # Refuses to start a stack that would expose ports publicly, use fallback passwords, etc.
  bash "$SCRIPT_DIR/security-check.sh" "$DIR"
  # Stops before starting anything if a test container name would collide with a live one
  for name in $("${COMPOSE[@]}" config --format json | python3 -I -c 'import json,sys; print(" ".join(s.get("container_name","") for s in json.load(sys.stdin)["services"].values()))'); do
    if [ "$name" = rixus-frontend ] || [ "$name" = cloudflared-tunnel ]; then
      echo "docker-compose.test.yml must rename $name" >&2; exit 1
    fi
  done
  "${COMPOSE[@]}" up -d --build
}

smoke() {
  local base="http://127.0.0.1:$PORT" failed=0
  echo "Waiting for $base ..."
  for _ in $(seq 1 90); do curl -fsS "$base/" >/dev/null 2>&1 && break; sleep 2; done
  curl -fsS "$base/" | grep -q '<div id="root">' && echo "ok   GET /" || { echo "FAIL GET /"; failed=1; }
  # Browser-only labs have no API to check
  if ! grep -q 'location /api/' frontend/nginx.conf; then return $failed; fi
  for _ in $(seq 1 90); do curl -fsS "$base/api/health" >/dev/null 2>&1 && break; sleep 2; done
  curl -fsS "$base/api/health" >/dev/null && echo "ok   GET /api/health" || { echo "FAIL GET /api/health"; failed=1; }
  # Every demo's `test: { method, path }` from the catalog
  while IFS=$'\t' read -r method path; do
    body="$(curl -sS -X "$method" "$base$path" || true)"
    verdict="$(printf '%s' "$body" | python3 -I -c '
import json, sys
try:
    r = json.load(sys.stdin)
    checks = r.get("checks") or []
    bad = [c["name"] for c in checks if not c.get("passed")]
    print("ok  " if checks and not bad else "FAIL", f"{len(checks)-len(bad)}/{len(checks)} checks", "; ".join(bad))
except Exception as e:
    print("FAIL", "not a DemoResult:", str(e)[:80])
')"
    echo "$verdict  $method $path"
    [[ "$verdict" == ok* ]] || failed=1
  done < <(grep -oE "test: \{ *method: '[A-Z]+', *path: '[^']+'" frontend/src/demos/catalog.js \
           | sed -E "s/.*method: '([A-Z]+)', *path: '([^']+)'/\1\t\2/")
  return $failed
}

case "$ACTION" in
  up) up ;;
  smoke) smoke ;;
  down) "${COMPOSE[@]}" down -v --remove-orphans ;;
  all) up && smoke ;;
  *) echo "Action must be up, smoke or down" >&2; exit 2 ;;
esac
