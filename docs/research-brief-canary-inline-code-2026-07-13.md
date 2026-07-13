# Research Brief

**Date**: 2026-07-13T11:46:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #244 -- canary inline-code false positives + dist_compile host expansion
**Scope**: prompt_injection_canaries code-span handling; hosts.py + dist_compile target matrix

---

## Executive Summary

Both #244 items verified live; neither is addressed by a merged PR. Item 1: the
`--mask-code-blocks` flag already exists (Phase 53) but the audit site is
DELIBERATELY strict, so the consumer's `` `node <script> --help` `` ABORT is the
documented posture, not a bug -- the remaining gap is per-class nuance (the
hidden-html class is structural, so a code-span hit is a placeholder/example,
while the instruction classes are imperative anywhere). Item 2: hosts.py has an
extensible registry with four hosts and dist_compile has four targets; the
external framework's published adapter matrix maps two new targets cheaply
(Cursor's skills layout is claude-shaped; Cline/Windsurf/Roo share one
flattened command-file layout).

## Findings

### Item 1: canary scanner

- qor/scripts/prompt_injection_canaries.py:98-102 -- the hidden-html canary is
  `<!--\s*system:\s*|<script\b`; `<script\b` matches the placeholder in
  `` `node <script> --help` ``.
- :133-148 -- `mask_code_blocks` + `--mask-code-blocks` exist since Phase 53;
  the docstring records the strict-at-audit rationale ("a canary hidden inside
  backticks would still be detected at the audit gate").
- :106-119 -- `scan` returns spans; a hit's span can be tested against masked
  regions, enabling per-class downgrade WITHOUT changing prose behavior.
- Class asymmetry (the design key): instruction-redirect / role-redefinition /
  pass-coercion / meta-override are imperative sentences -- an LLM reads them
  inside code spans too, so they must stay binding everywhere.
  hidden-html is structural markup: inside a code span it is, with high
  probability, a CLI placeholder or an XSS/countermeasure EXAMPLE, exactly the
  false-positive class the consumer hit.

### Item 2: host expansion

- qor/hosts.py:84-89 -- `_HOSTS` registry (claude, kilo-code, codex, gemini);
  `register_host` (:92) is the third-party seam; the module docstring already
  names Cursor and Windsurf as intended extensions.
- qor/scripts/dist_compile.py:22 -- `TARGETS = ("claude", "kilo-code",
  "codex", "gemini")`; per-target emit dispatch at :131-143.
- External framework's published matrix (generalized): Cursor consumes
  `.cursor/skills/` markdown skill dirs (claude-shaped); Cline, Windsurf, and
  Roo share `.clinerules/workflows/command-<id>.md` (one flattened markdown
  command file per skill); Gemini/Qwen use `.gemini/commands/<id>.toml`
  (already shipped).
- Weak-tier classification: Cursor and the Cline family are exactly the
  below-design-tier deployment channels Phase 187 targets -> both new variants
  receive `inject_negative_constraints` (claude stays the only untransformed
  variant, preserving the install_drift_check mirror).
- tests/test_install_sync_with_source.py checks claude/codex/kilo-code and
  documents the gemini exclusion; new variants need explicit coverage
  (cursor: claude-shaped so sync-testable with injection expectation; cline:
  flattened layout, needs its own content test like gemini).

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| Issue: "exempt code spans from the hidden-HTML class ... or downgrade to WARN with --strict" | masking exists but is all-class and opt-in; no per-class downgrade | MATCH (gap confirmed) |
| Issue: Qor-logic already ships the gemini TOML target | dist_compile.py:22 + gemini_variant.py | MATCH |
| hosts.py docstring names Cursor/Windsurf as extension targets | qor/hosts.py:4-5 | MATCH |

## Recommendations

1. (P1) Per-class code-span downgrade: in the CLI, compute masked regions;
   a hidden-html hit fully inside a masked region prints as
   `CANARY WARN [hidden-html/code-span]` and does NOT count toward exit 1;
   `--strict` restores current behavior. All other classes unchanged.
   `scan()` itself stays pure/strict (audit skills embed the CLI, not scan()).
2. (P1) Add `cursor` (claude-shaped skills layout, `.cursor/skills/`) and
   `cline` (flattened `command-<id>.md` under `.clinerules/workflows/`,
   serving Cline/Windsurf/Roo) to hosts.py `_HOSTS` and dist_compile TARGETS;
   both variants receive the Phase 187 risk-skill injection.
3. (P2) Extend the sync/exclusion tests: cursor joins the injected-sync
   contract; cline gets a content test (frontmatter handling + injection).

## Updated Knowledge

The adapter matrix is now a two-axis surface: layout shape (skill-dir mirror /
flattened command file / TOML command) x transform (identity for claude,
negative-constraints injection for every weak-tier channel).

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
