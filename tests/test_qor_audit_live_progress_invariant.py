"""Phase 74 P2: qor-audit Ghost UI Pass Live-Progress Invariant (GH #58)."""
from pathlib import Path

SKILL = Path("qor/skills/governance/qor-audit/SKILL.md")


def _ghost_ui_region(text: str) -> str:
    if "Ghost UI Pass" not in text:
        raise AssertionError("missing Ghost UI Pass section in audit SKILL.md")
    start = text.index("Ghost UI Pass")
    # Region extends until next #### or the Macro-Level / Infrastructure heading
    rest = text[start:]
    next_h4 = rest.find("\n#### ", 10)
    return rest[: next_h4 if next_h4 != -1 else 4000]


def test_ghost_ui_pass_names_live_progress_invariant():
    text = SKILL.read_text(encoding="utf-8")
    region = _ghost_ui_region(text)
    assert "Live-Progress Invariant" in region, (
        "Ghost UI Pass must name the Live-Progress Invariant sub-rule"
    )
    lowered = region.lower()
    assert "intermediate" in lowered and "progress" in lowered, (
        "Live-Progress Invariant body must describe intermediate-state requirement"
    )
    assert "event stream" in lowered or "websocket" in lowered or "subscribe" in lowered, (
        "Live-Progress Invariant body must require event-stream subscription"
    )


def test_ghost_ui_pass_names_fake_jump_pattern():
    text = SKILL.read_text(encoding="utf-8")
    region = _ghost_ui_region(text)
    assert "SG-FakeProgress-A" in region, (
        "Ghost UI Pass must cross-reference SG-FakeProgress-A"
    )
    assert "fake-jump" in region.lower() or "0%" in region and "100%" in region, (
        "Ghost UI Pass must name the fake-jump pattern (0%->100% with no intermediate)"
    )
    assert "live-progress-fake" in region, (
        "Ghost UI Pass must name the VETO sub-tag live-progress-fake"
    )
