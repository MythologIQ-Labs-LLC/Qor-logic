"""Phase 262 (GH #437): bind ``_VALID_CATEGORIES`` to the audit schema enum.

``findings_signature._VALID_CATEGORIES`` is a hand-maintained mirror of the
``findings_categories`` enum in ``qor/gates/schema/audit.schema.json``. Nothing
compared the two, so they drifted: the schema gained ``feature-test-undeclared``
and the frozenset did not. ``compute_record`` raises on any value outside the
frozenset, and ``stall_walk`` calls it unguarded at both sites behind
``cycle_count_escalator.check`` and ``check_session_total`` -- so a correct audit
emitting that category made the *next* cycle's escalation check raise.

These tests bind the two sources three ways: as sets, per value through the
function that raises, and through the call path the issue describes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from qor.scripts import audit_history, findings_signature, stall_walk
from qor.scripts import validate_gate_artifact as vga
from qor import workdir as _workdir

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "qor" / "gates" / "schema" / "audit.schema.json"


def _schema_categories() -> set[str]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return set(schema["properties"]["findings_categories"]["items"]["enum"])


@pytest.fixture
def isolate_gates_dir(tmp_path, monkeypatch):
    """Re-point the gate dir at tmp_path, via both resolvers.

    ``vga.GATES_DIR`` and ``_workdir.gate_dir`` are separate resolvers and
    ``audit_history.history_path`` uses the second. Patching one leaves the
    other pointed at the live tree, which writes real gate artifacts under a
    session id the conftest sweep does not match.
    """
    isolated = tmp_path / ".qor" / "gates"
    monkeypatch.setattr(vga, "GATES_DIR", isolated)
    monkeypatch.setattr(_workdir, "gate_dir", lambda: isolated)
    yield isolated


def test_schema_enum_and_valid_categories_are_identical():
    """The mirror equals its source, in both directions.

    Set equality rather than containment: a value dropped from the schema but
    left in the frozenset is drift too, and would let a retired category keep
    signing.
    """
    assert _schema_categories() == set(findings_signature._VALID_CATEGORIES)


def test_compute_record_accepts_every_schema_category():
    """Every category the schema admits can actually be signed.

    Distinct from the set comparison above: this exercises the function that
    raises, so it fails on the behaviour rather than on a collection mismatch.
    """
    unsignable = []
    for category in sorted(_schema_categories()):
        record = {"verdict": "VETO", "findings_categories": [category]}
        try:
            findings_signature.compute_record(record)
        except findings_signature.UnmappedCategoryError:
            unsignable.append(category)
    assert not unsignable, (
        "audit.schema.json admits categories findings_signature cannot sign: "
        f"{unsignable}. _VALID_CATEGORIES has drifted from the schema enum."
    )


def test_stall_walk_survives_every_schema_category(isolate_gates_dir):
    """The escalator call path tolerates every category the schema admits.

    ``count_session_signature_totals`` reads a single JSONL through
    ``audit_history.read``; seeding per-category files into the gate directory
    would yield an empty history and pass vacuously. Records are appended with
    distinct timestamps so each is a separate history entry.
    """
    session_id = "fixture-parity-262"
    categories = sorted(_schema_categories())
    for index, category in enumerate(categories):
        audit_history.append(
            {
                "phase": "audit",
                "ts": f"2026-01-01T00:{index:02d}:00Z",
                "session_id": session_id,
                "target": "docs/plan-fixture.md",
                "verdict": "VETO",
                "findings_categories": [category],
            },
            session_id,
        )

    totals = stall_walk.count_session_signature_totals(session_id)

    assert len(totals) == len(categories), (
        "each distinct category set should hash to its own signature; "
        f"expected {len(categories)} signatures, got {len(totals)}"
    )
    assert all(count == 1 for count in totals.values())
