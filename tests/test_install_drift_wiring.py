"""Phase 32 Phase 1 Rule-4 structural lint:
- /qor-plan SKILL.md Step 0.2 invokes install_drift_check
- doctrine-governance-enforcement §8 Install Currency exists
- Install Drift glossary entry present with correct home + referenced_by
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import doc_integrity  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
QOR_PLAN_SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-plan" / "SKILL.md"
GOVERNANCE_DOCTRINE = REPO_ROOT / "qor" / "references" / "doctrine-governance-enforcement.md"
GLOSSARY = REPO_ROOT / "qor" / "references" / "glossary.md"


def test_plan_skill_has_install_drift_step_0_2():
    body = QOR_PLAN_SKILL.read_text(encoding="utf-8")
    assert "### Step 0.2" in body, (
        "/qor-plan SKILL.md must define Step 0.2 (Phase 32 wiring)"
    )
    # Body must reference the check module
    step_start = body.find("### Step 0.2")
    step_end = body.find("### Step 0.5", step_start)
    if step_end < 0:
        step_end = body.find("### Step 1", step_start)
    section = body[step_start:step_end]
    assert "install_drift_check" in section, (
        "Step 0.2 must invoke qor.scripts.install_drift_check"
    )


def test_governance_enforcement_doctrine_has_install_currency_section():
    body = GOVERNANCE_DOCTRINE.read_text(encoding="utf-8")
    assert "## 8." in body or "## Install Currency" in body, (
        "doctrine-governance-enforcement.md must declare §8 Install Currency"
    )
    idx = max(body.find("## 8."), body.find("## Install Currency"))
    next_section = body.find("\n## ", idx + 1)
    section_body = body[idx:next_section if next_section > 0 else len(body)]
    assert len(section_body) > 80, (
        f"Install Currency section too short ({len(section_body)} chars); "
        "likely metadata-only declaration"
    )


def test_install_drift_glossary_entry_exists():
    entries = {e.term: e for e in doc_integrity.parse_glossary(str(GLOSSARY))}
    assert "Install Drift" in entries, (
        f"'Install Drift' missing from glossary; got {sorted(entries.keys())}"
    )
    entry = entries["Install Drift"]
    assert entry.home == "qor/references/doctrine-governance-enforcement.md", (
        f"Unexpected home: {entry.home}"
    )
    expected_consumers = {
        "qor/scripts/install_drift_check.py",
        "qor/skills/sdlc/qor-plan/SKILL.md",
    }
    missing = expected_consumers - set(entry.referenced_by)
    assert not missing, f"referenced_by missing consumers: {missing}"
