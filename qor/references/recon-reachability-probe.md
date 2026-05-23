# Reference: Recon Reachability Probe (Phase 96, GH #108)

Detailed protocol for the V1 reachability probe wired into
`/qor-deep-audit-recon` Phase 3 Round 0. Progressive-disclosure
companion to the inline SKILL.md summary (per GH #92 doctrine).

## Purpose

`/qor-deep-audit-recon`'s Phase 1-3 vectors historically accepted
**grep-shaped evidence** (file exists, symbol defined, command
registered, claim string present) as sufficient proof to grade a code
surface HIGH severity. The recon never validated the runtime contract.
The consequence is **zombie code** — live registrations + production-
style invocations pointing at a layer whose runtime is broken — grading
the same as production code.

The reachability probe runs five checks against each cited surface
before HIGH/production-critical grading is permitted to persist past
Phase 3.

## The five checks

### 1. Importability

The cited symbol must be importable from a clean Python process using
the project's actual path setup.

- Operative test: `python -c "from <module> import <symbol>"` (or
  `python -c "import <module>"` when `symbol` is absent) run from the
  repository root with `cwd` set to the project root.
- Pass: subprocess returns exit code 0.
- Fail: emit `reachability-importability-failed`. Detail includes the
  trailing lines of stderr.

### 2. Test collection

At least one test exercising the surface must collect cleanly under the
project's standard test runner.

- Heuristic for test discovery: walk `tests/` for files containing the
  module name or symbol name in their source text.
- Operative test: for each candidate, run `pytest --collect-only -q
  <candidate>`; the check passes if at least one collects with exit 0.
- Fail mode 1: no candidate test file references the surface — emit
  `reachability-test-collection-failed` with detail "no test file
  references this module/symbol".
- Fail mode 2: candidates exist but none collect cleanly — emit the
  same category with detail "N candidate test file(s) failed to
  collect".

### 3. Caller graph

At least one production code path (non-test, non-scratch, non-doc) must
import or invoke the cited surface.

- Filter for "production": exclude any path containing `tests`, `test`,
  `.agent`, `.claude`, `.qor`, or `docs` in its parts. Exclude the
  cited file itself (self-import doesn't count).
- Operative test: walk `*.py` in the repo, read each candidate's text,
  match the module or symbol name as a substring.
- Pass: any production file matches.
- Fail: emit `reachability-no-production-caller` with detail naming
  the unreachable module.

### 4. Packaging

The cited file path must be included in the production build manifest.

- For Python projects, the default manifest is `pyproject.toml`.
- Operative test: read the manifest text and check whether the
  top-level package name (first dotted component of the module) OR the
  full file path appears in the text.
- Fail mode 1: manifest does not exist — emit
  `reachability-packaging-missing` with detail "manifest not found at
  <path>".
- Fail mode 2: manifest exists but does not reference the package —
  emit the same category with detail naming the missing top-level
  package.

For non-Python projects, pass `--manifest <path>` to point the probe at
the project-appropriate manifest (Tauri `tauri.conf.json` files,
Docker `COPY` directives in a Dockerfile, etc). V1 expects the
manifest to be a text file whose contents can be substring-matched.

### 5. Interface match

The call site's invocation arity must match the called module's current
export.

- Skipped when `claim.symbol` or `claim.call_site` is absent (interface
  match needs both to compare).
- Operative test: parse the called module with `ast.parse`, locate the
  matching `FunctionDef` / `AsyncFunctionDef` / `ClassDef`, extract its
  positional arg names. Then read the call-site file as text, match
  `<symbol>(...)` invocations via regex, extract the positional arg
  names from the invocation.
- Pass: same arity.
- Fail mode 1: symbol not found in module — emit
  `reachability-interface-mismatch` with detail "symbol not found".
- Fail mode 2: call site does not invoke the symbol — emit the same
  category with detail "call site does not invoke <symbol>".
- Fail mode 3: arity mismatch — emit with detail "signature drift:
  module exports (...) but call site invokes (...)".

ClassDef matches always pass at V1 (class signatures are harder to
compare reliably without instantiation tracing).

## Downgrade rule

Any single failing check means the finding cannot retain a HIGH or
production-critical grade in V1. The recon brief author must:

1. Annotate the finding with `reachability-gap` classification.
2. Cite the failing probe category in the brief's evidence column.
3. Either gather end-to-end runtime evidence (re-run probe after the
   gap is closed) or downgrade the finding's severity.

V1 is WARN-only at the CLI level — the probe exits 0 by default even
with findings present. Phase 99 V2 layers blocking enforcement in
`/qor-audit` Step 3 Infrastructure Alignment Pass.

## Invocation

```bash
# Run probe against a single claim or list:
python -m qor.scripts.reachability_probe --claims path/to/claims.json

# Opt in to CI-style failure exit:
python -m qor.scripts.reachability_probe --claims path/to/claims.json --exit-on-any

# Override the manifest path for non-Python projects:
python -m qor.scripts.reachability_probe --claims claims.json --manifest tauri.conf.json
```

Claims-file format (JSON; one object or array):

```json
[
  {
    "module": "qor.scripts.skill_size_budget_lint",
    "symbol": "check_skills",
    "file_path": "qor/scripts/skill_size_budget_lint.py",
    "call_site": "qor/scripts/some_caller.py:42"
  }
]
```

`symbol` and `call_site` are optional. `module` and `file_path` are
required.

## Originating case study: COREFORGE Phase 371

Per GH #108, Phase 371 of the COREFORGE data-protection foundation
remediation graded `DPF-LIE-01` (persona IPC envelope claims
AES-256-GCM but no cipher code path exists) as HIGH severity purely on
grep evidence:

- `src/personas/constants.py:11` declares
  `DEFAULT_IPC_ENCRYPTION_SCHEME = "AES-256-GCM"`.
- `src/personas/ipc.py` schema includes `EncryptionMetadata` fields.
- Zero matches for `aesgcm.encrypt` in the package.

Plan, audit, and implement cycles all consumed cycle cost on a HIGH-
graded finding. Only at implementation time did the test author
discover:

- `src/personas/communication.py:21-25` imports `PersonaIPCBridge`,
  `PersonaIPCEnvelope`, `PersonaChannel`, `PersonaHandshake` from
  `.ipc` — none of them defined in current `src/personas/ipc.py`.
  Runtime import would fail.
- `src/personas/alden.py:33` imports `main` — module does not exist
  in repo.
- `tests/test_persona_ipc.py` has `from __future__ import annotations`
  not at file top — collection fails on `SyntaxError`.
- Zero non-test importers of `src/personas/` from any production code
  path.
- Production Python sidecar (invoked from Rust
  `src-tauri/src/alden_legacy.rs`) uses `python/cli/*.py`, not
  `src/personas/`.

The Phase 96 V1 reachability probe would have caught this at recon
time across all five checks: importability fails, test collection
fails (SyntaxError), caller graph fails (no production caller),
packaging fails (entire `src/` tree marked abandoned per PR #223),
interface match fails (call site imports symbols not exported).

Operator framing preserved from the original COREFORGE Phase 371
cycle:

> "So the right classification is not 'dead code, ignore it.' It is
> **zombie legacy code with live command registration and broken
> runtime/import packaging.**
>
> Claude caught a real implementation risk, but the summary is too
> blunt. The actual failure is governance-level: the audit accepted
> grep-shaped evidence for a runtime path without proving
> importability, command registration, packaging, and test inclusion
> end to end."

## Cross-references

- `qor/references/doctrine-shadow-genome-countermeasures.md` —
  `SG-GrepShapedRunclaim-A` doctrine entry (binding).
- `qor/skills/meta/qor-deep-audit-recon/SKILL.md` — Phase 3 Round 0
  wiring point.
- `qor/scripts/reachability_probe.py` — the V1 probe module.
- `tests/test_reachability_probe.py` — behavior + dogfooding tests.
- `docs/plan-qor-phase96-recon-reachability-probe.md` — the sealed
  Phase 96 plan.
- GH #108 — originating issue.
- Future Phase 99 — V2 enforcement in `/qor-audit` Step 3
  Infrastructure Alignment Pass.
