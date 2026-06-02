# Plan: Citation consumer-trace — executable reachability check

**change_class**: feature

**doc_tier**: standard

**boundaries**:
- limitations: Ships the executable grep-recursive reachability primitive the Phase 83 consumer-trace sub-check specified but never built. `citation_consumer_trace.trace_reachable(repo_root, entry_path, symbol)` greps the entry-point file for the symbol and, if absent, follows the file's in-repo import targets (Python `import`/`from` + JS/TS `from '...'` / `require('...')`) recursively up to a depth bound, returning whether the symbol is reached. The auditor supplies the (entry-point, symbol) pair from the Locked Decision under review (matching the existing operator-driven prose procedure); the check does not auto-extract claims from free-form plan text.
- non_goals: A full call-graph / AST resolver (this is a lexical grep-recursive trace, per the issue's framing); cross-repo tracing; auto-discovery of which plan citations to trace; replacing the operator's identification of the entry-point surface.
- exclusions: A missing entry-point file is a SKIP (exit 0 + notice), not a false "unreachable". Non-code citations (docs, env vars) are out of scope for the trace.

## Open Questions

None. The check is operator-driven (entry-point + symbol supplied per LD), exactly as the Phase 83 prose procedure already is; this phase makes the grep step a runnable command instead of a manual grep. Depth bound + visited-set prevent runaway/cyclic import recursion.

## Feature Inventory Touches

(`docs/FEATURE_INDEX.md` absent; declared for traceability. Touches `qor/scripts` + skill reference + tests.)

- entry_id: `n/a` · operation: `NEW` · test_path: `tests/test_citation_consumer_trace.py` · test_descriptor: `trace_reachable returns True when the symbol is defined in the entry file or in a file transitively imported from it, and False (-> finding) when the symbol exists only in an un-imported file; missing entry file -> skip`

## Phase 1: Reachability primitive + CLI (`qor/scripts/citation_consumer_trace.py`)

### Affected Files

- `tests/test_citation_consumer_trace.py` - NEW. Behavioral positive/negative fixtures over synthetic files (see Unit Tests). Written first; red before the module exists.
- `qor/scripts/citation_consumer_trace.py` - NEW. Import resolution + recursive grep trace + `main(argv)` dispatchable via `qor-logic scripts citation_consumer_trace`.

### Changes

```python
@dataclass(frozen=True)
class TraceResult:
    reachable: bool
    skipped: bool          # entry file absent / not a code file
    visited: tuple[str, ...]  # files walked (for the audit report)

_PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)
_JS_IMPORT_RE = re.compile(r"""(?:from|require\()\s*['"]([^'"]+)['"]""")

def resolve_imports(text: str, base_file: Path, repo_root: Path) -> list[Path]:
    """In-repo files imported by base_file (Python dotted modules under repo_root
    + JS/TS relative paths resolved against base_file's dir). Out-of-repo /
    stdlib / node_modules imports are dropped."""

def trace_reachable(repo_root: Path, entry_path: Path, symbol: str,
                    max_depth: int = 5) -> TraceResult:
    """BFS from entry_path: a file 'reaches' the symbol if `\bsymbol\b` appears
    in it; else recurse into resolve_imports() up to max_depth (visited-set
    guards cycles). skipped=True when entry_path is absent."""

def main(argv: list[str] | None = None) -> int:
    """--repo-root PATH --entry PATH --symbol NAME [--max-depth N]. Exit 1 +
    print an `infrastructure-mismatch` finding when the symbol is NOT reachable
    from a present entry file; exit 0 when reachable OR when the entry file is
    absent (skip notice)."""
```

De-complecting: `resolve_imports` (pure parse) is separate from `trace_reachable` (BFS policy) and `main` (process/exit). The trace is lexical (`\bsymbol\b` grep), matching the Phase 83 "grep the reachability" step — not an AST call-graph.

### Unit Tests

- `tests/test_citation_consumer_trace.py::test_symbol_in_entry_file_reachable` - entry file defines `def foo`; `trace_reachable(root, entry, "foo")` -> `reachable=True`.
- `::test_symbol_via_transitive_import_reachable` - entry imports `pkg.mid`, which imports `pkg.leaf`, which defines `target_sym`; `trace_reachable` reaches it (depth>1).
- `::test_symbol_in_unimported_file_unreachable` - `target_sym` defined only in `pkg.orphan` that nothing imports from entry; `reachable=False`.
- `::test_missing_entry_file_skips` - nonexistent entry path; `TraceResult.skipped is True`, `reachable is False` (not a false positive).
- `::test_resolve_imports_drops_stdlib_and_external` - a file importing `os`, `json`, `react`, and `qor.scripts.x`; `resolve_imports` returns only the in-repo `qor/scripts/x.py` path.
- `::test_cycle_does_not_hang` - two files importing each other, symbol absent; `trace_reachable` terminates and returns `reachable=False` (visited-set guard).
- `::test_main_exit_1_on_unreachable` - synthetic repo where the symbol is orphaned; `main(["--repo-root", r, "--entry", e, "--symbol", s])` returns 1.
- `::test_main_exit_0_when_reachable` - reachable case; `main` returns 0.
- `::test_main_exit_0_skip_on_missing_entry` - absent entry; `main` returns 0 and prints a `SKIP` notice.

## Phase 2: Wire into the Phase 37 pass

### Affected Files

- `tests/test_citation_consumer_trace_wiring.py` - NEW. Asserts the phase37 reference names the runnable command (prompt-contract).
- `qor/skills/governance/qor-audit/references/phase37-subpasses.md` - in the consumer-trace sub-check, replace the manual "Grep the reachability" step with the runnable command `qor-logic scripts citation_consumer_trace --entry <surface-file> --symbol <cited-symbol> --repo-root .` (exit 1 => the `infrastructure-mismatch` VETO); keep the operator's entry-point identification + verdict prose.

### Changes

The sub-check stays operator-driven for identifying the entry-point + symbol (Step 1), but Step 2 ("Grep the reachability") becomes the executable command instead of a manual grep, and Step 3's verdict keys on its exit code. No change to the binding VETO category.

### Unit Tests

- `tests/test_citation_consumer_trace_wiring.py::test_phase37_names_runnable_trace` - read `phase37-subpasses.md`; assert it contains `citation_consumer_trace` with both `--entry` and `--symbol` (the manual-grep step is now runnable).

## Definition of Done

### Deliverable: executable consumer-trace check

- **D1**: the Phase 83 consumer-trace "grep the reachability" step is a runnable command, not prose; an unreached citation is detectable by exit code.
- **D2**: `qor/scripts/citation_consumer_trace.py` with `resolve_imports`, `trace_reachable`, `main`; dispatchable as `qor-logic scripts citation_consumer_trace`.
- **D3**: phase37-subpasses.md updated to the runnable command; META_LEDGER seal entry; version bump.
- **D4**: `tests/test_citation_consumer_trace.py::test_symbol_via_transitive_import_reachable` + `::test_symbol_in_unimported_file_unreachable` + `::test_main_exit_1_on_unreachable` + `tests/test_citation_consumer_trace_wiring.py::test_phase37_names_runnable_trace`.

## CI Commands

- `python -m pytest tests/test_citation_consumer_trace.py tests/test_citation_consumer_trace_wiring.py -q` — primitive + wiring.
- `python -m qor.cli scripts citation_consumer_trace --repo-root . --entry qor/cli.py --symbol _do_governance_index` — self-check: a real reachable symbol returns 0.
- `python -m pytest -q` — full suite green before substantiate.
