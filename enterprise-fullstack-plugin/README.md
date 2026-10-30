# enterprise-fullstack: Claude Code plugin

Role-based agents, convention skills, and guardrail hooks for enterprise full stack work:
Java/Spring Boot, Postgres/Flyway, Kafka, Redis, Elasticsearch, React/TypeScript/SASS, D3/Three.js,
Python ETL, Docker/Compose, Azure/AWS, CI/CD, and integration testing.

## What's inside

```
enterprise-fullstack/
├── .claude-plugin/plugin.json      plugin manifest
├── agents/                         roles (each runs in its own context)
│   ├── architect.md                designs: spec, OpenAPI, data model, tasks (writes docs/specs only)
│   ├── backend-engineer.md         Java/Spring, Postgres/Flyway, Kafka, Redis, Elasticsearch
│   ├── frontend-engineer.md        React/TS, SASS, D3, Three.js
│   ├── data-engineer.md            Python ETL, backfills, indexing jobs
│   ├── platform-engineer.md        Docker/Compose, CI/CD, Azure/AWS IaC
│   ├── test-engineer.md            Testcontainers, contract, Playwright
│   └── code-reviewer.md            read-only review against spec + skills
├── skills/                         team conventions, loaded on demand
│   ├── feature/                    /enterprise-fullstack:feature - the orchestration workflow
│   ├── api-design/                 + templates/openapi.yaml
│   ├── db-migrations/              + scripts/new-migration.sh
│   ├── spring-service/             (includes Redis caching)
│   ├── event-streaming/            Kafka, outbox, idempotent consumers, DLT
│   ├── search-indexing/            Elasticsearch
│   ├── react-ui/
│   ├── data-viz/                   + references/d3.md, references/three.md
│   ├── etl-pipeline/
│   ├── local-env/                  + templates/docker-compose.yml
│   ├── cloud-deploy/               + references/azure.md, references/aws.md
│   ├── integration-testing/
│   └── workflow-automation/
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       ├── protect-migrations.sh   blocks edits to committed Flyway migrations
│       └── format-file.sh          runs project prettier / ruff after edits
└── templates/
    ├── CLAUDE.md                   copy into each repo root and fill in
    └── mcp.example.json            example MCP servers (not auto-loaded)
```

## Install

**Try it locally** (loads the plugin for one session):
```bash
claude --plugin-dir /path/to/enterprise-fullstack
```

**Share with a team**: put this folder in a git repo set up as a plugin marketplace (with a `marketplace.json`; see the Claude Code plugin docs), then teammates run:
```
/plugin install enterprise-fullstack --marketplace <owner>/<repo>
```
(On older Claude Code versions: `/plugin marketplace add <owner>/<repo>` then `/plugin install enterprise-fullstack@<marketplace-name>`.)

Validate the structure after changes:
```bash
claude plugin validate /path/to/enterprise-fullstack
```

Hook scripts need `bash` and `git`, and `jq` or `python3` to read the hook payload.

## Using it

1. Copy `templates/CLAUDE.md` to your repo root and fill in the TODOs (layout, commands, rules).
2. Build a feature end to end:
   ```
   /enterprise-fullstack:feature Add order returns: customers can request a return within 30 days
   ```
   architect -> (approve design) -> engineers in parallel -> test-engineer -> code-reviewer.
3. Or call a role directly: "Use the backend-engineer agent to add a Kafka consumer for ...",
   "Use the code-reviewer agent on this branch".
4. Skills also load on their own when a task matches (e.g. writing a migration loads db-migrations).

## Customizing (start here)

Every place that needs your team's real conventions is marked `TODO(team)`:
```bash
grep -rn "TODO(team)" .
```

Suggested order:
1. `templates/CLAUDE.md` -> your repo
2. Build/test commands in each agent file
3. `api-design`, `db-migrations`, `event-streaming`, `integration-testing` (highest-leverage conventions)
4. Everything else as you notice Claude getting something wrong

Tips:
- A skill's `description` decides when it loads. If a skill isn't being picked up, make its description more specific about the situations it covers.
- Keep SKILL.md files focused; move long material into `references/` and point to it.
- Add a `model:` (e.g. a faster model) to agents that do routine work if you want to save cost.
- Hooks enforce rules; skills only ask. If something must never happen, make it a hook.
