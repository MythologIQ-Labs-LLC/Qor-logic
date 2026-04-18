"""Phase 31 Phase 1: session marker path unified across Python + bash refs.

Before Phase 31, session.MARKER_PATH was `.qor/current_session` but the
substantiate Step 4.6 and implement Step 5.5 bash blocks referenced
`.qor/session/current`. Two different paths; Python writes one, bash reads
the other. Phase 31 renames MARKER_PATH to `.qor/session/current` to match
the bash refs.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "qor" / "scripts"))
import session  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent
SUBSTANTIATE_SKILL = REPO_ROOT / "qor" / "skills" / "governance" / "qor-substantiate" / "SKILL.md"
IMPLEMENT_SKILL = REPO_ROOT / "qor" / "skills" / "sdlc" / "qor-implement" / "SKILL.md"


def test_marker_path_is_session_current():
    assert session.MARKER_PATH.name == "current", (
        f"MARKER_PATH filename must be 'current'; got {session.MARKER_PATH.name}"
    )
    assert session.MARKER_PATH.parent.name == "session", (
        f"MARKER_PATH parent dir must be 'session'; got {session.MARKER_PATH.parent.name}"
    )


def test_substantiate_bash_refs_match_marker():
    body = SUBSTANTIATE_SKILL.read_text(encoding="utf-8")
    assert ".qor/session/current" in body, (
        "substantiate SKILL.md must reference .qor/session/current"
    )
    assert ".qor/current_session" not in body, (
        "substantiate SKILL.md still references deprecated .qor/current_session path"
    )


def test_implement_bash_refs_match_marker():
    body = IMPLEMENT_SKILL.read_text(encoding="utf-8")
    assert ".qor/session/current" in body, (
        "implement SKILL.md must reference .qor/session/current"
    )
    assert ".qor/current_session" not in body, (
        "implement SKILL.md still references deprecated .qor/current_session path"
    )
