---
name: software-intake-planner
description: Interviews the user about a software project, inspects any existing codebase first, and writes a validated requirements-spec.md and a phased development-plan.md under docs/plans/. Use when the user wants to start a new greenfield app or service, plan a substantial feature in an existing repository, or plan a legacy migration or stack modernization, with phrasing like "gather requirements", "plan this project", "create a development plan", "write a spec and implementation plan", "design a migration plan", or "/software-intake-planner". Not for bug fixes, small single-file changes, or carrying out an existing plan.
argument-hint: [project idea, path to a PRD/ticket/notes, or the feature to plan]
allowed-tools: Read, Glob, Grep, Write(docs/plans/**), Edit(docs/plans/**), Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/validate_intake.py *), Bash(git log *), Bash(git ls-files *)
---

# Software intake planner

Turn **$ARGUMENTS** into two reviewed documents:

1. `requirements-spec.md`: what is being built, for whom, under which constraints.
2. `development-plan.md`: how it will be built, in verifiable milestones.

If `$ARGUMENTS` is empty, ask for a 2–3 sentence description of the project, or a path to
a PRD, ticket or notes, then continue.

Skill files (all under `${CLAUDE_SKILL_DIR}`):

- `references/core-intake-checklist.md`: probes for spec sections 1–8 and the follow-up triggers. Read it at the start of Phase 2.
- `references/track-a-greenfield.md`, `references/track-b-brownfield.md`, `references/track-c-migration.md`: track-specific probes and recon steps. Read only the file for the chosen track, at the end of Phase 1.
- `templates/requirements-intake.template.md`: spec skeleton. Read it in Phase 3.
- `templates/development-plan.template.md`: plan skeleton. Read it in Phase 4.
- `scripts/validate_intake.py`: deterministic checker for both documents.

## Ground rules

- **Never invent facts.** If the user does not know a number, owner, vendor or decision, put it in the spec's Unknowns register (see "Markers" below). An invented "500 req/s" becomes a design input nobody questions, while a logged unknown gets resolved.
- **Plan only.** Do not create or edit source code, configs or migrations. Write only inside the output folder. If the user wants to start implementing, finish the plan first, then hand off.
- **Recon before questions.** Never ask what the repository, the given documents or earlier answers already tell you. State inferred facts and let the user correct them, because that is faster than asking.
- **At most 6 questions per round**, numbered, grouped by topic. Use `AskUserQuestion` for closed choices (track, hosting, auth provider, rollout style) and put your recommended option first. Ask open questions in a numbered message.
- **Scale depth to the project.** A weekend CLI tool does not need CDC, a DLQ topology or p99 budgets. Keep every required section, but answer non-applicable items with `N/A: <reason>` rather than asking about them. Ask about distributed-systems topics only when the triggers in the checklist fire.
- **Accept "you decide".** If the user delegates a choice, make it, label it `[ASSUMED: UNK-n]`, record the rationale in the register, and keep going.

## Output location

`<root>/docs/plans/<YYYY-MM-DD>-<initiative-slug>/`, where `<root>` is the git repository
root that contains the working directory. For a greenfield project with no repository yet,
ask where the new project will live and use that path. Pre-approved writes cover only
`docs/plans/**` relative to the working directory, so other locations ask for permission,
which is expected. Use today's date and a short kebab-case slug, for example
`2026-10-29-listing-alerts`.

## Phase 1: Triage and reconnaissance

1. Read every document the user referenced (PRD, ticket text, RFC, notes).
2. Classify the track and state it with one line of reasoning:
   - **A, Greenfield:** new system or service with no existing code to change.
   - **B, Brownfield:** new capability inside an existing codebase.
   - **C, Migration:** replacing, re-platforming or modernizing an existing system or module.

   If it is ambiguous (for example a new service that also absorbs a legacy module), ask, and recommend the track that carries the most risk.
3. Read the matching track file.
4. **Recon (required for B and C, and for A when it sits inside an existing repo).** Follow the recon steps in the track file. At minimum, detect:
   - languages, frameworks and versions (`package.json`, `go.mod`, `pom.xml`, `build.gradle`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `*.csproj`)
   - data stores and schema history (`docker-compose*.yml`, migration folders, ORM models)
   - API surface (routers and handlers, OpenAPI/proto files) and integration clients (HTTP clients, queues, SDKs)
   - test frameworks, CI config (`.github/workflows`, `Jenkinsfile`, `.gitlab-ci.yml`) and deploy scripts
   - recent activity in the affected area (`git log --oneline -20 -- <path>`)

   For a large repository (more than about 500 tracked files), delegate the sweep to an `Explore` agent and ask it for a facts-only summary with file paths.
5. Show the user a short **Recon summary** (facts with `file:line` sources, plus the gaps you will ask about) before starting Round 1.

## Phase 2: Discovery interview (3 rounds)

Read `references/core-intake-checklist.md`. Map what you already know against spec
sections 1–9, then ask only about the gaps.

| Round | Covers | Done when |
|---|---|---|
| 1. Scope and invariants | Sections 1–3: problem, users, success metrics, in scope, **non-goals**, user stories, **hard business invariants** | You can write `US-n` stories with acceptance criteria and at least one non-goal, and you know which states must never occur (`INV-n`). |
| 2. Data, scale, integrations | Sections 4–6: entities, system of record, access patterns, consistency tolerance, latency and throughput targets, upstream and downstream failure handling | Every `NFR-n` has a value, an `N/A: reason`, or an `UNK-n`. |
| 3. Security, ops, track mechanics | Sections 7–9: authN/authZ, PII, secrets, hosting, observability, CI/CD, plus the track file's probes | You know the rollout and rollback approach. |

After each round, briefly summarize what you learned and which follow-up triggers
fired. Skip a round entirely if recon and earlier answers already cover it. Stop asking
after round 3: anything still open goes to the Unknowns register, not into a fourth round,
unless the user asks to keep going.

## Phase 3: Requirements spec and approval gate

1. Read `templates/requirements-intake.template.md` and write `requirements-spec.md` in the output folder. Replace every `[FILL: ...]`, keep only the matching track subsection (9A, 9B or 9C), and delete the guidance comments.
2. Validate:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/validate_intake.py <output-folder>/requirements-spec.md
   ```

3. Fix every ERROR and re-run. Fix WARNs or say in the spec why they stand.
4. **Gate:** show the user the file path, the counts the validator printed (stories, invariants, NFRs, unknowns), the list of unknowns and assumptions, and anything you inferred rather than were told. Ask them to approve or correct it. Do not write the plan until they approve. Plan rework is much more expensive than spec rework.

## Phase 4: Development plan

1. Read `templates/development-plan.template.md` and write `development-plan.md` next to the spec.
2. Requirements for the content:
   - Every decision in section 1 cites the `INV-n` / `NFR-n` that drives it and names at least one rejected alternative.
   - Milestones are **vertical slices** (each one deployable and demoable), not layers ("all models, then all endpoints"). M0 is foundations: repo, CI, environments, skeleton deploy.
   - Every milestone has `**Covers:**` (requirement IDs), concrete tasks, and `**Verification:**` with runnable commands or observable pass/fail criteria. "Tests pass" alone is not a criterion; name the tests or the behaviour.
   - Every `INV-n` gets an explicit test in section 7, and a concurrency test when it involves shared mutable state.
   - Every `UNK-n` appears in section 11 with the milestone it blocks, so open questions block work and are not forgotten.
   - Use the codebase's real names (packages, tables, endpoints, commands) found in recon. Do not use generic placeholders.
   - Brownfield: schema changes use expand → migrate → contract, behind a flag. Migration: include the parity matrix and the cutover and rollback runbook.
3. Validate with the traceability cross-check:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/validate_intake.py --plan <output-folder>/development-plan.md --spec <output-folder>/requirements-spec.md
   ```

4. Fix every ERROR and re-run.

## Phase 5: Verify and hand off

Before reporting, re-read the plan once against this checklist:

- [ ] Both validator runs end with `RESULT: PASS`.
- [ ] No milestone depends on a later milestone.
- [ ] The first milestone that touches production data or traffic has a rollback trigger and a rollback procedure.
- [ ] Every assumption the user did not explicitly confirm is marked `ASSUMED`.

Then report to the user: both file paths, the track, the milestone list (one line each),
the open unknowns with the milestone each blocks, and the suggested next step (usually:
resolve the unknowns that block M1, then start M0).

**Circuit breaker:** if the validator fails 3 times on the same error, stop and show the
user the error and the relevant section. Do not loop. If the user abandons the interview
midway, write the spec with what you have, register the rest as unknowns, and tell them
it is a draft.

## Markers

| Marker | Meaning | Rule |
|---|---|---|
| `[FILL: hint]` | Template slot | Must not remain in output. |
| `US-n`, `INV-n`, `NFR-n` | Requirement IDs | Defined in the spec, referenced in the plan. Never renumber after the user approves the spec. |
| `[UNKNOWN: UNK-n]` | User does not know yet | Needs a row in spec section 10 with Owner, Action and Due (a date or milestone). |
| `[ASSUMED: UNK-n]` | You or the user chose a provisional value | Same register row, Type = Assumption, with the rationale in the Item column. |
| `N/A: reason` | Not applicable at this scale | The reason is required. |

`TBD`, `TODO` and bare `[UNKNOWN]` are rejected by the validator. Use a register entry instead.
