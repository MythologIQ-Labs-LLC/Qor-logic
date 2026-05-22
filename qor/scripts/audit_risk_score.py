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


@dataclass(frozen=True)
class RiskAssessment:
    """Author-momentum risk for one plan.

    ``flags`` names every risk signal that fired; ``option_b_required`` is
    True iff at least one fired (GH #82: auto-dispatch when ANY signal hits).
    """
    flags: tuple[str, ...]
    option_b_required: bool


def score_plan(plan_path: Path) -> RiskAssessment:
    """Score a plan for SG-007 author-momentum risk.

    Fires ``config-file-cite`` when the plan cites >=1 ``*.config.*`` file,
    and ``high-citation-surface`` when it carries >=5 grep-evidence
    statements. A missing plan scores as no risk.
    """
    if not plan_path.exists():
        return RiskAssessment(flags=(), option_b_required=False)
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    flags: list[str] = []
    if _CONFIG_CITE_RE.search(text):
        flags.append("config-file-cite")
    if len(_GREP_EVIDENCE_RE.findall(text)) >= _CITATION_SURFACE_THRESHOLD:
        flags.append("high-citation-surface")
    return RiskAssessment(flags=tuple(flags), option_b_required=bool(flags))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.audit_risk_score")
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args(argv)

    assessment = score_plan(args.plan)
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
