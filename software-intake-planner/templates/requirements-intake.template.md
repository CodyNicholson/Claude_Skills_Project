# Requirements Spec: [FILL: initiative name]

**Date:** [FILL: YYYY-MM-DD]
**Track:** [FILL: A | B | C] ([FILL: Greenfield | Brownfield | Migration])
**Status:** Draft, awaiting approval
**Requested by:** [FILL: person or team]
**Sources:** [FILL: documents read, recon scope, interview rounds held]

<!-- GUIDE: Replace every [FILL: ...]. Delete all GUIDE comments and the two track subsections that do not apply in section 9. Unknowns go in section 10 as [UNKNOWN: UNK-n] / [ASSUMED: UNK-n]; never write TBD. Non-applicable items: "N/A: reason". -->

## 0. Recon summary

<!-- GUIDE: Facts inferred from the codebase and documents, each with a source (file:line or doc name). Write "N/A: no existing code" for pure greenfield. -->

- [FILL: fact (source)]

## 1. Context and Problem

### 1.1 Problem statement

[FILL: one paragraph: who has the problem, what it costs today, why now]

### 1.2 Users and stakeholders

| Role | Needs | Notes |
|---|---|---|
| [FILL: role] | [FILL: need] | [FILL: notes] |

### 1.3 Success metrics

| Metric | Baseline | Target | Measured by |
|---|---|---|---|
| [FILL: metric] | [FILL: baseline] | [FILL: target] | [FILL: method/tool] |

## 2. Scope

### 2.1 In scope

- [FILL: capability]

### 2.2 MVP versus later

| Capability | MVP | Later |
|---|---|---|
| [FILL: capability] | [FILL: yes/no] | [FILL: phase or "-"] |

### 2.3 Explicit non-goals

<!-- GUIDE: At least one. Things people will assume are included but are not. -->

- [FILL: non-goal and why it is excluded]

### 2.4 Constraints

- **Deadline:** [FILL: date and driver, or N/A: reason]
- **Team:** [FILL: who builds and maintains it]
- **Mandated or forbidden technology:** [FILL: list, or none]
- **Budget:** [FILL: amount or N/A: reason]

## 3. Functional Requirements

### 3.1 Actors and roles

| Actor | Permissions |
|---|---|
| [FILL: actor] | [FILL: what they can do] |

### 3.2 User stories

<!-- GUIDE: One block per story. IDs are permanent once the spec is approved. -->

**US-1: [FILL: title]**
As a [FILL: role], I want [FILL: capability] so that [FILL: outcome].

- Acceptance: [FILL: Given / When / Then, or testable bullet]

### 3.3 Hard business invariants

<!-- GUIDE: States that must never occur, plus how concurrency is controlled. At least one. A product with genuinely none: "None: reason" (the validator warns). -->

- **INV-1:** [FILL: invariant]. Enforcement: [FILL: constraint, lock, transaction, idempotency key...]

### 3.4 Edge cases and error states

- [FILL: edge case → expected behaviour]

## 4. Data and Storage

### 4.1 Core entities

| Entity | Key fields | Relationships | System of record |
|---|---|---|---|
| [FILL: entity] | [FILL: fields] | [FILL: relations] | [FILL: this system / external] |

### 4.2 Derived data and views

- [FILL: cache, search index, report; how it is refreshed and how stale it may be. Or N/A: reason]

### 4.3 Access patterns

| Pattern | Type | Frequency | Notes |
|---|---|---|---|
| [FILL: query or write] | [FILL: read/write] | [FILL: per sec/day] | [FILL: filters, sort, pagination] |

**Read/write ratio:** [FILL: e.g. 20:1]

### 4.4 Consistency tolerance

[FILL: where strong consistency is required and where eventual consistency is fine, with max staleness]

### 4.5 Volume, growth and retention

- **Initial volume:** [FILL: rows/GB]
- **Growth:** [FILL: per month]
- **Retention and deletion:** [FILL: rules, legal holds, user deletion requests]

## 5. Scale and SLOs

<!-- GUIDE: Every row needs a number, [UNKNOWN: UNK-n], [ASSUMED: UNK-n], or "N/A: reason". Keep the p95, p99 and throughput rows. Add rows as needed. -->

| ID | Metric | Target | Scope / notes |
|---|---|---|---|
| NFR-1 | p95 latency | [FILL: e.g. 200 ms] | [FILL: which endpoints/interactions] |
| NFR-2 | p99 latency | [FILL: e.g. 800 ms] | [FILL: scope] |
| NFR-3 | Peak throughput | [FILL: e.g. 50 req/s, 1k events/min] | [FILL: when the peak happens] |
| NFR-4 | Availability | [FILL: e.g. 99.5% monthly] | [FILL: what counts as down] |
| NFR-5 | RPO / RTO | [FILL: e.g. 15 min / 1 h] | [FILL: scope] |

## 6. Integrations and Interfaces

### 6.1 Upstream dependencies (we call)

| System | Purpose | Protocol / auth | Limits / SLA | On failure |
|---|---|---|---|---|
| [FILL: system or N/A] | [FILL] | [FILL] | [FILL] | [FILL: fail / degrade / queue / stale] |

### 6.2 Downstream consumers (call us or consume our events)

| Consumer | Interface | Compatibility promise |
|---|---|---|
| [FILL: consumer or N/A] | [FILL] | [FILL] |

### 6.3 API and event surface

- [FILL: style (REST/GraphQL/gRPC/events), main endpoints or topics, versioning]

### 6.4 Failure handling

- **Timeouts and retries:** [FILL]
- **Idempotency:** [FILL: which writes need keys, and the dedup window; or N/A: reason]
- **Dual writes:** [FILL: outbox/CDC, or N/A: single store]

## 7. Security and Compliance

- **Authentication:** [FILL]
- **Authorization model:** [FILL: roles, ownership, tenant isolation]
- **Sensitive data:** [FILL: PII/financial/health classes and protection]
- **Secrets:** [FILL: where stored, how rotated]
- **Compliance:** [FILL: regimes, or N/A: reason]
- **Abuse cases:** [FILL: top threats and mitigations]

## 8. Operations

- **Hosting and environments:** [FILL]
- **CI/CD:** [FILL: existing pipeline or to be created]
- **Observability:** [FILL: logs, metrics, traces, alerts on symptoms]
- **Ownership and on-call:** [FILL]
- **Testing frameworks:** [FILL: unit, integration, e2e tools]

## 9. Track-Specific Requirements

<!-- GUIDE: Keep only the subsection that matches **Track:** above. -->

### 9A. Greenfield

- **Why a new system:** [FILL]
- **Architecture shape:** [FILL: modular monolith / services, and why]
- **Build versus buy:**

  | Capability | Decision | Rationale |
  |---|---|---|
  | [FILL] | [FILL: build / buy / OSS] | [FILL] |

- **Stack:** [FILL: language, framework, DB, hosting, each with a one-line reason]
- **Seed or initial data:** [FILL or N/A: reason]
- **Local developer setup:** [FILL]

### 9B. Brownfield

- **Blast radius:** [FILL: tables, endpoints, jobs and views affected, with paths]
- **Convention to mirror:** [FILL: closest existing feature, with path]
- **Must stay unchanged:** [FILL: reference INV-n IDs]
- **Hot-path risks:** [FILL: N+1 queries, indexes, lock contention]
- **Schema change plan:** [FILL: expand / migrate / contract steps]
- **Feature flag and kill switch:** [FILL: name, off-behaviour, removal date]
- **Backward compatibility:** [FILL: consumers and rules]

### 9C. Migration

- **Driver and definition of done:** [FILL]
- **Parity matrix:**

  | Capability | Decision | Notes |
  |---|---|---|
  | [FILL] | [FILL: keep as-is / redesign / deprecate] | [FILL] |

- **Data mapping and ID strategy:** [FILL]
- **Bad-record handling:** [FILL]
- **Backfill and sync:** [FILL: bulk + CDC / freeze-and-copy]
- **Cutover pattern:** [FILL: strangler fig / cohort / big bang, and why]
- **Parity verification:** [FILL: shadow reads, reconciliation, accepted mismatch rate]
- **Rollback window:** [FILL: until when, and how data written in the new system is handled]

## 10. Unknowns and Assumptions Register

<!-- GUIDE: One row per UNK-n referenced above, plus any free-standing open questions. Owner, Action and Due are required. Due = a date or the milestone it must be resolved before. Write "None" under the table if there are no rows, and delete the example row. -->

| ID | Type | Item | Owner | Action | Due |
|---|---|---|---|---|---|
| UNK-1 | [FILL: Unknown / Assumption] | [FILL: question, or assumption + rationale] | [FILL] | [FILL: how it gets resolved] | [FILL: date or "before M1"] |
