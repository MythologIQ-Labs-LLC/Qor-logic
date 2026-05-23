"""Substantiate-time structural check for a plan's Definition of Done (Phase 92; GH #86).

Invoked at ``/qor-substantiate`` Step 4.6.7 (between procedural-fidelity 4.6.6
and documentation integrity 4.7). Emits one finding per defect:

- ``missing-dod-section`` -- plan has no ``## Definition of Done`` block.
- ``deliverable-missing-tier`` -- a deliverable omits one or more D-tiers
  (and has no ``D4.d`` waiver).
- ``waiver-without-rationale`` -- a ``D4.d`` row has empty or whitespace-
  only rationale.
- ``waiver-without-followup`` -- a ``D4.d`` row lacks a follow-up phase
  reference.

V1 contract: severity is always ``warn``; CLI ``main()`` exits 0 even when
findings are present (mirrors ``delivery_branch_lint`` /
``ci_coverage_lint`` WARN-only convention). V2 may tighten specific
categories to ``severity="block"`` once adoption matures and operator
evidence confirms low false-positive rate.

Closes the substantiate-side half of GH #86; the plan-emission half is in
``qor.scripts.dod_record``. Doctrine: ``qor/references/doctrine-definition-of-done.md``.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts.dod_record import DodRecord, parse_plan

_REQUIRED_TIERS = ("d1", "d2", "d3")  # d4 OR d4.d waiver must be present


@dataclass(frozen=True)
class CheckFinding:
    """One V1 Definition-of-Done finding."""

    plan: str
    category: str
    deliverable: str | None
    detail: str
    severity: str  # 'warn' in V1


def _has_dod_section(plan_path: Path) -> bool:
    if not plan_path.is_file():
        return False
    text = plan_path.read_text(encoding="utf-8", errors="replace")
    return "## Definition of Done" in text


def _check_record(plan_path: Path, rec: DodRecord) -> list[CheckFinding]:
    findings: list[CheckFinding] = []
    plan_str = str(plan_path)

    missing_required = [t for t in _REQUIRED_TIERS if getattr(rec, t) is None]
    has_d4 = rec.d4 is not None
    has_d4_d = rec.d4_waiver_rationale is not None or rec.d4_waiver_followup is not None
    if not has_d4 and not has_d4_d:
        missing_required.append("d4")
    if missing_required:
        findings.append(CheckFinding(
            plan=plan_str,
            category="deliverable-missing-tier",
            deliverable=rec.deliverable,
            detail=f"missing tier(s): {', '.join(t.upper() for t in missing_required)}",
            severity="warn",
        ))

    # D4.d waiver shape checks
    if has_d4_d:
        if not rec.d4_waiver_rationale or not rec.d4_waiver_rationale.strip():
            findings.append(CheckFinding(
                plan=plan_str,
                category="waiver-without-rationale",
                deliverable=rec.deliverable,
                detail="D4.d row carries empty or whitespace-only rationale",
                severity="warn",
            ))
        if not rec.d4_waiver_followup:
            findings.append(CheckFinding(
                plan=plan_str,
                category="waiver-without-followup",
                deliverable=rec.deliverable,
                detail="D4.d row lacks a '**Follow-up phase**:' reference",
                severity="warn",
            ))

    return findings


def check_plan(plan_path: Path) -> list[CheckFinding]:
    """Walk plan's Definition of Done; emit one finding per defect.

    Returns [] when the plan declares a complete DoD block with no
    waiver-shape issues. V1 severity is always 'warn'; downstream
    substantiate Step 4.6.7 surfaces findings in the seal report but
    does not abort the seal.
    """
    if not _has_dod_section(plan_path):
        return [CheckFinding(
            plan=str(plan_path),
            category="missing-dod-section",
            deliverable=None,
            detail="plan has no '## Definition of Done' section",
            severity="warn",
        )]
    records = parse_plan(plan_path)
    findings: list[CheckFinding] = []
    for rec in records:
        findings.extend(_check_record(plan_path, rec))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qor.scripts.dod_check")
    parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args(argv)
    findings = check_plan(args.plan)
    if not findings:
        return 0
    print(f"dod_check: {len(findings)} finding(s)")
    for f in findings:
        scope = f.deliverable if f.deliverable else "(plan-level)"
        print(f"  WARN [{f.category}] {scope}")
        print(f"    detail: {f.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
