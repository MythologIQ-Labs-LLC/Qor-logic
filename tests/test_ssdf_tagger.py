"""Phase 52: NIST SSDF tagger pure functions (closes G-1).

Functionality tests per Phase 46 doctrine — invoke the unit, assert on
returned values.
"""
from __future__ import annotations

from pathlib import Path

import pytest


def test_module_importable_with_canonical_api():
    from qor.scripts import ssdf_tagger as st
    assert callable(st.compute_tags)
    assert callable(st.format_tag_line)
    assert callable(st.files_touched_from_git)
    assert callable(st.main)


def test_compute_tags_feature_implementation_includes_pw_practices():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags(
        "feature",
        ["qor/skills/sdlc/qor-implement/SKILL.md", "tests/test_x.py"],
        include_seal=False,
    )
    assert "PW.1.1" in tags
    assert "PW.5.1" in tags


def test_compute_tags_breaking_change_includes_pw_4_1():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags("breaking", [], include_seal=False)
    assert "PW.4.1" in tags
    assert "PO.1.4" in tags


def test_compute_tags_hotfix_includes_rv_2_1():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags("hotfix", [], include_seal=False)
    assert "RV.2.1" in tags


def test_compute_tags_audit_skill_change_includes_ps_3_2():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags(
        "feature",
        ["qor/skills/governance/qor-audit/SKILL.md"],
        include_seal=False,
    )
    assert "PS.3.2" in tags
    assert "PW.4.1" in tags


def test_compute_tags_shadow_genome_change_includes_rv_practices():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags(
        "feature",
        ["qor/scripts/shadow_process.py"],
        include_seal=False,
    )
    assert "RV.1.1" in tags
    assert "RV.1.2" in tags


def test_compute_tags_include_seal_adds_ps_2_1():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags("feature", ["docs/META_LEDGER.md"], include_seal=True)
    assert "PS.2.1" in tags
    tags_no_seal = compute_tags("feature", ["docs/META_LEDGER.md"], include_seal=False)
    assert "PS.2.1" not in tags_no_seal or "docs/META_LEDGER.md" in str(tags_no_seal)
    # Note: ledger file matches no pattern rule, so PS.2.1 only comes from include_seal


def test_compute_tags_returns_sorted_unique():
    from qor.scripts.ssdf_tagger import compute_tags
    tags = compute_tags(
        "feature",
        [
            "qor/skills/sdlc/qor-implement/SKILL.md",
            "qor/skills/sdlc/qor-implement/references/foo.md",  # dup PW.1.1, PW.5.1
        ],
        include_seal=False,
    )
    assert tags == sorted(set(tags))


def test_format_tag_line_canonical_block():
    from qor.scripts.ssdf_tagger import format_tag_line
    line = format_tag_line(["PS.2.1", "PW.1.1"])
    assert line == "**SSDF Practices**: PS.2.1, PW.1.1"


def test_extract_ssdf_practices_round_trips_emitted_block(tmp_path):
    """Emit via format_tag_line, append to fixture ledger entry, parse via
    ledger_hash.extract_ssdf_practices; round-trip equality."""
    from qor.scripts.ssdf_tagger import compute_tags, format_tag_line
    from qor.scripts.ledger_hash import extract_ssdf_practices

    tags = compute_tags(
        "feature",
        ["qor/scripts/foo.py", "qor/skills/governance/qor-audit/SKILL.md"],
        include_seal=True,
    )
    line = format_tag_line(tags)
    fixture = tmp_path / "META_LEDGER.md"
    fixture.write_text(
        f"### Entry #1: SESSION SEAL -- Phase 52 feature substantiated\n"
        f"\n"
        f"**Session**: `s1`\n"
        f"\n"
        f"**Content Hash (session seal)**: `aaa`\n"
        f"**Previous Hash**: `bbb`\n"
        f"**Chain Hash (Merkle seal)**: `ccc`\n"
        f"\n"
        f"{line}\n"
        f"\n"
        f"---\n",
        encoding="utf-8",
    )
    parsed = extract_ssdf_practices(fixture)
    assert 1 in parsed, f"entry #1 should be parsed; got {parsed}"
    assert sorted(parsed[1]) == sorted(tags)
