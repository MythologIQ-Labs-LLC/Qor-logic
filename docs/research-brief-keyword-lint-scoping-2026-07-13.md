# Research Brief

**Date**: 2026-07-13T09:20:00Z
**Analyst**: The Qor-logic Analyst
**Target**: GH #265 -- shadow-genome keyword-only lint keys by bare function name (cross-module false positives)
**Scope**: the collision mechanism, current collisions, resolution rule preserving true positives

---

## Executive Summary

The SG-033 lint (tests/test_shadow_genome_doctrine.py:15-53, verified live)
collects keyword-only functions into a dict keyed by BARE NAME -- last
definition in rglob order silently wins -- and matches call sites by bare
name across all search roots. Two same-named definitions with different
positional arities therefore misattribute call sites: the issue's consumer
reproduction saw 7 false positives when a new module defined a 5-positional
`_emit` colliding with governance_index's 1-positional keyword-only `_emit`.
Live collisions already exist in-tree (`check`: model_pinning_lint vs
override_friction; `scan`: sast_scan vs secret_scanner) -- benign today only
because the colliding arities happen to agree. Resolution rule chosen over
the same-file-only minimum: same-file definitions take precedence; a
tree-unique name is still checked cross-module (preserving today's real
coverage, e.g. tests calling a unique qor/scripts function positionally);
colliding bare names without a same-file definition SKIP as ambiguous.

## Findings

### F1. Mechanism (verified live)

- `_collect_keyword_only_functions` (line 15): `out[node.name] = (...)` --
  last-write-wins on collisions. `_find_positional_violations` (line 35):
  bare-name lookup, one definition consulted per name regardless of the call
  site's module.

### F2. Live collisions

- `check`: model_pinning_lint.py:102 (`repo_root, *, current_model`) vs
  override_friction.py:63 (`session_id, *, threshold, log_path`) -- both
  1-positional, so no CURRENT false positive; any third `check` with a
  different arity flips coin-toss behavior. `scan`: sast_scan.py:86 vs
  secret_scanner.py:140 -- same accident. The issue's `_emit` scenario shows
  the failure the moment arities diverge.

### F3. Resolution rule (decision)

- Multimap `dict[str, list[(path, lineno, positional)]]`. Per call site:
  same-file defs if any; else the single def when the name is tree-unique;
  else skip (ambiguous bare name -- attribute-resolution is the GH #265
  follow-on if ever needed). This strictly dominates same-file-only matching
  on true-positive retention and eliminates the collision false-positive
  class entirely. A violation requires exceeding EVERY consulted candidate's
  positional arity (same-file candidates are same-name overloads across
  scopes -- rare; exceeding all is the honest bar).

## Blueprint Alignment

| Contract claim | Actual finding | Status |
|----------------|---------------|--------|
| SG-033: call sites updated when signatures change | Coin-toss attribution under collisions | DRIFT (the fix) |

## Recommendations

1. (P0) Multimap + three-tier resolution in the lint's two helpers.
2. (P0) Tests: a synthetic collision fixture proving (a) the false-positive
   class is gone, (b) same-file violations still flag, (c) unique-name
   cross-module violations still flag.

## Updated Knowledge

None; lint precision fix inside the test that hosts it.

---

_Research complete. Findings are advisory -- implementation decisions remain with the Governor._
