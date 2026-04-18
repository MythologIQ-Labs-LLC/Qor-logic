"""Phase 30 Phase 2: terminology unification (change_class; phase XML tag case).

Closes GAP-REPO-06: `change_type` was occasionally used as a synonym for
`change_class`; XML `<phase>` tags had inconsistent case vs YAML frontmatter.
"""
from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = list((REPO_ROOT / "qor" / "skills").rglob("SKILL.md"))
DOCTRINES = list((REPO_ROOT / "qor" / "references").glob("doctrine-*.md"))


def test_no_change_type_synonym():
    """`change_type` as a standalone identifier (not `change_class`) must not
    appear in skill text or doctrine text. Ledger entries are immutable and
    excluded from scan. Fixture files excluded as well."""
    violations: list[str] = []
    for f in SKILLS + DOCTRINES:
        body = f.read_text(encoding="utf-8")
        # Match `change_type` (backticked) or bare \bchange_type\b outside code fences.
        stripped = re.sub(r"```[\s\S]*?```", "", body)
        if re.search(r"\bchange_type\b", stripped):
            violations.append(str(f.relative_to(REPO_ROOT)))
    assert not violations, (
        f"change_type synonym must be replaced by change_class; "
        f"files still carrying it: {violations}"
    )


def test_phase_xml_tag_case_matches_yaml():
    """Flag only true case drift on the same token (GAP-REPO-06 narrow fix).

    Historical incident: some SKILL.md files had `<phase>PLAN</phase>`
    (uppercase) while YAML said `phase: plan` (lowercase) -- same token,
    inconsistent case. That's drift.

    Legitimate difference: XML `<phase>GATE</phase>` vs YAML `phase: audit`
    -- different concepts (XML is the humanized role label; YAML is the
    SDLC slot). Leave those alone.

    Violation = XML first-token and YAML value match case-insensitively
    but differ in case."""
    violations: list[str] = []
    for f in SKILLS:
        body = f.read_text(encoding="utf-8")
        xml_match = re.search(r"<phase>([^<]+)</phase>", body)
        yaml_match = re.search(r"^phase:\s*(\S+)\s*$", body, re.MULTILINE)
        if not (xml_match and yaml_match):
            continue
        xml_val = xml_match.group(1).strip()
        yaml_val = yaml_match.group(1).strip()
        xml_first = xml_val.split()[0] if xml_val else ""
        # Same token, different case only -> drift. Different tokens -> OK.
        if xml_first.lower() == yaml_val.lower() and xml_first != yaml_val:
            violations.append(
                f"{f.relative_to(REPO_ROOT)}: XML=<phase>{xml_val}</phase> "
                f"vs YAML=phase:{yaml_val} (same token, case drift)"
            )
    assert not violations, (
        f"XML <phase> tag case drift vs YAML frontmatter: {violations}"
    )
