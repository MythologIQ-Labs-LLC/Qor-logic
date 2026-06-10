"""Phase 107 D-107.5: CODEOWNERS solo-owner doctrine note assertions."""
from __future__ import annotations

import pathlib

# Resolve from __file__ so the test runs from any cwd (GAP-TEST-10), not only repo-root.
_REPO = pathlib.Path(__file__).resolve().parent.parent
_DOCTRINE = _REPO / "qor" / "references" / "doctrine-governance-enforcement.md"
_CODEOWNERS = _REPO / ".github" / "CODEOWNERS"


def test_doctrine_documents_solo_owner_mode():
    """Doctrine §6.1 names solo-owner-mode + 4 trigger conditions for expansion."""
    text = _DOCTRINE.read_text(encoding="utf-8").lower()
    assert "codeowners operational mode" in text, (
        "doctrine must carry §6.1 'CODEOWNERS operational mode' subsection"
    )
    assert "solo-owner" in text or "solo owner" in text, (
        "doctrine must explicitly use the 'solo-owner' framing"
    )
    # 4 trigger conditions for expansion
    trigger_phrases = [
        "second maintainer",
        "federates",
        "compliance audit",
        "operator-initiated",
    ]
    missing = [t for t in trigger_phrases if t not in text]
    assert not missing, (
        f"doctrine must name all 4 expansion trigger conditions; missing: {missing}"
    )


def test_codeowners_file_consistent_with_doctrine():
    """`.github/CODEOWNERS` has @Knapp-Kevin as sole owner (matches solo-owner doctrine)."""
    lines = _CODEOWNERS.read_text(encoding="utf-8").splitlines()
    owners_seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        for token in parts[1:]:
            if token.startswith("@"):
                owners_seen.add(token)
    assert owners_seen == {"@Knapp-Kevin"}, (
        f"CODEOWNERS must list only @Knapp-Kevin (solo-owner mode per doctrine §6.1); "
        f"got owners: {sorted(owners_seen)}"
    )
