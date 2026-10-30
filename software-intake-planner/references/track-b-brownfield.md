# Track B: Brownfield (new feature in an existing system)

Read this at the end of Phase 1 when the track is B. Recon is mandatory and must finish
before any technical question. Spec section 9B records the findings and the change
mechanics.

## Recon steps

1. **Map the stack:** build files, framework versions, database engine and ORM or query layer, test frameworks, CI workflow, deploy scripts.
2. **Find the blast radius:** `Grep` for the domain nouns from the request (entity names, routes, table names). List:
   - the tables or collections touched, and their migration history (latest migration files)
   - handlers, services and repositories that read or write them
   - the frontend views and API clients that call those endpoints
   - jobs, consumers or cron tasks that touch the same data
3. **Find conventions to copy:** the closest existing feature of a similar shape (CRUD resource, async job, integration). Record its file paths. The plan should say "mirror `<path>`".
4. **Check the test baseline:** where the tests for the affected area live, and whether they exist at all. Missing coverage on code the feature will change is a risk.
5. **Check recent churn:** `git log --oneline -20 -- <affected paths>` shows active work, owners and possible conflicts.

Present the findings with `file:line` references before Round 1.

## Probes for section 9B

**Impact and risk**

- Which existing behaviour must stay unchanged? Write it as `INV-n`. Regressions are the main brownfield risk.
- Are the touched endpoints or tables on a hot path? Look for N+1 queries, missing indexes on new filter columns, and lock contention when adding writes to busy rows.
- Do other teams, services or mobile apps consume the affected API or events? If so, what are the backward-compatibility rules?

**Schema change mechanics (expand → migrate → contract)**

- **Expand:** add new columns or tables as nullable or defaulted; never rename or drop in the same release as the code change.
- **Migrate:** backfill in batches (state the batch size and throttling); dual-read or dual-write only behind a flag.
- **Contract:** remove old columns or paths in a later release, after verification.
- For large tables, ask about the row count and whether the database engine locks on `ALTER`. Plan online migration tooling if needed.

**Release controls**

- A feature flag (existing flag system or a new one?), the kill-switch behaviour when the flag is off, and the flag's removal date.
- Rollout audience stages (internal → percentage → all) and the metrics watched at each stage.

**Fit**

- Does the feature belong in an existing module, or does it justify a new one? Follow the existing layering. Do not introduce a new architecture style inside one feature.

## Plan implications

- Every schema change in plan section 2 is split into expand, migrate and contract steps across milestones. The contract step is never in the same milestone as the expand step.
- Plan section 7 includes regression tests for each "must stay unchanged" `INV-n`, run before the feature code merges.
- Plan section 8 gives the flag name, the stages, the rollback trigger (for example, error rate above baseline + X% for 10 minutes) and the rollback action (flag off; migrations stay because they are additive).
- Tasks name the real files to change, taken from recon.
