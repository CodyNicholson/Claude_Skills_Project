#!/usr/bin/env bash
# PostToolUse hook: format the file Claude just edited, using the project's own tools when present.
# Never fails the tool call: formatting problems are reported but always exit 0.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
file="$(bash "$here/read-file-path.sh")"

[[ -z "$file" || ! -f "$file" ]] && exit 0

dir="$(cd "$(dirname "$file")" && pwd)"

# Walk up from the file to find the nearest directory containing a marker file.
find_up() {
  local d="$dir"
  while [[ "$d" != "/" ]]; do
    for marker in "$@"; do
      [[ -e "$d/$marker" ]] && { echo "$d"; return 0; }
    done
    d="$(dirname "$d")"
  done
  return 1
}

case "$file" in
  *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.json|*.css|*.scss|*.sass|*.html|*.md|*.yml|*.yaml)
    # Only use the project's local prettier, so versions match the team's.
    if root="$(find_up node_modules/.bin/prettier)"; then
      "$root/node_modules/.bin/prettier" --write --log-level warn "$file" >&2 || true
    fi
    ;;
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      ruff format --quiet "$file" >&2 || true
    elif command -v black >/dev/null 2>&1; then
      black --quiet "$file" >&2 || true
    fi
    ;;
  *.java)
    # TODO(team): Spotless across the whole module is slow per-edit. Enable if you want it,
    # or rely on `./gradlew spotlessApply` before commit.
    # if root="$(find_up gradlew)"; then (cd "$root" && ./gradlew -q spotlessApply -PspotlessFiles="$file") >&2 || true; fi
    :
    ;;
esac

exit 0
