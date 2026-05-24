# Reference: Audit Runtime Contract Walk (Phase 99, GH #108 V2)

Detailed protocol for the V2 import-graph walk wired into `/qor-audit`
Step 3 Infrastructure Alignment Pass. Progressive-disclosure companion
to the inline SKILL.md summary (per `SG-SkillCorpusGrowth-A`).

## Purpose

Phase 96 V1 (`reachability_probe`) catches grep-shaped recon claims
BEFORE plan authoring. Phase 99 V2 catches grep-shaped plan claims at
AUDIT time, after plan but before implement. Same defect class
(grep-shaped runclaim) at a different lifecycle phase requires a
different mechanism:

- V1 probe (recon): five-check per-claim (importability, test
  collection, caller graph, packaging, interface match).
- V2 walk (audit): two-direction import-graph walk per plan-cited
  module (forward callees, backward callers).

## The two-direction walk

### Forward walk (callees)

For each Python module path cited in the plan:

1. Locate the module file on disk (`qor/path/to/<module>.py` or
   `qor/path/to/<package>/__init__.py`).
2. Parse it with `ast.parse`. If syntax error: emit
   `forward: cited module fails to parse: SyntaxError: ...`
3. Walk the AST for `Import` and `ImportFrom` nodes; collect every
   `qor.*` module the cited module depends on.
4. For each `qor.*` dependency: subprocess `python -c "import X"`
   from the repo root. If non-zero exit: emit
   `forward: callee 'X' fails import: <stderr-tail>`

### Backward walk (callers)

For each Python module path cited in the plan:

1. Walk the repo's `*.py` files filtering OUT `tests/`, `test/`,
   `.agent/`, `.claude/`, `.qor/`, `docs/` (anything non-production).
2. Skip the cited module file itself (self-import doesn't count).
3. For each remaining production .py file: read text, check if the
   module path appears as a substring, then `ast.parse` to confirm
   the caller itself parses cleanly.
4. The check passes if at least one parseable production caller
   exists.
5. Otherwise emit `backward: no production caller imports/invokes <module>`.

## WARN ramp rationale

V2 ships WARN-only because Phase 96 V1 has not yet accumulated
operator evidence on false-positive rate (same-session cluster).
Per the cluster's V1/V2 split discipline (Phases 89-95), WARN-only
ramps protect against new lints blocking legitimate work when their
heuristics are untested in production.

The conservative wiring at `/qor-audit` Step 3 uses `|| true` to
swallow non-zero exits from the walk. The walk's `--exit-on-any`
flag IS available so operators can promote it to a hard fail in
their own CI environments.

A future V2-of-V2 phase will:
1. Gather operator evidence on V1 false-positive rate.
2. Tune V2 walk thresholds and skip rules.
3. Remove the `|| true` wrap at the audit-site.
4. Convert the walk to a hard VETO with the
   `runtime-contract-mismatch` category.

## Invocation

```bash
# Default WARN-only (V2 ramp):
python -m qor.scripts.runtime_contract_walk --plan path/to/plan.md

# Opt in to hard-fail exit (operator CI hardening):
python -m qor.scripts.runtime_contract_walk --plan path/to/plan.md --exit-on-any

# Override the repo root if needed:
python -m qor.scripts.runtime_contract_walk --plan path/to/plan.md --repo-root /path/to/repo
```

Walk-finding format on stdout:

```
runtime_contract_walk: N finding(s)
  [WARN] forward: qor.scripts.foo -- callee 'qor.scripts.bar' fails import: ModuleNotFoundError
  [WARN] backward: qor.scripts.baz -- no production caller imports/invokes qor.scripts.baz
```

## Cross-references

- `qor/scripts/runtime_contract_walk.py` — the V2 walk module.
- `qor/references/doctrine-shadow-genome-countermeasures.md`
  `SG-GrepShapedRunclaim-A` — binding doctrine (V1 + V2).
- `qor/skills/governance/qor-audit/SKILL.md` Step 3 Infrastructure
  Alignment Pass — V2 wiring site.
- `qor/scripts/reachability_probe.py` — Phase 96 V1 (recon-side
  five-check probe).
- `qor/references/recon-reachability-probe.md` — V1 detailed protocol.
- `docs/plan-qor-phase99-audit-runtime-contract-walk.md` — sealed
  Phase 99 plan.
- GH #108 — originating issue (closed at Phase 99 substantiate).
