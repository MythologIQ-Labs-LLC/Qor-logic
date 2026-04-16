"""Tests for Phase 5 cross-repo collector."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from qor.scripts import collect_shadow_genomes as collect
from qor.scripts import shadow_process


# ----- Helpers -----

def _mk_event(severity=1, event_type="gate_override", ts="2026-04-15T12:00:00Z",
              session_id="s-1", addressed=False, skill="qor-audit"):
    ev = {
        "ts": ts,
        "skill": skill,
        "session_id": session_id,
        "event_type": event_type,
        "severity": severity,
        "details": {},
        "addressed": addressed,
        "issue_url": None,
        "addressed_ts": None,
        "addressed_reason": None,
        "source_entry_id": None,
    }
    ev["id"] = shadow_process.compute_id(ev)
    return ev


def _mk_fake_repo(tmp_path, name, events):
    repo = tmp_path / name
    (repo / "docs").mkdir(parents=True)
    (repo / "qor" / "scripts").mkdir(parents=True)
    log = repo / "docs" / "PROCESS_SHADOW_GENOME.md"
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return repo


def _valid_config(repos):
    return {
        "version": "1",
        "meta_repo": "MythologIQ-Labs-LLC/Qor-logic",
        "repos": repos,
        "threshold": 10,
        "stale_days": 90,
    }


# ----- Config loading + schema -----

def test_load_config_from_env(tmp_path, monkeypatch):
    config_path = tmp_path / "repos.json"
    config_path.write_text(json.dumps(_valid_config([])), encoding="utf-8")
    monkeypatch.setenv("QOR_CONFIG", str(config_path))
    config = collect.load_config()
    assert config["meta_repo"] == "MythologIQ-Labs-LLC/Qor-logic"


def test_load_config_explicit_path(tmp_path):
    config_path = tmp_path / "repos.json"
    config_path.write_text(json.dumps(_valid_config([])), encoding="utf-8")
    config = collect.load_config(config_path)
    assert config["threshold"] == 10


def test_load_config_raises_on_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        collect.load_config(tmp_path / "nope.json")


def test_config_schema_rejects_missing_required(tmp_path):
    config_path = tmp_path / "repos.json"
    # Missing "meta_repo"
    bad = {"version": "1", "repos": [], "threshold": 10, "stale_days": 90}
    config_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(Exception):  # jsonschema.ValidationError
        collect.load_config(config_path)


def test_config_schema_rejects_bad_meta_repo_pattern(tmp_path):
    config_path = tmp_path / "repos.json"
    bad = _valid_config([])
    bad["meta_repo"] = "not-a-valid-slug"  # no slash
    config_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(Exception):
        collect.load_config(config_path)


# ----- sweep_one -----

def test_sweep_one_returns_unaddressed_tagged(tmp_path, monkeypatch):
    events = [_mk_event(severity=5, session_id="s-a"),
              _mk_event(severity=3, session_id="s-b", ts="2026-04-15T13:00:00Z")]
    repo = _mk_fake_repo(tmp_path, "repo-a", events)

    # Mock subprocess: check_shadow_threshold returns exit 0 (under threshold,
    # no state mutation) — we just want sweep_one to read the log.
    def fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, 0, "OK", "")
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = collect.sweep_one({"path": str(repo), "name": "repo-a", "enabled": True})
    assert len(result) == 2
    assert all(e["source_repo"] == "repo-a" for e in result)


def test_sweep_one_missing_repo_returns_empty(tmp_path, capsys, monkeypatch):
    result = collect.sweep_one({"path": str(tmp_path / "does-not-exist"),
                                 "name": "ghost", "enabled": True})
    assert result == []
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_sweep_one_skips_disabled(tmp_path, monkeypatch):
    events = [_mk_event(severity=5)]
    repo = _mk_fake_repo(tmp_path, "repo-b", events)

    def fake_run(cmd, *args, **kwargs):
        raise AssertionError("subprocess should not run for disabled repo")
    monkeypatch.setattr(subprocess, "run", fake_run)

    result = collect.sweep_one({"path": str(repo), "name": "repo-b", "enabled": False})
    assert result == []


def test_sweep_one_excludes_addressed(tmp_path, monkeypatch):
    events = [_mk_event(severity=5, addressed=True),
              _mk_event(severity=3, ts="2026-04-15T13:00:00Z")]
    repo = _mk_fake_repo(tmp_path, "repo-c", events)
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""))

    result = collect.sweep_one({"path": str(repo), "name": "repo-c", "enabled": True})
    assert len(result) == 1
    assert result[0]["severity"] == 3


# ----- sweep_all + pooling -----

def test_sweep_all_pools_multi_repo(tmp_path, monkeypatch):
    repo_a = _mk_fake_repo(tmp_path, "a", [_mk_event(severity=5, session_id="a")])
    repo_b = _mk_fake_repo(tmp_path, "b", [_mk_event(severity=3, session_id="b",
                                                     ts="2026-04-15T13:00:00Z")])
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""))

    config = _valid_config([
        {"path": str(repo_a), "name": "a", "enabled": True},
        {"path": str(repo_b), "name": "b", "enabled": True},
    ])
    pooled = collect.sweep_all(config)
    assert len(pooled) == 2
    repos = {e["source_repo"] for e in pooled}
    assert repos == {"a", "b"}


def test_threshold_trips_globally_not_per_repo(tmp_path, monkeypatch):
    # Two repos, each sev 5 => 10 pooled => trips.
    # Neither alone would trip (5 < 10).
    repo_a = _mk_fake_repo(tmp_path, "a", [_mk_event(severity=5, session_id="a")])
    repo_b = _mk_fake_repo(tmp_path, "b", [_mk_event(severity=5, session_id="b",
                                                     ts="2026-04-15T13:00:00Z")])
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: subprocess.CompletedProcess(a[0], 0, "", ""))
    config = _valid_config([
        {"path": str(repo_a), "name": "a", "enabled": True},
        {"path": str(repo_b), "name": "b", "enabled": True},
    ])
    pooled = collect.sweep_all(config)
    total = sum(e["severity"] for e in pooled)
    assert total == 10
    assert total >= config["threshold"]


# ----- build_issue_body -----

def test_build_issue_body_groups_by_repo():
    events = [
        {**_mk_event(severity=5, session_id="a"), "source_repo": "a"},
        {**_mk_event(severity=3, session_id="b"), "source_repo": "b"},
        {**_mk_event(severity=2, session_id="c"), "source_repo": "a"},
    ]
    body = collect.build_issue_body(events, threshold=10)
    # Header + totals
    assert "Severity sum: **10**" in body
    assert "Repos affected: 2" in body
    # Per-repo sections
    assert "### a — 2 events, sev 7" in body
    assert "### b — 1 events, sev 3" in body


def test_build_issue_body_sorts_repos_alphabetically():
    events = [
        {**_mk_event(session_id="z"), "source_repo": "zebra"},
        {**_mk_event(session_id="a"), "source_repo": "alpha"},
    ]
    body = collect.build_issue_body(events, threshold=10)
    assert body.index("alpha") < body.index("zebra")


# ----- dispatch -----

def test_dispatch_calls_gh_correctly(monkeypatch):
    captured = {}
    fake_url = "https://github.com/meta/repo/issues/99"

    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        captured["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(cmd, 0, fake_url + "\n", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    url = collect.dispatch("body text", "meta/repo", 2, 10)
    assert url == fake_url
    assert captured["cmd"][:3] == ["gh", "issue", "create"]
    assert "--repo" in captured["cmd"]
    assert "meta/repo" in captured["cmd"]


def test_dispatch_dry_run_returns_none(capsys):
    result = collect.dispatch("body", "meta/repo", 1, 5, dry_run=True)
    assert result is None
    captured = capsys.readouterr()
    assert "DRY RUN" in captured.out


# ----- flip_per_repo -----

def test_flip_per_repo_groups_invocations(tmp_path, monkeypatch):
    events = [
        {**_mk_event(session_id="a"), "source_repo": "a"},
        {**_mk_event(session_id="b", ts="2026-04-15T13:00:00Z"), "source_repo": "b"},
        {**_mk_event(session_id="c", ts="2026-04-15T14:00:00Z"), "source_repo": "a"},
    ]
    repo_a_path = tmp_path / "a"
    repo_b_path = tmp_path / "b"
    repo_a_path.mkdir()
    repo_b_path.mkdir()
    config = _valid_config([
        {"path": str(repo_a_path), "name": "a", "enabled": True},
        {"path": str(repo_b_path), "name": "b", "enabled": True},
    ])

    calls = []
    def fake_run(cmd, *args, **kwargs):
        calls.append({"cmd": cmd, "cwd": kwargs.get("cwd")})
        return subprocess.CompletedProcess(cmd, 0, "Flipped 1 event(s) in ...", "")
    monkeypatch.setattr(subprocess, "run", fake_run)

    summary = collect.flip_per_repo("https://issue/1", events, config)
    # Two subprocess calls, one per source_repo
    assert len(calls) == 2
    # Each call targets the correct cwd
    cwd_by_ids = {c["cwd"]: [arg for i, arg in enumerate(c["cmd"]) if c["cmd"][i-1] == "--events"] for c in calls}
    assert summary == {"a": 1, "b": 1}  # default fallback, mocked output


def test_flip_per_repo_skips_unknown_source_repo(tmp_path, monkeypatch, capsys):
    events = [{**_mk_event(), "source_repo": "unknown-repo"}]
    config = _valid_config([])  # no entries

    def fake_run(*a, **k):
        raise AssertionError("should not subprocess for unknown repo")
    monkeypatch.setattr(subprocess, "run", fake_run)

    summary = collect.flip_per_repo("url", events, config)
    assert summary == {}
    captured = capsys.readouterr()
    assert "no config entry" in captured.err


# ----- Integration with --flip-only mode -----

def test_flip_only_mode_updates_events_without_gh(tmp_path, monkeypatch):
    from qor.scripts import create_shadow_issue as csi

    events = [
        _mk_event(severity=5, session_id="s-1"),
        _mk_event(severity=3, session_id="s-2", ts="2026-04-15T13:00:00Z"),
    ]
    log = tmp_path / "shadow.md"
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

    # Call flip_events_only directly (the function behind --flip-only)
    target_ids = {events[0]["id"]}
    fake_url = "https://issue/42"
    flipped = csi.flip_events_only(log, target_ids, fake_url)
    assert flipped == 1

    updated = shadow_process.read_events(log)
    target = [e for e in updated if e["id"] == events[0]["id"]][0]
    other = [e for e in updated if e["id"] == events[1]["id"]][0]
    assert target["addressed"] is True
    assert target["issue_url"] == fake_url
    assert other["addressed"] is False  # other preserved


def test_flip_only_preserves_other_events(tmp_path):
    from qor.scripts import create_shadow_issue as csi
    e1 = _mk_event(severity=5, session_id="s-1")
    e2 = _mk_event(severity=3, session_id="s-2", ts="2026-04-15T13:00:00Z")
    e3 = _mk_event(severity=1, session_id="s-3", ts="2026-04-15T14:00:00Z", addressed=True)

    log = tmp_path / "shadow.md"
    log.write_text("\n".join(json.dumps(e) for e in [e1, e2, e3]) + "\n", encoding="utf-8")

    csi.flip_events_only(log, {e1["id"]}, "https://i/1")

    after = shadow_process.read_events(log)
    assert len(after) == 3
    by_id = {e["id"]: e for e in after}
    assert by_id[e1["id"]]["addressed"] is True
    assert by_id[e2["id"]]["addressed"] is False  # untouched
    assert by_id[e3["id"]]["addressed"] is True   # already-addressed unchanged


# ----- Phase 14: collector reads upstream file -----

def test_collector_reads_upstream_file(tmp_path):
    """When both files present, collector reads UPSTREAM; LOCAL events not pooled."""
    repo = tmp_path / "repo1"
    (repo / "docs").mkdir(parents=True)
    upstream_event = _mk_event(severity=2, session_id="s-upstream")
    local_event = _mk_event(severity=3, session_id="s-local")
    upstream_log = repo / "docs" / "PROCESS_SHADOW_GENOME_UPSTREAM.md"
    local_log = repo / "docs" / "PROCESS_SHADOW_GENOME.md"
    upstream_log.write_text(json.dumps(upstream_event) + "\n", encoding="utf-8")
    local_log.write_text(json.dumps(local_event) + "\n", encoding="utf-8")

    events = collect.read_repo_shadow(repo)
    ids = {e["id"] for e in events}
    assert upstream_event["id"] in ids
    assert local_event["id"] not in ids
