"""End-to-end integration tests for Phase 10.

Each test exercises 3+ modules in a realistic sequence to verify they
compose correctly. Unit tests verify modules in isolation; these verify
the assembly.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import session
import gate_chain
import shadow_process
import qor_platform as qplat
import qor_audit_runtime as audit_runtime
import check_shadow_threshold as cst
import create_shadow_issue as csi
import collect_shadow_genomes as collect


# ----- Fixtures -----

@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Wire every module to tmp_path. Returns a namespace of sub-paths."""
    sm = tmp_path / "current_session"
    pm = tmp_path / "platform.json"
    log = tmp_path / "shadow.md"
    gates = tmp_path / "gates"
    marker = tmp_path / "remediate-pending"

    monkeypatch.setattr(session, "MARKER_PATH", sm)
    monkeypatch.setattr(qplat, "MARKER_PATH", pm)
    monkeypatch.setattr(shadow_process, "LOG_PATH", log)
    monkeypatch.setattr(gate_chain, "GATES_DIR", gates)
    monkeypatch.setattr(cst, "MARKER_PATH", marker)
    monkeypatch.setattr(csi, "MARKER_PATH", marker)

    return type("ns", (), {
        "session_marker": sm, "platform_marker": pm, "shadow_log": log,
        "gates_dir": gates, "remediate_marker": marker, "tmp": tmp_path,
    })


def _mk_event(severity=1, event_type="gate_override", ts=None,
              session_id="s-default", skill="qor-audit", addressed=False,
              source_entry_id=None, details=None):
    ev = {
        "ts": ts or shadow_process.now_iso(),
        "skill": skill,
        "session_id": session_id,
        "event_type": event_type,
        "severity": severity,
        "details": details or {},
        "addressed": addressed,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": source_entry_id,
    }
    ev["id"] = shadow_process.compute_id(ev)
    return ev


# ----- E2E 1: Full advisory chain flow -----

def test_full_chain_advisory_flow(isolated):
    """research → plan → audit, each writing a valid prior artifact."""
    sid = session.get_or_create()
    session_dir = isolated.gates_dir / sid
    session_dir.mkdir(parents=True)

    # Research writes its artifact
    research = {
        "phase": "research", "ts": shadow_process.now_iso(), "session_id": sid,
        "questions": ["q1"], "findings": [{"f": 1}],
    }
    (session_dir / "research.json").write_text(json.dumps(research), encoding="utf-8")

    # Plan checks its prior (research) — should pass
    result = gate_chain.check_prior_artifact("plan", session_id=sid)
    assert result.found and result.valid

    # Plan writes its artifact
    plan = {
        "phase": "plan", "ts": shadow_process.now_iso(), "session_id": sid,
        "plan_path": "docs/test.md", "phases": ["p1"],
    }
    (session_dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    # Audit checks its prior (plan) via audit_runtime
    audit_result = audit_runtime.check_prior_artifact(session_id=sid)
    assert audit_result.found and audit_result.valid


# ----- E2E 2: Override path with shadow event + threshold -----

def test_override_path_full_cycle(isolated):
    """Skip plan; audit overrides; event lands; threshold sees it."""
    sid = session.get_or_create()

    # Audit checks prior — not found
    result = audit_runtime.check_prior_artifact(session_id=sid)
    assert not result.found

    # User confirms override
    audit_runtime.emit_gate_override("test override: no plan", sid)

    # Event landed
    events = shadow_process.read_events()
    assert len(events) == 1
    assert events[0]["event_type"] == "gate_override"
    assert events[0]["severity"] == 1
    assert events[0]["details"]["current_phase"] == "audit"
    assert events[0]["details"]["prior_phase"] == "plan"

    # Threshold check sees the event but does not breach
    import sys as _s
    _s.argv = ["check", "--log", str(isolated.shadow_log)]
    rc = cst.main()
    assert rc == 0  # 1 < threshold 10
    assert not isolated.remediate_marker.exists()


# ----- E2E 3: Capability shortfall pipeline -----

def test_capability_shortfall_pipeline(isolated):
    """claude-code-solo → adversarial check returns False → shortfall logged."""
    qplat.apply_profile("claude-code-solo")
    sid = session.get_or_create()

    # Adversarial mode unavailable (claude-code but no codex-plugin)
    assert audit_runtime.should_run_adversarial_mode() is False

    # Skill emits capability_shortfall
    audit_runtime.emit_capability_shortfall("codex-plugin", sid)

    # Event is in the log with sev 2
    events = shadow_process.read_events()
    assert len(events) == 1
    assert events[0]["event_type"] == "capability_shortfall"
    assert events[0]["severity"] == 2
    assert events[0]["details"]["capability"] == "codex-plugin"


# ----- E2E 4: Threshold breach writes marker -----

def test_threshold_breach_writes_marker(isolated):
    """Append events totaling sev >= 10; marker written with aggregated ids."""
    events = [
        _mk_event(severity=5, ts="2026-04-15T10:00:00Z", session_id="s-a"),
        _mk_event(severity=5, ts="2026-04-15T11:00:00Z", session_id="s-b"),
    ]
    isolated.shadow_log.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
    )

    import sys as _s
    _s.argv = ["check", "--log", str(isolated.shadow_log), "--now", "2026-04-15T12:00:00Z"]
    rc = cst.main()
    assert rc == 10

    assert isolated.remediate_marker.exists()
    payload = json.loads(isolated.remediate_marker.read_text())
    assert payload["severity_sum"] == 10
    assert payload["event_count"] == 2
    assert len(payload["event_ids"]) == 2


# ----- E2E 5: Aged escalation idempotence (full cycle) -----

def test_aged_high_severity_self_escalation_idempotent(isolated):
    """Aged sev-3 -> escalation event (sev 5); 2nd sweep produces no duplicate."""
    aged = _mk_event(severity=3, ts="2026-01-01T00:00:00Z", session_id="s-old")
    isolated.shadow_log.write_text(json.dumps(aged) + "\n", encoding="utf-8")

    import sys as _s
    # 1st sweep: now is well past 90 days from Jan 1
    _s.argv = ["check", "--log", str(isolated.shadow_log), "--now", "2026-04-15T12:00:00Z"]
    cst.main()

    after_first = shadow_process.read_events()
    escalations_1 = [e for e in after_first if e["event_type"] == "aged_high_severity_unremediated"]
    assert len(escalations_1) == 1
    assert escalations_1[0]["source_entry_id"] == aged["id"]
    assert escalations_1[0]["severity"] == 5

    # 2nd sweep: same args, no duplicate escalation
    _s.argv = ["check", "--log", str(isolated.shadow_log), "--now", "2026-04-15T13:00:00Z"]
    cst.main()

    after_second = shadow_process.read_events()
    escalations_2 = [e for e in after_second if e["event_type"] == "aged_high_severity_unremediated"]
    assert len(escalations_2) == 1  # still one, not two


# ----- E2E 6: Session continuity across modules -----

def test_session_continuity_across_modules(isolated):
    """Same session id flows through gate_chain, shadow events, gates dir."""
    sid_1 = session.get_or_create()

    # gate_chain emits an override using sid_1
    audit_runtime.emit_gate_override("test", sid_1)

    # Shadow event carries sid_1
    event = shadow_process.read_events()[0]
    assert event["session_id"] == sid_1

    # session.current() returns the same sid_1
    sid_2 = session.current()
    assert sid_1 == sid_2

    # Gate dir uses sid_1
    expected_dir = isolated.gates_dir / sid_1
    expected_dir.mkdir(parents=True)
    plan = {
        "phase": "plan", "ts": shadow_process.now_iso(), "session_id": sid_1,
        "plan_path": "x", "phases": ["p"],
    }
    (expected_dir / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    # Audit runtime resolves the same sid and finds the artifact
    sid_3 = audit_runtime.session_id()
    assert sid_3 == sid_1
    result = audit_runtime.check_prior_artifact(session_id=sid_3)
    assert result.found and result.valid


# ----- E2E 7: Compile drift full cycle -----

def test_compile_drift_full_cycle(tmp_path, monkeypatch):
    """Compile real fake source → tamper dist → drift detects → recompile → clean."""
    import compile as compile_mod
    import check_variant_drift as drift_mod

    # Build a minimal source tree
    skills = tmp_path / "skills"
    agents = tmp_path / "agents"
    (skills / "governance" / "qor-test").mkdir(parents=True)
    (skills / "governance" / "qor-test" / "SKILL.md").write_text(
        "# qor-test\n", encoding="utf-8"
    )
    (agents / "governance").mkdir(parents=True)
    (agents / "governance" / "qor-test-agent.md").write_text(
        "# agent\n", encoding="utf-8"
    )

    monkeypatch.setattr(compile_mod, "SKILLS_SRC", skills)
    monkeypatch.setattr(compile_mod, "AGENTS_SRC", agents)

    out = tmp_path / "dist"
    compile_mod.compile_all(out)

    # Drift after compile = 0
    monkeypatch.setattr(drift_mod, "COMMITTED_DIST", out)
    import sys as _s
    _s.argv = ["drift", "--committed", str(out)]
    assert drift_mod.main() == 0

    # Tamper dist
    (out / "variants" / "claude" / "skills" / "qor-test" / "SKILL.md").write_text(
        "# TAMPERED\n", encoding="utf-8"
    )
    assert drift_mod.main() == 1  # drift detected

    # Recompile fixes drift
    compile_mod.compile_all(out)
    assert drift_mod.main() == 0


# ----- E2E 8: Collector subprocess chain -----

def test_collector_subprocess_chain(tmp_path, monkeypatch):
    """Mocked: collector runs check_shadow_threshold per repo, pools, posts issue, flips."""
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    for r in (repo_a, repo_b):
        (r / "docs").mkdir(parents=True)

    e_a = _mk_event(severity=5, session_id="s-a")
    e_b = _mk_event(severity=5, session_id="s-b", ts="2026-04-15T13:00:00Z")
    (repo_a / "docs" / "PROCESS_SHADOW_GENOME.md").write_text(json.dumps(e_a) + "\n", encoding="utf-8")
    (repo_b / "docs" / "PROCESS_SHADOW_GENOME.md").write_text(json.dumps(e_b) + "\n", encoding="utf-8")

    config = {
        "version": "1",
        "meta_repo": "MythologIQ-Labs-LLC/Qor-logic",
        "repos": [
            {"path": str(repo_a), "name": "repo-a", "enabled": True},
            {"path": str(repo_b), "name": "repo-b", "enabled": True},
        ],
        "threshold": 10, "stale_days": 90,
    }

    fake_url = "https://github.com/meta/repo/issues/77"

    def fake_run(cmd, *args, **kwargs):
        # check_shadow_threshold per repo: exit 10 (breach)
        if cmd[1].endswith("check_shadow_threshold.py"):
            return subprocess.CompletedProcess(cmd, 10, "BREACH", "")
        # gh issue create: returns URL
        if cmd[:3] == ["gh", "issue", "create"]:
            return subprocess.CompletedProcess(cmd, 0, fake_url + "\n", "")
        # create_shadow_issue.py --flip-only: succeed silently
        if cmd[1].endswith("create_shadow_issue.py"):
            return subprocess.CompletedProcess(cmd, 0, "Flipped 1 event(s)", "")
        raise AssertionError(f"Unexpected: {cmd}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    pooled = collect.sweep_all(config)
    assert len(pooled) == 2
    assert {e["source_repo"] for e in pooled} == {"repo-a", "repo-b"}

    sev_sum = sum(e["severity"] for e in pooled)
    assert sev_sum == 10

    body = collect.build_issue_body(pooled, threshold=10)
    url = collect.dispatch(body, "MythologIQ-Labs-LLC/Qor-logic", 2, 10)
    assert url == fake_url

    summary = collect.flip_per_repo(url, pooled, config)
    assert set(summary.keys()) == {"repo-a", "repo-b"}


# ----- E2E 9: Platform marker affects audit-runtime decisions -----

def test_platform_marker_affects_audit_runtime(isolated, monkeypatch):
    """Sequential profile changes -> audit-runtime decisions reflect each immediately.

    NOTE: should_run_adversarial_mode reads detected.host (not declared.host_declared).
    Tests must set CLAUDE_PROJECT_DIR for the detection to return 'claude-code'.
    Documented as Gap #1 in docs/phase10-findings.md.
    """
    # Profile 1: solo (env set so detected.host = claude-code; codex declared off)
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/fake/project")
    qplat.apply_profile("claude-code-solo")
    assert audit_runtime.should_run_adversarial_mode() is False

    # Profile 2: with-codex -> adversarial on
    qplat.apply_profile("claude-code-with-codex")
    assert audit_runtime.should_run_adversarial_mode() is True

    # Profile 3: kilo-code declared but env still says claude-code-detected;
    # adversarial uses detected.host, so this test confirms the
    # detected-vs-declared split: declaration alone does not switch host.
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    qplat.apply_profile("kilo-code")
    assert audit_runtime.should_run_adversarial_mode() is False

    # Clear marker -> False (no platform)
    qplat.clear()
    assert audit_runtime.should_run_adversarial_mode() is False
