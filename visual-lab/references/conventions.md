# Visual lab conventions

Distilled from the workspace labs: `Redis_Visual_Lab_Project` (closest match to the starter),
`Kafka_Visual_Lab_Project` and `Flink_Visual_Lab` (live SSE telemetry driving a topology),
`LangChain_LangGraph_Visual_Project` (Angular + FastAPI, setup guides, pros/cons page,
`.env` secrets). Open those for working examples of anything below.

## Contents
- Deploy contract
- Folder layout
- The DemoResult contract
- Catalog entry schema
- What every feature page shows
- Pitfalls, anti-patterns and troubleshooting
- Animation toolkit
- Overview page
- Self-test suite
- Public-site safety
- README outline

## Deploy contract (do not change)

- The public UI container is named **`rixus-frontend`**, listens on **:80**, and joins the
  external **`tunnel-net`** network. The Cloudflare tunnel routes to `http://rixus-frontend:80`.
- `pipeline-run.sh` (git-ignored): create `.env` from `.env.example` if missing, read
  `TUNNEL_TOKEN` (global env first, then only that one line of `.env`), run
  `git-pull-project.sh`, **remove all containers on the host**, start `cloudflared-tunnel`
  on `tunnel-net`, then `docker compose up -d --build`.
- `git-pull-project.sh` (committed) skips the pull when the branch has no upstream.
- Only one app is live at a time. **Never run `pipeline-run.sh` to test**: it tears down the
  live app. Test with `scripts/test-isolated.sh` from the skill.
- nginx in the frontend image serves the build and proxies `/api/` to `backend:<port>` using
  Docker DNS (`resolver 127.0.0.11`) and a variable upstream, so nginx starts before the
  backend does. Buffering is off so SSE streams pass through.

## Folder layout

```
<Tool>_Visual_Lab_Project/
├── .env                  # real secrets, git-ignored, chmod 600
├── .env.example          # every variable, empty values, comments
├── .gitignore            # .env*, pipeline-run.sh, build output, claude_logs/
├── README.md
├── docker-compose.yml    # tool service(s) + backend + rixus-frontend
├── docker-compose.test.yml
├── git-pull-project.sh
├── pipeline-run.sh       # git-ignored
├── backend/              # Dockerfile with `test` and `runtime` stages
└── frontend/             # Dockerfile with `build`, `test`, `runtime` stages; nginx.conf
```

## The DemoResult contract

Every demo endpoint returns:

```json
{
  "demo": "feature-id",
  "commands": ["the exact calls / commands / queries the backend ran, with timings"],
  "data": { "whatever the visual needs to draw" },
  "checks": [{ "name": "What was verified", "passed": true, "detail": "measured value" }],
  "elapsedMs": 12.3
}
```

- `commands` are real: the actual API calls, CLI commands, SQL, HTTP requests or code paths
  executed, in order. The UI types them out in a terminal.
- `checks` prove the feature behaved as explained: "INCR lost no updates", "the retry landed
  on the DLT", "graph resumed from checkpoint 3". Each demo has 1–5 checks. The UI's
  self-test suite and the backend tests both fail if any check fails.
- Errors return a non-2xx status with `{ "error": "message" }`.
- `/api/health` returns 200 once the backend can reach the tool.
- Live streams (optional): `GET /api/events/stream`, SSE event name `lab-event`, payload
  `{ type, ts, ...}`; set `LIVE_EVENTS = true` in `App.jsx`. Use this when the tool is
  asynchronous (brokers, stream processors, pub/sub, schedulers, agents) so the UI animates
  each step as it actually happens, as in the Kafka and Flink labs.

## Catalog entry schema (`frontend/src/demos/catalog.js`)

```js
{
  id: 'kebab-id',                    // also the URL hash
  category: 'One of CATEGORIES',     // 4–8 categories, ordered basics → advanced → operations
  title: 'Feature name',
  tagline: 'One line: what it gives you',
  description: [                     // 2–4 short paragraphs, plain language
    'What it is and the problem it solves (the mental model).',
    'What the buttons do and what to watch in the diagram and visual.',
    'Limits, gotchas, production advice.',
  ],
  keyApis: ['function()', 'CONFIG_OPTION'],   // names a reader can search the docs for
  useCases: ['Real-world use', '…'],
  snippet: { lang: 'python', name: 'demo.py', code: '…' },  // the real code the backend runs, trimmed
  inputs: [{ name, label, type: 'text'|'number'|'select'|'textarea'|'checkbox'|'color', default, options?, min?, max? }],
  flow: [['ui','api','POST /api/demos/x'], ['api','tool','…'], ['tool','tool','work inside the node'], …],
  actions: [{
    id, label, method: 'GET'|'POST'|'PUT'|'DELETE',
    path: '/api/demos/x' | (inputs) => string,
    params?: (inputs) => ({ query params }), body?: (inputs) => ({ JSON body }),
    tone?: 'accent'|'store'|'ghost',
    flow?: (inputs) => steps,                 // diagram for this button
    flowFor?: (result, inputs) => steps,      // diagram chosen after the result (cache HIT vs MISS)
  }],
  pitfalls: [{                        // 1–4 per demo, see "Pitfalls, anti-patterns and troubleshooting"
    mistake: 'What people do wrong',
    symptom: 'The exact error text or wrong behaviour they see',
    why: 'The cause',
    fix: 'How to resolve it once it happened',
    avoid: 'How to prevent it',
    lang?, wrongCode?, rightCode?,     // side-by-side "Don't" / "Do" code
    reproduce?: 'action id',           // a button that triggers the failure for real
  }],
  visual: 'name in visuals/index.js',
  test: { method: 'POST', path: '/api/demos/x?small=params' },   // used by Run all + test-isolated.sh
}
```

`NODE_META` / `NODE_ORDER` define the diagram participants (browser, backend, the tool's
components such as broker/partition/consumer, storage). Name them after the tool's real
architecture: `producer`, `broker`, `jobmanager`, `taskmanager`, `primary`, `replica`, …
Add a CSS color variable for each.

Keep the `test` path's literal format `test: { method: 'X', path: '…' }` on one line:
`test-isolated.sh` greps it.

## What every feature page shows

Top to bottom (already laid out by `DemoView.jsx`):

1. **Header**: category chip, title, tagline.
2. **How it works**: the paragraphs, Key APIs chips, Used-for chips.
3. **Request flow**: animated SVG diagram; a packet travels each step, the active edge
   dashes, busy nodes glow and pulse; captions and a numbered step list follow along. Replay.
4. **Controls**: inputs and action buttons that call the real backend.
5. **Visual**: a feature-specific animated picture of `result.data`. This is where the lab
   earns its name. One component per feature; never just dump JSON.
6. **The code**: the snippet with copy button.
7. **Common mistakes and how to fix them**: the demo's `pitfalls` (mistake, the real error,
   why, fix, avoid, Don't/Do code, and a "Reproduce it for real" button when `reproduce` is set).
8. **Result panel**: commands typed out line by line, self-checks popping in, server and
   browser timings.

Visual ideas by feature type:
- Counts, sizes, timings, comparisons → animated `Bar`s and `Stat` tiles, before/after pairs.
- Ordering, queues, logs, streams → items that pop in and slide along a tape or lane.
- Concurrency, locks, retries, timeouts → Gantt timelines with lanes per worker.
- Graphs, pipelines, DAGs, topologies → SVG nodes and edges with travelling packets.
- State over time, TTLs, windows → countdown rings, sliding-window tracks, `useNow`.
- Sets, partitions, sharding → Venn diagrams, colored grids, buckets that fill.
- Search, similarity, ranking → ranked lists with score bars that re-sort with transitions.
- Geometry, layout, rendering libraries → draw the actual output in SVG/canvas.
- Errors and failure modes → show the failure happening (red lanes, oversold counters),
  then the fix succeeding beside it.

## Pitfalls, anti-patterns and troubleshooting

A lab teaches how **not** to use the tool as well as how to use it. Three places hold it, and the
`#pitfalls` page (`PitfallsPage.jsx`, "⚠ Mistakes, errors & fixes" in the sidebar) gathers all
three into one page with a search box that visitors can paste an error message into:

- `OVERVIEW.antiPatterns` (`guide.js`): `{ dont, why, instead }` misuses of the tool as a whole:
  the wrong job for it (Redis as the primary database of record, Kafka as a task queue with
  per-message acks, LangChain agents where a single prompt would do), architectures that fight
  its design, scale or cost traps. 4–10 entries. The overview page lists them too.
- `OVERVIEW.troubleshooting` (`guide.js`): `{ mistake, symptom, why, fix, avoid }` errors that
  belong to no single feature: install and dependency conflicts, connection refused / wrong host
  inside Docker, auth and permissions, missing config, breaking changes between major versions,
  platform quirks (ARM images, file watchers, memory limits). 5–12 entries.
- `pitfalls` on every catalog entry: the mistakes specific to that feature, 1–4 each.

Writing them:
- Research them, don't invent them: official troubleshooting / FAQ / "common errors" pages,
  migration and upgrade guides, deprecation notices, the most-voted Stack Overflow questions for
  the tag, the GitHub issues with the most reactions or duplicates, and the tool's own error
  message list. Keep the source URLs in the session log and the README.
- `symptom` is the **exact** error text as the current version prints it (exception class and
  message, CLI output, HTTP status and body), or the precise wrong behaviour when there is no
  error ("the consumer silently re-reads every message after a restart"). That is what people
  search for. Check the wording against the version in the lab.
- `fix` resolves it when it has already happened (commands, config, code change, recovery
  steps for corrupted state). `avoid` is the habit or design that prevents it next time. Keep
  them distinct and concrete: name the setting, flag, method or version.
- Add `wrongCode` / `rightCode` when the difference is visible in a few lines.
- Note when a pitfall is version-specific ("since 4.0", "removed in v2").

Reproduce them for real wherever it is safe:
- Give a feature demo a "Do it wrong" action (`tone: 'ghost'`) and point the pitfall's
  `reproduce` at it. The backend runs the wrong way against the real tool, captures the genuine
  error with `d.attempt(...)` (in both backend starters), then runs the fix. Checks pass when the
  failure happened as described **and** the fix worked, so self-tests stay green.
- For bigger failure modes (lost updates without a transaction, a rebalance storm, an
  unbounded memory blow-up capped at a safe size, a race condition, N+1 queries, a deadlock),
  add demos in a dedicated **"Common mistakes"** category near the end: wrong and right side by
  side in the visual, with a red lane for the failure and a green one for the fix.
- Keep reproductions inside the public-site limits: clamp sizes, cap memory and time, and reset
  any state the mistake damages so the next visitor starts clean. Don't reproduce what would
  crash or wedge the shared service; describe those in the pitfall text only.

## Animation toolkit (already in the starter)

- `FlowDiagram.jsx`: SMIL `animateMotion` packets (started with `beginElement()`), dashed
  edge animation, glow filter, pulse ring.
- CSS keyframes in `App.css`: `fade-up`, `pop`, `grow` (scaleX bars), `rise` (scaleY
  columns), `pulse`, `dash`, `draw` (SVG line drawing via `stroke-dashoffset`), `flash`,
  `type-in`, `blink`. Use `animation-delay: i * 60–90ms` for staggered lists.
- `useStepper(n, runKey, ms)` in `common.jsx` steps through a sequence for "watch it happen"
  visuals; `useNow(ms)` for countdowns; transitions on `width`/`transform` for re-sorting.
- `prefers-reduced-motion` is honoured globally in `App.css` and in `FlowDiagram`.
- No animation libraries are needed. Add one only if a feature truly needs physics or
  complex timelines, and pin its version.

## Overview page (`frontend/src/demos/guide.js`)

The landing page (`#overview`): what the tool is and its mental model, version facts, an
animated "create a project" walkthrough (commands typed in a terminal, then the first
files), honest pros / cons / when to use / when not to use, "How not to use <Tool>"
(`antiPatterns`, linking to `#pitfalls`), alternatives with how they differ, and a clickable
map of every feature. `troubleshooting` lives in `guide.js` too but is shown on `#pitfalls`. For two related tools (LangChain vs
LangGraph) add a side-by-side comparison page like the LangChain lab's `compare-page.ts`.

## Self-test suite

`#suite` runs every demo's `test` call in order and shows pass/fail and check counts; the
sidebar marks each demo ✓/✗. The backend test suite runs the same endpoints (starter:
`test_every_demo_passes_its_own_checks`).

## Public-site safety

The lab is public through the tunnel:
- Clamp every visitor-controlled number (threads, rows, iterations, durations, payload size)
  with `clamp()`; cap request bodies (nginx `client_max_body_size`, framework limits).
- Never execute visitor-supplied code or shell commands. Inputs select among prepared
  scenarios or feed data into fixed code.
- Paid APIs (LLMs, cloud services): default to an offline/mock mode, enable live mode only
  when a key is in `.env`, and rate-limit live runs per minute and hour (see the LangChain
  lab's `ALLOW_LIVE_MODE`, `LIVE_RUNS_PER_MINUTE`, `LIVE_RUNS_PER_HOUR`).
- Secrets only in `.env` → compose `environment:`. Optional keys (paid APIs) use
  `VAR: ${VAR:-}`; passwords the stack needs use `${VAR:?Set VAR in .env}` with **no
  fallback value**, so a missing `.env` stops compose instead of starting with a password
  published in the repo, and are generated by `pipeline-run.sh` (`GENERATED_SECRETS`).
  Same in app config: no `${DB_PASSWORD:postgres}` defaults. Never bake secrets into images,
  the frontend bundle, logs or the README, and keep `.env.example` values empty.
- Host ports: always `"127.0.0.1:<host>:<container>"`. Docker writes its own iptables rules,
  which bypass `ufw`, so a bare `"3000:80"` serves the app on the server's public IP and skips
  Cloudflare (WAF, rate limits, Access). The tunnel reaches `rixus-frontend` over `tunnel-net`,
  which the binding does not affect.
- Networks: only `rixus-frontend` joins `tunnel-net`. Databases, brokers and other tool
  services sit only on `backend-net` (`internal: true`), so the public nginx container cannot
  reach them and they have no route out; the backend joins both `backend-net` and `default`.
- Destructive or admin endpoints (reset, flush, wipe, drop all data): the site has no login,
  so anyone can call `/api/*`. Require `X-Admin-Token` equal to `ADMIN_TOKEN` (constant-time
  compare), answer 404 while `ADMIN_TOKEN` is empty (the default), and keep them out of README
  and compose-comment `curl` examples unless the example sends the token.
- `scripts/security-check.sh <lab dir>` checks the mechanical parts of this list (ports,
  fallback secrets, tunnel-net, git-ignored files and history) and flags admin-style routes.
- Containers: `security_opt: no-new-privileges:true`, non-root user in runtime images,
  memory caps for JVM/heavy services.

## README outline

Title + one-paragraph pitch · What each page shows · Quick start (`docker network create
tunnel-net` once, `docker compose up -d --build`, open http://localhost:3000) · Service /
container / port table · Feature coverage table (Area | Demo | Features/APIs) ·
Architecture diagram (ASCII) · How not to use it and common errors (anti-patterns, then a
table of Error / Cause / Fix / Avoid for the most common errors, with source links; point to the
`#pitfalls` page for the rest) · Configuration (`.env` variables) · Tests (backend, frontend,
in-UI self-test, isolated stack) · Local development · Deployment (pipeline-run.sh, the
`rixus-frontend` contract) · Notes and limits (what is not demonstrated and why).
