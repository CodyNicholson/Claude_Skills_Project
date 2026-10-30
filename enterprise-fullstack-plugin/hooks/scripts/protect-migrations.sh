#!/usr/bin/env bash
# PreToolUse hook: block edits to Flyway migrations that are already committed.
# New (uncommitted) migration files can be created and edited freely.
#
# Exit 0 = allow. Exit 2 = block; stderr is shown to Claude so it can write a new migration instead.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
file="$(bash "$here/read-file-path.sh")"

[[ -z "$file" ]] && exit 0

# Only Flyway versioned/repeatable SQL migrations: V<ver>__*.sql, R__*.sql under a migration dir.
# TODO(team): adjust the pattern if your migrations live elsewhere.
case "$file" in
  */db/migration/V*__*.sql|*/db/migration/*/V*__*.sql|*/migrations/V*__*.sql) ;;
  *) exit 0 ;;
esac

# New file -> allowed.
[[ -e "$file" ]] || exit 0

dir="$(dirname "$file")"
repo_root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)" || exit 0
rel="${file#"$repo_root"/}"

# Committed in HEAD -> blocked.
if git -C "$repo_root" cat-file -e "HEAD:$rel" 2>/dev/null; then
  echo "Blocked: $rel is a committed Flyway migration. Editing it breaks Flyway checksums in every environment that already ran it. Create a NEW migration (see the db-migrations skill) instead." >&2
  exit 2
fi

exit 0
