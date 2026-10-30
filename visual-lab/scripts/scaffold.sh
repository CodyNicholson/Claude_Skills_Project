#!/bin/bash
# Scaffolds a new visual lab from the skill's templates. Never overwrites an existing file.
#
#   scaffold.sh --dir /home/rixus/workspace/Foo_Visual_Lab_Project --tool "Foo" --slug foo-lab \
#               --backend python-fastapi|node-express|none [--port 8000] [--test-port 3900]
#
# --backend none copies no backend starter (write a custom one, e.g. Spring Boot, from
# references/backends.md; or delete the backend service for a browser-only library).
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATES="$SKILL_DIR/templates"
DIR="" TOOL="" SLUG="" BACKEND="python-fastapi" PORT="" TEST_PORT="3900"

while [ $# -gt 0 ]; do
  case "$1" in
    --dir) DIR="$2"; shift 2 ;;
    --tool) TOOL="$2"; shift 2 ;;
    --slug) SLUG="$2"; shift 2 ;;
    --backend) BACKEND="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --test-port) TEST_PORT="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -n "$DIR" ] && [ -n "$TOOL" ] && [ -n "$SLUG" ] || { echo "Need --dir, --tool and --slug" >&2; exit 2; }
[[ "$SLUG" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "--slug must be lower-case letters, digits and dashes" >&2; exit 2; }
case "$BACKEND" in
  python-fastapi) PORT="${PORT:-8000}"; HEALTH="python -c \"import urllib.request; urllib.request.urlopen('http://127.0.0.1:$PORT/api/health')\"" ;;
  node-express) PORT="${PORT:-8000}"; HEALTH="wget -qO- http://127.0.0.1:$PORT/api/health || exit 1" ;;
  none) PORT="${PORT:-8080}"; HEALTH="exit 0" ;;
  *) echo "--backend must be python-fastapi, node-express or none" >&2; exit 2 ;;
esac

mkdir -p "$DIR"
DIR="$(cd "$DIR" && pwd)"
LAB_NAME="$TOOL Visual Lab"

copied=() skipped=()
# copy <src> <dest relative to DIR>
copy() {
  local dest="$DIR/$2"
  if [ -e "$dest" ]; then skipped+=("$2"); return; fi
  mkdir -p "$(dirname "$dest")"
  cp -p "$1" "$dest"
  copied+=("$2")
}

copy "$TEMPLATES/root/pipeline-run.sh" pipeline-run.sh
copy "$TEMPLATES/root/git-pull-project.sh" git-pull-project.sh
copy "$TEMPLATES/root/gitignore" .gitignore
copy "$TEMPLATES/root/env.example" .env.example
copy "$TEMPLATES/root/docker-compose.yml" docker-compose.yml
copy "$TEMPLATES/root/docker-compose.test.yml" docker-compose.test.yml

while IFS= read -r -d '' f; do
  copy "$f" "frontend/${f#"$TEMPLATES/frontend/"}"
done < <(find "$TEMPLATES/frontend" -type f -print0)

if [ "$BACKEND" != none ]; then
  while IFS= read -r -d '' f; do
    copy "$f" "backend/${f#"$TEMPLATES/backends/$BACKEND/"}"
  done < <(find "$TEMPLATES/backends/$BACKEND" -type f -print0)
fi

# Fill placeholders in the files copied this run only
for rel in "${copied[@]}"; do
  LAB_NAME="$LAB_NAME" TOOL="$TOOL" SLUG="$SLUG" PORT="$PORT" TEST_PORT="$TEST_PORT" HEALTH="$HEALTH" \
  python3 -I - "$DIR/$rel" <<'PY'
import os, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    text = f.read()
for key, value in {
    "__LAB_NAME__": os.environ["LAB_NAME"],
    "__TOOL__": os.environ["TOOL"],
    "__SLUG__": os.environ["SLUG"],
    "__API_PORT__": os.environ["PORT"],
    "__TEST_PORT__": os.environ["TEST_PORT"],
    "__HEALTHCHECK__": os.environ["HEALTH"].replace('"', '\\"'),
    "__TAGLINE__": f"Every button runs real {os.environ['TOOL']} code",
}.items():
    text = text.replace(key, value)
with open(path, "w", encoding="utf-8") as f:
    f.write(text)
PY
done

chmod +x "$DIR/pipeline-run.sh" "$DIR/git-pull-project.sh"

# The real secrets file: git-ignored, owner-only
if [ ! -e "$DIR/.env" ]; then
  cp "$DIR/.env.example" "$DIR/.env"
  chmod 600 "$DIR/.env"
  copied+=(".env")
fi

echo "Scaffolded $LAB_NAME in $DIR (backend: $BACKEND, API port $PORT, isolated test UI port $TEST_PORT)"
echo "Created ${#copied[@]} files."
if [ ${#skipped[@]} -gt 0 ]; then
  echo "Kept ${#skipped[@]} existing files (not overwritten):"
  printf '  %s\n' "${skipped[@]}"
fi
grep -rl "__[A-Z_]*__" "$DIR" --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | sed 's/^/Unfilled placeholder in: /' || true
