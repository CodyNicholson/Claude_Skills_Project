---
name: visual-lab
description: Build a "visual lab" for any tool, library, framework, database or service - a new <Tool>_Visual_Lab_Project folder with a Dockerized backend that runs every feature for real, a React frontend with an animated, explained page per feature (including how not to use it, common errors and their fixes), and the git-ignored pipeline-run.sh that deploys it behind the Cloudflare tunnel (rixus-frontend:80 on tunnel-net). Use when the user asks for a visual lab, visual project, interactive demo site or feature explorer for a named technology, e.g. "/visual-lab RabbitMQ" or "make a visual lab for Polars".
argument-hint: <tool or library name> [notes, e.g. backend language, frontend framework, target folder]
---

# Visual lab builder

Build a complete, deployable visual lab for **$ARGUMENTS**, following the conventions of
the existing labs in `/home/rixus/workspace` (Redis, Kafka, Flink, LangChain/LangGraph).

The result is a new folder `<Tool>_Visual_Lab_Project` in which:
- a backend runs **every major feature of the tool for real** (no faked results), one
  endpoint per feature, each returning the commands it ran and self-checks it verified;
- a frontend gives each feature its own page: a plain-language explanation, an animated
  request-flow diagram, buttons that run the demo, an animated visual of the result, the
  code, and the commands and checks; plus an overview/getting-started page with pros and
  cons, and a "Run all demos" self-test page;
- the lab also teaches how **not** to use the tool: anti-patterns, the errors people hit most
  (with the exact error text), and how to avoid and fix each one, on every feature page and on
  a searchable "Mistakes, errors & fixes" page, with real reproductions where safe;
- `docker compose up -d --build` runs everything; `pipeline-run.sh` deploys it to the
  Cloudflare tunnel exactly like the other labs.

Skill files (paths relative to this SKILL.md's directory, `~/.claude/skills/visual-lab/`):
- `scripts/scaffold.sh`: creates the folder from `templates/` (never overwrites files)
- `scripts/test-isolated.sh`: builds, starts and smoke-tests the stack without touching the live app
- `references/conventions.md`: deploy contract, DemoResult contract, catalog schema, pitfalls / anti-patterns / troubleshooting, visual ideas, safety, README outline. **Read it before writing demos.**
- `references/backends.md`: choosing the backend language; Spring Boot, Node, browser-only and SSE notes

If `$ARGUMENTS` is empty, ask which tool or library the lab is for, then continue.

## Workflow

Keep the session log required by the user's CLAUDE.md up to date at each step.

### 1. Pin down the target

- Tool name as the user wrote it, e.g. "RabbitMQ". Folder:
  `/home/rixus/workspace/<Tool>_Visual_Lab_Project` (spaces and dots → `_`, e.g.
  `Apache_Pulsar_Visual_Lab_Project`) unless the user names another. Slug: lower-case
  dashes, e.g. `rabbitmq-lab`.
- If the folder already exists, look at it first. An empty clone (only `.git`, README,
  LICENSE) is fine to fill; anything with real content: ask before touching it.
- Note any user preferences in `$ARGUMENTS` (backend language, Angular instead of React,
  specific features). The defaults are React + Vite and the backend from
  `references/backends.md`. Don't ask about choices that have a sensible default.

### 2. Research the tool (current, not from memory)

- Find the **current stable version** (Docker Hub tag, `pip index versions`, `npm view`,
  Maven Central, GitHub releases) and check the official docs for what changed recently.
  Run version checks inside Docker containers; the host has no node and only Python 3.10.
- Build a **feature inventory**: every major feature, API family and operational concern
  in the official docs, grouped into 4–8 categories ordered from basics to advanced to
  operations. Aim for complete coverage of what a user of the tool would need to know,
  usually 12–30 demos. Write the inventory (with doc URLs) into the session log.
- Build a **pitfall inventory** too, from sources rather than memory: the official
  troubleshooting / FAQ / common-errors pages, migration and upgrade guides, the most-voted
  Stack Overflow questions for the tool's tag, and the GitHub issues with the most reactions or
  duplicates. Collect (a) anti-patterns: ways the tool is misused or used for the wrong job;
  (b) general errors: install, connection, auth, config, version upgrades; (c) per-feature
  mistakes. For each: the exact error text in the current version, the cause, the fix, and how
  to avoid it. Mark which ones the lab can reproduce safely. Write it, with URLs, into the
  session log.
- Note features that cannot run in a single-host lab (multi-region clusters, paid cloud
  features) and list them under "Notes and limits" in the README rather than faking them.
  Where a small multi-container setup can show it (replicas, a 3-node cluster), prefer
  showing it.

### 3. Scaffold

```bash
bash ~/.claude/skills/visual-lab/scripts/scaffold.sh \
  --dir /home/rixus/workspace/<Tool>_Visual_Lab_Project --tool "<Tool>" --slug <slug> \
  --backend python-fastapi|node-express|none [--port <api port>] [--test-port 3900]
```

This creates `pipeline-run.sh`, `git-pull-project.sh`, `.gitignore`, `.env.example`, a
chmod-600 `.env`, `docker-compose.yml`, `docker-compose.test.yml`, the React frontend
starter and, for Python or Node, a backend starter with one example demo. For Spring Boot,
Go or a browser-only lab use `--backend none` and follow `references/backends.md`.

If the folder is not a git repository, run `git init -b main` there (local only). Don't
add remotes, commit or push unless the user asks.

### 4. Backend: one real demo per feature

- Add the tool's own service(s) to `docker-compose.yml` (pinned image tag, healthcheck,
  volume, only on the internal `backend-net`) and mirror each renamed container in
  `docker-compose.test.yml`. Bind any host port to `127.0.0.1` (see "Public-site safety"
  in `references/conventions.md`).
- Implement every feature in the inventory as an endpoint under `/api/demos/...` that
  calls the real tool and returns the DemoResult (`commands`, `data`, `checks`,
  `elapsedMs`). Checks must prove the behaviour the page explains.
- Reproduce the pitfalls marked safe: a "Do it wrong" mode on the feature's endpoint (or a
  demo in a "Common mistakes" category) that runs the mistake against the real tool, records
  the genuine error with `d.attempt(...)`, then runs the fix. Checks pass when the failure
  happened as described and the fix worked. Reset any state the mistake damages.
- Seed any data the demos need on startup, idempotently.
- Clamp every visitor-controlled number; never run visitor-supplied code. Paid APIs:
  offline mode by default, live mode only with a key in `.env`, rate-limited.
- Secrets go in `.env` (listed, empty, in `.env.example`) and reach containers only through
  `environment:` entries in compose. Passwords get no fallback (`${DB_PASSWORD:?Set
  DB_PASSWORD in .env}`); add them to `GENERATED_SECRETS` in `pipeline-run.sh`.
- Destructive or admin endpoints (reset, flush, wipe, drop) need a token (`X-Admin-Token`
  equal to `ADMIN_TOKEN`, compared in constant time) and are off while the token is empty.
  Prefer resetting per demo inside the demo itself. Never document an unauthenticated
  `curl -X POST …/reset` in the README or compose comments.
- Tests: the backend test suite calls every demo endpoint and fails on any failed check.

### 5. Frontend: explain and animate every feature

Edit the starter in `frontend/src/` (see `references/conventions.md`):
- `demos/catalog.js`: `NODE_META`/`NODE_ORDER` named after the tool's real components,
  `CATEGORIES`, and one `DEMOS` entry per backend demo (explanation paragraphs, keyApis,
  useCases, snippet, inputs, flow steps, actions, visual, test).
- `pitfalls` on every `DEMOS` entry (1–4: mistake, exact symptom, why, fix, avoid, optional
  Don't/Do code and a `reproduce` action id). Vitest fails if any demo has none.
- `visuals/`: one animated visual component per demo, grouped in a file per category and
  registered in `visuals/index.js`. Make the feature visible: things should move, fill,
  re-sort, light up or count down. Never just print JSON.
- `demos/guide.js`: the overview page content (mental model, versions, typed-out
  getting-started steps, pros, cons, when to use / not use, alternatives) plus
  `antiPatterns` (how not to use the tool) and `troubleshooting` (general errors). Both also
  feed the `#pitfalls` page. See "Pitfalls, anti-patterns and troubleshooting" in
  `references/conventions.md` for what good entries look like.
- `App.css`: set `--accent`, `--accent-rgb`, `--accent-text` to suit the tool, add a color
  variable for each diagram node, add per-visual styles at the bottom. Keep the layout
  usable on a phone.
- `App.jsx`: update the header tagline; set `LIVE_EVENTS = true` if the backend streams SSE.
- Write explanations in plain language for someone new to the tool: what it is, why it
  matters, what to watch while it runs.
- Generate `package-lock.json` inside Docker so builds use `npm ci`:
  `docker run --rm --user "$(id -u):$(id -g)" -e npm_config_cache=/tmp/.npm -v "$PWD/frontend":/app -w /app node:22-alpine npm install --no-audit --no-fund`
  then delete the host `frontend/node_modules` it leaves behind (the image installs its own).

### 6. Verify (never with pipeline-run.sh)

Run each step and record the real results in the session log:

```bash
cd <lab dir>
docker build --target test backend          # backend tests (if the backend has a test stage)
docker build --target test frontend         # Vitest: catalog completeness + every page renders
bash ~/.claude/skills/visual-lab/scripts/test-isolated.sh <lab dir>        # up + smoke test
bash ~/.claude/skills/visual-lab/scripts/test-isolated.sh <lab dir> down   # always clean up
```

`test-isolated.sh` first runs `scripts/security-check.sh` and stops on any FAIL (a host port
not bound to `127.0.0.1`, a password with a fallback value, a non-frontend service on
`tunnel-net`, `.env`/`pipeline-run.sh`/`claude_logs/` tracked or in git history). Resolve its
`warn` lines too: each admin/reset route it lists must be token-protected. It then runs the stack as a separate compose project with renamed containers,
no `tunnel-net` and only the UI published (default http://localhost:3900), then checks the
UI, `/api/health` and every catalog `test` call through nginx. It refuses to start if a
container would be called `rixus-frontend` or `cloudflared-tunnel`. Fix every failure
before finishing. If a port is taken, pass `--test-port` at scaffold time or edit
`docker-compose.test.yml`.

Never run `pipeline-run.sh`, `docker compose up` without `-p`, or anything that removes
other containers: only one app is live in the tunnel and those would replace it.

### 7. Finish

- Write `README.md` following the outline in `references/conventions.md`, with the
  feature coverage table, the "How not to use it and common errors" section with source
  links, and the tests you actually ran.
- Confirm `git status` shows neither `.env` nor `pipeline-run.sh` (`git check-ignore -v`
  both), and run `bash ~/.claude/skills/visual-lab/scripts/security-check.sh <lab dir>` again
  before any commit or push: GitHub repos are public.
- Commit only if the user asks, using their git identity, and with no AI attribution
  (no `Co-Authored-By` naming an AI and no "Generated with" lines), per their CLAUDE.md.
- Tell the user: the folder, what the lab covers (categories and demo count, and how many
  anti-patterns and pitfalls, how many reproduced for real), how it was
  verified with pass/fail numbers, anything not demonstrated, and that running
  `./pipeline-run.sh` deploys it to the tunnel and replaces the app that is live now.
