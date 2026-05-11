"""Phase 58 capability inventory tests."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import jsonschema

from qor.capabilities import KNOWN_CAPABILITIES, build_inventory
from qor.capabilities.types import Capability

SCHEMA = (
    Path(__file__).resolve().parent.parent
    / "qor" / "gates" / "schema" / "capability_inventory.schema.json"
)


def test_known_capabilities_is_tuple_of_capability():
    assert len(KNOWN_CAPABILITIES) >= 15
    assert all(isinstance(c, Capability) for c in KNOWN_CAPABILITIES)


def test_inventory_contains_core_lifecycle_capabilities():
    ids = {c.id for c in build_inventory(".")}
    for required in ("audit-tribunal", "implement-pass", "substantiate-seal", "validate-chain"):
        assert required in ids, f"missing core capability: {required!r}"


def test_inventory_contains_phase_59_hash_integrity_capability():
    ids = {c.id for c in KNOWN_CAPABILITIES}
    assert "hash-integrity" in ids


def test_inventory_contains_phase_57_sdk_alignment_capability():
    ids = {c.id for c in KNOWN_CAPABILITIES}
    assert "sdk-alignment" in ids


def test_inventory_contains_phase_56_federated_ledger_capability():
    ids = {c.id for c in KNOWN_CAPABILITIES}
    assert "federated-ledger-fragments" in ids


def test_inventory_contains_phase_55_documentation_touches_capability():
    ids = {c.id for c in KNOWN_CAPABILITIES}
    assert "documentation-touches" in ids


def test_every_capability_validates_against_schema():
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for cap in KNOWN_CAPABILITIES:
        # Round-trip via JSON: tuples -> lists (jsonschema "array" requires list)
        payload = json.loads(json.dumps(asdict(cap)))
        jsonschema.validate(payload, schema)
