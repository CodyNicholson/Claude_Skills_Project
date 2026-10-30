# Track A: Greenfield (new system or service)

Read this at the end of Phase 1 when the track is A. It drives spec section 9A and the
plan's M0 and architecture decisions.

## Recon

- With no repository: skip code recon. Ask where it will live, and whether there is an organization template, starter or sibling project to copy conventions from. If there is one, read its build files, CI and deploy scripts, and reuse them.
- Inside an existing monorepo or workspace: read neighbouring services for stack, layout, shared libraries, deploy pattern and CI. Default to their conventions unless the user has a reason to differ.

## Probes for section 9A

**Boundary and shape**

- Why a new system rather than a module in an existing one? A good reason is a different scaling profile, ownership, release cadence or compliance boundary. "Cleaner code" is a weak reason.
- Monolith, modular monolith or services? Default to a modular monolith for one team. Require a stated reason before planning multiple deployables.
- Which bounded context does it own, and which data does it **not** own?

**Build versus buy**

- For each major capability (auth, payments, search, email, file storage, notifications, admin UI), decide: build, buy or SaaS, or use open source. Record it as a decision table with cost and lock-in notes.
- Is any part of the product commodity that a managed service covers well enough?

**Stack selection**

- Constraints: team skills, hosting, mandated technology, existing operations tooling.
- For each choice (language, framework, database, queue, hosting), give one line of rationale tied to an `NFR-n` or to team constraints. "Popular" is not a rationale.

**Bootstrap and data**

- Is there initial data to seed or import (reference data, a customer list, a catalogue)? Where does it come from, how clean is it, and is it a one-time or recurring import?
- Local developer setup: a one-command start (`docker compose up`, `make dev`)?
- Environments needed at launch (local, staging, prod) and how they are created (IaC or manual).

**Ownership**

- Who operates it after launch? Which runbooks are needed on day one?

## Plan implications

- **M0** covers the repository skeleton, CI (lint, test, build), a "hello world" deployed to the first real environment, config and secrets handling, and basic logging and health checks. Prove the path to production before writing features.
- **M1** is the thinnest end-to-end slice of the most important `US-n`, including persistence and auth, so the riskiest integration is exercised early.
- Seed or import tooling is a milestone task with its own verification (row counts, a sample spot-check).
- Record build-versus-buy and stack choices as decisions in plan section 1.
