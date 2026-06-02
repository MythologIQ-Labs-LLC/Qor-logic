# Shadow Genome Graph — production-hardening roadmap (GH #164)

Decision record for the five production-hardening capabilities that GH #139 (the
causal-graph core, PR #146, v0.80.0) declined and #164 tracked. Each is decided
here so the roadmap is explicit, not buried. Phase 134 closes #164 with this
record (and ships the one accepted-now capability).

| Capability | Decision | Rationale |
|---|---|---|
| **export** (JSON / DOT) | **SHIPPED** (Phase 134) | Cheap, self-contained, and aligned with "Qor-logic proper": operators and CI can serialize the genome for inspection / diffing / external graph tooling. Implemented as `ShadowGenomeGraph.to_dict/to_json/to_dot` + the `export` CLI subcommand. |
| **dashboard / query-API surface** | **DEFERRED (post-1.0)** | A served query/dashboard API is SaaS-grade product surface, not something a governance-skills *package* needs to be 1.0-complete. The existing `trace` / `query` / `snapshot` CLI already covers programmatic read access. Revisit if a hosted Qor-logic service is built. |
| **trust-transition modeling** | **DEFERRED (post-1.0)** | Modeling trust state transitions over the genome is research-grade and has no current consumer; the shadow-genome's job today is failure causality, not trust scoring. Revisit if a trust/reputation feature is specified. |
| **cross-workspace federation** | **DEFERRED (post-1.0)** | The META_LEDGER already carries the federation primitives (content-addressable Entry IDs, `previous_hash` uniqueness checks). A *graph*-level federation layer is heavy and speculative without a multi-workspace deployment driving it. Revisit alongside a concrete federation use case. |
| **retention / pruning policy** | **DEFERRED (post-1.0)** | The genome is append-only JSONL; growth is real but not yet a measured latency source the way the SKILL.md corpus was (SG-SkillCorpusGrowth-A). Premature pruning risks losing causal history. Revisit when genome size is measured to be a problem; pair with an archival/export step (now available). |

## Status

`export` is the only capability in-scope for the 1.0.0 line; the other four are
post-1.0 roadmap items. None is split into a new open tracking issue (that would
keep the #147 cluster open) — this document IS the durable record, and the
operator can re-prioritize any item into a future phase when a driving use case
appears. Per `qor/references/doctrine-shadow-genome-countermeasures.md` and the
GH #139 causal-graph doctrine.
