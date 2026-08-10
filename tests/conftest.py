"""Pytest config for qor-logic test suite."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _git_no_auto_maintenance(monkeypatch):
    """Suppress git's auto-maintenance for every git call a test makes.

    Phase 214 (GH #308). git >= 2.5x runs `git maintenance run --auto --detach`
    after commit/merge. Because it daemonizes, `git repack -d` keeps rewriting a
    scratch repository's object store AFTER the foreground call has returned,
    deleting loose objects and their `objects/xx` shard directories while the
    fixture's next call is using them -- surfacing as intermittent exit 128,
    most often `unable to create temporary file: No such file or directory`.

    Three things this must not be mistaken for:

    * It is NOT fixture hardening. Phase 209 pinned GIT_CONFIG_GLOBAL and
      GIT_CONFIG_SYSTEM to a nonexistent path and could not have fixed this:
      auto-maintenance is a built-in default, not a configured behavior.
    * It must use the ENV-CONFIG layer, not a config file. That same Phase 209
      pinning would read a global or system entry out of scope, so the earlier
      fix would silently defeat this one. The env layer is read independently.
    * `gc.auto=0` is insufficient -- the repack still runs via the geometric /
      incremental-repack task. Only `maintenance.auto=false` suppresses it.

    Appends rather than assuming index 0 is free, so a future fixture adding its
    own entry cannot silently lose one of the two.
    """
    index = int(os.environ.get("GIT_CONFIG_COUNT", "0"))
    monkeypatch.setenv(f"GIT_CONFIG_KEY_{index}", "maintenance.auto")
    monkeypatch.setenv(f"GIT_CONFIG_VALUE_{index}", "false")
    monkeypatch.setenv("GIT_CONFIG_COUNT", str(index + 1))


@pytest.fixture(autouse=True)
def _qor_gate_provenance_optional(monkeypatch):
    """Phase 52: bypass write_gate_artifact provenance check for the test suite.

    Tests use monkeypatch.setattr(GATES_DIR, tmp_path) and direct helper calls
    that don't have QOR_SKILL_ACTIVE set. The provenance binding is for
    production skill invocations; tests opt out via this autouse fixture.

    Tests that EXERCISE the provenance check (test_gate_chain_provenance.py)
    explicitly delenv this var via monkeypatch.delenv(..., raising=False)
    inside the test body.
    """
    monkeypatch.setenv("QOR_GATE_PROVENANCE_OPTIONAL", "1")
    yield


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_session_pollution():
    """Phase 58: sweep `.qor/gates/test*` directories at session-end.

    Some tests construct synthetic session IDs (e.g. ``test-session``,
    ``test-session-kb``, ``cli-test``) and call gate_chain.write_gate_artifact
    against them, which writes to the live `.qor/gates/<sid>/` tree rather
    than to a tmp_path. This fixture removes pollution at session-end so the
    repo stays clean.

    Pattern is conservative: matches `test*` and `cli-*` and `t1`-`t5`
    (Phase 58 fixture aliases); skips real session IDs (timestamp-prefixed
    `2026-...`) by name pattern. Idempotent; safe to re-run.
    """
    yield
    gates = Path(".qor") / "gates"
    if not gates.exists():
        return
    for entry in gates.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        # Pollution patterns: test*, cli-*, t1-t9 single-letter-digit aliases
        is_pollution = (
            name.startswith("test")
            or name.startswith("cli-")
            or (len(name) <= 3 and name[0] == "t" and name[1:].isdigit())
        )
        if is_pollution:
            shutil.rmtree(entry, ignore_errors=True)
