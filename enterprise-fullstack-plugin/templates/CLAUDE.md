# Project guide for Claude

Copy this file to the root of each repository as `CLAUDE.md` and fill in the TODOs.
Keep it short: it is loaded into every session and every agent. Detailed how-tos belong in skills.

## What this repo is

TODO(team): one paragraph. What the system does, who uses it, which services live here.

## Layout

TODO(team): adjust to the real tree.

```
backend/            Spring Boot services (Java 21, Gradle)
  src/main/resources/db/migration/   Flyway migrations
frontend/           React + TypeScript (Vite), SASS
pipelines/          Python ETL jobs
infra/              IaC (Terraform/Bicep/CDK), Dockerfiles
docker-compose.yml  Local stack: postgres, kafka, redis, elasticsearch
docs/specs/         Feature specs written by the architect agent
```

## Commands

TODO(team): replace with the real ones.

| Task | Command |
|---|---|
| Start local stack | `docker compose up -d` |
| Backend build + tests | `cd backend && ./gradlew build` |
| Frontend type-check / lint / test | `cd frontend && npx tsc --noEmit && npm run lint && npm test` |
| Pipelines tests | `cd pipelines && pytest -q` |
| Integration tests | `cd backend && ./gradlew integrationTest` |

## Rules that apply everywhere

- Contract first: every new or changed endpoint is defined in `docs/specs/<feature>/openapi.yaml` before it is implemented.
- Never edit a committed Flyway migration. Add a new one.
- No secrets in the repo. Use environment variables locally and the secret store in cloud.
- Every change ships with tests. Run them and report the result before calling work done.
- Follow existing patterns in the surrounding code before introducing new ones.

## Workflow

For a new feature, run `/enterprise-fullstack:feature <description>`. It drives:
architect -> backend/frontend/data/platform engineers (parallel) -> test-engineer -> code-reviewer.

## Branches and commits

TODO(team): e.g. `feature/<ticket>-<slug>`, Conventional Commits, PR template location.
