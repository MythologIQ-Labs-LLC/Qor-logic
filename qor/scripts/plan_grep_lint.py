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
    #: producers name their kind.
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

    warnings.extend(check_citation_evidence(text, plan=str(plan_path), repo_root=repo_root))
    return warnings


# --- Citation-drift enforcement (Phase 125; GH #152 / SG-CitationDrift-A P1) ---
_EVIDENCE_RE = re.compile(r"grep\b.*->")
_GIT_SHOW_RE = re.compile(r"git show\s+\S+:\S+")
_MIGRATION_RE = re.compile(r"\b\d{8,}[_-][\w-]+\.sql\b")
_FILE_LINE_RE = re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|sql|rs|go|js):\d+\b")
_LD_HEADING_RE = re.compile(r"^#+\s.*(locked decision|citation inventory)", re.IGNORECASE)
_ANY_HEADING_RE = re.compile(r"^#+\s")


# --- Evidence-statement parsing and resolution (Phase 223; GH #330) ---
#: `[git show <ref>:]<path> | grep ... -> <NN>:<observed>`. The `NN:` observation
#: is required: a statement without one carries nothing a truth check can resolve.
_EVIDENCE_STMT_RE = re.compile(
    r"(?:git\s+show\s+(?P<ref>\S+):(?P<gitpath>\S+)\s*\|\s*)?"
    r"grep\b[^\n]*?->\s*(?P<line>\d+):(?P<observed>[^\n]*)"
)
_WT_PATH_RE = re.compile(r"([\w./-]+\.(?:py|ts|tsx|sql|rs|go|js|md|json|toml))")


@dataclass(frozen=True)
class EvidenceStatement:
    """One grep-evidence statement parsed into a mechanically resolvable value."""

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
    """Return the cited line's text, or None when it cannot be resolved."""
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
    """Return Locked-Decision / Citation-Inventory regions."""
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


#: Phase 226 (GH #336): the canonical `/qor-plan` grep-n statement is itself a
#: truth-checked citation kind. A bare `git show <ref>:<path>` remains
#: presence-only because it still carries no line or expected text.
TRUTH_CHECKED_KINDS = ("file:line", "grep-n evidence")
PRESENCE_ONLY_KINDS = ("migration filename", "bare git show <ref>:<path>")


def _file_line_citations(block: str) -> list[tuple[str, int, int]]:
    """(citation, start, end) for every `path.ext:NN` span in the block."""
    return [(m.group(0), m.start(), m.end()) for m in _FILE_LINE_RE.finditer(block)]


def _demand_set(block: str) -> list[str]:
    """Distinct bare `file:line` citations owing paired evidence."""
    spans = [(m.start(), m.end()) for m in _EVIDENCE_STMT_RE.finditer(block)]
    seen: dict[str, None] = {}
    for citation, start, _end in _file_line_citations(block):
        if any(a <= start < b for a, b in spans):
            continue
        seen.setdefault(citation, None)
    return list(seen)


def _statement_index(block: str) -> dict[tuple[str, int], EvidenceStatement]:
    return {(s.path, s.line): s for s in parse_evidence_statements(block)}


def _statement_citation(stmt: EvidenceStatement) -> str:
    prefix = f"{stmt.ref}:" if stmt.ref else ""
    return f"{prefix}{stmt.path}:{stmt.line}"


def _truth_target_keys(block: str) -> set[tuple[str, int]]:
    keys = {(s.path, s.line) for s in parse_evidence_statements(block)}
    for citation in _demand_set(block):
        path, _, raw_line = citation.rpartition(":")
        keys.add((path, int(raw_line)))
    return keys


def check_citation_evidence(
    text: str, plan: str = "<plan>", repo_root: Path | None = None,
) -> list[LintWarning]:
    """Truth-check canonical grep-n evidence and pair bare file:line citations.

    Canonical ``git show <ref>:<path> | grep -nE ... -> NN:text`` statements are
    adjudicated directly. They no longer need an additional bare ``file:line``
    token elsewhere in the block to enter the truth-check set.
    """
    warnings: list[LintWarning] = []
    for start_line, block in _ld_blocks(text):
        statements = _statement_index(block)

        # First-class check for every canonical grep-n statement. This closes
        # GH #336: /qor-plan's mandated evidence form cannot pass merely because
        # the string contains `grep ... ->`.
        for stmt in statements.values():
            citation = _statement_citation(stmt)
            if resolve_line(stmt, repo_root) is None:
                warnings.append(LintWarning(
                    plan=plan, line=start_line, citation=citation,
                    reason="grep-n evidence names a path or line that will not resolve at the cited revision",
                    kind="evidence-unresolvable",
                ))
            elif not reproduces(stmt, repo_root):
                warnings.append(LintWarning(
                    plan=plan, line=start_line, citation=citation,
                    reason="grep-n evidence does not reproduce: the cited line does not hold the quoted text",
                    kind="evidence-not-reproducible",
                ))

        # Bare file:line citations still owe a statement naming the same path and
        # line. A present statement was already adjudicated above, so do not emit
        # a duplicate mismatch warning here.
        for citation in _demand_set(block):
            path, _, raw_line = citation.rpartition(":")
            if (path, int(raw_line)) in statements:
                continue
            warnings.append(LintWarning(
                plan=plan, line=start_line, citation=citation,
                reason="file:line citation carries no grep-evidence statement naming the same path and line",
                kind="unpaired-citation",
            ))

        if _EVIDENCE_RE.search(block):
            continue
        for citation in _sealed_citations(block):
            if _FILE_LINE_RE.fullmatch(citation):
                continue
            warnings.append(LintWarning(
                plan=plan, line=start_line, citation=citation,
                reason="sealed-infrastructure citation in a Locked-Decision block lacks paired grep-evidence (git show ... | grep ... -> observed)",
                kind="unpaired-citation",
            ))
    return warnings


def count_truth_checked(
    text: str, repo_root: Path | None = None,
) -> tuple[int, list[LintWarning]]:
    """Return distinct mechanically examined path/line targets and findings."""
    total = sum(len(_truth_target_keys(block)) for _, block in _ld_blocks(text))
    return total, check_citation_evidence(text, repo_root=repo_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.plan_grep_lint")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path.cwd()
    warnings = check_plan(args.plan, repo_root)

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
    return 0  # WARN-only by existing contract


if __name__ == "__main__":
    raise SystemExit(main())