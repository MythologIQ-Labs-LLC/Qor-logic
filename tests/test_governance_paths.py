from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts.governance_paths import (
    resolve_architecture_authority,
    resolve_registered_governance_path,
)


def _write_index(root: Path, rows: list[tuple[str, str]]) -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    body = [
        "# Governance Index",
        "",
        "| Artifact | Path | Freshness marker |",
        "|---|---|---|",
    ]
    body.extend(f"| {artifact} | `{path}` | current |" for artifact, path in rows)
    (docs / "GOVERNANCE_INDEX.md").write_text("\n".join(body) + "\n", encoding="utf-8")


def test_registered_architecture_plan_is_authority(tmp_path: Path) -> None:
    _write_index(tmp_path, [("Architecture Plan", "docs/ARCHITECTURE_PLAN.md")])
    expected = tmp_path / "docs" / "ARCHITECTURE_PLAN.md"
    expected.write_text("# Architecture\n", encoding="utf-8")

    assert resolve_architecture_authority(tmp_path) == expected.resolve()


def test_missing_registered_architecture_fails_closed(tmp_path: Path) -> None:
    _write_index(tmp_path, [("Architecture Plan", "docs/ARCHITECTURE_PLAN.md")])

    with pytest.raises(ValueError, match="no existing registered architecture"):
        resolve_architecture_authority(tmp_path)


def test_multiple_architecture_authorities_fail_closed(tmp_path: Path) -> None:
    _write_index(
        tmp_path,
        [
            ("Architecture Plan", "docs/ARCHITECTURE_PLAN.md"),
            ("Architecture Reference", "docs/architecture.md"),
        ],
    )
    (tmp_path / "docs" / "ARCHITECTURE_PLAN.md").write_text("# A\n", encoding="utf-8")
    (tmp_path / "docs" / "architecture.md").write_text("# B\n", encoding="utf-8")

    with pytest.raises(ValueError, match="multiple architecture authorities"):
        resolve_architecture_authority(tmp_path)


def test_registered_active_plan_accepts_non_phase_filename(tmp_path: Path) -> None:
    _write_index(tmp_path, [("Plans (all)", "docs/plan-*.md")])
    plan = tmp_path / "docs" / "plan-m0-inc4-brumgrom-containment.md"
    plan.write_text("# Plan\n", encoding="utf-8")

    assert resolve_registered_governance_path(plan.relative_to(tmp_path), tmp_path) == plan.resolve()


@pytest.mark.parametrize(
    "raw",
    [
        "../outside.md",
        "README.md",
        "docs/unregistered.md",
        "docs/plan.txt",
    ],
)
def test_invalid_governance_paths_are_rejected(tmp_path: Path, raw: str) -> None:
    _write_index(tmp_path, [("Plans (all)", "docs/plan-*.md")])
    candidate = tmp_path / raw
    if ".." not in raw:
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text("x\n", encoding="utf-8")

    with pytest.raises(ValueError):
        resolve_registered_governance_path(raw, tmp_path)
