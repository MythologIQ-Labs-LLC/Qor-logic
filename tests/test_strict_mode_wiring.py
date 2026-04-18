"""Phase 32 Phase 3 Rule-4 structural lint:
- Strict Mode glossary entry present with expected home + referenced_by
- doctrine-documentation-integrity declares strict-mode is live
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"
DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-documentation-integrity.md"


def test_strict_mode_glossary_entry_exists():
    entries = {e.term: e for e in doc_integrity.parse_glossary(str(GLOSSARY))}
    assert "Strict Mode" in entries, (
        f"'Strict Mode' missing from glossary; got {sorted(entries.keys())}"
    )
    entry = entries["Strict Mode"]
    assert entry.home == "qor/references/doctrine-documentation-integrity.md"
    expected_consumers = {
        "qor/scripts/doc_integrity.py",
        "qor/scripts/doc_integrity_strict.py",
        "qor/skills/governance/qor-substantiate/SKILL.md",
    }
    missing = expected_consumers - set(entry.referenced_by)
    assert not missing, f"Strict Mode referenced_by missing: {missing}"


def test_doc_integrity_doctrine_declares_strict_live():
    body = DOCTRINE.read_text(encoding="utf-8")
    # Allow flexible matching: phrase "strict mode is live" or "strict-mode is live"
    # case-insensitive, and any reference to Step 4.7
    assert "step 4.7" in body.lower() or "Step 4.7" in body, (
        "Doctrine must reference Step 4.7 in strict-mode context"
    )
    # Check for live-wiring indication (any variant)
    live_indicators = ["strict mode is live", "strict-mode is live", "strict=true", "live at"]
    assert any(ind.lower() in body.lower() for ind in live_indicators), (
        "Doctrine must declare strict-mode is live (Phase 32 wiring)"
    )
