# AUDIT REPORT

**Tribunal Date**: 2026-07-13T09:41:58Z
**Target**: docs/plan-qor-phase186-provenance-autodetect.md (Phase 186; GH #242 host half)
**Risk Grade**: L1
**Session**: `2026-07-13T0940-f515e2`
**Auditor**: The Qor-logic Judge (solo mode; codex-plugin shortfall event `29770868b5bd...` emitted; no external reviewer configured; audit_risk_score option_b_required: false)
**Verdict**: PASS

---

## VERDICT: PASS

---

### Executive Summary

Empirically-grounded transparency fix: the host-detection signal family comes from a LIVE enumeration inside this very Claude Code session (where `CLAUDE_PROJECT_DIR` -- the only signal the code checks -- is absent while `CLAUDECODE`/`CLAUDE_CODE_*` are present), and the manifest builder gains a fresh-detection fallback so a session that never ran `apply_profile` stops recording unknown. The model half is deferred on the HONEST ground the same enumeration establishes: no ambient model signal exists, so auto-detection would fabricate provenance -- exactly what the no-fabrication discipline forbids. The phase carries a built-in live acceptance: this session's own subsequent gate writes flip from the WARN to `host: claude-code`. No binding-VETO pass fired.

### Audit Results

#### Prompt Injection Pass
**Result**: PASS -- canaries exit 0.

#### Security Pass (L3) / OWASP Top 10 Pass
**Result**: PASS
Env-presence checks only; the ladder ADDS truthful detection without trusting any env VALUE (host is derived from key presence, not content). No fabrication path: both detection layers fall through to "unknown" + the existing WARN.

#### Ghost UI / Razor / Dependency / Feature Coverage Passes
**Result**: PASS -- ~10 net lines; stdlib; exempt.

#### Self-Application Sub-Pass (originating_remediation: GH #242)
**Result**: PASS -- discipline: record what is true, never invent. The plan defers the model half precisely because recording it would require invention; the host half records only what the environment demonstrably declares.

#### Test Functionality Pass
**Result**: PASS
Ladder tests invoke `detect_host` under controlled env and assert the returned host (two red today); the integration test invokes `build_manifest` with no platform marker and asserts BOTH the manifest field and the absence of the WARN (capsys). Live self-application is observable in-session post-implement.

#### Infrastructure Alignment Pass
**Result**: PASS
Anchors verified live: detect_host single-signal at qor_platform.py:33; _detect_host cached-marker-only at ai_provenance.py:61; the provenance schema's free-form host string (no enum, no schema change). The signal family is evidence from THIS session's environment, quoted in the brief. Runtime Contract Walk: 0 findings.

#### Filter-Stage / Orphan / Macro-Architecture Passes
**Result**: PASS -- ladder precedence is a chain; no new modules.

#### Documentation Drift (advisory)
**Result**: clean (minimal tier).

### Violations Found

| ID  | Category | Location | Description |
| --- | -------- | -------- | ----------- |
| (none) | | | |

## Process Pattern Advisory

<!-- qor:veto-pattern-advisory -->

No repeated-VETO pattern detected in the last 2 sealed phases.

### Verdict Hash

SHA256 of this report is recorded as the Content Hash of the META_LEDGER.md GATE TRIBUNAL entry for Phase 186.

---
_This verdict is binding._
