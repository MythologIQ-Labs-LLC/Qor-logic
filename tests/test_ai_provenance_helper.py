"""Phase 54: AI provenance helper tests."""
from __future__ import annotations


import pytest

from qor.scripts import ai_provenance, validate_gate_artifact as vga
from qor.scripts.ai_provenance import HumanOversight


def _is_iso_utc(ts: str) -> bool:
    return len(ts) == 20 and ts.endswith("Z") and ts[10] == "T"


def test_build_manifest_returns_schema_valid_dict():
    manifest = ai_provenance.build_manifest(
        "audit", host="claude-code", model_family="claude-opus-4-7",
        human_oversight=HumanOversight.PASS,
    )
    assert manifest["system"] == "Qor-logic"
    assert manifest["host"] == "claude-code"
    assert manifest["model_family"] == "claude-opus-4-7"
    assert manifest["human_oversight"] == "pass"
    assert _is_iso_utc(manifest["ts"])
    payload = {
        "phase": "audit", "ts": "2026-04-30T18:00:00Z",
        "session_id": "test-sess", "target": "p.md", "verdict": "PASS",
        "ai_provenance": manifest,
    }
    assert vga._validate_data("audit", payload) == []


def test_build_manifest_reads_system_version_from_pyproject():
    manifest = ai_provenance.build_manifest(
        "audit", host="x", model_family="y",
        human_oversight=HumanOversight.PASS,
    )
    pyproject_version = ai_provenance._read_system_version()
    assert manifest["version"] == pyproject_version
    assert pyproject_version != "unknown", "pyproject.toml must declare version"


@pytest.mark.parametrize("phase", ["audit", "substantiate", "validate"])
def test_build_manifest_rejects_invalid_human_oversight_for_decision_phase(phase):
    with pytest.raises(ValueError, match="absent"):
        ai_provenance.build_manifest(
            phase, host="x", model_family="y",
            human_oversight=HumanOversight.ABSENT,
        )


@pytest.mark.parametrize("phase", ["research", "plan", "implement"])
def test_build_manifest_rejects_pass_for_non_decision_phase(phase):
    with pytest.raises(ValueError):
        ai_provenance.build_manifest(
            phase, host="x", model_family="y",
            human_oversight=HumanOversight.PASS,
        )


@pytest.mark.parametrize("phase,oversight", [
    ("audit", HumanOversight.PASS),
    ("audit", HumanOversight.VETO),
    ("audit", HumanOversight.OVERRIDE),
    ("substantiate", HumanOversight.PASS),
    ("validate", HumanOversight.PASS),
    ("research", HumanOversight.ABSENT),
    ("plan", HumanOversight.ABSENT),
    ("implement", HumanOversight.ABSENT),
    ("research", HumanOversight.OVERRIDE),
])
def test_build_manifest_accepts_valid_phase_oversight_combinations(phase, oversight):
    manifest = ai_provenance.build_manifest(
        phase, host="x", model_family="y", human_oversight=oversight,
    )
    assert manifest["human_oversight"] == oversight.value


def test_build_manifest_warns_once_on_missing_host(monkeypatch, capsys):
    # Force fallback by clearing detect path and warning state.
    monkeypatch.setattr(ai_provenance, "_detect_host", lambda: "unknown")
    monkeypatch.delenv(ai_provenance._QUIET_ENV, raising=False)
    ai_provenance._warned_keys.clear()

    ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    out_first = capsys.readouterr().err
    assert "host fell back" in out_first

    # Second call same process: no duplicate warn
    ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    out_second = capsys.readouterr().err
    assert "host fell back" not in out_second


def test_build_manifest_warning_suppressible_by_env(monkeypatch, capsys):
    monkeypatch.setattr(ai_provenance, "_detect_host", lambda: "unknown")
    monkeypatch.setenv(ai_provenance._QUIET_ENV, "1")
    ai_provenance._warned_keys.clear()

    ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    err = capsys.readouterr().err
    assert "host fell back" not in err


def test_build_manifest_autodetects_host_without_marker(monkeypatch, capsys):
    """Phase 186 (GH #242): when the cached platform marker yields nothing,
    _detect_host falls back to fresh env detection, so a Claude Code session
    that never ran apply_profile still records host=claude-code (no WARN)."""
    from qor.scripts import qor_platform as qplat

    monkeypatch.setattr(qplat, "current", lambda: None)
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.delenv(ai_provenance._QUIET_ENV, raising=False)
    ai_provenance._warned_keys.clear()

    manifest = ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    assert manifest["host"] == "claude-code"
    assert "host fell back" not in capsys.readouterr().err


def test_build_manifest_reads_model_family_from_env(monkeypatch):
    monkeypatch.setenv(ai_provenance._MODEL_ENV, "claude-sonnet-4-6")
    manifest = ai_provenance.build_manifest(
        "audit", host="x", human_oversight=HumanOversight.PASS,
    )
    assert manifest["model_family"] == "claude-sonnet-4-6"


def test_build_manifest_falls_back_to_unknown_model_when_env_unset(monkeypatch):
    monkeypatch.delenv(ai_provenance._MODEL_ENV, raising=False)
    monkeypatch.setenv(ai_provenance._QUIET_ENV, "1")
    manifest = ai_provenance.build_manifest(
        "audit", host="x", human_oversight=HumanOversight.PASS,
    )
    assert manifest["model_family"] == "unknown"


# ----- Phase 269 (GH #427): the pyproject at the computed path may not be ours -----

_FOREIGN = b'[project]\nname = "some-other-package"\nversion = "0.15.1"\n'
_OURS = b'[project]\nname = "qor-logic"\nversion = "9.9.9"\n'


def _point_at(monkeypatch, tmp_path, body: bytes, name: str = "pyproject.toml"):
    p = tmp_path / name
    if body is not None:
        p.write_bytes(body)
    monkeypatch.setattr(ai_provenance, "_PYPROJECT", p)
    return p


def _metadata_returns(monkeypatch, value):
    """Pin metadata: CI installs editable and a dev workspace has a stale one,
    so an unmocked assertion compares different values in the two places."""
    import importlib.metadata as md

    def _v(_name):
        if value is None:
            raise md.PackageNotFoundError(_name)
        return value

    monkeypatch.setattr(ai_provenance.importlib.metadata, "version", _v)


def test_version_ignores_a_foreign_pyproject(monkeypatch, tmp_path):
    """_REPO_ROOT resolves to site-packages when installed, so the file there
    may belong to an unrelated project entirely."""
    _point_at(monkeypatch, tmp_path, _FOREIGN)
    _metadata_returns(monkeypatch, "1.2.3")
    assert ai_provenance._read_system_version() != "0.15.1"


def test_version_survives_a_malformed_foreign_pyproject(monkeypatch, tmp_path):
    """Nothing about a stranger's file may escape a provenance helper: this is
    called unconditionally from build_manifest, so raising blocks every gate."""
    _point_at(monkeypatch, tmp_path, b'[project\nname = "broken"\n')
    _metadata_returns(monkeypatch, "1.2.3")
    assert ai_provenance._read_system_version() == "1.2.3"


def test_version_survives_a_non_utf8_pyproject(monkeypatch, tmp_path):
    """tomllib.load takes a binary handle and owns the UTF-8 decode, so a
    non-UTF-8 file raises UnicodeDecodeError before any TOML parsing."""
    _point_at(monkeypatch, tmp_path, b'[project]\nname = "caf\xe9"\n')
    _metadata_returns(monkeypatch, "1.2.3")
    assert ai_provenance._read_system_version() == "1.2.3"


def test_version_survives_a_non_table_project_key(monkeypatch, tmp_path):
    """`project = "text"` is legal TOML and makes a bare .get raise."""
    _point_at(monkeypatch, tmp_path, b'project = "text"\n')
    _metadata_returns(monkeypatch, "1.2.3")
    assert ai_provenance._read_system_version() == "1.2.3"


def test_version_falls_back_to_metadata_when_no_pyproject(monkeypatch, tmp_path):
    """The plain wheel install, and the OSError fall-through it depends on."""
    _point_at(monkeypatch, tmp_path, None, name="absent.toml")
    _metadata_returns(monkeypatch, "4.5.6")
    assert ai_provenance._read_system_version() == "4.5.6"


def test_version_falls_through_when_ours_declares_dynamic_version(monkeypatch, tmp_path):
    """A matching name selects the SOURCE, not the RESULT."""
    _point_at(monkeypatch, tmp_path, b'[project]\nname = "qor-logic"\ndynamic = ["version"]\n')
    _metadata_returns(monkeypatch, "7.8.9")
    assert ai_provenance._read_system_version() == "7.8.9"


@pytest.mark.parametrize("spelling", ["qor-logic", "qor_logic", "qor.logic", "QOR-LOGIC"])
def test_version_accepts_pep503_spellings_of_the_name(monkeypatch, tmp_path, spelling):
    body = f'[project]\nname = "{spelling}"\nversion = "9.9.9"\n'.encode()
    _point_at(monkeypatch, tmp_path, body)
    _metadata_returns(monkeypatch, None)
    assert ai_provenance._read_system_version() == "9.9.9"


def test_version_reads_a_pyproject_that_names_this_project(monkeypatch, tmp_path):
    _point_at(monkeypatch, tmp_path, _OURS)
    _metadata_returns(monkeypatch, None)
    assert ai_provenance._read_system_version() == "9.9.9"


def test_version_is_unknown_when_neither_source_answers(monkeypatch, tmp_path):
    _point_at(monkeypatch, tmp_path, _FOREIGN)
    _metadata_returns(monkeypatch, None)
    assert ai_provenance._read_system_version() == "unknown"


def test_version_warns_once_when_it_falls_back_to_unknown(monkeypatch, tmp_path, capsys):
    """host and model_family both warn on 'unknown'; version was the one field
    outside that convention, and D1 makes 'unknown' more reachable."""
    _point_at(monkeypatch, tmp_path, _FOREIGN)
    _metadata_returns(monkeypatch, None)
    monkeypatch.delenv(ai_provenance._QUIET_ENV, raising=False)
    ai_provenance._warned_keys.clear()

    ai_provenance.build_manifest(
        "audit", host="claude-code", model_family="y",
        human_oversight=HumanOversight.PASS,
    )
    assert "version fell back" in capsys.readouterr().err

    ai_provenance.build_manifest(
        "audit", host="claude-code", model_family="y",
        human_oversight=HumanOversight.PASS,
    )
    assert "version fell back" not in capsys.readouterr().err


def test_version_does_not_warn_when_explicitly_passed(monkeypatch, capsys):
    """A caller passing a value has made a choice; do not second-guess it."""
    monkeypatch.delenv(ai_provenance._QUIET_ENV, raising=False)
    ai_provenance._warned_keys.clear()
    ai_provenance.build_manifest(
        "audit", host="claude-code", model_family="y", system_version="unknown",
        human_oversight=HumanOversight.PASS,
    )
    assert "version fell back" not in capsys.readouterr().err


def test_project_name_constant_matches_this_repos_pyproject():
    """A rename must not silently disarm the discriminator."""
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert ai_provenance._canonical(data["project"]["name"]) == ai_provenance._PROJECT_NAME


def test_this_repos_pyproject_parses_and_names_this_project():
    """The 'our own manifest is loud' property, asserted where it belongs.

    It cannot live in _read_system_version, which by construction does not know
    whose file it holds until after the parse.
    """
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert ai_provenance._canonical(data["project"]["name"]) == "qor-logic"
    assert isinstance(data["project"].get("version"), str)


def test_version_survives_a_damaged_metadata_lookup(monkeypatch, tmp_path):
    """The second reader is external state too.

    Nominated by the reviewer and confirmed by enumerating exits: a .dist-info
    whose METADATA is not decodable raises UnicodeDecodeError out of
    importlib.metadata.version, which PackageNotFoundError alone does not catch.
    Same class as the tomllib miss, in the same function.
    """
    _point_at(monkeypatch, tmp_path, _FOREIGN)

    def _boom(_name):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(ai_provenance.importlib.metadata, "version", _boom)
    assert ai_provenance._read_system_version() == "unknown"


def test_version_is_a_string_when_metadata_returns_none(monkeypatch, tmp_path):
    """importlib.metadata.version returns None for a .dist-info with no
    METADATA, or one carrying no Version field. The schema requires a string
    of minLength 1, so returning None would emit an invalid gate artifact."""
    _point_at(monkeypatch, tmp_path, _FOREIGN)
    monkeypatch.setattr(ai_provenance.importlib.metadata, "version", lambda _n: None)
    result = ai_provenance._read_system_version()
    assert isinstance(result, str) and result == "unknown"


def test_build_manifest_stays_schema_valid_when_no_version_resolves(monkeypatch, tmp_path):
    """The consequence that makes the None case a defect rather than a wart."""
    _point_at(monkeypatch, tmp_path, _FOREIGN)
    monkeypatch.setattr(ai_provenance.importlib.metadata, "version", lambda _n: None)
    manifest = ai_provenance.build_manifest(
        "audit", host="claude-code", model_family="y",
        human_oversight=HumanOversight.PASS,
    )
    payload = {
        "phase": "audit", "ts": "2026-04-30T18:00:00Z",
        "session_id": "test-sess", "target": "p.md", "verdict": "PASS",
        "ai_provenance": manifest,
    }
    assert vga._validate_data("audit", payload) == []


def test_version_survives_a_deeply_nested_foreign_pyproject(monkeypatch, tmp_path):
    """tomllib is recursive-descent, so nesting depth raises RecursionError,
    which no enumeration of TOML/OS/decode errors catches.

    Third instance of one class: an enumerated handler on a reader whose stated
    contract is totality. The fix is the uniform rule, not a fourth exception.
    """
    _point_at(monkeypatch, tmp_path, b"a = " + b"[" * 2000 + b"]" * 2000)
    _metadata_returns(monkeypatch, "1.2.3")
    assert ai_provenance._read_system_version() == "1.2.3"


def test_read_system_version_is_total(monkeypatch, tmp_path):
    """build_manifest calls this unconditionally, so a raise means no gate
    artifact can be written at all. It must always return a non-empty str."""
    def _explode(*a, **kw):
        raise RuntimeError("anything at all")

    _point_at(monkeypatch, tmp_path, _FOREIGN)
    monkeypatch.setattr(ai_provenance.tomllib, "load", _explode)
    monkeypatch.setattr(ai_provenance.importlib.metadata, "version", _explode)
    result = ai_provenance._read_system_version()
    assert isinstance(result, str) and result == "unknown"


def test_a_bug_in_our_own_coercion_still_raises(monkeypatch, tmp_path):
    """The other half of the rule: none of our logic sits inside a handler,
    so our own defects stay loud instead of degrading to 'unknown'."""
    _point_at(monkeypatch, tmp_path, b'[project]\nname = "qor-logic"\nversion = "9.9.9"\n')

    def _broken(_name):
        raise AssertionError("our own bug")

    monkeypatch.setattr(ai_provenance, "_canonical", _broken)
    with pytest.raises(AssertionError):
        ai_provenance._read_system_version()


def test_build_manifest_survives_a_permission_denied_platform_marker(tmp_path, monkeypatch):
    """A marker this process cannot read must not stop every gate write.

    _detect_host calls qor_platform.current() outside its import guard, so a
    propagating OSError reached build_manifest and no artifact could be written
    at all -- the same consequence that justified replacing D1's enumeration.
    """
    from pathlib import Path
    from qor.scripts import qor_platform as qplat

    marker = tmp_path / "platform.json"
    marker.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(qplat, "MARKER_PATH", marker)

    real = Path.read_text

    def _denied(self, *a, **kw):
        if self == marker:
            raise PermissionError(13, "Permission denied")
        return real(self, *a, **kw)

    monkeypatch.setattr(Path, "read_text", _denied)
    # The assertion is that a manifest is produced at all. host is NOT pinned:
    # _detect_host falls back to live environment detection, which differs
    # between this workspace and CI, and coupling to it would make the row
    # assert different things in the two places.
    manifest = ai_provenance.build_manifest(
        "audit", model_family="y", human_oversight=HumanOversight.PASS,
    )
    assert isinstance(manifest["host"], str) and manifest["host"]
    assert manifest["system"] == "Qor-logic"
    # Validate rather than merely observe. The None-return defect showed that a
    # produced-but-invalid artifact is quieter than a raise, so the cheap guard
    # against the analogous quiet failure is to run the schema over it.
    payload = {
        "phase": "audit", "ts": "2026-04-30T18:00:00Z",
        "session_id": "test-sess", "target": "p.md", "verdict": "PASS",
        "ai_provenance": manifest,
    }
    assert vga._validate_data("audit", payload) == []
