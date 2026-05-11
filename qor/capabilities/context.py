"""Phase 58: governance context packet."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SG_HEADING = re.compile(r"^## (SG-[^:\s]+):", re.MULTILINE)
_ENTRY_HEADING = re.compile(r"^### Entry #(\d+):", re.MULTILINE)


@dataclass(frozen=True)
class GovernanceContextPacket:
    target: str
    doctrines: tuple[str, ...]
    known_failure_patterns: tuple[str, ...]
    feature_inventory_rows: tuple[str, ...]
    recent_ledger_refs: tuple[str, ...]
    recommended_checks: tuple[str, ...]


def _list_doctrines(repo_root: Path) -> tuple[str, ...]:
    refs = repo_root / "qor" / "references"
    if not refs.exists():
        return ()
    return tuple(sorted(p.name for p in refs.glob("doctrine-*.md")))


def _list_sg_anchors(repo_root: Path) -> tuple[str, ...]:
    sg = repo_root / "qor" / "references" / "doctrine-shadow-genome-countermeasures.md"
    if not sg.exists():
        return ()
    return tuple(m.group(1) for m in _SG_HEADING.finditer(sg.read_text(encoding="utf-8")))


def _list_feature_rows(repo_root: Path) -> tuple[str, ...]:
    fi = repo_root / "docs" / "FEATURE_INDEX.md"
    if not fi.exists():
        return ()
    rows = []
    for line in fi.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and not all(c in "|-: " for c in s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if cells and cells[0].lower() not in ("id", "---"):
                rows.append(cells[0])
    return tuple(rows)


def _recent_ledger_refs(repo_root: Path, limit: int = 5) -> tuple[str, ...]:
    ledger = repo_root / "docs" / "META_LEDGER.md"
    if not ledger.exists():
        return ()
    nums = [int(m.group(1)) for m in _ENTRY_HEADING.finditer(ledger.read_text(encoding="utf-8"))]
    return tuple(f"Entry #{n}" for n in sorted(nums)[-limit:])


_RECOMMENDED_CHECKS_BY_PREFIX: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("qor/skills/governance/qor-substantiate", ("hash-integrity", "ledger-verify", "feature-inventory")),
    ("qor/skills/governance/qor-audit", ("filter-stage-ordering", "sdk-alignment")),
    ("qor/scripts/ledger_hash", ("hash-integrity", "ledger-verify")),
    ("qor/skills/sdlc/qor-implement", ("documentation-touches",)),
    ("qor/scripts/ledger_fragment", ("federated-ledger-fragments", "ledger-verify")),
)


def _prefix_match(target: str, prefix: str) -> bool:
    """Phase 61 wiring: delegates to ``qor.scripts.path_match.matches``."""
    from qor.scripts.path_match import matches as _shared
    return _shared(target, prefix)


def _recommended_checks(target: str) -> tuple[str, ...]:
    out: list[str] = []
    for prefix, checks in _RECOMMENDED_CHECKS_BY_PREFIX:
        if _prefix_match(target, prefix):
            for c in checks:
                if c not in out:
                    out.append(c)
    if not out:
        out.extend(("audit-tribunal", "doc-integrity"))
    return tuple(out)


def build_context_packet(repo_root: Path | str, target: str) -> GovernanceContextPacket:
    root = Path(repo_root)
    return GovernanceContextPacket(
        target=target,
        doctrines=_list_doctrines(root),
        known_failure_patterns=_list_sg_anchors(root),
        feature_inventory_rows=_list_feature_rows(root),
        recent_ledger_refs=_recent_ledger_refs(root),
        recommended_checks=_recommended_checks(target),
    )
