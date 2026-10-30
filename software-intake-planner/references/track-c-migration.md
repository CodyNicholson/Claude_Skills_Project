# Track C: Migration or modernization

Read this at the end of Phase 1 when the track is C. Recon of the legacy system is
mandatory. Spec section 9C holds the parity matrix, data migration rules and cutover
choice.

## Recon steps

1. **Inventory the legacy surface:** every entry point (routes, screens, CLI commands, scheduled jobs, queue consumers, stored procedures, triggers). Use `Grep` and `Glob` on route definitions, cron or job configs, and SQL files.
2. **Inventory the data:** schemas, row counts if the user can provide them, encodings and time zones, soft-delete conventions, and orphaned or denormalized data.
3. **Inventory the integrations:** who calls the legacy system, and what it calls. Hidden consumers (reports, spreadsheets, partner FTP drops) are the classic migration surprise, so ask explicitly.
4. **Inventory implicit behaviour:** triggers, default values, rounding, sort orders, and email side effects that users rely on but nobody documented.
5. **Read the target stack:** if the target exists, apply the Track B recon to it as well.

## Probes for section 9C

**Why and success**

- Why migrate now (end-of-life stack, cost, scaling, hiring, security)? This sets which shortcuts are acceptable.
- What does "done" mean: legacy decommissioned, or legacy read-only?

**Feature parity and deprecation matrix**

Build a table with one row per legacy capability:

| Capability | Decision | Notes |
|---|---|---|
| … | Keep as-is / Redesign / Deprecate | owner sign-off, replacement, consumers affected |

Ask the user to confirm every "Deprecate" row. Unconfirmed deprecations become
`[ASSUMED: UNK-n]`.

**Data migration**

- Mapping rules: field-by-field transforms, ID mapping (keep legacy IDs, or a new ID plus a mapping table?), enum and status translations, and time-zone normalization.
- Data quality: what happens to records that fail validation (quarantine table, fix-forward, drop with sign-off)?
- Backfill approach: a one-time bulk load plus continuous sync (CDC or change log) until cutover, versus a freeze-and-copy.
- Volume and duration: estimated load time, and whether the freeze window is acceptable.

**Cutover pattern**

- **Strangler fig:** route by capability through a facade, one slice at a time. Use for large systems that need incremental risk. The default recommendation.
- **Cohort:** move users or tenants in batches. Use when data is cleanly partitioned by customer.
- **Big bang:** one switch. Use only when the system is small, a freeze window is acceptable, and rollback is a tested restore.

**Verification and rollback**

- Shadow reads or dual runs: compare legacy and new responses for the same input, and set the acceptable mismatch rate.
- Reconciliation: row counts, checksums and sampled field-level diffs, run on a schedule during sync.
- Rollback: until which point is it possible? Is data written in the new system replicated back? This is a critical question, because one-way cutovers need much stricter gates.

## Plan implications

- Plan section 2 contains the mapping table and backfill and sync design. Plan section 8 contains a step-by-step cutover runbook with go/no-go criteria, a freeze window, a communications step and a timed rollback procedure.
- Milestones follow the parity matrix: each slice moves one or more capabilities, with shadow or parity verification as its exit criterion.
- The final milestone is decommissioning: remove routes, archive data, delete sync jobs, update DNS and docs. Do not leave legacy running indefinitely.
- Every "Keep as-is" row maps to at least one parity test in plan section 7.
