---
name: db-migrations
description: Postgres schema design and Flyway migration conventions - file naming and versioning, zero-downtime (expand/contract) changes, indexes, constraints, backfills, and rollback strategy. Use whenever creating or changing tables, columns, indexes, or writing any Flyway migration.
---

# Postgres + Flyway migrations

## Golden rules

1. **Never edit a migration that has been committed.** Flyway checksums will fail in every environment that already ran it. Write a new migration instead. A plugin hook blocks edits to committed migrations.
2. One logical change per migration file.
3. Every migration must be safe to run while the previous version of the app is still serving traffic.

## Creating a migration

Run the helper in this skill's `scripts/` folder (use the skill's base directory shown when it loads) to get the next version number and an empty file:

```bash
bash <skill-base-dir>/scripts/new-migration.sh <migrations-dir> "add order status index"
# -> <migrations-dir>/V20261030153000__add_order_status_index.sql
```

TODO(team): pick ONE versioning scheme and delete the other.
- Timestamp versions (`V20261030153000__...`) - default in the helper; avoids merge collisions between branches.
- Sequential versions (`V42__...`) - pass `--sequential` to the helper.

Default migrations directory: `src/main/resources/db/migration` (TODO(team): confirm).

## Naming

- Tables: plural snake_case (`purchase_orders`). Columns: snake_case.
- Primary key: `id uuid primary key default gen_random_uuid()`.
- Audit columns on every table: `created_at timestamptz not null default now()`, `updated_at timestamptz not null default now()`.
- Constraints and indexes named explicitly: `pk_<table>`, `fk_<table>_<ref>`, `uq_<table>_<cols>`, `ix_<table>_<cols>`, `ck_<table>_<rule>`.
- Use `timestamptz`, never `timestamp`. Use `text` (with a check constraint if needed) over `varchar(n)`. Money as `numeric(19,4)`.

## Zero-downtime patterns (expand / contract)

| Change | Safe approach |
|---|---|
| Add column | Add as nullable or with a constant default. Backfill separately. Add `NOT NULL` in a later migration after backfill. |
| Rename column | Add new column -> dual-write in app -> backfill -> switch reads -> drop old column in a later release. Never `RENAME` in one step. |
| Drop column | Remove all app usage first and deploy. Drop in a later migration. |
| Add index on a large table | `CREATE INDEX CONCURRENTLY` in its own migration, with Flyway's per-script setting to run outside a transaction. |
| Add foreign key on a large table | `ADD CONSTRAINT ... NOT VALID`, then `VALIDATE CONSTRAINT` in a separate migration. |
| Change column type | New column + backfill + swap, as for rename. |

For `CONCURRENTLY`, create a matching `V..._<name>.sql.conf` file containing `executeInTransaction=false` (Flyway script config). TODO(team): confirm your Flyway version supports script config files; otherwise use your existing approach.

## Backfills

- Do not backfill large tables inside a schema migration. Use a batched job (data-engineer) or a Java-based migration that updates in chunks of ~1-10k rows with commits between.
- Backfills must be re-runnable (`WHERE new_col IS NULL`).

## Rollback

Flyway Community has no automatic undo. Every migration's PR description states how to roll back (usually: a new forward migration). Destructive steps (drops) only happen in the contract phase, after the code no longer needs the data.

## Checklist

- [ ] New file, never an edit to a committed one
- [ ] Safe with the old app version still running
- [ ] Explicit constraint and index names
- [ ] Indexes for every foreign key and every column used in frequent WHERE/ORDER BY
- [ ] Large-table operations use CONCURRENTLY / NOT VALID
- [ ] Runs cleanly on an empty database and on a copy of current schema (`./gradlew flywayMigrate` against the compose Postgres)
