# Plan: one owned primitive for the ledger's hash-triple markup

**change_class**: hotfix

**doc_tier**: standard

**boundaries**:
- limitations: Extracts the three-line hash-triple markup (`**Content
  Hash**`/`**Previous Hash**`/`**Chain Hash (Merkle seal)**`) that
  `ledger_emit.render`, `ledger_migrate.canonical_block`, and
  `reconcile.append_reconciliation_entry` each currently write independently
  into one primitive in `ledger_emit`, and wires all three through it. It does
  not change any entry's rendered bytes, does not touch `reconcile.py`'s
  heading/field/`Scope` construction (only its trailing hash lines), and does
  not add a writer-side lint/detector.
- non_goals: GH #468's own "Order of work" note flags a broader question --
  whether `ledger_dialect` should grow a writer surface at all, and what AST
  sink-rule a future detector should use. Neither is this phase's scope; this
  phase only supplies the primitive the issue's suggested shape already names
  (`hash_block`) and removes the three duplicate copies of its output.
- exclusions: No change to `reconcile.py`'s full-entry shape (no `Decision`
  field, no trailing `---` separator added) -- GH #468's own design comment
  calls that mapping "almost" direct for `reconcile.py`, not exact, and
  changing the RECONCILE entry shape is a separate, unasked-for decision this
  phase does not make. No touch to the two audit-template dialects (#464) or
  the reader-side ownership question (#467).

## Open Questions

None.

## Locked Decisions

### LD-1: the duplication is real and is exactly the hash triple, not the whole entry

Three independent copies of the same three lines exist at this plan's fork
point (`f3e069b`, pre-fix; this phase's own commits remove the duplication
these citations describe). The bodies of the three functions immediately
following each citation below hand-roll the identical hash-triple markup
(backticked source content is not quotable through this tool's own
backtick-stripping evidence grammar, so each citation anchors its function's
signature line rather than the triple's own text):

> `git show f3e069b:qor/scripts/ledger_emit.py | grep -n '^def render'` -> `38:def render(entry: LedgerEntry, *, content: str, previous: str, chain: str) -> str:`
> `git show f3e069b:qor/scripts/ledger_migrate.py | grep -n '^def canonical_block'` -> `111:def canonical_block(content: str, prev: str, chain: str) -> str:`
> `git show f3e069b:qor/scripts/reconcile.py | grep -n '^def append_reconciliation_entry'` -> `98:def append_reconciliation_entry(`

All three bodies format the triple identically: a `Content Hash` line, a
`Previous Hash` line, and a `Chain Hash (Merkle seal)` line, each backticking
its hex value, the first two without a trailing blank line, matching current
bytes exactly.

### LD-2: a block-level primitive, not a forced `render()` call, per the issue's own design comment

GH #468 comment (2026-09-08T17:40:28Z) distinguishes the two call sites:
`reconcile.py` builds a whole entry (heading, fields, hash triple, body) while
`ledger_migrate.py` injects only the hash triple into an already-existing
entry via `_inject`. Forcing `ledger_migrate` through `render()` would need an
entry it does not have; forcing `reconcile.py`'s RECONCILE entries through
`render()` would add a `Decision` field and trailing `---` no existing
RECONCILE entry carries. The comment's own suggested shape is a primitive
`render()` itself calls:

> "So the owner surface needs a **block-level primitive** that `render` itself
> calls: `def hash_block(content, previous, chain) -> str: ...`"

`ledger_emit.hash_block(content, previous, chain)` returns exactly the
three-line block above. `render()` is refactored to build its hash-triple
lines by calling `hash_block()` (same output, single source). `canonical_block`
in `ledger_migrate.py` becomes a delegating call to `ledger_emit.hash_block`
(kept as a named function since nothing outside `ledger_migrate.py` needs to
change its import). `reconcile.append_reconciliation_entry`'s trailing three
lines are built by calling `ledger_emit.hash_block` instead of an inline
f-string.

### LD-3: a wiring test proves delegation, not merely matching output

A black-box string-equality test cannot distinguish "delegates to the shared
primitive" from "independently produces the same string" -- both read
identically before and after this phase. Per this repo's own established
wiring-test pattern (`tests/test_substantiate_tag_ci_gate_wiring.py`), each of
the two call sites gets a monkeypatch-based test that replaces
`ledger_emit.hash_block` with a sentinel-returning stub and asserts the
sentinel appears in that call site's own output. This is red against the
current hand-rolled code (the sentinel cannot appear; nothing calls the stub)
and green only once the call site actually delegates.

## CI Commands

- `python -m pytest tests/test_ledger_emit.py tests/test_ledger_migrate.py tests/test_reconcile.py -q` — the suites owning the changed modules, including the new primitive and wiring tests.
- `python -m qor.scripts.plan_grep_lint --plan docs/plan-qor-phase293-ledger-emit-hash-block.md --repo-root .` — this plan's own citations are truth-checked.
- `python -m ruff check qor/ tests/` — lint.
- `python -m pytest -q` — full suite.
