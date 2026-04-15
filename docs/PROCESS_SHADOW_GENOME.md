# Process Shadow Genome

Append-only log of Qor process failures, gate overrides, and capability shortfalls.

Format: JSONL (one JSON event per line). Schema defined in `qor/gates/schema/shadow_event.schema.json` (authored Phase 4, deferred).

Severity rubric: gate_override=1, capability_shortfall=2, regression=3, hallucination=4, degradation=5.

---

{"ts":"2026-04-15T00:00:00Z","skill":"qor-audit","session_id":"2026-04-15T00:00-bootstrap","event_type":"gate_override","severity":1,"details":{"target":"docs/plan-qor-migration-final.md","audit_report":".agent/staging/AUDIT_REPORT.md","ledger_entry":16,"verdict":"VETO","violation_count":5,"rationale":"Audit loop hit diminishing returns at round 4 (5 violations, flat across round 5). Root cause: plan-whack-a-mole against adversarial judge as prose plan exceeds efficient review surface. User-approved remediation per /qor-debug analysis: (A) cut plan to SSoT migration only (Phases 0/1/1.5/7); (C) override advisory gate, proceed to implementation. Remaining 5 violations carried as known-risk accepted: destinations missing from \u00a72 tree, 21-item ingest collisions, merge-order ambiguity for internal/scripts, deferred R-5/R-6 classifications, over-aggressive CI grep.","carried_violations":["V-1: \u00a72.B destinations not in \u00a72 tree","V-2: 21 ingest/skills vs ingest/scripts collisions","V-3: merge-order ingest/internal/scripts","V-4: R-5/R-6 deferred decisions","V-5: Phase 7 grep matches historical audit refs"],"override_authority":"user"},"addressed":false,"issue_url":null,"addressed_ts":null,"addressed_reason":null,"source_entry_id":null,"id":"a754f6c9d9c850f78fced6f8863f55ac2704cea822e32719872979ad2ccc980d"}
