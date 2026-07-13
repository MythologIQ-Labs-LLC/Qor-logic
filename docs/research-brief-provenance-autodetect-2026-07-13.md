# Research Brief

**Date**: 2026-07-13T09:41:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #242 -- ai_provenance auto-detect host/model inside Claude Code
**Scope**: live-session signal enumeration, detection-chain gaps, honest model posture

---

## Executive Summary

Enumerated LIVE inside a real Claude Code session (the strongest evidence this
issue can get): the environment exposes `CLAUDECODE=1` plus a family of
`CLAUDE_CODE_*` variables (ENTRYPOINT, SESSION_ID, EXECPATH, SSE_PORT, ...) --
and `CLAUDE_PROJECT_DIR`, the ONLY signal `qor_platform.detect_host` consults,
is ABSENT. Every provenance manifest written in this working session therefore
warned "host fell back to 'unknown'" while running inside the primary
supported host. No model-identifying variable exists in the live environment
(no ANTHROPIC_MODEL or similar), so model auto-detection has NOTHING honest to
read: `QOR_MODEL_FAMILY` remains the explicit channel and the issue's model
half defers until hosts expose a documented signal.

## Findings

### F1. Live signals (this session; the defect demonstrated on itself)

- Present: `CLAUDECODE=1`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`,
  `CLAUDE_CODE_EXECPATH`, `CLAUDE_CODE_SSE_PORT`, others in the family.
  Absent: `CLAUDE_PROJECT_DIR` (unset in CLI sessions like this one) and ANY
  model identifier. Consequence: dozens of `host fell back to 'unknown'`
  WARNs across this session's own gate writes -- the false-unknown class.

### F2. Detection chain (verified live)

- `qor_platform.detect_host`: `CLAUDE_PROJECT_DIR` -> "claude-code", else
  "unknown". `ai_provenance._detect_host`: reads the CACHED platform marker
  via `qor_platform.current()`; no fresh-detection fallback -- a session that
  never ran `apply_profile` records unknown even when signals are ambient.

### F3. Fix shape

- `detect_host` ladder: `CLAUDECODE` or any `CLAUDE_CODE_*` key or
  `CLAUDE_PROJECT_DIR` -> "claude-code" (the empirical family, most-specific
  first); future host families slot alongside. `_detect_host` falls back to a
  FRESH `detect_host()` when the marker yields nothing. Model: no honest
  source exists -- the WARN text stays, pointing at `QOR_MODEL_FAMILY`; the
  model half of GH #242 defers with this session's enumeration as evidence.
- Schema: host is a free-form string (no enum) -- no schema change.

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| Manifests record the harness host (EU AI Act Art. 13/50 surface) | unknown inside the primary host (demonstrated live) | DRIFT (the fix) |
| No fabricated provenance | Model auto-detection would have to invent a value | MATCH (defer the model half) |

## Recommendations

1. (P0) `detect_host` signal family + `_detect_host` fresh-detection fallback.
2. (P0) Tests: env-ladder cases (CLAUDECODE alone, CLAUDE_CODE_* alone,
   CLAUDE_PROJECT_DIR alone, none), and a build_manifest integration case
   asserting host == "claude-code" without any platform marker.
3. (P1) Record the model-half deferral on GH #242 with the live enumeration.

## Updated Knowledge

The live enumeration itself (F1) is the transferable fact.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
