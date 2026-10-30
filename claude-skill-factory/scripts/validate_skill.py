#!/usr/bin/env python3
"""Validate a Claude Code skill directory (structure, metadata, safety, quality).

Usage: validate_skill.py <skill-dir> [--strict] [--api]

  --strict  treat warnings as errors (exit 1 if any warning)
  --api     the skill will also be uploaded to the Anthropic API: reserved
            substrings in `name` become errors instead of warnings

Exit codes: 0 = pass, 1 = errors found, 2 = bad invocation.
Uses only the standard library (PyYAML is used if installed).
"""
import os
import re
import sys

KNOWN_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "arguments",
    "allowed-tools", "disable-model-invocation", "user-invocable", "context",
    "agent", "model", "effort", "paths", "hooks", "shell", "version", "metadata",
    "license", "compatibility",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED = ("claude", "anthropic")
CLUTTER = {"readme.md", "changelog.md", "contributing.md", "license", "license.md"}
# Directories ignored when scanning the package (local session logs, VCS, caches).
IGNORED_DIRS = {"claude_logs", ".git", "__pycache__", "node_modules"}
LIST_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s+\S")
PATH_RE = re.compile(
    r"(?<![\w./-])((?:references|scripts|assets|templates)/"
    r"[A-Za-z0-9_./-]*[A-Za-z0-9_])"
)
PATH_RE_PREFIXED = re.compile(
    r"\$\{CLAUDE_SKILL_DIR\}/((?:[A-Za-z0-9_-]+/)*[A-Za-z0-9_.-]*[A-Za-z0-9_])"
)
MD_LINK_RE = re.compile(r"\]\((?!https?:|mailto:|#)([^)\s]+)\)")
SIDE_EFFECT_RE = re.compile(
    r"\b(deploy|publish|release|git push|force[- ]push|drop table|truncate|"
    r"rm -rf|reset[- ]db|delete|destroy|migrat\w*|terraform apply|kubectl apply)\b",
    re.I,
)
CONFIRM_RE = re.compile(r"\b(confirm|confirmation|ask the user|explicit \"?yes|dry[- ]run)\b", re.I)
VERIFY_RE = re.compile(r"\b(verif\w*|validat\w*|test\w*|lint\w*|check)\b", re.I)
BREAKER_RE = re.compile(
    r"(circuit breaker|\b\d+\s+times\b|\b(two|three|four|five) times\b|stop and report|do not retry)",
    re.I,
)
BROAD_TOOL_RE = re.compile(
    r"^(Bash|Bash\(\*\)|Bash\((python3?|node|bash|sh|npx|sudo|curl|wget)( \*|\*)\))$"
)


class Report:
    def __init__(self):
        self.errors, self.warnings, self.passes = [], [], []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def ok(self, msg):
        self.passes.append(msg)


def parse_frontmatter(text):
    """Return (dict, body_start_line, error). Falls back to a minimal parser."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, 0, "SKILL.md must start with a '---' frontmatter line"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, 0, "frontmatter has no closing '---' line"
    raw = "\n".join(lines[1:end])
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return None, end + 1, "frontmatter is not a YAML mapping"
        return data, end + 1, None
    except ImportError:
        pass
    except Exception as e:  # yaml.YAMLError
        return None, end + 1, f"frontmatter is not valid YAML: {e}"
    return _mini_yaml(lines[1:end]), end + 1, None


def _mini_yaml(lines):
    """Parse top-level `key: value`, block scalars (| >) and `- item` lists."""
    data, key, block, items = {}, None, None, None
    for line in lines:
        if key and (line.startswith((" ", "\t")) or not line.strip()):
            s = line.strip()
            if items is not None and s.startswith("- "):
                items.append(_scalar(s[2:]))
            elif block is not None:
                block.append(s)
            elif s and isinstance(data[key], str):
                data[key] = (data[key] + " " + s).strip()
            continue
        if key and block is not None:
            data[key] = " ".join(x for x in block if x) if block_style == ">" else "\n".join(block).strip()
        key = block = items = None
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("|", ">", "|-", ">-", "|+", ">+"):
            block, block_style, data[key] = [], val[0], ""
        elif val == "":
            items = data[key] = []
        else:
            data[key] = _scalar(val)
    if key and block is not None:
        data[key] = " ".join(x for x in block if x) if block_style == ">" else "\n".join(block).strip()
    return data


def _scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    return v


def check_name(fm, skill_dir, r, api):
    name = fm.get("name")
    dirname = os.path.basename(os.path.normpath(skill_dir))
    if name is None:
        r.err(f"frontmatter 'name' is missing (it would default to '{dirname}'; set it explicitly)")
        return
    name = str(name)
    if not 1 <= len(name) <= 64:
        r.err(f"name is {len(name)} chars; must be 1-64")
    if not NAME_RE.match(name):
        r.err(f"name '{name}' must be lowercase a-z, 0-9 and single hyphens, not starting or ending with '-'")
    if name != dirname:
        r.err(f"name '{name}' does not match directory name '{dirname}'")
    hits = [w for w in RESERVED if w in name]
    if hits:
        msg = f"name contains reserved substring(s) {hits}: fine for local .claude/skills, rejected by the Anthropic API"
        (r.err if api else r.warn)(msg)
    if not r.errors:
        r.ok(f"name '{name}' is valid")


def check_description(fm, r):
    desc = fm.get("description")
    if not desc or not str(desc).strip():
        r.err("frontmatter 'description' is missing or empty (the skill will not auto-trigger)")
        return
    desc = str(desc).strip()
    before = len(r.errors)
    if len(desc) >= 1024:
        r.err(f"description is {len(desc)} chars; must be under 1024")
    if "<" in desc or ">" in desc:
        r.err("description contains '<' or '>' (XML brackets are not allowed)")
    if re.match(r"^(I|I'm|You|We|This skill helps you)\b", desc):
        r.warn("description should be third person (start with a verb such as 'Generates...', not 'I'/'You')")
    if not re.search(r"\b(use (it )?(when|for|to|if)|when the user|triggers? on)\b", desc, re.I):
        r.warn("description does not say when to use the skill (add 'Use when ...')")
    if len(desc) < 80:
        r.warn(f"description is only {len(desc)} chars; likely too vague to trigger reliably")
    if len(r.errors) == before:
        r.ok(f"description is {len(desc)} chars with no forbidden characters")


def check_keys(fm, r):
    unknown = sorted(k for k in fm if k not in KNOWN_KEYS)
    for k in unknown:
        hint = ""
        for known in KNOWN_KEYS:
            if k.replace("_", "-") == known or k.replace("-", "_") == known:
                hint = f" (did you mean '{known}'?)"
        r.warn(f"unknown frontmatter key '{k}' is ignored by Claude Code{hint}")
    ctx = fm.get("context")
    if ctx is not None and ctx not in ("inline", "fork"):
        r.err(f"context must be 'inline' or 'fork', got '{ctx}'")
    if fm.get("agent") and ctx != "fork":
        r.warn("'agent' is set but 'context' is not 'fork', so it has no effect")
    for b in ("disable-model-invocation", "user-invocable"):
        if b in fm and not isinstance(fm[b], bool):
            r.err(f"'{b}' must be true or false, got '{fm[b]}'")


def split_tools(value):
    if isinstance(value, list):
        return [str(t).strip() for t in value if str(t).strip()]
    tools, depth, cur = [], 0, ""
    for ch in str(value):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch in ", " and depth == 0:
            if cur.strip():
                tools.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        tools.append(cur.strip())
    return tools


def check_safety(fm, body, r):
    tools = split_tools(fm.get("allowed-tools", ""))
    broad = [t for t in tools if BROAD_TOOL_RE.match(t)]
    for t in broad:
        r.err(f"allowed-tools entry '{t}' pre-approves arbitrary shell/code execution; scope it to command prefixes")
    for t in tools:
        if re.search(r"git push|rm |kubectl (apply|delete)|terraform (apply|destroy)|npm publish", t):
            r.warn(f"allowed-tools pre-approves a destructive command: '{t}'")
    if tools and not broad:
        r.ok(f"allowed-tools scoped: {', '.join(tools)}")
    text = f"{fm.get('description', '')}\n{body}"
    side = sorted({m.group(1).lower() for m in SIDE_EFFECT_RE.finditer(text)})
    if side and fm.get("disable-model-invocation") is not True:
        if CONFIRM_RE.search(body):
            r.warn(f"mentions side effects {side}; it has a confirmation step, but consider "
                   "disable-model-invocation: true (ignore if these words are only examples)")
        else:
            r.warn(f"mentions side effects {side} with no confirmation gate and no "
                   "disable-model-invocation: true (ignore if these words are only examples)")


def scan_body(body_lines, body_offset, r):
    """Blank-line-before-list check and line-count check, skipping code fences."""
    in_fence, in_list, prev = False, False, ""
    bad = []
    for i, line in enumerate(body_lines):
        s = line.strip()
        if s.startswith(("```", "~~~")):
            in_fence = not in_fence
            prev, in_list = line, False
            continue
        if in_fence:
            continue
        if LIST_RE.match(line):
            if not in_list and prev.strip() and not prev.lstrip().startswith("|"):
                bad.append(body_offset + i + 1)
            in_list = True
        elif s and not line.startswith((" ", "\t")):
            in_list = False
        prev = line
    for n in bad:
        r.err(f"SKILL.md line {n}: list starts without a blank line before it")
    if not bad:
        r.ok("every list is preceded by a blank line")


def referenced_paths(text):
    """Yield (path, in_code, explicit) for package-relative paths in markdown text."""
    in_fence = False
    for line in text.split("\n"):
        if line.strip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        found = set()
        for m in PATH_RE_PREFIXED.finditer(line):
            found.add((m.group(1), True))
        for m in PATH_RE.finditer(line):
            found.add((m.group(1), False))
        for m in MD_LINK_RE.finditer(line):
            p = m.group(1).split("#")[0]
            if p and not p.startswith(("/", "~", "$")):
                found.add((p, True))
        for p, explicit in found:
            yield p.rstrip("."), in_fence, explicit


def check_paths(skill_dir, body, r):
    missing, seen = [], set()
    for p, in_code, explicit in referenced_paths(body):
        if p in seen:
            continue
        seen.add(p)
        if not os.path.exists(os.path.join(skill_dir, p)):
            missing.append((p, in_code and not explicit))
    for p, soft in missing:
        if soft:
            r.warn(f"code block mentions '{p}', which is not in the package (fine if it is a path in the target repo)")
        else:
            r.err(f"SKILL.md references '{p}', which does not exist in the package")
    if not [m for m in missing if not m[1]]:
        r.ok(f"all {len(seen)} referenced package paths exist")
    return seen


def check_reference_hops(skill_dir, refs, r):
    for p in sorted(refs):
        if not (p.startswith("references/") and p.endswith(".md")):
            continue
        full = os.path.join(skill_dir, p)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as f:
            text = f.read()
        nested = sorted({q for q, _, _ in referenced_paths(text)
                         if q.startswith("references/") and q.endswith(".md") and q != p})
        if nested:
            r.warn(f"{p} links to {nested}: nested reference chain; link those directly from SKILL.md")
        n = text.count("\n") + 1
        if n > 300 and not re.search(r"(?im)^#+\s*(contents|table of contents)|^\s*1\.\s", text[:3000]):
            r.warn(f"{p} is {n} lines with no table of contents near the top")


def check_package(skill_dir, refs, r):
    all_files = []
    for root, dirs, files in os.walk(skill_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), skill_dir)
            all_files.append(rel)
            if fn.lower() in CLUTTER:
                r.err(f"human-only file '{rel}' does not belong in a skill package")
            if re.search(r"\.(env|pem|key)$|^\.env", fn):
                r.err(f"'{rel}' looks like a secrets file; remove it from the package")
    for rel in all_files:
        if rel.startswith("scripts/") and not rel.endswith((".md", ".json", ".txt")):
            full = os.path.join(skill_dir, rel)
            with open(full, "rb") as f:
                shebang = f.read(2) == b"#!"
            if shebang and not os.access(full, os.X_OK):
                r.warn(f"{rel} has a shebang but is not executable (chmod +x)")
        top = rel.split(os.sep)[0]
        if rel != "SKILL.md" and top in ("references",) and rel not in refs:
            r.warn(f"{rel} is never referenced from SKILL.md, so Claude will not know to read it")


def check_quality(fm, body, r):
    if re.search(r"\$(ARGUMENTS|\d)\b", body) and not fm.get("argument-hint"):
        r.warn("body uses $ARGUMENTS/$N but no argument-hint is set")
    tail = "\n".join(body.strip().split("\n")[-80:])
    if not VERIFY_RE.search(body):
        r.err("no verification step found (add a test/lint/validation command with pass/fail criteria)")
    elif not VERIFY_RE.search(tail):
        r.warn("verification is not near the end of the workflow; close the workflow with it")
    else:
        r.ok("workflow includes a verification step")
    if not BREAKER_RE.search(body):
        r.warn("no circuit breaker found (e.g. 'if it fails 3 times on the same error, stop and report')")


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    if len(args) != 1 or flags - {"--strict", "--api"}:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    skill_dir = os.path.abspath(args[0])
    if os.path.basename(skill_dir) == "SKILL.md":
        skill_dir = os.path.dirname(skill_dir)
    path = os.path.join(skill_dir, "SKILL.md")
    r = Report()
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found")
        return 1
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm, body_start, fm_err = parse_frontmatter(text)
    lines = text.split("\n")
    n_lines = len(lines) - (1 if text.endswith("\n") else 0)
    if fm_err:
        r.err(fm_err)
        fm = {}
    else:
        check_name(fm, skill_dir, r, "--api" in flags)
        check_description(fm, r)
        check_keys(fm, r)
    body = "\n".join(lines[body_start:])
    if n_lines >= 500:
        r.err(f"SKILL.md is {n_lines} lines; must be under 500 (move detail into references/)")
    else:
        r.ok(f"SKILL.md is {n_lines} lines")
    scan_body(lines[body_start:], body_start, r)
    refs = check_paths(skill_dir, body, r)
    check_reference_hops(skill_dir, refs, r)
    check_package(skill_dir, refs, r)
    check_safety(fm, body, r)
    check_quality(fm, body, r)

    print(f"Validating {skill_dir}")
    for m in r.passes:
        print(f"  PASS  {m}")
    for m in r.warnings:
        print(f"  WARN  {m}")
    for m in r.errors:
        print(f"  ERROR {m}")
    failed = bool(r.errors) or ("--strict" in flags and bool(r.warnings))
    print(f"RESULT: {'FAIL' if failed else 'PASS'} "
          f"({len(r.errors)} error(s), {len(r.warnings)} warning(s))")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
