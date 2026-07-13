"""Governance artifact health checker (Phase 109, D-109.1).

Classifies the required governance artifacts as ``OK``, ``UNINITIALIZED``,
``MISSING``, ``DAMAGED``, or ``INCOMPLETE`` and reports, per finding, the only
legal next action. The invariant: no ``/qor-*`` prompt may synthesize a plan,
audit, implementation, or seal from assumptions when an artifact is missing,
damaged, or incomplete. ``DAMAGED`` and ``INCOMPLETE`` never return seed or
bootstrap as legal repair (D-109.1 D2).

Pure API (no side effects); a thin ``main`` exposes ``python -m
qor.scripts.governance_health`` with the exit-code contract 0/1/2.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from qor.seed import scaffold_file_targets


class ArtifactStatus(str, Enum):
    OK = "ok"
    UNINITIALIZED = "uninitialized"
    MISSING = "missing"
    DAMAGED = "damaged"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class ArtifactFinding:
    path: str
    status: ArtifactStatus
    reason: str
    legal_next: str


REQUIRED_ARTIFACTS: tuple[str, ...] = (
    "docs/META_LEDGER.md",
    "docs/CONCEPT.md",
    "docs/ARCHITECTURE_PLAN.md",
    "docs/SYSTEM_STATE.md",
    "docs/SHADOW_GENOME.md",
    "docs/BACKLOG.md",
    "docs/FEATURE_INDEX.md",
    "docs/GOVERNANCE_INDEX.md",
)

# Scaffold-owned (seed-repairable) artifacts, pinned to seed's file targets so
# the seed list and the required-artifact list cannot drift (Phase 109 LD3).
SCAFFOLD_OWNED: frozenset[str] = scaffold_file_targets()

# Named required-artifact profiles for CLI/preflight selection.
PROFILES: dict[str, tuple[str, ...]] = {"skill-entry": REQUIRED_ARTIFACTS}

_LEDGER = "docs/META_LEDGER.md"
_PROJECT_DNA = ("docs/CONCEPT.md", "docs/ARCHITECTURE_PLAN.md")
# GH #200: match TEMPLATE-FORM placeholders only -- a structural cue, not the
# bare word. Prose mentions of "TODO"/"FIXME" (e.g. "TODO stubs", "cosmetic
# TODOs") must NOT trip INCOMPLETE; a "TODO:" label, an HTML-comment scaffold,
# or a bracketed fill-in slot must. Mirrors the discipline already in
# _ledger_incomplete (which only flags an unfilled scaffold).
_PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTODO\s*:"),
    re.compile(r"\bFIXME\s*:"),
    re.compile(r"<!--\s*(?:TODO|FIXME)"),
    re.compile(r"\{\{\s*verify"),
    re.compile(r"INSTRUCTION:"),
    re.compile(r"\[Your "),
    re.compile(r"\[Keyword"),
    re.compile(r"\[ISO 8601"),
    re.compile(r"\[Why "),
)

_NEXT_BOOTSTRAP = "/qor-bootstrap (or `qor-logic seed` when an autonomous skill owns recovery)"
_NEXT_SEED = "`qor-logic seed` (scaffold-owned artifact; missing scaffold may be seeded)"
_NEXT_REMEDIATE = "/qor-remediate (must be repaired, never seeded or bootstrapped over)"
_NEXT_RESTORE = (
    "restore via `qor-logic scripts governance_snapshot restore --from "
    ".agent/local-backup/governance/<sid>` (or from git history), then "
    "/qor-remediate -- never seeded or re-initialized over"
)
_NEXT_COMPLETE = "complete the required sections of {path} before continuing (never seeded)"


def _is_initialized(base: Path) -> bool:
    """A workspace is initialized once a ledger or any project DNA file exists."""
    if (base / _LEDGER).is_file():
        return True
    return any((base / rel).is_file() for rel in _PROJECT_DNA)


def _classify_missing(
    rel_path: str, initialized: bool, prior_evidence: str | None = None
) -> ArtifactFinding:
    if not initialized:
        # Phase 175 (GH #267): a workspace that was governed before but lost
        # its DNA files must never route to bootstrap over recoverable
        # history -- surface the restore path instead.
        if prior_evidence:
            return ArtifactFinding(
                rel_path, ArtifactStatus.MISSING,
                f"previously initialized ({prior_evidence}); governance state lost",
                _NEXT_RESTORE,
            )
        return ArtifactFinding(
            rel_path, ArtifactStatus.UNINITIALIZED,
            "no ledger and no project DNA present", _NEXT_BOOTSTRAP,
        )
    if rel_path in SCAFFOLD_OWNED:
        return ArtifactFinding(
            rel_path, ArtifactStatus.MISSING,
            "scaffold-owned artifact absent in an initialized workspace", _NEXT_SEED,
        )
    return ArtifactFinding(
        rel_path, ArtifactStatus.MISSING,
        "required non-scaffold artifact absent", _NEXT_REMEDIATE,
    )


def _ledger_damage(base: Path, text: str) -> str | None:
    """Return a damage reason for the ledger, or None when structurally sound."""
    has_title = "Meta Ledger" in text or text.lstrip().startswith("# ")
    has_entries = "### Entry" in text
    if not has_title and not has_entries:
        return "malformed ledger: no recognizable header or entries"
    if has_entries:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = _verify_ledger_chain(base / _LEDGER)
        if rc != 0:
            # GH #199: strict verify rejects single-lineage manual-era residuals
            # that the release gate already tolerates. Fall back to the
            # post-anchor surface: a disclosed pre-anchor failure (entry at or
            # below the auto-detected boundary) is tolerated here exactly as it
            # is at release; only a genuine post-anchor failure is real damage.
            with contextlib.redirect_stdout(io.StringIO()):
                rc_post = _verify_post_anchor(base / _LEDGER)
            if rc_post != 0:
                return "ledger chain verification failed"
    return None


def _verify_ledger_chain(ledger_path: Path) -> int:
    from qor.scripts import ledger_hash

    return ledger_hash.verify(ledger_path)


def _verify_post_anchor(ledger_path: Path) -> int:
    from qor.scripts import ledger_hash

    return ledger_hash.verify_post_anchor(ledger_path)


def _damage_reason(base: Path, rel_path: str, text: str) -> str | None:
    if text.strip() == "":
        return "file is empty"
    if rel_path == _LEDGER:
        return _ledger_damage(base, text)
    return None


def _ledger_incomplete(text: str) -> str | None:
    """An active ledger (any sealed ``### Entry``) is complete; only a bare
    unfilled scaffold ledger is INCOMPLETE. This keeps historical grounding-tag
    mentions inside sealed entries from being read as live placeholders."""
    if "### Entry" in text:
        return None
    if "INSTRUCTION:" in text or "[ISO 8601" in text:
        return "ledger is an unfilled scaffold (no sealed entries)"
    return None


def _incomplete_reason(rel_path: str, text: str) -> str | None:
    if rel_path == _LEDGER:
        return _ledger_incomplete(text)
    for pattern in _PLACEHOLDER_PATTERNS:
        match = pattern.search(text)
        if match:
            return f"contains unresolved placeholder marker {match.group(0)!r}"
    return None


def _classify_one(
    base: Path, rel_path: str, initialized: bool, prior_evidence: str | None = None
) -> ArtifactFinding:
    target = base / rel_path
    if not target.is_file():
        return _classify_missing(rel_path, initialized, prior_evidence=prior_evidence)
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return ArtifactFinding(rel_path, ArtifactStatus.DAMAGED, f"unreadable: {exc}", _NEXT_REMEDIATE)
    damage = _damage_reason(base, rel_path, text)
    if damage:
        return ArtifactFinding(rel_path, ArtifactStatus.DAMAGED, damage, _NEXT_REMEDIATE)
    incomplete = _incomplete_reason(rel_path, text)
    if incomplete:
        return ArtifactFinding(
            rel_path, ArtifactStatus.INCOMPLETE, incomplete, _NEXT_COMPLETE.format(path=rel_path)
        )
    return ArtifactFinding(rel_path, ArtifactStatus.OK, "passes health checks", "")


def check_governance_health(
    base: Path, *, required: Iterable[str] | None = None
) -> list[ArtifactFinding]:
    """Classify each required governance artifact under ``base``.

    Classification runs in precondition order per artifact: existence first,
    then structural damage, then completeness (a file must exist before it can
    be parsed, and parse-clean before completeness is meaningful).
    """
    base = Path(base)
    artifacts = tuple(required) if required is not None else REQUIRED_ARTIFACTS
    initialized = _is_initialized(base)
    # Phase 175 (GH #267): probe prior-initialization evidence only when the
    # workspace reads as uninitialized (avoids a git subprocess on healthy runs).
    prior_evidence = None
    if not initialized:
        from qor.scripts import governance_snapshot
        prior_evidence = governance_snapshot.prior_initialization_evidence(base)
    return [
        _classify_one(base, rel, initialized, prior_evidence=prior_evidence)
        for rel in artifacts
    ]


# Severity order for the status health gate: a damaged artifact is the most
# urgent, then incomplete, then missing, then a wholly uninitialized workspace.
_GATE_PRIORITY = (
    ArtifactStatus.DAMAGED,
    ArtifactStatus.INCOMPLETE,
    ArtifactStatus.MISSING,
    ArtifactStatus.UNINITIALIZED,
)


def gate_finding(findings: list[ArtifactFinding]) -> ArtifactFinding | None:
    """Return the highest-severity blocking finding, or None when all are OK."""
    for status in _GATE_PRIORITY:
        for finding in findings:
            if finding.status is status:
                return finding
    return None


def recommended_next(findings: list[ArtifactFinding]) -> tuple[str, str]:
    """(state, next_action) the health gate surfaces BEFORE lifecycle routing.

    ``/qor-status`` consults this before its existence-only decision tree so a
    DAMAGED or INCOMPLETE artifact routes to repair/completion instead of to
    ``/qor-plan`` or ``/qor-implement``.
    """
    blocker = gate_finding(findings)
    if blocker is None:
        return ("OK", "continue lifecycle routing")
    return (blocker.status.value.upper(), blocker.legal_next)


def _exit_code(findings: list[ArtifactFinding]) -> int:
    statuses = {f.status for f in findings}
    if ArtifactStatus.DAMAGED in statuses:
        return 2
    blocking = {ArtifactStatus.MISSING, ArtifactStatus.INCOMPLETE, ArtifactStatus.UNINITIALIZED}
    return 1 if statuses & blocking else 0


def _resolve_required(profile: str | None, required: list[str] | None) -> Iterable[str] | None:
    if profile is not None:
        return PROFILES[profile]
    if required:
        return required
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify governance artifact health.")
    parser.add_argument("--repo-root", default=".", help="workspace root to inspect")
    parser.add_argument("--profile", choices=sorted(PROFILES), default=None, help="named required-artifact set")
    parser.add_argument("--required", nargs="*", default=None, help="explicit required artifact paths")
    args = parser.parse_args(argv)
    findings = check_governance_health(Path(args.repo_root), required=_resolve_required(args.profile, args.required))
    for finding in findings:
        print(f"{finding.status.value.upper():13} {finding.path}  {finding.reason}  -> {finding.legal_next}")
    return _exit_code(findings)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
