# Development Plan: [FILL: initiative name]

**Date:** [FILL: YYYY-MM-DD]
**Track:** [FILL: A | B | C]
**Spec:** [requirements-spec.md](requirements-spec.md) (approved [FILL: date])
**Status:** Draft

<!-- GUIDE: Replace every [FILL: ...] and delete all GUIDE comments. Reference requirement IDs (US-n, INV-n, NFR-n, UNK-n) exactly as they appear in the spec. Use real names from recon: paths, tables, commands. -->

## 0. Summary

[FILL: 3–5 sentences: what is being built, the overall approach, number of milestones, the biggest risk]

## 1. Architecture and Key Decisions

[FILL: short description of components and data flow. Add a mermaid diagram if it has more than 3 components.]

<!-- GUIDE: One block per decision. Every decision cites the driving requirement IDs and at least one rejected alternative. -->

### D1: [FILL: decision title]

- **Decision:** [FILL]
- **Driven by:** [FILL: INV-n / NFR-n / constraint]
- **Alternatives rejected:** [FILL: option, and why not]
- **Consequences:** [FILL: trade-offs accepted]

## 2. Data and Schema Evolution

<!-- GUIDE: Tables/collections, columns, indexes, constraints that enforce INV-n. Brownfield: expand / migrate / contract steps mapped to milestones. Migration: mapping table and backfill/sync design. -->

[FILL]

## 3. API and Event Contracts

<!-- GUIDE: Endpoint list (method, path, auth, request/response shape, errors) and event schemas (name, key, payload, ordering). Note versioning and compatibility. -->

[FILL]

## 4. Consistency, Synchronization and Failure Handling

- **Transactions and isolation:** [FILL: per write path, tied to INV-n]
- **Idempotency:** [FILL]
- **Derived data sync:** [FILL: outbox, CDC, batch, or N/A: reason]
- **Retries, timeouts, DLQ:** [FILL]
- **Degraded modes:** [FILL: behaviour when each dependency fails]

## 5. Security Implementation

- [FILL: authN/authZ enforcement points, data protection, secrets, rate limits, audit logging]

## 6. Implementation Milestones

<!-- GUIDE: Vertical slices. M0 = foundations (repo/CI/envs/skeleton deploy). Each milestone is deployable and has Covers + Verification. No milestone depends on a later one. -->

### M0: Foundations

- **Goal:** [FILL]
- **Covers:** [FILL: requirement IDs, or "enables all"]
- **Tasks:**
  - [ ] [FILL: concrete task with real path/tool]
- **Verification:** [FILL: runnable commands or observable pass/fail criteria]
- **Exit criteria:** [FILL]
- **Size:** [FILL: S / M / L or days]

### M1: [FILL: thinnest end-to-end slice of the top story]

- **Goal:** [FILL]
- **Covers:** [FILL: US-n, INV-n, NFR-n]
- **Tasks:**
  - [ ] [FILL]
- **Verification:** [FILL]
- **Exit criteria:** [FILL]
- **Size:** [FILL]

## 7. Test Strategy

| Level | What | Tool | Requirement IDs |
|---|---|---|---|
| Unit | [FILL] | [FILL] | [FILL] |
| Integration | [FILL] | [FILL] | [FILL] |
| Invariant / concurrency | [FILL: one test per INV-n] | [FILL] | [FILL: INV-n] |
| End-to-end | [FILL] | [FILL] | [FILL] |
| Performance | [FILL: against NFR targets, or N/A: reason] | [FILL] | [FILL: NFR-n] |

## 8. Rollout and Rollback

- **Release mechanism:** [FILL: flag name / cohort / strangler route / direct deploy]
- **Stages:** [FILL: internal → % → all, with metrics watched at each]
- **Rollback triggers:** [FILL: concrete thresholds]
- **Rollback procedure:** [FILL: exact steps and expected time]
- **Cutover runbook:** [FILL: Track C only: go/no-go criteria, freeze, steps, comms. Otherwise N/A: not a migration]

## 9. Observability and Operational Readiness

- **Dashboards and metrics:** [FILL]
- **Alerts:** [FILL: symptom, threshold, who is notified]
- **Runbooks:** [FILL]
- **Logs and traces:** [FILL]

## 10. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation | Milestone |
|---|---|---|---|---|
| [FILL] | [FILL: L/M/H] | [FILL: L/M/H] | [FILL] | [FILL] |

## 11. Open Items Carried from the Spec

<!-- GUIDE: Every UNK-n from spec section 10, with the milestone it blocks. Write "None" if the register is empty. -->

| ID | Item | Blocks | Owner | Due |
|---|---|---|---|---|
| [FILL: UNK-n] | [FILL] | [FILL: milestone] | [FILL] | [FILL] |

## 12. Traceability Matrix

<!-- GUIDE: Every US-n, INV-n and NFR-n from the spec, one row each. -->

| Requirement | Milestone(s) | Verified by |
|---|---|---|
| [FILL: ID] | [FILL: M-n] | [FILL: test or check] |
