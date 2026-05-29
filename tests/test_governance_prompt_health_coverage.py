"""Phase 109 D-109.2: every source skill that reads or routes from governance
artifacts must carry a governance-health preflight marker or a justified
exemption. Tests invoke the scanner over the live skill corpus and assert on its
output, so a skill that drops its marker fails the suite.
"""
from __future__ import annotations

import re
from pathlib import Path

_SKILLS_ROOT = Path("qor/skills")
_PREFLIGHT = "qor:governance-health-preflight"
_EXEMPT = "qor:governance-health-exempt"

# Live governance-artifact reads/routes that require a preflight.
_GOVERNANCE_PATH_RE = re.compile(
    r"docs/META_LEDGER\.md|docs/CONCEPT\.md|docs/ARCHITECTURE_PLAN\.md|"
    r"docs/SYSTEM_STATE\.md|docs/BACKLOG\.md|docs/FEATURE_INDEX\.md|"
    r"docs/GOVERNANCE_INDEX\.md|\.qor/gates/|\.agent/staging/"
)
_EXEMPT_RE = re.compile(r"<!--\s*qor:governance-health-exempt([^>]*)-->")


def _skill_files() -> list[Path]:
    return sorted(_SKILLS_ROOT.rglob("SKILL.md"))


def _reads_governance(text: str) -> bool:
    return bool(_GOVERNANCE_PATH_RE.search(text))


def test_governance_reading_skills_have_preflight_marker():
    missing = []
    for path in _skill_files():
        text = path.read_text(encoding="utf-8")
        if _reads_governance(text) and _PREFLIGHT not in text and _EXEMPT not in text:
            missing.append(path.as_posix())
    assert missing == [], f"skills read governance artifacts but lack preflight/exempt: {missing}"


def test_exemptions_require_reason():
    bad = []
    for path in _skill_files():
        text = path.read_text(encoding="utf-8")
        for match in _EXEMPT_RE.finditer(text):
            attrs = match.group(1)
            if 'reason="' not in attrs and "reason='" not in attrs:
                bad.append(path.as_posix())
    assert bad == [], f"governance-health-exempt markers missing a reason: {bad}"


def test_no_prompt_treats_damaged_as_seedable():
    """No skill text may say a DAMAGED artifact is repairable by seed/bootstrap.
    A sentence naming 'damaged' alongside seed/bootstrap is allowed only when it
    negates the pairing (the canonical 'never to seed or bootstrap' clause)."""
    hits = []
    for path in _skill_files():
        text = path.read_text(encoding="utf-8")
        for sentence in re.split(r"(?<=[.\n])", text):
            low = sentence.lower()
            if "damaged" in low and ("seed" in low or "bootstrap" in low):
                if "never" not in low and " not " not in low:
                    hits.append((path.as_posix(), sentence.strip()[:120]))
    assert hits == [], f"skill text treats damaged governance as seedable: {hits}"
