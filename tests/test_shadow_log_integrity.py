"""Phase 297 (LD-10): integrity invariants over the tracked Shadow Genome logs.

Every event validates against ``shadow_event.schema.json``, carries the id that
``shadow_process.compute_id`` derives from it, has a unique id, and the log text
is publication-boundary clean. Invariants only: no specific id or hash is
asserted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from qor.scripts import publication_boundary_lint, shadow_process

REPO = Path(__file__).resolve().parent.parent
LOGS = ("docs/PROCESS_SHADOW_GENOME.md", "docs/PROCESS_SHADOW_GENOME_UPSTREAM.md")


@pytest.mark.parametrize("rel", LOGS)
def test_every_event_validates_against_schema(rel):
    events = shadow_process.read_events(REPO / rel)
    assert events, f"{rel}: no events parsed"
    for event in events:
        shadow_process.validate(event)


@pytest.mark.parametrize("rel", LOGS)
def test_every_event_id_is_computed_and_unique(rel):
    events = shadow_process.read_events(REPO / rel)
    mismatched = [e["id"] for e in events if e["id"] != shadow_process.compute_id(e)]
    assert not mismatched, f"{rel}: ids not equal to compute_id: {mismatched}"
    ids = [e["id"] for e in events]
    assert len(ids) == len(set(ids)), f"{rel}: duplicate event ids"


@pytest.mark.parametrize("rel", LOGS)
def test_log_is_publication_boundary_clean(rel):
    text = (REPO / rel).read_text(encoding="utf-8")
    assert publication_boundary_lint.scan_text(rel, text, []) == []
