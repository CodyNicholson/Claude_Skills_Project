# Skill patterns and audit rubric

Read this file during Step 2 (designing frontmatter and structure) and Step 5 (manual
validation). Sections:

1. Frontmatter specification
2. Description formula
3. Directory layouts
4. Body templates by degree of freedom
5. Companion primitives: hooks, subagents, CLAUDE.md
6. Audit checklist (manual equivalent of `scripts/validate_skill.py`)
7. Refactoring a bloated skill or CLAUDE.md

---

## 1. Frontmatter specification

Fields recognized by Claude Code for `SKILL.md` (checked against Claude Code 2.1.x). Only
`description` is strictly needed for auto-triggering; `name` defaults to the directory
name, but always set it explicitly.

| Field | Type | Purpose and rules |
|---|---|---|
| `name` | string | Slash-command name. 1-64 chars, `^[a-z0-9]+(-[a-z0-9]+)*$`. Must equal the directory name. Avoid `claude` / `anthropic` if the skill will also be uploaded to the Anthropic API. |
| `description` | string | Shown in the Skill tool listing; drives auto-invocation. Under 1,024 chars, no `<` or `>`, third person, what + when. |
| `when_to_use` | string | Extra trigger guidance appended to the tool description. Optional; prefer putting triggers in `description` so other runtimes see them too. |
| `argument-hint` | string | Placeholder shown after `/name` in the menu, e.g. `[env] [--dry-run]`. Set whenever the body uses `$ARGUMENTS`. |
| `allowed-tools` | string or list | Tools pre-approved (no permission prompt) while the skill is active. Comma-separated or YAML list. It does **not** deny other tools; use `permissions.deny` or a hook for that. |
| `disable-model-invocation` | bool | `true` = only the user can run it via `/name`; the model cannot call it. Required for side-effecting skills. |
| `user-invocable` | bool | `false` hides the slash command from users (model-only background knowledge skills). |
| `context` | `inline` \| `fork` | `fork` runs the skill in a subagent and returns only its final message to the main session. |
| `agent` | string | Subagent type to spawn when `context: fork` (e.g. `Explore`, `general-purpose`, or a custom agent name). Ignored without `context: fork`. |
| `model` | string | Model override: `haiku`, `sonnet`, `opus`, `fable`, a full model ID, or `inherit`. |
| `effort` | string or int | Thinking effort: `low`, `medium`, `high`, `max`, or an integer. |
| `paths` | glob or list | The skill only loads when the model touches files matching these globs. Good for language/framework convention skills. |
| `hooks` | object | Hooks registered only while the skill is active; same shape as `settings.json` `hooks`. Not a global guardrail: it does nothing when the skill is not running. |
| `shell` | string | Shell used for the skill's command execution, where supported. Rarely needed. |

### Substitutions in the body

| Token | Expands to |
|---|---|
| `$ARGUMENTS` | Everything typed after `/name`. |
| `$ARGUMENTS[N]` / `$N` | The Nth whitespace-separated argument (0-based). |
| `${CLAUDE_SKILL_DIR}` | Absolute path of the skill's directory. Use it for every script invocation. |
| `${CLAUDE_SESSION_ID}` | The current session ID (useful for log or temp file names). |

If `$ARGUMENTS` does not appear in the body, Claude Code appends the arguments to the end
of the skill content, so a skill still works without it.

### `allowed-tools` patterns

| Good (least privilege) | Bad |
|---|---|
| `Read, Grep, Glob` | `Bash` (any command, no prompt) |
| `Bash(git diff *), Bash(git log *)` | `Bash(*)` |
| `Bash(npm run test *)` | `Bash(npm *)` (includes `npm publish`) |
| `Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/check.py *)` | `Bash(python3 *)` (runs any Python) |
| `Edit(src/**)` | `Write` when the skill only reads |

Never pre-approve `git push`, `rm`, `kubectl apply`, `terraform apply`, `docker system
prune`, or database CLIs in a model-invocable skill.

---

## 2. Description formula

```
<Verb phrase: what it does, naming concrete artifacts>. Use when <user intents, with
phrasing users actually type>, <file types / tools / domain terms>, or <adjacent intent>.
```

Checks:

- Third person ("Generates...", "Audits..."), never "I" or "you".
- Names concrete artifacts: file extensions, tool names, directory names, commands.
- Lists 3-6 trigger intents. Include the slash form if the skill is commonly typed (`"/deploy staging"`).
- Excludes neighbours explicitly when there is overlap ("Not for Terraform; use infra-plan").
- No angle brackets: write `the Tool name` or `[tool]`, not `<tool>`.

Examples:

- Weak: `Helps with database stuff.`
- Too broad: `Use for any backend or coding task.`
- Good: `Writes and reviews Alembic migrations for the orders Postgres schema. Use when the user adds or changes a SQLAlchemy model, asks for a migration, sees "Target database is not up to date", or wants a migration reviewed for locking and downtime risk.`

---

## 3. Directory layouts

Minimal (procedure only):

```
my-skill/
└── SKILL.md
```

Standard:

```
my-skill/
├── SKILL.md              # Tier 2: workflow, decision tree, guardrails, verification
├── references/           # Tier 3: read on demand, each linked directly from SKILL.md
│   ├── api-schema.md
│   └── edge-cases.md
├── scripts/              # Deterministic work: validation, parsing, scaffolding
│   └── verify.sh
└── assets/               # Templates copied into outputs, never read into context whole
    └── template.yaml
```

Rules:

- No `README.md`, `CHANGELOG.md`, `LICENSE`, `.git/`, editor files, or test fixtures that the skill never uses.
- Reference files over ~300 lines get a table of contents at the top so Claude can jump to the section it needs.
- Scripts are executable (`chmod +x`), have a shebang, print a clear PASS/FAIL line, and exit non-zero on failure.
- Scripts read inputs from arguments, never from hard-coded user paths.

---

## 4. Body templates by degree of freedom

### Low freedom (deploys, migrations, history rewrites)

````markdown
---
name: deploy-service
description: Deploys the api service to staging or production with Helm. Use when the user types /deploy-service or asks to ship, release, or roll back the api service.
argument-hint: [staging|production] [image-tag]
disable-model-invocation: true
allowed-tools: Read, Bash(helm diff *), Bash(kubectl get *), Bash(kubectl rollout status *)
---

# Deploy api service

Environment: `$0`. Image tag: `$1`. Stop and ask if either is missing.

## Steps

1. Run exactly: `helm diff upgrade api ./chart -f values/$0.yaml --set image.tag=$1`
2. Show the diff and ask the user to confirm. Do not continue without an explicit "yes".
3. Run exactly: `helm upgrade api ./chart -f values/$0.yaml --set image.tag=$1 --atomic --timeout 5m`
4. Verify: `kubectl rollout status deploy/api -n $0 --timeout=300s` must report success.

## Circuit breaker

If step 3 or 4 fails, do not retry. `--atomic` has rolled back; report the error output.
````

### Medium freedom (endpoints, tests, reviews)

````markdown
## Steps

1. Find the closest existing example (`Grep` for the router registration) and mirror its structure.
2. Generate handler, request/response types, and a table-driven test.
3. Decision rules:
   - Mutating endpoint -> add an auth middleware check and an idempotency note.
   - Pagination -> cursor-based, matching the existing list endpoints.
4. Verify: `go test ./internal/api/...` passes; `go vet ./...` is clean.
5. If tests fail 3 times on the same error, stop and report it.
````

### High freedom (architecture reviews, refactors)

````markdown
## Heuristics

- Prefer deleting code to adding abstractions; flag any interface with one implementation.
- Check for the anti-patterns below, and report each with file:line and a concrete fix.

## Anti-patterns to check

- Business logic in HTTP handlers
- Cross-module imports that bypass the public package API

## Output

A ranked list (highest impact first), with no more than 10 items, each stating the
tradeoff of fixing it versus leaving it. Verify each claim by opening the cited file
before reporting it.
````

### Forked analysis skill

```yaml
---
name: dependency-audit
description: Audits npm and pip dependencies for known-vulnerable, unmaintained, or duplicated packages. Use when the user asks for a dependency audit, supply-chain review, or "which packages should we upgrade".
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(npm audit --json), Bash(pip-audit *)
---
```

The body must end by defining the exact summary format to return, because only the
forked agent's final message reaches the main session.

---

## 5. Companion primitives

### Hook for a zero-exception rule (blocks edits to generated files)

`.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block-generated.sh" }
        ]
      }
    ]
  }
}
```

`.claude/hooks/block-generated.sh` (make it executable):

```bash
#!/usr/bin/env bash
# Exit 2 = block the tool call; stderr is shown to Claude as the reason.
path=$(jq -r '.tool_input.file_path // empty')
case "$path" in
  */generated/*|*.pb.go|*_gen.ts)
    echo "Blocked: $path is generated. Edit the source schema and re-run codegen." >&2
    exit 2 ;;
esac
exit 0
```

Other common hooks:

| Rule | Event | Matcher | Action |
|---|---|---|---|
| Format after every edit | `PostToolUse` | `Edit\|Write` | Run the formatter on `tool_input.file_path`; exit 0. |
| Block dangerous shell flags | `PreToolUse` | `Bash` | Inspect `tool_input.command`; exit 2 on `--force`, `rm -rf /`, `--no-verify`. |
| Require tests before finishing | `Stop` | (none) | Run the test suite; exit 2 with failures on stderr so Claude keeps working. |

Test a hook by piping sample JSON into it: `echo '{"tool_input":{"file_path":"a/generated/x.go"}}' | .claude/hooks/block-generated.sh; echo $?` must print `2`.

### Subagent (`.claude/agents/<name>.md`)

```markdown
---
name: migration-reviewer
description: Reviews database migration files for locking, downtime, and irreversible changes. Use proactively after any migration is created or edited.
tools: Read, Grep, Glob
model: sonnet
---

You review migrations. For each file, report: lock level, estimated duration on a large
table, reversibility, and a safer alternative if one exists. Return at most 10 findings.
```

Choose a subagent over `context: fork` when the same isolated worker is reused by several
skills or should be invoked proactively by the model; choose `context: fork` when the
isolation belongs to one procedure.

### CLAUDE.md

Put a fact there only if it is needed in most sessions (build/test commands, repo layout,
universal standards). Keep it under 200 lines. If a CLAUDE.md section is only relevant
for one kind of task, move it into a skill and leave a one-line pointer.

---

## 6. Audit checklist

Mark each item PASS / FAIL / N/A. Any FAIL in sections A-C blocks delivery.

**A. Structure**

- [ ] Directory name equals `name`; `SKILL.md` exists at its root.
- [ ] Frontmatter is the first thing in the file, delimited by `---` lines, valid YAML.
- [ ] No unknown frontmatter keys (typos such as `allowed_tools` are silently ignored).
- [ ] SKILL.md is under 500 lines.
- [ ] A blank line precedes every list (otherwise some renderers merge it into the paragraph).
- [ ] Every path referenced in SKILL.md exists in the package.
- [ ] References are one hop deep: no reference file sends the reader to another reference file.
- [ ] No README.md, CHANGELOG.md, or other human-only files.

**B. Metadata**

- [ ] `name`: 1-64 chars, lowercase alphanumerics and single hyphens, no leading/trailing hyphen.
- [ ] `description`: present, under 1,024 chars, no `<` or `>`, third person, states what and when.
- [ ] `argument-hint` is set if the body uses `$ARGUMENTS` or `$N`.

**C. Safety**

- [ ] `allowed-tools` contains no bare `Bash`, `Bash(*)`, or broad interpreter patterns.
- [ ] Side-effecting skills (deploy, publish, delete, migrate, push, reset) set `disable-model-invocation: true` or include an explicit user-confirmation gate before the action.
- [ ] Every hard "never" rule that matters has a companion hook.
- [ ] Scripts do not download and execute remote code, and do not embed secrets.

**D. Quality**

- [ ] Single responsibility: the skill does one job; multi-phase work is split.
- [ ] The workflow ends in a verification step with a concrete pass/fail criterion.
- [ ] A circuit breaker bounds retries.
- [ ] Non-obvious constraints explain why.
- [ ] No tokens spent on things Claude already knows (language syntax, basic git).
- [ ] Each reference file is linked with an instruction saying when to read it.

---

## 7. Refactoring a bloated skill or CLAUDE.md

1. Inventory every section and tag it: `always` (CLAUDE.md), `procedure` (skill body), `detail` (reference file), `hard-rule` (hook), `isolated-exploration` (subagent or fork), `obsolete` (delete).
2. Group `procedure` sections by job; each group with its own trigger becomes a micro-skill.
3. Move `detail` sections into `references/<topic>.md`, one topic per file, each linked from the owning SKILL.md.
4. Convert `hard-rule` sections into hooks and leave a one-line note in the skill saying the hook enforces it.
5. Run the validator on every resulting skill and check that their descriptions do not overlap; overlapping descriptions make the model pick inconsistently.
