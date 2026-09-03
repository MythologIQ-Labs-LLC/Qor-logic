"""Pre-audit lint: detect infrastructure-mismatch citations in plan files (Phase 55).

Walks a plan file; extracts cited Python module paths
(``qor.scripts.<name>``, ``qor.policy.<name>``, etc.) and skill paths
(``qor/skills/**/*.md``); verifies each cited path resolves at HEAD.
References declared as NEW in the plan's Affected Files block are excluded.

Closes the Phase 53/54/55 recurring infrastructure-mismatch pattern at the
pre-audit lint layer per ``qor/references/doctrine-shadow-genome-countermeasures.md``
SG-PreAuditLintGap-A.

The evidence-statement grammar and citation scanning live in ``plan_evidence``
(Phase 225); this module keeps the policy: what a plan owes, and the findings
when it does not pay.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts.plan_evidence import (  # noqa: F401 -- re-exported grammar names
    EvidenceStatement,
    _EVIDENCE_RE,
    _EVIDENCE_STMT_RE,
    _FILE_LINE_RE,
    _WT_PATH_RE,
    _demand_set,
    _ld_blocks,
    _sealed_citations,
    _statement_index,
    parse_evidence_statements,
    reproduces,
    resolve_line,
)


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
# Phase 255: a plan that DISCUSSES an unresolvable path is indistinguishable
# from one that CITES it. Mirrors publication_boundary_lint's
# `boundary-lint: ok=<reason>` and prose_test_lint's `# prose-lint: ok=<reason>`:
# the reason is required (`\S`) so an empty marker cannot silence the control,
# and scope is per line -- no file-level or directory-level suppression.
_ALLOW_RE = re.compile(r"grep-lint:\s*ok=(\S[^\s>]*)")
# Placeholder citations the reference family uses by convention.
_REFERENCE_PLACEHOLDERS = ("foo", "bar", "baz", "example", "nonexistent",
                          "fake", "synthetic", "new-thing")
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

        if not _ALLOW_RE.search(line):
            for match in _REFERENCE_PATH_RE.finditer(line):
                ref_path = match.group(0)
                if ref_path in new_paths:
                    continue
                stem = ref_path.rsplit("/", 1)[-1][:-3]
                bare = stem[len("doctrine-"):] if stem.startswith("doctrine-") else stem
                if bare in _REFERENCE_PLACEHOLDERS:
                    continue
                if not (repo_root / ref_path).exists():
                    warnings.append(LintWarning(
                        plan=str(plan_path), line=line_no,
                        citation=ref_path,
                        reason="reference path does not exist",
                        kind="reference-path-missing",
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


#: Citation kinds whose truth is mechanically checkable. A migration filename
#: or a bare `git show` reference carries no line to verify, so those stay
#: presence-only. Names must survive the doctrine ceiling test's parser:
#: no period or comma inside a kind name.
TRUTH_CHECKED_KINDS = ("file:line", "grep-n evidence")
PRESENCE_ONLY_KINDS = ("migration filename", "bare git show ref-path")


def _adjudicate(stmt: EvidenceStatement, repo_root: Path | None) -> tuple[str, str] | None:
    """(kind, reason) when the statement fails its truth check; None when clean."""
    at_ref = f" at {stmt.ref}" if stmt.ref else ""
    if resolve_line(stmt, repo_root) is None:
        return ("evidence-unresolvable",
                f"grep-evidence names a path or line that will not resolve{at_ref}")
    if not reproduces(stmt, repo_root):
        return ("evidence-not-reproducible",
                f"grep-evidence{at_ref} does not reproduce: the cited line does not "
                "hold the quoted text")
    return None


def check_citation_evidence(
    text: str, plan: str = "<plan>", repo_root: Path | None = None,
) -> list[LintWarning]:
    """Adjudicate every statement on its own account; pair bare citations.

    A parsed statement is evidence in itself (Phase 225; GH #336) -- nothing
    needs to demand it. Findings carry bare `<path>:<line>` citation keys; a
    statement's ref lives in the reason. Bare citations still owe a statement
    at the same `(path, line)`; one that has it was adjudicated above, so no
    duplicate finding. Non-file:line kinds keep the block-level presence rule.
    """
    warnings: list[LintWarning] = []
    for start_line, block in _ld_blocks(text):
        statements = _statement_index(block)
        for (path, line), stmt in statements.items():
            verdict = _adjudicate(stmt, repo_root)
            if verdict is not None:
                warnings.append(LintWarning(plan=plan, line=start_line,
                                            citation=f"{path}:{line}",
                                            reason=verdict[1], kind=verdict[0]))
        for citation in _demand_set(block):
            path, _, raw_line = citation.rpartition(":")
            if (path, int(raw_line)) in statements:
                continue
            warnings.append(LintWarning(
                plan=plan, line=start_line, citation=citation,
                reason="file:line citation carries no grep-evidence statement "
                       "naming the same path and line",
                kind="unpaired-citation"))
        if _EVIDENCE_RE.search(block):
            continue
        for citation in _sealed_citations(block):
            if _FILE_LINE_RE.fullmatch(citation):
                continue  # adjudicated above
            warnings.append(LintWarning(
                plan=plan, line=start_line, citation=citation,
                reason="sealed-infrastructure citation in a Locked-Decision block "
                       "lacks paired grep-evidence (git show ... | grep ... -> observed)",
                kind="unpaired-citation"))
    return warnings


def _truth_targets(block: str) -> set[tuple[str, int]]:
    """Distinct (path, line) targets examined: statements union bare demands."""
    keys = {(s.path, s.line) for s in parse_evidence_statements(block)}
    for citation in _demand_set(block):
        path, _, raw_line = citation.rpartition(":")
        keys.add((path, int(raw_line)))
    return keys


def count_truth_checked(
    text: str, repo_root: Path | None = None,
) -> tuple[int, list[LintWarning]]:
    """Distinct `(path, line)` targets examined, and the findings against them.

    The count is the per-block union of parsed statements and demanded
    citations. A plan citing solely in the mandated form reports what it
    checked instead of zero -- reporting zero while having checked one was the
    GH #336 defect restated.
    """
    total = sum(len(_truth_targets(block)) for _, block in _ld_blocks(text))
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
