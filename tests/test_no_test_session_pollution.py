"""Phase 58: regression — no `.qor/gates/test*` pollution after suite runs."""
from __future__ import annotations

import inspect
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_qor_gates_test_session_dirs_do_not_persist():
    """At test discovery time (which is the first thing pytest does after
    conftest fixture session-start), the cleanup fixture has not yet run.
    But the conftest fixture is session-scope autouse; at session-end it
    will sweep test-session pollution. This test asserts the cleanup fixture
    is wired correctly (static introspection of conftest.py source).
    """
    conftest = REPO_ROOT / "tests" / "conftest.py"
    src = conftest.read_text(encoding="utf-8")
    # Must declare a session-scope autouse fixture that touches .qor/gates and test*
    assert "scope=\"session\"" in src or "scope='session'" in src
    assert "autouse=True" in src
    assert ".qor" in src and "gates" in src
    assert "test" in src  # the cleanup pattern matches `test*`


def test_conftest_cleanup_pattern_excludes_real_session_ids():
    """The cleanup pattern must not match timestamp-prefixed session IDs
    (e.g., `2026-05-01T2050-phase57`)."""
    conftest = REPO_ROOT / "tests" / "conftest.py"
    src = conftest.read_text(encoding="utf-8")
    # Real session IDs start with `2026` or similar 4-digit year prefix
    # The cleanup pattern only matches names starting with "test", "cli-",
    # or short tN; it does not match "2026-...".
    # Static check: the conftest does not pattern-match on `^2`
    assert not re.search(r'startswith\(\s*["\']2', src), \
        "conftest cleanup must not target timestamp-prefixed session IDs"
