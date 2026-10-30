#!/usr/bin/env python3
"""Validate a software-intake-planner requirements spec or development plan.

Usage:
  validate_intake.py SPEC.md
  validate_intake.py --plan PLAN.md [--spec SPEC.md]

With --spec, the plan is cross-checked for traceability: every US-n, INV-n and
NFR-n in the spec must appear in plan section 12, and every UNK-n in the spec's
register must appear in plan section 11.

Exit codes: 0 = PASS (warnings allowed), 1 = FAIL, 2 = bad invocation.
Standard library only.
"""
import argparse
import re
import sys
from pathlib import Path

FILL_RE = re.compile(r"\[FILL:[^\]]*\]")
HARD_PLACEHOLDER_RE = re.compile(r"\b(TBD|TBC)\b|\[(?:PLACEHOLDER|TODO|TK|XXX)[^\]]*\]")
SOFT_PLACEHOLDER_RE = re.compile(r"\bTODO\b")
MARKER_RE = re.compile(r"\[(UNKNOWN|ASSUMED):\s*(UNK-\d+)[^\]]*\]")
BAD_MARKER_RE = re.compile(r"\[(UNKNOWN|ASSUMED)(?!:\s*UNK-\d+)[^\]]*\]")
REQ_ID_RE = re.compile(r"\b(?:US|INV|NFR)-\d+\b")
UNK_ID_RE = re.compile(r"\bUNK-\d+\b")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(\S.*)$")
NA_RE = re.compile(r"^\s*N/A\s*:\s*\S.{2,}", re.I)
EMPTY_CELL = {"", "-", "?", "n/a", "na", "tbd", "unknown"}

SPEC_SECTIONS = range(1, 11)
PLAN_SECTIONS = range(0, 13)


class Report:
    def __init__(self, path):
        self.path = path
        self.errors, self.warnings, self.info = [], [], []

    def err(self, msg, line=None):
        self.errors.append(f"{self.path}:{line}: {msg}" if line else f"{self.path}: {msg}")

    def warn(self, msg, line=None):
        self.warnings.append(f"{self.path}:{line}: {msg}" if line else f"{self.path}: {msg}")


def load(path):
    p = Path(path)
    if not p.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    return p.read_text(encoding="utf-8")


def mask(text):
    """Blank out fenced code, inline code and HTML comments, keeping line numbers."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))

    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", blank, text, flags=re.S | re.M)
    text = re.sub(r"`[^`\n]*`", blank, text)
    return text.split("\n")


def section(lines, level, key):
    """Return (start_line_no, body_lines) of the heading `#*level key...`, or (None, [])."""
    hashes = "#" * level
    head_re = re.compile(rf"^{hashes}\s+{re.escape(key)}(?:[.\s:]|$)")
    stop_re = re.compile(rf"^#{{1,{level}}}\s")
    for i, line in enumerate(lines):
        if head_re.match(line):
            body = []
            for nxt in lines[i + 1:]:
                if stop_re.match(nxt):
                    break
                body.append(nxt)
            return i + 1, body
    return None, []


def table_rows(body):
    rows = []
    for line in body:
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and not re.match(r"^\|[\s:|-]+\|$", s):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


def check_common(raw, lines, rep):
    # Check FILL slots in fenced code too, but not inside guidance comments.
    no_comments = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw, flags=re.S)
    for i, line in enumerate(no_comments.split("\n"), 1):
        for m in FILL_RE.finditer(line):
            rep.err(f"unfilled template slot {m.group(0)[:60]}", i)
    for i, line in enumerate(lines, 1):
        for m in HARD_PLACEHOLDER_RE.finditer(line):
            rep.err(f"placeholder '{m.group(0)}': use an [UNKNOWN: UNK-n] register entry instead", i)
        if SOFT_PLACEHOLDER_RE.search(line):
            rep.warn("'TODO' found: if it is a placeholder, replace it with a register entry", i)
        for m in BAD_MARKER_RE.finditer(line):
            rep.err(f"malformed marker '{m.group(0)[:60]}': expected [UNKNOWN: UNK-n] or [ASSUMED: UNK-n]", i)
    if "<!--" in raw:
        rep.warn("HTML guidance comments remain; delete them")


def check_spec(raw, rep):
    lines = mask(raw)
    check_common(raw, lines, rep)
    text = "\n".join(lines)

    for n in SPEC_SECTIONS:
        if section(lines, 2, f"{n}.")[0] is None:
            rep.err(f"missing section '## {n}.'")

    m = re.search(r"^\*\*Track:\*\*\s*([ABC])\b", text, re.M)
    track = m.group(1) if m else None
    if not track:
        rep.err("missing or invalid '**Track:** A|B|C' header line")
    else:
        if section(lines, 3, f"9{track}.")[0] is None:
            rep.err(f"track is {track} but subsection '### 9{track}.' is missing")
        for other in "ABC".replace(track, ""):
            if section(lines, 3, f"9{other}.")[0] is not None:
                rep.warn(f"subsection '### 9{other}.' does not match track {track}; delete it")

    ln, body = section(lines, 3, "2.3")
    if ln is None:
        rep.err("missing subsection '### 2.3' (explicit non-goals)")
    else:
        items = [LIST_ITEM_RE.match(l).group(1) for l in body if LIST_ITEM_RE.match(l)]
        real = [it for it in items if not re.match(r"^(N/A|None)\b", it, re.I)]
        if not real:
            rep.err("section 2.3 needs at least one explicit non-goal", ln)

    ln, body = section(lines, 3, "3.2")
    stories = set(re.findall(r"\bUS-\d+\b", "\n".join(body)))
    if ln is None:
        rep.err("missing subsection '### 3.2' (user stories)")
    elif not stories:
        rep.err("section 3.2 defines no US-n user stories", ln)
    elif sum(1 for l in body if re.search(r"acceptance", l, re.I)) < len(stories):
        rep.warn("some user stories in 3.2 appear to lack acceptance criteria", ln)

    ln, body = section(lines, 3, "3.3")
    joined = "\n".join(body)
    if ln is None:
        rep.err("missing subsection '### 3.3' (hard business invariants)")
    elif not re.search(r"\bINV-\d+\b", joined):
        if re.search(r"^\s*(?:[-*]\s+)?None\s*:\s*\S", joined, re.M | re.I):
            rep.warn("section 3.3 declares no invariants; double-check concurrency and data-integrity rules", ln)
        else:
            rep.err("section 3.3 defines no INV-n invariants (or 'None: reason')", ln)

    ln, body = section(lines, 2, "5.")
    if ln is not None:
        rows = table_rows(body)
        for label in ("p95", "p99", "throughput"):
            if not any(label in " ".join(r).lower() for r in rows):
                rep.err(f"section 5 has no '{label}' row", ln)
        nfr_rows = [r for r in rows if r and re.match(r"^NFR-\d+$", r[0])]
        if not nfr_rows:
            rep.err("section 5 defines no NFR-n rows", ln)
        for r in nfr_rows:
            target = r[2] if len(r) > 2 else ""
            if not (re.search(r"\d", target) or MARKER_RE.search(target) or NA_RE.match(target)):
                rep.err(f"{r[0]} target '{target}' needs a number, an UNK marker, or 'N/A: reason'", ln)

    ln, body = section(lines, 2, "10.")
    register = {}
    if ln is not None:
        for r in table_rows(body):
            if not r or not re.match(r"^UNK-\d+$", r[0]):
                continue
            uid = r[0]
            if uid in register:
                rep.err(f"duplicate register entry {uid}", ln)
            register[uid] = r
            cells = (r + [""] * 6)[:6]
            if cells[1].lower() not in ("unknown", "assumption"):
                rep.warn(f"{uid} type '{cells[1]}' should be Unknown or Assumption", ln)
            for name, val in zip(("Item", "Owner", "Action", "Due"), cells[2:6]):
                if val.lower() in EMPTY_CELL:
                    rep.err(f"{uid} has no {name}", ln)

    referenced = {}
    for i, line in enumerate(lines, 1):
        for m in MARKER_RE.finditer(line):
            referenced.setdefault(m.group(2), i)
    for uid, i in sorted(referenced.items()):
        if uid not in register:
            rep.err(f"{uid} is referenced but has no row in the section 10 register", i)

    ids = set(REQ_ID_RE.findall(text))
    kinds = {k: sorted({i for i in ids if i.startswith(k + "-")}, key=lambda s: int(s.split("-")[1]))
             for k in ("US", "INV", "NFR")}
    n_assumed = sum(1 for r in register.values() if len(r) > 1 and r[1].lower() == "assumption")
    rep.info.append(
        f"Track {track or '?'} | stories {len(kinds['US'])} | invariants {len(kinds['INV'])} | "
        f"NFRs {len(kinds['NFR'])} | unknowns {len(register) - n_assumed} | assumptions {n_assumed}"
    )
    return ids, set(register)


def check_plan(raw, rep, spec_ids=None, spec_unks=None):
    lines = mask(raw)
    check_common(raw, lines, rep)
    text = "\n".join(lines)

    for n in PLAN_SECTIONS:
        if section(lines, 2, f"{n}.")[0] is None:
            rep.err(f"missing section '## {n}.'")
    if "requirements-spec.md" not in raw:
        rep.warn("plan header does not link requirements-spec.md")

    milestones = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"^###\s+M(\d+)\b", line)
        if m:
            milestones.append((int(m.group(1)), i))
    if len(milestones) < 2:
        rep.err("section 6 needs M0 plus at least one feature milestone ('### M<n>: ...')")
    nums = [n for n, _ in milestones]
    if nums and nums != list(range(nums[0], nums[0] + len(nums))) or (nums and nums[0] != 0):
        rep.warn(f"milestones are not numbered consecutively from M0: {['M%d' % n for n in nums]}")
    for n, ln in milestones:
        _, body = section(lines, 3, f"M{n}")
        for field in ("Covers", "Verification"):
            idx = next((k for k, l in enumerate(body) if f"**{field}:**" in l), None)
            if idx is None:
                rep.err(f"M{n} has no **{field}:** line", ln)
                continue
            after = body[idx].split(f"**{field}:**", 1)[1].strip()
            nxt = next((l for l in body[idx + 1:] if l.strip()), "")
            if not after and not LIST_ITEM_RE.match(nxt):
                rep.err(f"M{n} **{field}:** is empty", ln)

    plan_ids = set(REQ_ID_RE.findall(text))
    if spec_ids is not None:
        _, trace = section(lines, 2, "12.")
        trace_ids = set(REQ_ID_RE.findall("\n".join(trace)))
        for rid in sorted(spec_ids - trace_ids):
            rep.err(f"{rid} from the spec is missing from the section 12 traceability matrix")
        _, tests = section(lines, 2, "7.")
        test_ids = set(REQ_ID_RE.findall("\n".join(tests)))
        for rid in sorted(i for i in spec_ids if i.startswith("INV-") and i not in test_ids):
            rep.warn(f"{rid} has no test listed in section 7")
        for rid in sorted(plan_ids - spec_ids):
            rep.warn(f"{rid} appears in the plan but is not defined in the spec")
        _, open_items = section(lines, 2, "11.")
        open_ids = set(UNK_ID_RE.findall("\n".join(open_items)))
        for uid in sorted((spec_unks or set()) - open_ids):
            rep.err(f"{uid} from the spec register is missing from section 11")

    rep.info.append(f"milestones {len(milestones)} | requirement IDs referenced {len(plan_ids)}")


def emit(rep):
    for e in rep.errors:
        print(f"ERROR: {e}")
    for w in rep.warnings:
        print(f"WARN:  {w}")
    for i in rep.info:
        print(f"INFO:  {i}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec_path", nargs="?", help="requirements-spec.md to validate")
    ap.add_argument("--plan", help="development-plan.md to validate")
    ap.add_argument("--spec", help="spec to cross-check the plan against (with --plan)")
    args = ap.parse_args()

    reports = []
    if args.plan:
        spec_path = args.spec or args.spec_path
        spec_ids = spec_unks = None
        if spec_path:
            srep = Report(spec_path)
            spec_ids, spec_unks = check_spec(load(spec_path), srep)
            if srep.errors:
                print(f"NOTE: the spec itself has {len(srep.errors)} error(s); validate it separately.")
        prep = Report(args.plan)
        check_plan(load(args.plan), prep, spec_ids, spec_unks)
        reports.append(prep)
    elif args.spec_path:
        rep = Report(args.spec_path)
        check_spec(load(args.spec_path), rep)
        reports.append(rep)
    else:
        ap.print_usage(sys.stderr)
        sys.exit(2)

    n_err = sum(len(r.errors) for r in reports)
    n_warn = sum(len(r.warnings) for r in reports)
    for r in reports:
        emit(r)
    print(f"RESULT: {'FAIL' if n_err else 'PASS'} ({n_err} errors, {n_warn} warnings)")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
