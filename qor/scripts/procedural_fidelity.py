"""Phase 58: procedural-fidelity check at /qor-substantiate Step 4.6.6.

Static analyzer over the implement-gate `files_touched` set. Emits
Deviation records when the seal commit's surface coverage doesn't match
the doc-surface coverage rule (skills/scripts/doctrines/schemas touched
without at least one system-tier doc updated). Closes B23 (operator
request from Phase 57 substantiate cycle).

WARN-only at Step 4.6.6: deviations append severity-2 events to the
Process Shadow Genome but do NOT abort substantiate. Operators learn
from accumulated events; future phase may tighten to BLOCK.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from qor.scripts import shadow_process


DEVIATION_CLASSES: frozenset[str] = frozenset({
    "missing-step",
    "doc-surface-uncovered",
    "ordering-drift",
    "argv-shape-divergence",
})


@dataclass(frozen=True)
class Deviation:
    deviation_class: str
    severity: int
    step_id: str | None
    description: str
    files_referenced: tuple[str, ...]


# The four system-tier docs that satisfy the at-least-one threshold
# (per Phase 58 Open Question 2 default).
_SYSTEM_TIER_DOCS: frozenset[str] = frozenset({
    "docs/SYSTEM_STATE.md",
    "docs/operations.md",
    "docs/architecture.md",
    "docs/lifecycle.md",
})

# File-path patterns that trigger the doc-surface coverage requirement.
# When the implement gate's files_touched contains any path matching one
# of these, at least one entry from _SYSTEM_TIER_DOCS must also be present.
_TRIGGER_PREFIXES: tuple[str, ...] = (
    "qor/skills/",
    "qor/scripts/",
    "qor/references/doctrine-",
    "qor/gates/schema/",
)


def _is_trigger(path: str) -> bool:
    """True when `path` is a doc-surface coverage trigger."""
    if path.endswith(".py") and not path.startswith("qor/scripts/"):
        return False
    return any(path.startswith(p) for p in _TRIGGER_PREFIXES)


def _detect_doc_surface_coverage(touched: list[str]) -> list[Deviation]:
    """Phase 58 primary detector. Skill/script/doctrine/schema changes
    require at least one system-tier doc update."""
    triggers = [p for p in touched if _is_trigger(p)]
    if not triggers:
        return []
    has_system_doc = any(p in _SYSTEM_TIER_DOCS for p in touched)
    if has_system_doc:
        return []
    return [Deviation(
        deviation_class="doc-surface-uncovered",
        severity=2,
        step_id="substantiate-step-6",
        description=(
            "Seal commit touches skill/script/doctrine/schema surface but does not "
            "update any of: " + ", ".join(sorted(_SYSTEM_TIER_DOCS))
        ),
        files_referenced=tuple(triggers),
    )]


def _detect_missing_step(touched: list[str], repo_root: Path) -> list[Deviation]:
    """Phase 58 v1: stub returning []. Implementation lands when the
    failure-mode catalog grows past doc-surface coverage."""
    return []


def _detect_ordering_drift(touched: list[str]) -> list[Deviation]:
    """Phase 58 v1: stub. Reserved for future ordering-drift detection."""
    return []


def _detect_argv_shape_divergence(touched: list[str]) -> list[Deviation]:
    """Phase 58 v1: stub. Reserved for future argv-shape detection."""
    return []


def _read_implement_gate(repo_root: Path, session_id: str) -> dict | None:
    gate = repo_root / ".qor" / "gates" / session_id / "implement.json"
    if not gate.exists():
        return None
    try:
        return json.loads(gate.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def check_seal_commit(
    repo_root: Path, session_id: str,
) -> list[Deviation]:
    """Run all v1 detectors against the implement-gate files_touched set.

    Returns aggregated deviations. Empty list when clean.
    Raises FileNotFoundError when the implement gate is missing (the CLI
    catches this and exits 2; library callers can decide).
    """
    payload = _read_implement_gate(repo_root, session_id)
    if payload is None:
        raise FileNotFoundError(
            f"implement gate not found at "
            f"{repo_root}/.qor/gates/{session_id}/implement.json"
        )
    touched: list[str] = payload.get("files_touched") or []
    findings: list[Deviation] = []
    findings.extend(_detect_doc_surface_coverage(touched))
    findings.extend(_detect_missing_step(touched, repo_root))
    findings.extend(_detect_ordering_drift(touched))
    findings.extend(_detect_argv_shape_divergence(touched))
    return findings


def to_findings_json(findings: list[Deviation]) -> list[dict]:
    """Convert Deviation list to gate_chain-compatible JSON."""
    return [{
        "class": d.deviation_class,
        "severity": d.severity,
        "step_id": d.step_id,
        "description": d.description,
        "files_referenced": list(d.files_referenced),
        "addressed": False,
    } for d in findings]


def _emit_genome_events(findings: list[Deviation], session_id: str) -> None:
    """Append severity-2 events per deviation to the Process Shadow Genome."""
    for d in findings:
        try:
            shadow_process.append_event({
                "ts": shadow_process.now_iso(),
                "skill": "qor-substantiate",
                "session_id": session_id,
                "event_type": "procedural_deviation",
                "severity": d.severity,
                "details": {
                    "class": d.deviation_class,
                    "step_id": d.step_id,
                    "description": d.description,
                    "files_referenced": list(d.files_referenced),
                },
                "addressed": False, "issue_url": None, "addressed_ts": None,
                "addressed_reason": None, "source_entry_id": None,
            })
        except Exception:
            # Hook-style: errors writing genome events must not break substantiate.
            # KeyboardInterrupt / SystemExit propagate.
            pass


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qor.scripts.procedural_fidelity")
    p.add_argument("--session", required=True,
                   help="Session ID (reads .qor/gates/<session>/implement.json)")
    p.add_argument("--repo-root", default=".",
                   help="Repo root (default: cwd)")
    p.add_argument("--out", default=None,
                   help="Findings JSON output path (default: stdout-only)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    try:
        findings = check_seal_commit(repo_root, args.session)
    except FileNotFoundError as e:
        sys.stderr.write(f"ERROR: {e}\n")
        return 2

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(to_findings_json(findings), indent=2),
            encoding="utf-8",
        )

    if findings:
        sys.stderr.write(
            f"WARN: {len(findings)} procedural-fidelity deviation(s) detected\n"
        )
        for d in findings:
            sys.stderr.write(
                f"  [{d.deviation_class}] severity={d.severity} {d.description}\n"
            )
        _emit_genome_events(findings, args.session)

    # WARN posture: exit 0 even with deviations (per Open Question 1 default).
    return 0


if __name__ == "__main__":
    sys.exit(main())
