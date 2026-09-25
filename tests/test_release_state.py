"""Tests for explicit exceptional release-state validation."""
from __future__ import annotations

import json

import pytest

from qor.scripts.release_state import ReleaseStateError, load_exceptions, validate_payload


def _payload(*entries: dict[str, str]) -> dict[str, object]:
    return {"schema": "qor.release-state/v1", "exceptions": list(entries)}


def _entry(
    version: str = "0.175.0",
    state: str = "sealed_unpublished",
    reason: str = "not published",
) -> dict[str, str]:
    return {"version": version, "state": state, "reason": reason}


def test_validate_payload_accepts_sealed_and_legacy_states():
    payload = _payload(
        _entry(),
        _entry("0.102.2", "legacy_untagged", "historical tag state uncertain"),
    )
    assert validate_payload(payload, {"0.175.0", "0.102.2"}) == {
        "0.175.0",
        "0.102.2",
    }


def test_local_tag_is_not_part_of_release_state_validation():
    payload = _payload(_entry(reason="sealed locally, not published remotely"))
    assert validate_payload(payload, {"0.175.0"}) == {"0.175.0"}


def test_duplicate_version_is_rejected():
    payload = _payload(_entry(), _entry(reason="second claim"))
    with pytest.raises(ReleaseStateError, match="duplicate"):
        validate_payload(payload, {"0.175.0"})


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"schema": "wrong", "exceptions": []}, "schema"),
        ({"schema": "qor.release-state/v1", "exceptions": [], "extra": True}, "schema"),
        (_payload(_entry(state="released_maybe")), "unsupported"),
        (_payload(_entry(version="0.175")), "MAJOR.MINOR.PATCH"),
        (_payload(_entry(reason="   ")), "reason"),
        ({"schema": "qor.release-state/v1", "exceptions": {}}, "list"),
    ],
)
def test_malformed_release_state_is_rejected(payload, message):
    with pytest.raises(ReleaseStateError, match=message):
        validate_payload(payload, {"0.175.0"})


def test_version_missing_from_changelog_is_rejected():
    with pytest.raises(ReleaseStateError, match="missing CHANGELOG"):
        validate_payload(_payload(_entry()), set())


def test_entry_with_extra_field_is_rejected():
    entry = _entry()
    entry["extra"] = "nope"
    with pytest.raises(ReleaseStateError, match="version/state/reason"):
        validate_payload(_payload(entry), {"0.175.0"})


def test_load_exceptions_reads_valid_json(tmp_path):
    path = tmp_path / "release-state.json"
    path.write_text(json.dumps(_payload(_entry())), encoding="utf-8")
    assert load_exceptions(path, {"0.175.0"}) == {"0.175.0"}


def test_load_exceptions_wraps_invalid_json(tmp_path):
    path = tmp_path / "release-state.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(ReleaseStateError, match="cannot read"):
        load_exceptions(path, {"0.175.0"})
