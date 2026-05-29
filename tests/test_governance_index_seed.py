"""Phase 112 (#140): GOVERNANCE_INDEX scaffold + registry coupling."""
from __future__ import annotations

from pathlib import Path

from qor import seed
from qor.scripts import governance_health


def test_seed_creates_governance_index(tmp_path):
    seed.seed(base=tmp_path, quiet=True)
    index = tmp_path / "docs" / "GOVERNANCE_INDEX.md"
    assert index.is_file()
    body = index.read_text(encoding="utf-8")
    for tier in ("Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5", "Tier 6"):
        assert tier in body, f"template missing {tier} heading"


def test_required_and_scaffold_sets_include_index():
    assert "docs/GOVERNANCE_INDEX.md" in governance_health.REQUIRED_ARTIFACTS
    assert "docs/GOVERNANCE_INDEX.md" in governance_health.SCAFFOLD_OWNED


def test_phase109_scaffold_owned_invariant_holds():
    # Phase 109 LD3 anti-drift invariant must still hold after the addition.
    assert governance_health.SCAFFOLD_OWNED == seed.scaffold_file_targets()
