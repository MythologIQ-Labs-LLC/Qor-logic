"""Phase 190 (GH #239 Phase A): deterministic spec delta merge."""
from __future__ import annotations

import pytest

from qor.scripts.spec_lint import check
from qor.scripts.spec_merge import SpecMergeError, apply

SPEC = """# Capability: gate-chain

### Requirement: Artifacts are immutable
The system SHALL never rewrite a versioned gate artifact after it is written.

#### Scenario: Rerun does not mutate
- GIVEN a sealed phase with a versioned artifact on disk
- WHEN the same phase runs again
- THEN a new iteration file is written and the sealed bytes are unchanged

### Requirement: Latest iteration resolves
The resolver MUST return the highest iteration file for a phase.

#### Scenario: Two iterations exist
- GIVEN iter1 and iter2 artifacts for the plan phase
- WHEN the latest artifact path is resolved
- THEN the iter2 path is returned
"""

ADDED_BLOCK = """### Requirement: Sidecars pair with artifacts
Every versioned artifact SHALL have a provenance sidecar written atomically with it.

#### Scenario: Sidecar exists after write
- GIVEN a phase writes a versioned artifact
- WHEN the write completes
- THEN a matching provenance sidecar exists beside it
"""

DELTA_ADD = f"""## ADDED Requirements

{ADDED_BLOCK}"""

DELTA_MODIFY = """## MODIFIED Requirements

### Requirement: Latest iteration resolves
The resolver MUST return the highest-numbered iteration file, ignoring gaps.

#### Scenario: Gapped iterations
- GIVEN iter1 and iter3 artifacts for the plan phase
- WHEN the latest artifact path is resolved
- THEN the iter3 path is returned
"""

DELTA_REMOVE = """## REMOVED Requirements

- Artifacts are immutable
"""


def test_added_appends_block():
    merged = apply(SPEC, DELTA_ADD)
    assert "Sidecars pair with artifacts" in merged
    assert merged.index("Latest iteration resolves") < merged.index("Sidecars pair")


def test_modified_replaces_whole_block_in_place():
    merged = apply(SPEC, DELTA_MODIFY)
    assert "ignoring gaps" in merged
    assert "iter3 path is returned" in merged
    assert "iter2 path is returned" not in merged
    # unmodified neighbor keeps exact bytes and stays first
    first_block = SPEC[SPEC.index("### Requirement: Artifacts"):SPEC.index("### Requirement: Latest")]
    assert first_block in merged
    assert merged.index("Artifacts are immutable") < merged.index("Latest iteration resolves")


def test_removed_deletes_block():
    merged = apply(SPEC, DELTA_REMOVE)
    assert "Artifacts are immutable" not in merged
    assert "Latest iteration resolves" in merged


def test_modified_absent_target_raises():
    delta = DELTA_MODIFY.replace("Latest iteration resolves", "No such requirement")
    with pytest.raises(SpecMergeError, match="No such requirement"):
        apply(SPEC, delta)


def test_removed_absent_target_raises():
    with pytest.raises(SpecMergeError, match="Ghost requirement"):
        apply(SPEC, "## REMOVED Requirements\n\n- Ghost requirement\n")


def test_added_duplicate_raises():
    delta = DELTA_ADD.replace("Sidecars pair with artifacts", "Artifacts are immutable")
    with pytest.raises(SpecMergeError, match="Artifacts are immutable"):
        apply(SPEC, delta)


def test_merge_is_deterministic():
    assert apply(SPEC, DELTA_ADD) == apply(SPEC, DELTA_ADD)
    assert apply(SPEC, DELTA_MODIFY).encode() == apply(SPEC, DELTA_MODIFY).encode()


def test_merged_output_passes_lint():
    merged = apply(apply(SPEC, DELTA_ADD), DELTA_MODIFY)
    assert check(merged) == [], "merged output must satisfy the grammar"
