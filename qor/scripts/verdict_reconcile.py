"""Reconcile an audit report against its gate artifact (Phase 218; GH #313).

`/qor-implement` Step 2 branches on the verdict string in
`.agent/staging/AUDIT_REPORT.md`. That directory is not session-scoped, so a
report from an earlier phase survives indefinitely and the interdiction passes
on a PASS belonging to different work -- passing for the wrong reason, which is
worse than failing.

The gate artifact already records `target` and `target_content_hash`. This
module compares them. It answers "do these two records describe the same
audit?", not "was the audit correct".
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_TARGET_RE = re.compile(r"^\*\*Target\*\*:\s*(\S+)\s*$", re.MULTILINE)
_VERDICT_RE = re.compile(r"^\*\*Verdict\*\*:\s*(\w+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Finding:
    """One disagreement between the two records."""

    code: str
    detail: str


def _normalize(target: str | None) -> str | None:
    """Compare paths by separator-independent form.

    A gate artifact written on Windows records `docs\plan-x.md` while the
    report carries `docs/plan-x.md`. Comparing raw strings reports
    `target-mismatch` on identical paths, which would ABORT every implement on
    that platform -- a false positive in the fix for false negatives.
    """
    return target.replace("\\", "/") if target is not None else None


def _read_report(report_path: Path) -> tuple[str | None, str | None]:
    try:
        body = Path(report_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None
    target = _TARGET_RE.search(body)
    verdict = _VERDICT_RE.search(body)
    return (target.group(1) if target else None,
            verdict.group(1) if verdict else None)


def _read_artifact(artifact_path: Path) -> dict | None:
    try:
        data = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def reconcile(
    report_path: Path,
    artifact_path: Path,
    *,
    plan_digest: str | None = None,
) -> list[Finding]:
    """Return every disagreement; empty means the two records agree.

    `plan_digest` is the current content hash of the plan. When supplied it is
    compared against the artifact's `target_content_hash`, which catches a
    report written against a since-amended plan -- a case path comparison alone
    accepts.
    """
    findings: list[Finding] = []
    artifact = _read_artifact(artifact_path)
    if artifact is None:
        return [Finding("artifact-missing",
                        f"no readable audit gate artifact at {artifact_path}")]

    report_target, report_verdict = _read_report(report_path)
    if report_target is None:
        findings.append(Finding("report-unreadable",
                                f"no **Target** line in {report_path}"))
    elif _normalize(report_target) != _normalize(artifact.get("target")):
        findings.append(Finding(
            "target-mismatch",
            f"report names {report_target!r}; artifact names "
            f"{artifact.get('target')!r}"))

    if report_verdict != "PASS":
        findings.append(Finding("verdict-not-pass",
                                f"report verdict is {report_verdict!r}"))

    recorded = artifact.get("target_content_hash")
    if plan_digest is not None and recorded is not None and plan_digest != recorded:
        findings.append(Finding(
            "digest-mismatch",
            f"plan digest {plan_digest[:16]} != audited {recorded[:16]}; "
            "the plan changed after the verdict"))
    return findings


def main(argv: list[str] | None = None) -> int:
    """CLI surface. Phase 217 shipped a seal step wired to a flag its module
    never accepted; a module the skill cannot actually invoke is the same
    defect. This entry point exists so the wiring in /qor-implement Step 2 runs.
    """
    ap = argparse.ArgumentParser(prog="verdict_reconcile", description=__doc__.splitlines()[0])
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--artifact", required=True, type=Path)
    ap.add_argument("--plan-digest", default=None)
    args = ap.parse_args(argv)

    findings = reconcile(args.report, args.artifact, plan_digest=args.plan_digest)
    for finding in findings:
        print(f"[{finding.code}] {finding.detail}", file=sys.stderr)
    print(f"verdict_reconcile: {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
