# Core intake checklist (spec sections 1–8)

Use this file during Phase 2. For each section it lists **what the spec needs** and
**probes** to ask when recon and the user's documents leave a gap. **Triggers** are
conditional follow-ups: ask them only when the condition holds. Do not read the probes
aloud as a questionnaire. Pick the 4–6 that matter most for the current round.

---

## 1. Context and problem (Round 1)

Needs: the problem in one paragraph, who has it, how it is handled today, and how success
will be measured.

Probes:

- What happens today without this system? What does that cost (time, money, errors, churn)?
- Who are the primary users, and who are the secondary stakeholders (ops, support, finance, compliance)?
- How will you know it worked 3 months after launch? Ask for a metric with a baseline and a target.
- Is there a hard date, and what is driving it (contract, event, deprecation)?

Triggers:

- The user gives only output metrics ("ship X") → ask for an outcome metric ("reduce Y from A to B").
- Several user groups with conflicting needs → ask which group wins a conflict.

## 2. Scope (Round 1)

Needs: in scope, MVP versus later, **explicit non-goals**, and constraints (team, budget,
deadline, mandated technology).

Probes:

- What is the smallest version that would be worth shipping?
- What will people assume is included but is not? These are the non-goals. Offer 3 candidates from what you have heard so far and let the user confirm or reject them.
- Is any technology mandated or forbidden (language, cloud, database, vendor)?
- Who will build and maintain it, and at what skill level? A solo developer and a 10-person team need different plans.

Triggers:

- No non-goals after one ask → propose them yourself as `[ASSUMED: UNK-n]`. The validator requires at least one.
- A deadline under 4 weeks with broad scope → ask the user to rank features so the MVP cut is explicit.

## 3. Functional requirements and invariants (Round 1)

Needs: actors and roles, `US-n` stories with acceptance criteria, **`INV-n` hard business
invariants**, and the important edge or error states.

Probes:

- Walk me through the main workflow from the user's first action to the final outcome.
- For each step: who can do it, and what happens if it fails halfway?
- What must **never** happen? For example: double charge, oversold inventory, a user seeing another tenant's data, a lost submission, two people booking the same slot.
- Which actions must be reversible, and which are final?

Triggers:

- Money, balances, credits, inventory, seats, quotas or counters → ask how concurrent updates are isolated (row lock, optimistic version, serializable transaction, single writer). Record an `INV-n` and require an idempotency-key strategy in section 6.
- Multi-tenant data → add a tenant-isolation `INV-n` and ask how the tenant is enforced (query scoping, row-level security, separate schemas).
- Workflows that span several steps or services → ask about partial-failure semantics (saga or compensation versus a single transaction).
- Approval or state-machine flows → enumerate the states and the forbidden transitions as invariants.

Acceptance criteria format: `Given / When / Then`, or a short testable bullet list. Each
`US-n` needs at least one criterion.

## 4. Data and storage (Round 2)

Needs: core entities and relationships, system of record for each, derived or cached
views, access patterns, read/write ratio, consistency tolerance, and retention and volume
growth.

Probes:

- What are the main things the system stores, and which system owns each one (here or elsewhere)?
- What are the top 3 queries users will run, and the top 3 writes?
- How stale can a read be before it is wrong for the user: never, seconds, minutes, or until tomorrow?
- How much data on day one, and how fast does it grow? How long must it be kept, and must anything be deleted on request?

Triggers:

- Search, feeds, dashboards or analytics → separate the system of record from derived views and ask how the views are refreshed (synchronously in the transaction, outbox or CDC, batch).
- "Never stale" plus derived views → flag the tension and record the chosen trade-off as a decision.
- Files or media → ask about object storage, size limits, and virus or content scanning.
- Time-series or event data → ask about the partitioning and retention mechanism.

## 5. Scale and SLOs (Round 2)

Needs: `NFR-n` rows for p95 latency, p99 latency, peak throughput, availability target,
data volume, and RPO/RTO where data loss matters.

Probes:

- How many users or requests at launch, and at peak (time of day, seasonality, campaigns)?
- Which interaction must feel instant, and which can take seconds or run in the background?
- What does an hour of downtime cost? That sets the availability target.
- How much recent data can be lost in a disaster (RPO), and how fast must service return (RTO)?

Triggers:

- The user does not know the numbers → offer an order-of-magnitude bracket (10 / 100 / 1,000 req/s) and log the choice as `[ASSUMED: UNK-n]` with "measure after M1" as the action. Never invent a precise figure.
- Batch or CLI tools → p95/p99 can be `N/A: batch job; target is total runtime < X`. Add a runtime NFR instead.
- Availability of 99.9% or higher → ask about multi-zone deploys, health checks and on-call, because the target drives operations cost.

## 6. Integrations and interfaces (Round 2)

Needs: upstream dependencies (what we call), downstream consumers (who calls us or
consumes our events), API style and contracts, and failure handling for each integration.

Probes:

- Which external systems or APIs does this depend on? What are their rate limits, SLAs and auth methods?
- Who consumes our data or API? Are there contract-compatibility promises?
- When dependency X is down or slow, should we fail, degrade, queue, or serve stale data?

Triggers:

- Any non-idempotent write that is retried (payments, emails, orders) → require an idempotency key and a dedup window.
- Writes to the database plus a message, email or webhook in the same operation → flag the dual-write problem and plan a transactional outbox or equivalent.
- Asynchronous messaging → ask about ordering, retries, a dead-letter queue, poison messages and replay.
- A third-party API on a hot path → ask about timeouts, a circuit breaker, caching and cost per call.

## 7. Security and compliance (Round 3)

Needs: authentication, the authorization model, sensitive data classes, secrets handling,
compliance regimes, and the main abuse cases.

Probes:

- How do users log in (existing IdP, OAuth, magic link, API keys)? Do machines call the API too?
- Who can see or change what? Roles, ownership, tenant boundaries.
- What personal, financial or health data is stored? Any regulatory requirements (GDPR, CCPA, HIPAA, PCI, SOC 2)?
- What is the worst thing a malicious user could do with this feature?

Triggers:

- PII → ask about encryption at rest, access logging, a deletion or export path, and data residency.
- Payments → keep card data out of scope by using the provider's hosted fields or tokens, and say so.
- Public endpoints → rate limiting, bot protection and input-size limits.
- File uploads → content-type validation, size limits and scanning.

## 8. Operations (Round 3)

Needs: hosting and environments, CI/CD, observability (logs, metrics, traces, alerts),
ownership and on-call, and the testing frameworks to use.

Probes:

- Where will it run, and how do deploys happen today (or how should they)?
- What would tell you it is broken before a user does? Define alerts on symptoms, not causes.
- Who gets paged, or is best-effort fine?
- Which test frameworks and coverage expectations already exist?

Triggers:

- No CI exists → M0 must create it. Note this.
- Several environments → ask about config and secrets per environment, and how production data is kept out of dev.
- Background jobs or schedulers → ask about job monitoring, missed-run alerts and safe re-runs.
