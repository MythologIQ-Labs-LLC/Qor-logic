"""Author-momentum risk score for /qor-audit Step 1 (Phase 87; GH #82).

Scores the plan under audit for SG-007 author-audit-momentum risk and reports
whether the Option B independent reviewer is mandatory. Makes the Phase 68
Option B proactive: auto-mandated on the iteration where a risk signal first
appears, instead of operator-discretion dispatched reactively after a VETO.

V1 implements the two mechanically-deterministic GH #82 signals:
``config-file-cite`` and ``high-citation-surface``. Signals 2 and 3
(sealed-shared-module + new shared-type field; analytics emit + new
state-flow) are deferred -- see docs/plan-qor-phase87-audit-risk-score.md
boundaries. The ``RiskAssessment.flags`` tuple is open so they can be added
without an API change.

Extends ``SG-AuthorAuditMomentum-A`` (Phase 68) per
``qor/references/doctrine-shadow-genome-countermeasures.md``.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Signal 1: a cited *.config.{ts,js,yaml,toml} file (config-fabrication class).
_CONFIG_CITE_RE = re.compile(r"\b[\w./-]+\.config\.(?:ts|js|yaml|toml)\b")
# Signal 4: grep-evidence statements in the /qor-plan Step 2 Infrastructure
# Citation Inventory canonical form `git show <ref>:<path> | grep ...`.
_GREP_EVIDENCE_RE = re.compile(r"git show\b.+?\|\s*grep\b", re.IGNORECASE)
_CITATION_SURFACE_THRESHOLD = 5

# Phase 110 (#135) cascade signals -- SG-AffectedFilesContract-A. The lint
# modules own the canonical grammar; reuse it here to avoid divergence.
from qor.scripts._lint_utils import find_callers  # noqa: E402
from qor.scripts.plan_signature_widening_caller_lint import (  # noqa: E402
    _STOP_NAMES,
    _affected_paths,
    _widened_functions,
)
from qor.scripts.plan_data_round_trip_lint import (  # noqa: E402
    _field_additions,
    _persistence_files,
)

_CALLER_CASCADE_THRESHOLD = 3
_SCOPE_NARROW_RE = re.compile(r"[Uu]pdate\s+`(\w+)`\s+and\s+`(\w+)`")
_PUBLIC_FN_RE = re.compile(r"(?:pub\s+fn|def)\s+(\w+)")


def _detect_signature_widening_cascade(text: str, repo_root: Path) -> bool:
    for fn in _widened_functions(text):
        if fn in _STOP_NAMES or len(fn) < 8:
            continue
        if len(find_callers(fn, repo_root)) >= _CALLER_CASCADE_THRESHOLD:
            return True
    return False


def _detect_struct_field_cross_persistence(text: str, repo_root: Path) -> bool:
    return any(_persistence_files(struct, repo_root) for struct, _ in _field_additions(text))


def _detect_scope_narrowing_multi_entrypoint(text: str, repo_root: Path) -> bool:
    match = _SCOPE_NARROW_RE.search(text)
    if not match:
        return False
    named = set(match.groups())
    for rel in _affected_paths(text):
        path = repo_root / rel
        if not path.is_file():
            continue
        publics = set(_PUBLIC_FN_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
        if named & publics and (publics - named):
            return True
    return False


@dataclass(frozen=True)
class RiskAssessment:
    """Author-momentum risk for one plan.

    ``flags`` names every risk signal that fired; ``option_b_required`` is
    True iff at least one fired (GH #82: auto-dispatch when ANY signal hits).
    """
    flags: tuple[str, ...]
    option_b_required: bool


def score_plan(plan_path: Path, repo_root: Path | None = None) -> RiskAssessment:
    """Score a plan for SG-007 author-momentum risk.

    Fires ``config-file-cite`` when the plan cites >=1 ``*.config.*`` file, and
    ``high-citation-surface`` when it carries >=5 grep-evidence statements.
    Phase 110 (#135) adds three SG-AffectedFilesContract-A cascade signals
    (``signature-widening-cascade``, ``struct-field-cross-persistence-boundary``,
    ``scope-narrowing-prose-in-multi-entrypoint-file``) which require repo
    inspection; ``repo_root`` defaults to the current directory for API
    compatibility. A missing plan scores as no risk.
    """
    if not plan_path.exists():
        return RiskAssessment(flags=(), option_b_required=False)
    repo_root = Path(repo_root) if repo_root is not None else Path(".")
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    flags: list[str] = []
    if _CONFIG_CITE_RE.search(text):
        flags.append("config-file-cite")
    if len(_GREP_EVIDENCE_RE.findall(text)) >= _CITATION_SURFACE_THRESHOLD:
        flags.append("high-citation-surface")
    if _detect_signature_widening_cascade(text, repo_root):
        flags.append("signature-widening-cascade")
    if _detect_struct_field_cross_persistence(text, repo_root):
        flags.append("struct-field-cross-persistence-boundary")
    if _detect_scope_narrowing_multi_entrypoint(text, repo_root):
        flags.append("scope-narrowing-prose-in-multi-entrypoint-file")
    return RiskAssessment(flags=tuple(flags), option_b_required=bool(flags))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.audit_risk_score")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    assessment = score_plan(args.plan, repo_root=args.repo_root)
    if assessment.option_b_required:
        print(f"option_b_required: true (flags: {', '.join(assessment.flags)})")
        print(
            "Option B (independent reviewer) is MANDATORY for this audit -- "
            "the auditing agent must not run a solo audit."
        )
    else:
        print("option_b_required: false (no author-momentum risk signal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
