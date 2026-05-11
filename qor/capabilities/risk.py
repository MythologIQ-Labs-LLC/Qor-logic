"""Phase 58: risk routing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RiskRoutingReport:
    target: str
    risk_grade: str
    impacted_surfaces: tuple[str, ...]
    required_skills: tuple[str, ...]
    missing_evidence: tuple[str, ...]


_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...], str], ...] = (
    # (path prefixes that trigger, required skills/checks, risk grade)
    (
        ("qor/skills/governance/qor-substantiate", "qor/scripts/ledger_hash", "qor/scripts/hash_guard"),
        ("hash-integrity", "ledger-verify"),
        "L3",
    ),
    (
        ("docs/META_LEDGER.md", "qor/scripts/ledger_fragment", "qor/scripts/ledger_entry_id"),
        ("federated-ledger-fragments", "ledger-verify"),
        "L2",
    ),
    (
        ("qor/skills/sdlc/qor-implement",),
        ("documentation-touches",),
        "L2",
    ),
    (
        ("pyproject.toml", "requirements.txt", "requirements-dev.txt", "Cargo.toml", "package.json"),
        ("sdk-alignment", "dependency-justification"),
        "L2",
    ),
    (
        ("qor/scripts/dispatcher", "qor/compiler/execution_modes.py", "qor/compiler/compile.py"),
        ("filter-stage-ordering",),
        "L2",
    ),
)


def _matches_any(path: str, prefixes: tuple[str, ...]) -> bool:
    """Phase 61 wiring: delegates to the unified ``qor.scripts.path_match`` helper.
    The boundary discipline (match must end at `/`, `.`, or exact equality)
    originated as the Phase 60 fix for M1 and is now centralized."""
    from qor.scripts.path_match import matches_any as _shared
    return _shared(path, prefixes)


def route_risk(repo_root: Path | str, changed_files: tuple[str, ...]) -> RiskRoutingReport:
    _ = Path(repo_root)
    impacted: list[str] = []
    required: list[str] = []
    max_grade = "L1"
    grade_rank = {"L1": 1, "L2": 2, "L3": 3}
    for path in changed_files:
        for prefixes, checks, grade in _RULES:
            if _matches_any(path, prefixes):
                if path not in impacted:
                    impacted.append(path)
                for c in checks:
                    if c not in required:
                        required.append(c)
                if grade_rank[grade] > grade_rank[max_grade]:
                    max_grade = grade
    if not required:
        required.append("audit-tribunal")
    return RiskRoutingReport(
        target=",".join(changed_files) if changed_files else "",
        risk_grade=max_grade,
        impacted_surfaces=tuple(impacted),
        required_skills=tuple(required),
        missing_evidence=(),
    )
