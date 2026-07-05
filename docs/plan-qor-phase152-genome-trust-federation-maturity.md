# Plan: Phase 152 -- Shadow Genome trust / federation / maturity producers (GH #213)

**change_class**: feature

**doc_tier**: minimal

## Open Questions

None. Closes GH #213 (downstream consumer blocker). The Shadow Genome graph
(`qor.scripts.shadow_genome_graph`) emits only the causal layer (checkpoint / state / failure /
governance); the trust-transition, federation-peer, and learning-maturity surfaces were DECLINED in the
doctrine as "infrastructure without a consumer" (#139). That premise no longer holds -- a sibling governance repository (#196,
shipped) is the consumer. Operator decision settled: **emitter-API + derive** -- qor-logic owns the
canonical schema + recorder methods and surfaces them in `to_dict`; it DERIVES failure-node maturity from
its own linked data where available; trust-transitions + federation-peer status are fed by the downstream consumer
adapter through the API. All additions are strictly append-only (the doctrine's core invariant). The
doctrine's "Scope boundary" section is updated to record that the consumer now exists.

## Phase 1: trust-transition emitter

### Affected Files

- `qor/scripts/shadow_genome_graph.py` - add `TrustLevel`/`TrustDirection` enums, a `TRUST` node type, and `record_trust_transition(...)`.
- `tests/test_genome_trust_transitions.py` (NEW).

### Changes

Add `class TrustLevel(str, Enum)`: `CBT` / `KBT` / `IBT`; `class TrustDirection(str, Enum)`: `PROMOTION`
/ `DEMOTION`. Add `TRUST = "trust"` to `GenomeNodeType`. Add:
```python
def record_trust_transition(self, from_level, to_level, *, triggering_evidence=(),
                            governance_node_id=None, at=None) -> str:
```
It appends a `trust` node whose metadata is `{from_level, to_level, direction, at}` (direction derived
from the CBT<KBT<IBT ordering), then a `triggered_by` edge from each `triggering_evidence` node id and an
`applies_to` edge to `governance_node_id` when given. Returns the new node id. `to_dict` gains a
`trust_transitions` list: `{id, from_level, to_level, direction, at, triggering_evidence:[node_ids],
governance_node_id}` derived from the `trust` nodes + their edges (back-compat: `nodes`/`edges` unchanged).

### Unit Tests

- `tests/test_genome_trust_transitions.py`:
  - `test_record_promotion_sets_direction` - CBT->KBT records `direction == "promotion"`; KBT->CBT records `demotion`.
  - `test_transition_links_evidence_and_governance` - the trust node has `triggered_by` edges from each evidence node and an `applies_to` edge to the governance node.
  - `test_to_dict_surfaces_trust_transitions` - `to_dict()["trust_transitions"]` carries the from/to/direction/evidence/governance fields for a recorded transition.
  - `test_invalid_trust_level_rejected` - an unknown level raises `ValueError`.

## Phase 2: federation-peer emitter

### Affected Files

- `qor/scripts/shadow_genome_graph.py` - add `PeerState` enum, a `peer` JSONL op, `set_federation_peer(...)`, and `federation_peers` in `to_dict`.
- `tests/test_genome_federation_peers.py` (NEW).

### Changes

Add `class PeerState(str, Enum)`: `SYNCED` / `SYNCING` / `STALE` / `DEGRADED` / `INCOMPATIBLE` /
`UNAUTHORIZED` / `OFFLINE`. Add a `peer` op handled in `_apply` (maintains `self.peers: dict[str, dict]`,
latest-wins by peer id). Add:
```python
def set_federation_peer(self, peer_id, *, name, state, last_sync=None, origin=None) -> None:
```
which appends `{"op": "peer", "id", "name", "state", "last_sync", "origin"}`. `to_dict` gains
`federation_peers`: the current `{id, name, state, last_sync, origin}` per peer (latest record wins).
Append-only: each call is a new record; the derived view reflects the latest.

### Unit Tests

- `tests/test_genome_federation_peers.py`:
  - `test_set_peer_surfaces_in_to_dict` - a set peer appears in `to_dict()["federation_peers"]` with all fields.
  - `test_latest_state_wins` - two `set_federation_peer` calls for the same id -> `to_dict` shows the latest state (append-only, latest-wins derivation).
  - `test_peer_persists_across_reload` - reopening the graph from JSONL replays the peer op (persistence).
  - `test_invalid_peer_state_rejected` - an unknown state raises `ValueError`.

## Phase 3: failure-node maturity (annotate + derive)

### Affected Files

- `qor/scripts/shadow_genome_graph.py` - add `MaturityStage` enum, a `maturity` op, `annotate_failure_maturity(...)`, `derive_maturity_stage(...)`, and maturity on failure nodes in `to_dict`.
- `tests/test_genome_failure_maturity.py` (NEW).

### Changes

Add `class MaturityStage(str, Enum)`: `OBSERVED` / `CLASSIFIED` / `CONSTRAINT_EXTRACTED` / `DETECTABLE` /
`ENFORCED` / `VERIFIED`. Add a `maturity` op (maintains `self.maturity: dict[str, dict]`, latest-wins per
failure node id). Add:
```python
def annotate_failure_maturity(self, failure_node_id, *, classified=None, constraint_id=None,
                              detector_id=None, enforced_by=None, verified_window=None) -> None:
```
appending `{"op": "maturity", "node": failure_node_id, ...fields}`. Add a pure
`derive_maturity_stage(annotation: dict) -> MaturityStage` mapping the highest satisfied field to a stage
(`verified_window`->VERIFIED, else `enforced_by`->ENFORCED, else `detector_id`->DETECTABLE, else
`constraint_id`->CONSTRAINT_EXTRACTED, else `classified`->CLASSIFIED, else OBSERVED). `to_dict`'s failure
nodes gain a `maturity` field = `{stage, ...annotation}` (OBSERVED when un-annotated).

### Unit Tests

- `tests/test_genome_failure_maturity.py`:
  - `test_derive_stage_ladder` - each field combination derives the correct stage (verified > enforced > detectable > constraint > classified > observed).
  - `test_unannotated_failure_is_observed` - a failure node with no maturity annotation derives `OBSERVED`.
  - `test_annotation_surfaces_on_failure_node` - `to_dict` attaches `maturity.stage` + the annotation fields to the annotated failure node, and only to failure nodes.
  - `test_annotate_non_failure_rejected` - annotating a non-failure node raises `ValueError`.

## Phase 4: doctrine update

### Affected Files

- `qor/references/doctrine-shadow-genome-graph.md` - update the "Scope boundary" section: the trust / federation / maturity producers are now IN scope (consumer = a sibling governance repository #196 / #213), emitter-API + derive model; record the append-only handling.

## Definition of Done

### Deliverable: D-genome-producers

- **D1**: the Shadow Genome graph emits trust-transition events, federation-peer status, and failure-node maturity, so the sibling governance repository's render-ready surfaces are sourced.
- **D2**: `record_trust_transition` / `set_federation_peer` / `annotate_failure_maturity` + `derive_maturity_stage` exist and are append-only; `to_dict` gains `trust_transitions` + `federation_peers` and maturity on failure nodes; `nodes`/`edges` unchanged (back-compat).
- **D3**: ledger SEAL records #213 closed; the doctrine "Scope boundary" is updated (consumer now exists).
- **D4**: `test_record_promotion_sets_direction` + `test_to_dict_surfaces_trust_transitions` + `test_latest_state_wins` + `test_derive_stage_ladder` + `test_annotate_non_failure_rejected`.

## CI Commands

- `python -m pytest tests/test_genome_trust_transitions.py tests/test_genome_federation_peers.py tests/test_genome_failure_maturity.py tests/test_shadow_genome_graph.py -q` -- new + existing genome tests (run twice).
- `python -m pytest -q` -- full suite green.
