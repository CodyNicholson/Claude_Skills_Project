#!/usr/bin/env bash
# Create a new, empty Flyway migration with the next version number.
#
# Usage:
#   new-migration.sh <migrations-dir> "<description>" [--sequential]
#
# Default versioning is a UTC timestamp (V20261030153000__desc.sql), which avoids
# collisions between branches. --sequential uses max(existing V<n>) + 1.
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "usage: $0 <migrations-dir> \"<description>\" [--sequential]" >&2
  exit 1
fi

dir="$1"
desc="$2"
mode="${3:-}"

mkdir -p "$dir"

# "Add order status index" -> add_order_status_index
slug="$(printf '%s' "$desc" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/_/g; s/^_+//; s/_+$//')"
if [[ -z "$slug" ]]; then
  echo "description must contain letters or digits" >&2
  exit 1
fi

if [[ "$mode" == "--sequential" ]]; then
  last="$(find "$dir" -maxdepth 1 -type f -name 'V*__*.sql' -printf '%f\n' 2>/dev/null \
    | sed -nE 's/^V([0-9]+)__.*/\1/p' | sort -n | tail -1)"
  version=$(( ${last:-0} + 1 ))
else
  version="$(date -u +%Y%m%d%H%M%S)"
fi

file="$dir/V${version}__${slug}.sql"
if [[ -e "$file" ]]; then
  echo "already exists: $file" >&2
  exit 1
fi

cat > "$file" <<EOF
-- ${desc}
-- Rollback: <describe the forward migration that would undo this>

EOF

echo "$file"
