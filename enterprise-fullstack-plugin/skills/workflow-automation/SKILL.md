---
name: workflow-automation
description: CI/CD pipelines and workflow automation - GitHub Actions or Azure DevOps pipeline structure, build/test/scan/deploy stages, caching, environments and approvals, scheduled jobs, and scripting repetitive developer tasks. Use when creating or changing pipelines, scheduled automations, or developer tooling scripts.
---

# Workflow automation and CI/CD

TODO(team): GitHub Actions, Azure DevOps Pipelines, GitLab CI, or Jenkins? Keep only the relevant section and add your shared templates/reusable workflows.

## Pipeline stages (in order)

1. **Validate**: lint, format check, type-check (Java, TS, Python).
2. **Test**: unit tests, then integration tests (Testcontainers needs Docker on the runner).
3. **Scan**: dependency vulnerabilities, SAST, secret scanning, container image scan.
4. **Build**: container image tagged with the commit SHA; push to registry; record the digest.
5. **Deploy dev**: automatic on main. Run migrations, then roll out.
6. **Deploy higher envs**: same digest, gated by environment approvals.

## Conventions

- Path filters so a frontend-only change doesn't run the backend pipeline (monorepos).
- Cache dependencies (Gradle, npm, pip) keyed on lockfiles.
- Cloud auth via OIDC federation (GitHub -> Azure federated credential / AWS role). No stored cloud keys.
- Pin third-party actions/tasks to a full commit SHA or exact version.
- Required checks on PRs: validate + test + scan.
- Pipelines are idempotent and re-runnable.

## GitHub Actions skeleton

```yaml
name: backend
on:
  pull_request:
    paths: ["backend/**"]
  push:
    branches: [main]
    paths: ["backend/**"]
permissions:
  contents: read
  id-token: write   # OIDC to cloud
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { distribution: temurin, java-version: "21", cache: gradle }
      - run: ./gradlew build integrationTest
        working-directory: backend
```

## Scheduled and event-driven automation

- Scheduled jobs (reports, cleanups, syncs) are code in the repo with their schedule in IaC or pipeline config, not ad hoc cron on a VM.
- Each automation logs a run summary and alerts on failure. Long-running workflows (multi-step, with retries/compensation) belong in a workflow engine (Step Functions, Logic Apps/Durable Functions, Temporal, Airflow) rather than a script.

## Developer scripts

- Put repetitive local tasks in a `Makefile` or `scripts/` with `--help`. Scripts are `set -euo pipefail`, idempotent, and safe to re-run.

## Checklist

- [ ] Validate, test, scan stages before build/deploy
- [ ] OIDC, no stored cloud secrets
- [ ] Actions/tasks pinned
- [ ] Same artifact promoted across environments
- [ ] Failures alert someone
