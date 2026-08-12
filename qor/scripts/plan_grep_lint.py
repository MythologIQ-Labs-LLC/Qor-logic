"""Pre-audit lint: detect infrastructure-mismatch citations in plan files (Phase 55).

Walks a plan file; extracts cited Python module paths
(``qor.scripts.<name>``, ``qor.policy.<name>``, etc.) and skill paths
(``qor/skills/**/*.md``); verifies each cited path resolves at HEAD.
References declared as NEW in the plan's Affected Files block are excluded.

Closes the Phase 53/54/55 recurring infrastructure-mismatch pattern at the
pre-audit lint layer per ``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-PreAuditLintGap-A.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LintWarning:
    plan: str
    line: int
    citation: str
    reason: str
    #: Phase 223 (GH #330). Required, no default: a required field with honest
    #: values beats an optional one with a meaningless default, so all three
    #: producers name their kind. Five values -- the two `check_plan` path
    #: warnings plus the three citation-evidence kinds.
    kind: str


_MODULE_RE = re.compile(r"\bqor\.(?:scripts|policy|reliability|cli_handlers)\.([\w_]+)")
_SKILL_PATH_RE = re.compile(r"qor/skills/(?:[\w_-]+/)+SKILL\.md")
_REFERENCE_PATH_RE = re.compile(r"qor/references/[\w_-]+\.md")
_NEW_DECLARATION_RE = re.compile(
    r"^[-*]\s+`(?P<path>[^`]+)`.*\bNEW\b", re.MULTILINE,
)


def _module_to_path(module_segment: str, repo_root: Path) -> Path:
    """qor.scripts.foo → qor/scripts/foo.py"""
    parts = module_segment.split(".")
    return repo_root.joinpath(*parts).with_suffix(".py")


def _new_paths(text: str) -> set[str]:
    """Paths the plan declares as NEW in any Affected Files block."""
    return {m.group("path") for m in _NEW_DECLARATION_RE.finditer(text)}


def check_plan(plan_path: Path, repo_root: Path) -> list[LintWarning]:
    if not plan_path.exists():
        return []
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    new_paths = _new_paths(text)
    warnings: list[LintWarning] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in re.finditer(r"\bqor\.(scripts|policy|reliability|cli_handlers)\.([\w_]+)\b", line):
            module_name = match.group(2)
            # Skip placeholder-style citations and explicit test-fixture names.
            if len(module_name) <= 1 or (module_name.isupper() and len(module_name) <= 3):
                continue
            if any(token in module_name.lower() for token in ("fake", "nonexistent", "synthetic", "fixture", "new_helper", "new_module")):
                continue
            module = f"qor.{match.group(1)}.{module_name}"
            full_path = repo_root / "qor" / match.group(1) / f"{module_name}.py"
            if any(full_path.as_posix().endswith(p) for p in new_paths):
                continue
            if any(p.endswith(f"qor/{match.group(1)}/{module_name}.py") for p in new_paths):
                continue
            if not full_path.exists():
                warnings.append(LintWarning(
                    plan=str(plan_path), line=line_no,
                    citation=module,
                    reason=f"module path {full_path.relative_to(repo_root)} does not exist",
                    kind="module-path-missing",
                ))

        for match in _SKILL_PATH_RE.finditer(line):
            skill_path = match.group(0)
            if skill_path in new_paths:
                continue
            # Skip placeholder/test-fixture skill paths.
            if any(token in skill_path.lower() for token in ("fake-", "synthetic-", "nonexistent-")):
                continue
            full_path = repo_root / skill_path
            if not full_path.exists():
                warnings.append(LintWarning(
                    plan=str(plan_path), line=line_no,
                    citation=skill_path,
                    reason="skill path does not exist",
                    kind="skill-path-missing",
                ))

    warnings.extend(check_citation_evidence(text, plan=str(plan_path)))
    return warnings


# --- Citation-drift enforcement (Phase 125; GH #152 / SG-CitationDrift-A P1) ---
# A grep-evidence statement: a `grep` invocation completed with `-> <observed text>`.
_EVIDENCE_RE = re.compile(r"grep\b.*->")
# Sealed-infrastructure citation kinds (high-confidence, low false-positive).
_GIT_SHOW_RE = re.compile(r"git show\s+\S+:\S+")
_MIGRATION_RE = re.compile(r"\b\d{8,}[_-][\w-]+\.sql\b")
_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
# The check runs ONLY inside these regions so plans that don't use the
# Locked-Decision discipline produce zero findings (no over-flag).
_LD_HEADING_RE = re.compile(r"^#+\s.*(locked decision|citation inventory)", re.IGNORECASE)
_ANY_HEADING_RE = re.compile(r"^#+\s")


# --- Evidence-statement parsing and resolution (Phase 223; GH #330) ---
# The predicate above checks that a statement EXISTS. It reads neither the path,
# the line, nor the observed text, so a citation whose line does not hold its
# quoted content passes (ledger #565). These parse a statement into a value that
# can be resolved against the revision it names.

#: `[git show <ref>:]<path> | grep ... -> <NN>:<observed>`. The `NN:` observation
#: is required: a statement without one satisfies `_EVIDENCE_RE` and carries
#: nothing a truth check can resolve, so it is deliberately not parsed.
_EVIDENCE_STMT_RE = re.compile(
    r"(?:git\s+show\s+(?P<ref>\S+):(?P<gitpath>\S+)\s*\|\s*)?"
    r"grep\b[^\n]*?->\s*(?P<line>\d+):(?P<observed>[^\n]*)"
)
#: Fallback path capture for the working-tree form, which names its file inside
#: the grep invocation rather than before a pipe.
_WT_PATH_RE = re.compile(r"([\w./-]+\.(?:py|ts|tsx|sql|rs|go|js|md|json|toml))")


@dataclass(frozen=True)
class EvidenceStatement:
    """One grep-evidence statement, parsed into something resolvable.

    ``ref`` is None for the working-tree form. ``observed`` is the text right of
    the ``NN:`` prefix, unstripped -- comparison strips both sides so indentation
    does not fail a true citation.
    """

    ref: str | None
    path: str
    line: int
    observed: str


def parse_evidence_statements(block: str) -> list[EvidenceStatement]:
    """Parse every resolvable evidence statement in ``block``, in order."""
    out: list[EvidenceStatement] = []
    for match in _EVIDENCE_STMT_RE.finditer(block):
        path = match.group("gitpath")
        if path is None:
            candidates = _WT_PATH_RE.findall(match.group(0))
            if not candidates:
                continue
            path = candidates[0]
        out.append(EvidenceStatement(
            ref=match.group("ref"), path=path,
            line=int(match.group("line")), observed=match.group("observed"),
        ))
    return out


def resolve_line(stmt: EvidenceStatement, repo_root: Path | None = None) -> str | None:
    """Return the cited line's text, or None when it cannot be resolved.

    None is a distinct outcome from a mismatch: an environment that cannot answer
    is not an answer that is wrong, which is why the caller gives it its own
    finding kind.
    """
    root = repo_root or Path.cwd()
    if stmt.ref:
        completed = subprocess.run(
            ["git", "show", f"{stmt.ref}:{stmt.path}"],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
        )
        if completed.returncode != 0:
            return None
        body = completed.stdout
    else:
        target = root / stmt.path
        if not target.is_file():
            return None
        body = target.read_text(encoding="utf-8", errors="replace")

    lines = body.splitlines()
    if not 1 <= stmt.line <= len(lines):
        return None
    return lines[stmt.line - 1]


def reproduces(stmt: EvidenceStatement, repo_root: Path | None = None) -> bool:
    """True iff the cited line holds the quoted text, compared stripped."""
    actual = resolve_line(stmt, repo_root)
    return actual is not None and actual.strip() == stmt.observed.strip()


def _ld_blocks(text: str) -> list[tuple[int, str]]:
    """Return (start_line, block_text) for each Locked-Decision / Citation-Inventory
    region: from its heading up to (not including) the next heading."""
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        if _LD_HEADING_RE.match(lines[i]):
            start = i
            j = i + 1
            while j < len(lines) and not _ANY_HEADING_RE.match(lines[j]):
                j += 1
            blocks.append((start + 1, "\n".join(lines[start:j])))
            i = j
        else:
            i += 1
    return blocks


def _sealed_citations(block: str) -> list[str]:
    found: list[str] = []
    for rx in (_GIT_SHOW_RE, _MIGRATION_RE, _FILE_LINE_RE):
        found.extend(m.group(0) for m in rx.finditer(block))
    return found


#: Citation kinds whose truth is mechanically checkable. `.md` is absent from
#: `_FILE_LINE_RE`'s extension set, and a migration filename or a bare
#: `git show <ref>:<path>` carries no line, so those stay presence-only.
TRUTH_CHECKED_KINDS = ("file:line",)
PRESENCE_ONLY_KINDS = ("migration filename", "git show <ref>:<path>")


def _file_line_citations(block: str) -> list[tuple[str, int, int]]:
    """(citation, start, end) for every `path.ext:NN` span in the block."""
    return [(m.group(0), m.start(), m.end()) for m in _FILE_LINE_RE.finditer(block)]


def _demand_set(block: str) -> list[str]:
    """Distinct `file:line` citations owing evidence, in first-seen order.

    Two reductions, and they are not the same one. Span exclusion drops a
    citation lying inside a parsed statement, without which every statement
    would demand a statement. Deduplication by `(path, line)` then collapses
    restatements -- a table repeating a citation multiplies one location into
    several, and the reported count is of distinct locations.
    """
    spans = [(m.start(), m.end()) for m in _EVIDENCE_STMT_RE.finditer(block)]
    seen: dict[str, None] = {}
    for citation, start, _end in _file_line_citations(block):
        if any(a <= start < b for a, b in spans):
            continue
        seen.setdefault(citation, None)
    return list(seen)


def _statement_index(block: str) -> dict[tuple[str, int], EvidenceStatement]:
    return {(s.path, s.line): s for s in parse_evidence_statements(block)}


def check_citation_evidence(
    text: str, plan: str = "<plan>", repo_root: Path | None = None,
) -> list[LintWarning]:
    """Pair each `file:line` citation with its own reproducible evidence.

    Phase 125 satisfied a whole region whenever any statement appeared in it, so
    one true statement covered every citation beside it. The doctrine has said
    "paired" since Phase 72; this makes the implementation agree.

    Other citation kinds keep the legacy block-level presence rule, satisfied by
    ``_EVIDENCE_RE`` rather than by ``parse_evidence_statements`` -- a statement
    with no ``NN:`` observation still counts as presence, which is what keeps the
    Phase 125 suite's expectations true.
    """
    warnings: list[LintWarning] = []
    for start_line, block in _ld_blocks(text):
        statements = _statement_index(block)

        for citation in _demand_set(block):
            path, _, raw_line = citation.rpartition(":")
            stmt = statements.get((path, int(raw_line)))
            if stmt is None:
                kind, reason = ("unpaired-citation",
                                "file:line citation carries no grep-evidence statement "
                                "naming the same path and line")
            elif resolve_line(stmt, repo_root) is None:
                kind, reason = ("evidence-unresolvable",
                                "grep-evidence names a path that will not resolve at the "
                                "cited revision")
            elif not reproduces(stmt, repo_root):
                kind, reason = ("evidence-not-reproducible",
                                "grep-evidence does not reproduce: the cited line does not "
                                "hold the quoted text")
            else:
                continue
            warnings.append(LintWarning(
                plan=plan, line=start_line, citation=citation,
                reason=reason, kind=kind,
            ))

        if _EVIDENCE_RE.search(block):
            continue
        for citation in _sealed_citations(block):
            if _FILE_LINE_RE.fullmatch(citation):
                continue  # already adjudicated above
            warnings.append(LintWarning(
                plan=plan, line=start_line, citation=citation,
                reason="sealed-infrastructure citation in a Locked-Decision block "
                       "lacks paired grep-evidence (git show ... | grep ... -> observed)",
                kind="unpaired-citation",
            ))
    return warnings


def count_truth_checked(
    text: str, repo_root: Path | None = None,
) -> tuple[int, list[LintWarning]]:
    """Distinct `(path, line)` citations examined, and the findings against them.

    The count is of the deduplicated demand set. A run reporting zero
    truth-checked citations is not the same as a clean one, and stating the count
    is what keeps those distinguishable.
    """
    total = sum(len(_demand_set(block)) for _, block in _ld_blocks(text))
    return total, check_citation_evidence(text, repo_root=repo_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_grep_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path.cwd()
    warnings = check_plan(args.plan, repo_root)

    # State the ceiling where the lint reports. A ceiling stated only in a
    # doctrine nobody reads at the moment of use is not stated (Phase 223).
    if args.plan.exists():
        checked, _ = count_truth_checked(
            args.plan.read_text(encoding="utf-8", errors="replace"), repo_root,
        )
        print(
            f"plan-grep-lint: {checked} citation(s) truth-checked "
            f"[{', '.join(TRUTH_CHECKED_KINDS)}]; "
            f"presence-only kinds not verified [{', '.join(PRESENCE_ONLY_KINDS)}]",
            file=sys.stderr,
        )

    if not warnings:
        return 0
    for w in warnings:
        print(
            f"WARN [plan-grep-lint] {w.plan}:{w.line} [{w.citation}] {w.reason}",
            file=sys.stderr,
        )
    print(
        f"\n{len(warnings)} infrastructure-mismatch citations detected. "
        f"Either declare the cited path as NEW in Affected Files, or fix "
        f"the citation to match an existing repo path.",
        file=sys.stderr,
    )
    return 0  # WARN-only


if __name__ == "__main__":
    raise SystemExit(main())
