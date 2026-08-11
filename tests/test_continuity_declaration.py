"""Phase 216 (GH #285 Phase B): the execution-continuity declaration surface.

Covers the plan-declaration lint, the schema property, the config-backed
contract pin, and the two properties that keep Qor-logic from becoming a second
semantic authority over the upstream contract.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import continuity_contract as cc
from qor.scripts import plan_continuity_lint

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "qor" / "gates" / "schema"


def _valid_declaration() -> dict:
    return {
        "contract_version": "1.0",
        "base_revision": "a" * 40,
        "target_revision": "b" * 40,
        "successor_actor_classes": ["governed-worker"],
        "checkpoint_points": ["pre-handoff"],
        "receipt_required": True,
    }


def test_lint_accepts_versioned_declaration(tmp_path: Path):
    """A well-formed declaration lints clean."""
    findings = plan_continuity_lint.lint(_valid_declaration())
    assert findings == [], [f.code for f in findings]


@pytest.mark.parametrize(
    "mutate,expected_code",
    [
        (lambda d: d.pop("contract_version"), "missing-contract-version"),
        (lambda d: d.update({"provider_session_url": "https://x"}), "unknown-key"),
        (lambda d: d.update({"target_revision": 17}), "non-string-revision"),
        (lambda d: d.update({"successor_actor_classes": []}), "empty-successor-actors"),
        (lambda d: d.update({"checkpoint_points": {"nested": "object"}}), "nested-object"),
    ],
)
def test_lint_rejects_malformed_declaration(mutate, expected_code):
    """Each malformation yields its own finding code, not a generic failure."""
    decl = _valid_declaration()
    mutate(decl)
    findings = plan_continuity_lint.lint(decl)
    assert expected_code in [f.code for f in findings], [f.code for f in findings]


def test_plan_schema_accepts_and_rejects_declaration():
    """plan.schema.json carries execution_continuity and constrains it."""
    schema = json.loads((SCHEMA_DIR / "plan.schema.json").read_text(encoding="utf-8"))
    block = schema["properties"]["execution_continuity"]

    assert "execution_continuity" not in schema["required"], (
        "declaration must stay optional so existing plans remain valid"
    )
    assert block["additionalProperties"] is False, (
        "an open declaration cannot enforce the Qor-owned key set"
    )
    assert set(block["properties"]) == set(cc.QOR_OWNED_KEYS)


def test_contract_pin_reads_from_config(tmp_path: Path):
    """The pin is operator-declared config, and its absence is disclosed."""
    (tmp_path / ".qorlogic").mkdir()
    (tmp_path / ".qorlogic" / "config.json").write_text(
        json.dumps({"execution_continuity": {"contract_version": "1.0"}}),
        encoding="utf-8",
    )
    assert cc.load_pin(tmp_path) == "1.0"

    # Absent config is the disclosed-unpinned state, not an exception.
    assert cc.load_pin(tmp_path / "nonexistent") is None


@pytest.mark.parametrize("phase", ["validate", "remediate"])
@pytest.mark.parametrize("outcome", ["verified", "rejected", "inconclusive"])
def test_continuity_outcome_persists_in_routing_artifacts(phase, outcome):
    """The outcome has a home in the artifacts whose skills route on it."""
    schema = json.loads((SCHEMA_DIR / f"{phase}.schema.json").read_text(encoding="utf-8"))
    field = schema["properties"]["continuity_outcome"]
    assert outcome in field["enum"]
    assert "escalate" not in field["enum"], "only the three typed outcomes belong here"
    assert phase not in schema.get("required", []), "field stays optional"


def test_status_and_outcome_vocabularies_stay_separate():
    """LD-2 regression: `skip` and `inconclusive` must not merge.

    `skip` is the Phase 75 disclosed-skip and is acceptable-to-seal.
    `inconclusive` means the gate ran and the environment denied a conclusion,
    which must route to evidence repair. Widening validate.status is the cheap
    wrong fix; this test goes red the moment someone takes it.
    """
    schema = json.loads((SCHEMA_DIR / "validate.schema.json").read_text(encoding="utf-8"))
    per_criterion = schema["properties"]["criteria_results"]["items"]["properties"]
    status_enum = per_criterion["status"]["enum"]
    assert status_enum == ["pass", "fail", "skip"]
    assert "inconclusive" not in status_enum

    # The two vocabularies also live at different levels: `status` is per
    # criterion, `continuity_outcome` is per artifact. Merging them would be a
    # scope error as well as a semantic one.
    assert "continuity_outcome" not in per_criterion


def test_no_upstream_field_duplication():
    """The thirteenth required behavior, stated as a checkable property.

    Asserting "no upstream field name appears here" would require enumerating
    those names, which requires holding the upstream schema LD-5 says this
    repository does not have. Instead: we carry only our own keys, and only
    scalars. Duplication cannot hide inside a declaration that admits no
    nested structure.
    """
    schema = json.loads((SCHEMA_DIR / "plan.schema.json").read_text(encoding="utf-8"))
    block = schema["properties"]["execution_continuity"]

    assert set(block["properties"]) <= set(cc.QOR_OWNED_KEYS)
    assert "contract_version" in block["properties"], (
        "the contract must be referenced by version, not restated"
    )

    for name, spec in block["properties"].items():
        assert spec.get("type") != "object", f"{name} admits nested structure"
        if spec.get("type") == "array":
            assert spec["items"].get("type") == "string", (
                f"{name} must be an array of scalars"
            )

    for phase in ("validate", "remediate"):
        s = json.loads((SCHEMA_DIR / f"{phase}.schema.json").read_text(encoding="utf-8"))
        field = s["properties"]["continuity_outcome"]
        assert field["type"] == "string"
        assert sorted(field["enum"]) == sorted(cc.OUTCOMES)
