# Research Brief

**Date**: 2026-07-13T10:32:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #243 -- doctrine: negative rules for skills running below design tier
**Scope**: negative-rules doctrine, dist_compile injection surface, model_pinning_lint extension

---

## Executive Summary

GH #243 is fully unimplemented (no PR references it; no negative-rules doctrine, no
injection layer, no fabrication-guard lint exist). The issue's empirical finding: weak-tier
models follow positive skill structure but infer implicit negative constraints poorly --
mandatory definition/rationale slots became a secret-reproduction vector and a fabrication
vector in controlled A/B evals. Every load-bearing surface was verified against source; the
smallest compliant shape is a doctrine file + a deterministic compile-time preamble injection
for the three fabrication-risk governance skills in the kilo-code/codex/gemini variants +
a WARN-only model_pinning_lint extension.

## Findings

### dist_compile is identity for claude/kilo-code/codex; gemini has its own emitter
- qor/scripts/dist_compile.py:47-61 `emit_claude` (copytree/copy2, no transformation)
- qor/scripts/dist_compile.py:64-71 `emit_kilocode`/`emit_codex` delegate to `emit_claude`
- qor/scripts/dist_compile.py:104-106 gemini via `gemini_variant.emit_gemini`
- The module docstring (lines 4-5) is STALE ("codex writes only a .gitkeep stub") -- code
  identity-copies; tests/test_compile.py:74-81 locks codex==claude.

### Drift check regenerates through compile_all, so deterministic injection stays green
- qor/scripts/check_variant_drift.py:58-66 regenerates into a tempdir via
  `compile_mod.compile_all(tmp_path)` and hash-diffs against committed qor/dist
  (manifest.json excluded, line 22). Injection implemented INSIDE dist_compile is applied
  identically on both sides; one recompile+commit keeps the gate green.

### install_drift_check mirrors installs against SOURCE, not dist
- qor/scripts/install_drift_check.py:29-54 compares installed SKILL.md sha256 against
  `qor/skills/**` source. The claude variant is the layout installs mirror; injecting into
  the claude variant would manufacture permanent drift warnings. Injection therefore
  targets kilo-code/codex/gemini only -- which is precisely the issue's own risk framing
  ("per-host deployment (kilo/codex/gemini) ... make weak-tier execution likely").

### Source-SKILL.md headroom forbids inline rules in the two big governance skills
- tests/test_substantiate_staging_gates.py:48-62 locks qor-audit + qor-substantiate under
  HEADROOM_BYTES = 39*1024; current sizes 39,355 and 39,321 bytes leave ~600 bytes --
  an inline rules block does not fit. Compile-time injection sidesteps the budget (the
  size lint at seal walks --skills-root qor/skills only).

### model_pinning_lint shape supports a clean extension
- qor/scripts/model_pinning_lint.py:27-36 frontmatter regexes; :48-52
  `extract_capability_tier`; the check walks qor/skills/**/SKILL.md and emits WARN-only
  (exit 0). A fabrication-guard scan is an additive warning source in the same walk.

### Fabrication-risk skills and their pins
- qor/skills/governance/qor-audit/SKILL.md:19 `min_model_capability: opus`
- qor/skills/governance/qor-substantiate/SKILL.md:19 `min_model_capability: opus`
- qor/skills/sdlc/qor-plan/SKILL.md:18 `min_model_capability: opus`
- All three demand verdict/rationale/justification slots; none carries any negative rule
  (grep for never-reproduce/anti-fabrication forms: 0 production matches).

### Governance-index registration is fail-closed for new doctrine files
- docs/GOVERNANCE_INDEX.md tier tables register 7 doctrine rows; substantiate Step 4.7.5
  fail-closes on `unregistered`. The new doctrine MUST be registered at authoring time.

## Blueprint Alignment

| Blueprint Claim | Actual Finding | Status |
|----------------|---------------|--------|
| dist_compile v1 "codex writes only a .gitkeep stub" (docstring) | codex identity-copies claude (dist_compile.py:69-71; test_compile.py:74-81) | DRIFT (stale docstring; correct it in-phase) |
| Skills carry min_model_capability enforcement | WARN-only lint wired at /qor-plan Step 0.3 | MATCH |
| No negative-rules surface exists | 0 matches corpus-wide | MATCH (gap confirmed) |

## Recommendations

1. (P1) Author `qor/references/doctrine-negative-constraints.md`: NR-001 secret-shapes rule
   (never reproduce secret-shaped strings; refer by prefix/descriptor) + NR-002
   no-fabrication rule (mandatory slot without a source fact -> write "not established";
   never invent). Register in docs/GOVERNANCE_INDEX.md.
2. (P1) dist_compile: `_inject_negative_constraints(skill_md, target)` -- for targets
   kilo-code/codex/gemini and skills in `_FABRICATION_RISK_SKILLS` ({qor-audit, qor-plan,
   qor-substantiate}), insert a deterministic preamble block after frontmatter. Fix the
   stale docstring. Recompile dist; check_variant_drift green.
3. (P2) model_pinning_lint: WARN when a fabrication-risk skill's SOURCE lacks a guard
   pointer (the injected variants carry the rules; the source carries a one-line doctrine
   pointer OR the lint recognizes compile-time coverage) -- keep WARN-only.
4. (P3) The gemini emitter transforms format; verify injection composes with it (inject
   before format conversion by passing transformed content into emit paths, or inject
   within gemini_variant equivalently).

## Updated Knowledge

Compile-time content divergence is now a sanctioned dist_compile capability (v1 identity
assumption retired); check_variant_drift symmetry makes deterministic transforms safe.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
