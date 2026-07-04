# Research Brief: Evidence Reconstruction over Ceremony Artifacts (GH #251)

**Date**: 2026-07-04
**Analyst**: The Qor-logic Analyst
**Target**: GH #251 -- reconstruct audit evidence on demand from signals already recorded; freeze net-new ceremony artifacts (perspective-reset rec 5; MS agent-governance-toolkit ADR 0018 posture)
**Scope**: per-session signal inventory, existing assemblers, the freeze rule's smallest executable form

---

## Executive Summary

Every sealed phase already leaves eight independently-locatable evidence signals, all joinable from a session id or phase number: the ledger seal entry (extract via `gate_chain_completeness._extract_seal_sessions`, :34-49), gate artifacts + provenance sidecars (`.qor/gates/<sid>/`; verify via `gate_provenance.verify_sidecar`, :127-150), `audit_history.jsonl`, the intent-lock record (`.qor/intent-lock/<sid>.json`, intent_lock.py:66-139), shadow events filtered by session_id, the CHANGELOG release section, and the seal commit + tag in git. Partial assemblers exist (`compliance do_ai_provenance` walks a session's phases, compliance.py:55-74; `status_json` defines the final-line JSON contract) -- what is missing is ONE verb that joins all signals into a bundle with an explicit completeness field. For the freeze rule, the smallest executable form follows the Phase 166 lint model: a registry of approved gate schemas + a lint flagging net-new `qor/gates/schema/*.schema.json` files that lack a plan-declared justification, WARN-only in V1 in the audit Step 0.6 ladder.

## Findings

1. **Signal inventory (join keys verified)**: session_id joins gates dir, sidecars, audit_history, intent-lock, session key, and shadow events; phase number joins the ledger seal entry (and via it the session id); version joins CHANGELOG; the seal commit is locatable by tag `v<version>` or ledger-cited Merkle seal. Paths from qor/workdir.py:35-52.
2. **Existing assemblers**: `do_ai_provenance` (compliance.py:55-74) already walks `.qor/gates/<sid>/` per phase -- the shape to generalize; `seal_entry_check._parse_latest_entry` (:49-69) parses entry fields; `status_json` (Phase 165) provides the output contract (`schema_version/ts/.../overall` + final-line JSON).
3. **No new ceremony needed**: the bundle is pure reconstruction -- zero new per-phase writes, which is itself the ADR-0018 point. Completeness is reported, never fabricated (missing signals are named, mirroring the toolkit's partial-reconstruction surfacing).
4. **Freeze rule seam**: gate-artifact schemas live only in `qor/gates/schema/*.schema.json`; `write_gate_artifact` validates against them by phase name. A `SCHEMA_REGISTRY.json` baseline (current inventory) + `gate_schema_freeze_lint` (compare directory vs registry; unregistered schema without a plan-declared `new_ceremony_artifacts` justification -> WARN, exit 1 for the ladder's `|| true`) is the sg_closure_lint-shaped smallest form.

## Recommendations

1. **Phase 169 ships**: (a) `qor/scripts/evidence_bundle.py` -- `--session <sid>` or `--phase <N>` (resolved via the ledger), assembling `{schema_version, ts, query, signals:{ledger_entry, gate_artifacts, provenance, audit_history, intent_lock, shadow_events, changelog, seal_commit}, completeness:{found, missing[]}}` as the final stdout line (status_json contract); exit 0 iff the query resolved (completeness may be partial -- reported, not failed); (b) `qor/gates/SCHEMA_REGISTRY.json` baselined from the current schema directory; (c) `qor/scripts/gate_schema_freeze_lint.py` WARN-only in the audit Step 0.6 ladder; (d) plan.schema.json optional `new_ceremony_artifacts` (name + justification >= 100 chars); (e) doctrine rule via /qor-document.
2. git-derived signals (seal commit/tag) are best-effort with `found:false` off-repo -- the bundle never requires network.
3. V2 (deferred): freeze-lint WARN->FAIL flip; markdown/csv formatters.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
