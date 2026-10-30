---
name: feature
description: End-to-end workflow for building a feature with the role agents - design the contract, implement backend/frontend/data/infra in parallel, integration-test, then review. Run as /enterprise-fullstack:feature followed by a description of the feature.
disable-model-invocation: true
argument-hint: <feature description or ticket id>
---

# Feature workflow

The user wants to build: **$ARGUMENTS**

You are the orchestrator. You delegate to subagents and keep track of progress. Do not write feature code yourself.

## 0. Name the feature

Pick a short kebab-case slug for the feature (e.g. `order-returns`). All artifacts go in `docs/specs/<slug>/`.
If `docs/specs/<slug>/` already exists, read it and resume from the first unchecked task instead of starting over.

## 1. Design (architect)

Delegate to the **architect** agent with the full feature description and the slug. Pass it the path of `templates/tasks.md` in this skill's base directory as the format for `tasks.md`.
When it returns:
- Read `docs/specs/<slug>/README.md` and show the user the scope, key decisions, and open questions.
- **Stop and wait for the user** to answer open questions and approve the design. Do not proceed on an unapproved design.

## 2. Implement (in parallel)

Read `docs/specs/<slug>/tasks.md`. Group unchecked tasks by owner role.
Launch the owning agents in parallel where tasks are independent:
- **backend-engineer**: migrations, services, endpoints, consumers
- **frontend-engineer**: UI built against openapi.yaml
- **data-engineer**: pipelines, backfills, indexing jobs
- **platform-engineer**: compose services, Dockerfiles, CI, deploy config

Give each agent: the slug, the exact task lines it owns, and "read docs/specs/<slug>/ first".
Ordering rule: if a frontend or data task depends on a backend migration or topic, the backend task goes first.

When agents return, check `tasks.md` and the reported test results. Re-delegate anything incomplete or failing, including the failure output.

## 3. Integration test (test-engineer)

Delegate to **test-engineer** with the slug. If it reports implementation bugs, send each one back to the owning agent with the failing test, then re-run test-engineer.

## 4. Review (code-reviewer)

Delegate to **code-reviewer** with the slug and base branch. Send blockers and should-fix findings back to the owning agents. Re-review once after fixes.

## 5. Wrap up

Report to the user:
- what was built (one paragraph)
- test commands run and their results
- any remaining nits or follow-ups
- a suggested PR title and description

Do not commit or push unless the user asks.
