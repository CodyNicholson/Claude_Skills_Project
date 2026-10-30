---
name: claude-skill-factory
description: Design, scaffold, audit, and harden Claude Code skills (.claude/skills/). Use when the user asks to create a new Claude Code skill, convert a workflow or session into a reusable skill, review or optimize an existing SKILL.md for token efficiency and security, decide between a skill vs. CLAUDE.md vs. a Hook vs. a Subagent, or generate progressive-disclosure reference files and validation scripts.
argument-hint: [new skill idea | workflow to capture | path to an existing skill dir]
allowed-tools: Read, Grep, Glob, Bash(python3 *validate_skill.py *)
---

# Claude Skill Factory

Design, scaffold, and audit modular, token-efficient, and safe Claude Code skills using
progressive disclosure and deterministic verification loops.

Target for this run: **$ARGUMENTS** (if empty, ask what skill to build or which skill
directory to audit).

## When to Use

- Creating a new Claude Code skill from scratch or extracting a repeatable workflow from a conversation.
- Auditing, refactoring, or hardening an existing `.claude/skills/<skill-name>/` directory.
- Splitting a bloated CLAUDE.md or monolithic skill into composable micro-skills, hooks, and subagents.
- Adding safety controls (`allowed-tools`, `disable-model-invocation`, `context: fork`, or companion hooks) and self-verification scripts to a skill.

Save location: personal skills go in `~/.claude/skills/<name>/`, project skills in
`<repo>/.claude/skills/<name>/`. Ask if the user has not said which; the directory name
must equal the `name` field.

## Step 1: Run the Primitive Routing Gate

Before drafting a skill, verify that a Claude Code Skill is the right mechanism (or
determine which companion primitives are required).

- **Always-on repository facts** (build commands, repo layout, universal coding standards) belong in `CLAUDE.md` (keep under 200 lines), not a skill.
- **Zero-exception deterministic guardrails** (blocking edits to generated files, running a formatter after every edit, blocking dangerous shell flags) must be enforced via Hooks (`PreToolUse`, `PostToolUse`, or `Stop` in `.claude/settings.json`), because skills are probabilistic instructions.
- **Heavy context-consuming exploration** or isolated multi-file audits should run in a Subagent (`.claude/agents/`) or a skill configured with `context: fork` so intermediate tool output does not pollute the main session.
- **On-demand domain workflows**, specialized conventions, and repeatable procedures belong in a Skill (`.claude/skills/<skill-name>/SKILL.md`).

If a user wants both a workflow and a hard safety block, generate the Skill for the
procedure and provide the companion Hook configuration for the zero-exception rule.
State the routing decision and its reason to the user before writing files.

## Step 2: Calibrate Scope, Freedom, and Safety Controls

Define the skill's operating boundaries before writing instructions. Consult
`references/patterns-and-rubric.md` for full frontmatter specifications, architectural
templates, and the companion hook and subagent templates.

**Enforce Single Responsibility.** Scope the skill to one cohesive job. If a request spans
multiple distinct phases (for example, database schema design, REST controller
scaffolding, and load testing), propose composable micro-skills instead of a monolith.

**Calibrate Degrees of Freedom:**

- **Low Freedom (fragile/high-risk):** database migrations, deployments, security audits, or git history rewrites. Use exact sequential commands, strict parameter templates, and mandatory dry-run gates.
- **Medium Freedom (standardized patterns):** API endpoint generation, test suite authoring, or PR reviews. Provide canonical structure and decision rules while allowing adaptation to repo context.
- **High Freedom (exploratory/analytical):** architecture reviews or refactoring. Provide heuristics, tradeoffs, and anti-patterns to check.

**Configure Execution and Permission Frontmatter:**

- Scope `allowed-tools` to the minimum required capabilities (for example, `Read, Grep, Glob, Bash(git diff *), Bash(pytest *)` rather than unrestricted `Bash`). These tools run without permission prompts while the skill is active, so every entry is a pre-approval.
- Set `disable-model-invocation: true` for skills with side effects or destructive actions (such as `/deploy`, `/publish`, or `/reset-db`) so they can only be triggered explicitly by the user via `/skill-name`.
- Set `context: fork` when the skill performs broad file reading or verbose diagnostics and only needs to return a synthesized summary.
- Use `$ARGUMENTS` (or `$0`, `$1`) and `argument-hint` when the skill accepts target paths, issue IDs, or environment names.

## Step 3: Architect for Three-Tier Progressive Disclosure

Structure the skill directory so Claude pays zero token overhead for unused context.

**Tier 1: YAML frontmatter (`name` and `description`), always loaded:**

- `name`: 1 to 64 characters, lowercase a-z, 0-9, and hyphens only. Do not start or end with a hyphen. If the skill will also be uploaded to the Anthropic API, avoid the reserved substrings `claude` and `anthropic` in `name`.
- `description`: under 1,024 characters, no XML angle brackets. Write in third person. State both what the skill does and when to use it, including concrete file types, domain terms, and user phrasing.

**Tier 2: SKILL.md body (under 500 lines), loaded on invocation:**

- Include only the core workflow sequence, decision trees, critical guardrails, and a verification loop.
- Write in direct imperative form and explain the why behind non-obvious constraints so the agent does not rationalize workarounds under edge cases.
- Never include human-only clutter such as `README.md` or `CHANGELOG.md` inside the skill folder.

**Tier 3: on-demand auxiliary files (`references/`, `scripts/`, `assets/`):**

- Move detailed API schemas, language style guides, and edge-case catalogs into `references/<topic>.md` and link them explicitly from SKILL.md with clear instructions on when to read them.
- Keep reference links one hop deep from SKILL.md (never chain SKILL.md -> ref-a.md -> ref-b.md).
- Offload deterministic validation, parsing, or boilerplate generation into executable scripts in `scripts/`. Reference them as `${CLAUDE_SKILL_DIR}/scripts/<file>` so they resolve no matter which directory the session runs in.

## Step 4: Embed a Mandatory Self-Verification Loop

Never end a skill's workflow at code or artifact generation. Every generated skill must
close with an explicit verification step:

- Run a targeted test, build, or linter command (for example, `pytest`, `npm test`, `cargo check`, or `./mvnw test`).
- Execute a custom validation script bundled in `scripts/`.
- Evaluate the output against a concrete pass/fail checklist before returning control to the user.
- Define a circuit breaker (for example, "If verification fails 3 times on the same error, stop and report the root cause rather than looping indefinitely").

## Step 5: Validate the Skill Package

Before delivering or saving the skill, validate its structure and safety. With filesystem
access, run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/validate_skill.py <path-to-skill-dir>
```

Without filesystem access, verify manually against the checklist in
`references/patterns-and-rubric.md`. Confirm that:

- `name` and `description` meet all character and length rules.
- SKILL.md is under 500 lines and has a blank line before every list.
- Every file path referenced in SKILL.md exists in the package.
- Tool permissions follow least privilege and destructive actions require user confirmation or `disable-model-invocation: true`.

Fix every ERROR and either fix or justify every WARN, then re-run the validator. If it
fails 3 times on the same error, stop and report the blocking issue instead of looping.
Finish by telling the user the skill path, how it triggers (`/name` and/or automatic),
any companion hook or subagent files, and the final validator result.

## Gotchas

- **Probabilistic evasion on hard rules:** putting "NEVER edit files in generated/" inside SKILL.md can still fail under heavy context load. Always pair hard prohibitions with a `PreToolUse` hook that exits with code 2 when the target path matches the forbidden pattern.
- **Over-broad or under-specified descriptions:** a vague description ("Helps with backend tasks") causes under-triggering; an overly broad one ("Use for any coding file") hijacks unrelated prompts. Anchor descriptions to concrete artifacts and intents.
- **Unbounded shell permissions:** granting `allowed-tools: Bash` without command patterns allows arbitrary shell execution without prompts. Scope bash tools with explicit prefixes such as `Bash(git status)` or `Bash(npm run test *)`.
- **Teaching what Claude already knows:** do not waste tokens explaining standard syntax, basic Git concepts, or generic clean-code platitudes. Encode only repo-specific architecture, non-obvious failure modes, and domain invariants.
- **Nested reference chains:** if SKILL.md links to an overview reference that links to a details reference, Claude often stops after the first hop. Link all reference files directly from SKILL.md.
