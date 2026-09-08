"""Phase 169 (GH #251): evidence-bundle reconstruction tests.

Synthetic-repo fixtures; the bundle reconstructs from recorded signals only,
names missing signals, and never raises from a collector.
"""
from __future__ import annotations

import json
from pathlib import Path

from qor.scripts import evidence_bundle as eb

_SID = "2026-07-04T1200-abc123"

_LEDGER = f"""# LEDGER

### Entry #397: SESSION SEAL -- Phase 168 something (v0.116.0)

**Timestamp**: 2026-07-04T15:58:00Z
**Phase**: SUBSTANTIATE (Phase 168; feature)
**Session**: `{_SID}`

**Content Hash**: `{"a" * 64}`
**Previous Hash**: `{"b" * 64}`
**Chain Hash (Merkle seal)**: `{"c" * 64}`
"""


def _full_repo(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text(_LEDGER, encoding="utf-8")
    sess = tmp_path / ".qor" / "gates" / _SID
    sess.mkdir(parents=True)
    plan = {"phase": "plan", "ts": "2026-07-04T12:00:00Z", "session_id": _SID,
            "plan_path": "docs/plan-x.md", "phases": ["one"],
            "ci_commands": ["python -m pytest -q"]}
    (sess / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    for ph, extra in [("audit", {"verdict": "PASS", "target": "docs/plan-x.md",
                                 "report_path": "r.md", "risk_grade": "L2"}),
                      ("implement", {"files_touched": ["a.py"]}),
                      ("substantiate", {"verdict": "PASS", "merkle_seal": "c" * 64,
                                        "version": "0.116.0"})]:
        payload = {"phase": ph, "ts": "2026-07-04T12:00:00Z", "session_id": _SID, **extra}
        (sess / f"{ph}.json").write_text(json.dumps(payload), encoding="utf-8")
    for ph in ("plan", "audit", "implement", "substantiate"):
        from qor.scripts import gate_provenance as gp
        raw = (sess / f"{ph}.json").read_bytes()
        (sess / f"{ph}.provenance").write_text(
            json.dumps({"payload_sha256": gp.payload_digest(raw), "session_id": _SID}),
            encoding="utf-8")
    (sess / "audit_history.jsonl").write_text('{"verdict": "PASS"}\n', encoding="utf-8")
    lock_dir = tmp_path / ".qor" / "intent-lock"
    lock_dir.mkdir(parents=True)
    (lock_dir / f"{_SID}.json").write_text(json.dumps({"session_id": _SID}), encoding="utf-8")
    (docs / "PROCESS_SHADOW_GENOME.md").write_text("", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [0.116.0] - 2026-07-04\n\n- **Phase 168 (feature)**: x\n",
        encoding="utf-8")
    return tmp_path


def test_resolve_query_by_phase_and_session(tmp_path):
    root = _full_repo(tmp_path)
    ledger_text = (root / "docs" / "META_LEDGER.md").read_text(encoding="utf-8")
    assert eb.resolve_query(ledger_text, phase=168) == (168, _SID)
    assert eb.resolve_query(ledger_text, session=_SID) == (168, _SID)
    assert eb.resolve_query(ledger_text, phase=999) is None


def test_collectors_report_found_and_detail(tmp_path):
    root = _full_repo(tmp_path)
    bundle = eb.assemble(root, _SID, 168)
    signals = bundle["signals"]
    assert signals["ledger_entry"]["found"] is True
    assert signals["ledger_entry"]["chain_hash"] == "c" * 64
    assert signals["gate_artifacts"]["found"] is True
    assert {a["phase"] for a in signals["gate_artifacts"]["artifacts"]} == {
        "plan", "audit", "implement", "substantiate"}
    assert all(a["valid"] for a in signals["gate_artifacts"]["artifacts"])
    assert signals["provenance"]["found"] is True
    assert all(s["payload_ok"] for s in signals["provenance"]["sidecars"])
    assert signals["audit_history"]["found"] is True
    assert signals["audit_history"]["events"] == 1
    assert signals["intent_lock"]["found"] is True
    assert signals["changelog"]["found"] is True
    assert signals["changelog"]["version"] == "0.116.0"


def test_completeness_names_missing_signals(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "META_LEDGER.md").write_text(_LEDGER, encoding="utf-8")
    sess = tmp_path / ".qor" / "gates" / _SID
    sess.mkdir(parents=True)
    bundle = eb.assemble(tmp_path, _SID, 168)
    assert bundle["completeness"]["found"] < bundle["completeness"]["total"]
    missing = set(bundle["completeness"]["missing"])
    assert "intent_lock" in missing and "provenance" in missing
    assert "ledger_entry" not in missing
    assert bundle["errors"] == []  # collectors never raise


def test_short_chain_session_not_penalized(tmp_path):
    root = _full_repo(tmp_path)
    sess = root / ".qor" / "gates" / _SID
    (sess / "audit.json").unlink()
    (sess / "audit.provenance").unlink()
    plan = json.loads((sess / "plan.json").read_text(encoding="utf-8"))
    plan["change_class"] = "hotfix"
    plan["required_gate_artifacts"] = ["plan", "implement", "substantiate"]
    plan["affected_files"] = ["docs/notes.md"]
    (sess / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    bundle = eb.assemble(root, _SID, 168)
    arts = bundle["signals"]["gate_artifacts"]
    assert arts["found"] is True
    assert {a["phase"] for a in arts["artifacts"]} == {"plan", "implement", "substantiate"}
    assert arts["declared_set"] == ["plan", "implement", "substantiate"]


def test_main_final_line_json_and_exit_codes(tmp_path, capsys):
    root = _full_repo(tmp_path)
    rc = eb.main(["--phase", "168", "--repo-root", str(root)])
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    payload = json.loads(lines[-1])
    assert rc == 0
    assert payload["schema_version"] == "1"
    assert payload["query"] == {"session_id": _SID, "phase_num": 168}
    rc = eb.main(["--phase", "999", "--repo-root", str(root)])
    assert rc == 1


# ----- Phase 277 (GH #467): the hash fields read through ledger_dialect -----
#
# The content_hash pattern accepted only an inline-backtick value with no field
# suffix, reading 168 of 235 seal blocks. Its sibling chain_hash pattern already
# tolerated a suffix -- two fields in one dict following two conventions.
#
# The substitution is a RESTRUCTURE, not a pattern swap: _FIELD_RES is consumed
# by a generic `found.group(1)` loop, and CONTENT_HASH_RE has three capture
# groups (one per value form). Dropping it into that dict calls .group(1) on it,
# which yields None for two of the three forms -- leaving chain_hash at 219 of
# 235, exactly where it started, while appearing to have been fixed.


def _seal(body: str) -> str:
    return "### Entry #1: SESSION SEAL -- test\n\n**Session**: 2026-09-08T0000-aaaaaa\n" + body


def test_seal_block_reads_a_suffixed_content_hash_label():
    """`**Content Hash (session seal)**:` -- 59 of the 67 gains take this form."""
    blocks = eb._seal_blocks(_seal(
        "**Content Hash (session seal)**: `" + "a" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n"))

    assert blocks[0]["content_hash"] == "a" * 64


def test_seal_block_reads_a_non_backtick_content_hash_value():
    """The remaining 8 gains: a plain label whose value is not backticked."""
    blocks = eb._seal_blocks(_seal(
        "**Content Hash**: SHA256(plan.md) = " + "c" * 64 + "\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n"))

    assert blocks[0]["content_hash"] == "c" * 64


def test_seal_block_chain_hash_gains_coverage_not_just_content():
    """The .group(1) trap: a naive substitution leaves chain_hash at exactly its
    old coverage while content_hash appears to improve, so the fix looks done
    and is not. Asserted on a chain value form the old pattern could not read."""
    blocks = eb._seal_blocks(_seal(
        "**Content Hash**: `" + "a" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: SHA256(entry) = " + "d" * 64 + "\n"))

    assert blocks[0]["chain_hash"] == "d" * 64


def test_seal_block_still_reads_the_plain_backticked_forms():
    """No regression on the 168 blocks that already worked."""
    blocks = eb._seal_blocks(_seal(
        "**Content Hash**: `" + "a" * 64 + "`\n"
        "**Chain Hash (Merkle seal)**: `" + "b" * 64 + "`\n"))

    assert blocks[0]["content_hash"] == "a" * 64
    assert blocks[0]["chain_hash"] == "b" * 64
    assert blocks[0]["session_id"] == "2026-09-08T0000-aaaaaa"
