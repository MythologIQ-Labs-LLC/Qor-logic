"""GH #358: canonical consumer-contract fixtures for external Qor-logic
artifact consumers (a versioned adapter classifying every read into
ok/unavailable/malformed/unsupported/stale, plus a partial-migration mix).

Fixtures live under qor/fixtures/consumer-contract/ and are catalogued in
MANIFEST.json. This module proves each catalogued fixture actually exhibits
the state its manifest entry claims, using Qor-logic's own real parsers and
schemas (meta_ledger_walker, ledger_upgrade.schema_version,
feature_index_verify, jsonschema against the gate schemas) rather than
hand-waving the claim.

Two artifact types named in the originating ask -- "tracker manifest /
programs.yaml" -- have no Qor-logic-owned schema, parser, or producer
anywhere in this repository (confirmed by search before authoring this
module). MANIFEST.json records that row as out_of_scope with a reason
instead of fabricating fixtures for a format this repo does not define.
Two per-state cells (FEATURE_INDEX stale/unsupported-version, gate-artifact
unsupported-version) are similarly recorded as gaps: this repo defines no
timestamp or version marker for those cells today.
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from qor.scripts import ledger_upgrade
from qor.scripts import meta_ledger_walker
from qor.scripts import feature_index_verify as fiv

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "qor" / "fixtures" / "consumer-contract"
GATE_SCHEMA = json.loads(
    (ROOT / "qor" / "gates" / "schema" / "audit.schema.json").read_text(encoding="utf-8")
)
FEATURE_ROW_SCHEMA = json.loads(
    (ROOT / "qor" / "gates" / "schema" / "feature_index.schema.json").read_text(encoding="utf-8")
)


def _manifest() -> dict:
    return json.loads((FIXTURES / "MANIFEST.json").read_text(encoding="utf-8"))


def _read(rel: str) -> str:
    return (FIXTURES / rel).read_text(encoding="utf-8")


REQUIRED_STATES = {
    "supported", "missing-optional", "stale", "malformed",
    "unsupported-version", "partial-migration",
}


def test_manifest_declares_all_six_states_per_in_scope_artifact_type():
    manifest = _manifest()
    for artifact_type, entry in manifest["artifact_types"].items():
        if entry.get("out_of_scope"):
            assert entry.get("reason"), f"{artifact_type} marked out_of_scope needs a reason"
            continue
        declared = set(entry["states"].keys())
        assert declared == REQUIRED_STATES, (
            f"{artifact_type} must declare exactly the six contract states, got {declared}"
        )
        for state, cell in entry["states"].items():
            assert (
                "path" in cell or "path_pair" in cell
                or cell.get("represented_by") == "absence" or cell.get("gap")
            ), (
                f"{artifact_type}/{state} must be a real fixture, a documented file-absence "
                f"state, or an explicitly disclosed gap"
            )


def test_tracker_manifest_is_out_of_scope_not_fabricated():
    manifest = _manifest()
    tracker = manifest["artifact_types"]["tracker-manifest"]
    assert tracker["out_of_scope"] is True
    assert not (FIXTURES / "tracker_manifest").exists()


# --- META_LEDGER -------------------------------------------------------


def test_meta_ledger_supported_parses_and_declares_current_schema():
    text = _read("meta_ledger/supported.md")
    assert ledger_upgrade.schema_version(text) == ledger_upgrade.SCHEMA_VERSION
    records = meta_ledger_walker.walk(FIXTURES / "meta_ledger" / "supported.md")
    audit_like = [r for r in records if r.verdict in ("PASS", "VETO")]
    assert len(audit_like) >= 1
    assert all(r.target is not None for r in audit_like)


def test_meta_ledger_unsupported_version_exceeds_current_schema():
    text = _read("meta_ledger/unsupported-version.md")
    declared = ledger_upgrade.schema_version(text)
    assert declared > ledger_upgrade.SCHEMA_VERSION, (
        "fixture must declare a schema version this Qor-logic release does not yet define"
    )


def test_meta_ledger_partial_migration_predates_the_schema_marker():
    text = _read("meta_ledger/partial-migration.md")
    assert ledger_upgrade.schema_version(text) == 0, (
        "legacy/no-marker is the real partial-migration signal ledger_upgrade defines"
    )
    records = meta_ledger_walker.walk(FIXTURES / "meta_ledger" / "partial-migration.md")
    assert len(records) >= 1, "an unmigrated ledger still carries readable prior entries"


def test_meta_ledger_stale_entry_timestamp_predates_reference_now():
    manifest = _manifest()
    cell = manifest["artifact_types"]["meta-ledger"]["states"]["stale"]
    reference_now = cell["as_of"]
    records = meta_ledger_walker.walk(FIXTURES / "meta_ledger" / "stale.md")
    assert records, "stale fixture must still contain a parseable entry"
    latest_ts = max(r.ts for r in records if r.ts)
    assert latest_ts < reference_now, "latest entry must predate the fixture's stated reference time"


def test_meta_ledger_malformed_drops_entries_despite_real_content():
    raw = _read("meta_ledger/malformed.md")
    assert "AUDIT" in raw or "SEAL" in raw, "fixture must contain real governance content"
    records = meta_ledger_walker.walk(FIXTURES / "meta_ledger" / "malformed.md")
    assert len(records) == 0, (
        "corrupted entry headings must silently fail to parse -- this is exactly the "
        "false-negative a consumer must not mistake for 'no governance to report'"
    )


# --- FEATURE_INDEX -------------------------------------------------------


def test_feature_index_supported_all_rows_valid_and_tally_matches():
    text = _read("feature_index/supported.md")
    rows = fiv.parse_index_rows(text)
    assert len(rows) >= 3
    for row in rows:
        shaped = {"id": row["id"], "name": row.get("name", row["id"]), "status": row["status"]}
        if row["status"] == "n/a":
            shaped["n_a_rationale"] = "documented in fixture prose"
        jsonschema.validate(shaped, FEATURE_ROW_SCHEMA)


def test_feature_index_malformed_row_fails_schema_validation():
    text = _read("feature_index/malformed.md")
    rows = fiv.parse_index_rows(text)
    bad = [r for r in rows if r["status"] == "n/a"]
    assert bad, "fixture must include an n/a row with no rationale supplied"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"id": bad[0]["id"], "name": "x", "status": "n/a"}, FEATURE_ROW_SCHEMA)


def test_feature_index_partial_migration_has_untagged_legacy_rows():
    text = _read("feature_index/partial-migration.md")
    assert fiv.index_has_surface_column(text)
    rows = fiv.parse_index_rows(text)
    tagged = [r for r in rows if r["status"] != "n/a" and r.get("surface", "").strip()]
    untagged = [r for r in rows if r["status"] != "n/a" and not r.get("surface", "").strip()]
    assert tagged and untagged, (
        "partial migration must mix Surface-tagged (migrated) and untagged (legacy) rows"
    )


def test_feature_index_stale_and_unsupported_version_are_disclosed_gaps():
    manifest = _manifest()
    states = manifest["artifact_types"]["feature-index"]["states"]
    assert states["stale"]["gap"] is True
    assert states["unsupported-version"]["gap"] is True


# --- gate artifact (audit) -------------------------------------------------------


def test_gate_artifact_supported_validates_against_audit_schema():
    data = json.loads(_read("gate_artifact/supported.json"))
    jsonschema.validate(data, GATE_SCHEMA)


def test_gate_artifact_malformed_fails_veto_without_findings_categories():
    data = json.loads(_read("gate_artifact/malformed.json"))
    assert data["verdict"] == "VETO"
    assert "findings_categories" not in data
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, GATE_SCHEMA)


def test_gate_artifact_partial_migration_mixes_pre_and_post_phase67_shape():
    legacy = json.loads(_read("gate_artifact/partial-migration/legacy-pre-phase67.json"))
    current = json.loads(_read("gate_artifact/partial-migration/current-post-phase67.json"))
    jsonschema.validate(legacy, GATE_SCHEMA)
    jsonschema.validate(current, GATE_SCHEMA)
    assert "target_content_hash" not in legacy
    assert "target_content_hash" in current


def test_gate_artifact_stale_ts_predates_reference_now():
    manifest = _manifest()
    cell = manifest["artifact_types"]["gate-artifact"]["states"]["stale"]
    data = json.loads(_read("gate_artifact/stale.json"))
    jsonschema.validate(data, GATE_SCHEMA)
    assert data["ts"] < cell["as_of"]


def test_gate_artifact_unsupported_version_is_a_disclosed_gap():
    manifest = _manifest()
    assert manifest["artifact_types"]["gate-artifact"]["states"]["unsupported-version"]["gap"] is True
