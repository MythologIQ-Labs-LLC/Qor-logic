# Quarantined gate artifacts

`remediate-iter5.json` and its `.provenance` sidecar were hand-edited, which
bypassed `write_gate_artifact` and broke the Phase 158 provenance binding
(sidecar `payload_sha256` 3e476db8 vs actual 4dd31fad). The proposal was
re-emitted correctly as `remediate-iter6.json`.

They are held here rather than deleted because `audit-iter7.json` -- which IS
committed -- carries `reviews_remediate_gate` pointing at the iter5 path.
Deleting would leave that pointer dangling with no record of what it named.
The iter7 review is superseded by `audit-iter8.json`, which reviews iter6.

They are out of `.qor/gates/` because `gate_provenance.verify_committed` walks
that tree and a broken binding there is a real failure, not a suppressible one.
Relocating states what is true: this is evidence, not a gate artifact.

Recorded at META_LEDGER entry #577 and in the Phase 223 seal, entry #580.
