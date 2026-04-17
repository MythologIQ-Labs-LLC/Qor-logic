# Plan: Phase 26 -- Audit Report Language + Repeated-VETO Pattern Detector

**change_class**: feature

## Open Questions

- Severity number for the `repeated_veto_pattern` Shadow Genome event: plan defaults to **3** (cross-phase regression; below the severity-sum >=10 auto-trigger threshold individually, contributes to threshold over time). Adjust if the existing severity scale uses different anchors.
- Advisory position in AUDIT_REPORT: plan places the "Pattern detected" note as a dedicated `## Process Pattern Advisory` section after the summary table, before "Next Action". Adjustable without semantic impact.
- Whether `/qor-remediate` should be auto-invoked on pattern detection or only recommended: plan uses **recommend, never auto-invoke**. Auto-invocation risks silent state change mid-session; operator opts in.

## Goal

Two coupled capabilities:

1. **Audit report language with per-ground skill directives (B17)**: replace the generic "Mandated Remediation" header in `.agent/staging/AUDIT_REPORT.md` with a structured per-ground directive line. Each VETO ground names its correct next skill (or names the Governor for plan-text edits). Removes the skill-selection ambiguity operators hit when "Mandated Remediation" seemed to imply `/qor-remediate`.
2. **Repeated-VETO pattern detector (B18)**: detect when `/qor-audit` required multiple passes across consecutive sealed phases. Threshold: `>= 2 consecutive sealed phases where the audit pass count was > 1`. When detected, audit report surfaces a "Process Pattern Advisory" recommending `/qor-remediate` and a severity-3 `repeated_veto_pattern` Shadow Genome event is appended. Pattern is non-blocking; the actual VETO (if any) stands on its own merits.

## Design summary

- **Detector is a pure function.** `qor/scripts/veto_pattern.py` parses `docs/META_LEDGER.md`, groups entries by phase, counts AUDIT entries per phase, returns a `PatternResult` namedtuple. No I/O beyond reading the ledger path the caller passes in.
- **Per-ground directive is a template contract.** Each VETO ground in AUDIT_REPORT.md carries an explicit `**Required next action:** /qor-X` or `**Required next action:** Governor edit + re-audit` line. The canonical mapping lives in `qor/gates/delegation-table.md` (already source of truth) and is echoed in `qor/references/doctrine-audit-report-language.md` (new doctrine).
- **Language doctrine is enforceable.** A lint test walks `qor/skills/governance/qor-audit/references/qor-audit-templates.md` and asserts the template contains all required slots. A second lint walks the doctrine file and asserts it lists the same five ground-classes the template does.
- **Pattern detection runs at every audit.** `/qor-audit` calls `veto_pattern.check()` as part of Step 3 and appends the advisory to its report if the pattern fires. No new skill; behavior lives in the existing audit flow.
- **Shadow Genome wiring is append-only.** Event is emitted via `shadow_process.append_event` (existing helper) with `event_type: "repeated_veto_pattern"` and `severity: 3`. No new storage surface.

## Ground-class -> skill mapping (canonical)

| VETO ground class | Required next action |
|---|---|
| Section 4 Razor (function/file size, nesting, ternary) | `/qor-refactor` |
| Orphan file / Macro-arch breach (cyclic, layering, boundaries) | `/qor-organize` |
| Plan-text (A08 safe-load, dep audit, missing tests, ghost feature, wording) | Governor: amend plan text, re-run `/qor-audit` |
| Process-level (repeated VETO, SG threshold, capability shortfall cascade) | `/qor-remediate` |
| Code-logic defect (regression, hallucination, behavioral break) | `/qor-debug` |

## CI validation

```
pytest -q
```

Plus the new lint tests are part of the default `pytest -q` run.

---

## Phase 1: `veto_pattern.py` detector + Shadow Genome event

### Affected files

- `tests/test_veto_pattern_detector.py` (new) -- pure-function unit tests with fixture ledger text
- `tests/fixtures/ledger_no_pattern.md` (new) -- single-pass phases in sequence
- `tests/fixtures/ledger_pattern_fires.md` (new) -- 2 consecutive phases with >1 audit pass each
- `tests/fixtures/ledger_pattern_clears.md` (new) -- pattern fired then one clean phase resets it
- `tests/test_veto_pattern_event.py` (new) -- event-emission contract (pattern -> append_event call)
- `qor/scripts/veto_pattern.py` (new) -- pure detector + thin wrapper that emits SG event

### Unit Tests (write FIRST)

- `tests/test_veto_pattern_detector.py`
  - **Parser policy**: ledger markdown parsing uses plain string operations; no YAML or eval. If YAML appears (unlikely), `yaml.safe_load` only (enforced by existing discipline test).
  - `parse_phase_audit_counts(text)` on `ledger_no_pattern.md` returns a mapping like `{24: 1, 25: 1}` (one AUDIT per phase, then SEAL).
  - Same parser on `ledger_pattern_fires.md` returns `{24: 3, 25: 3}` (multi-pass phases).
  - Same parser on `ledger_pattern_clears.md` returns `{24: 3, 25: 3, 26: 1}`.
  - `detect_repeated_veto_pattern(counts, window=2)` returns `PatternResult(detected=False, ...)` for `ledger_no_pattern`.
  - Same detector returns `PatternResult(detected=True, recent_phases=[24, 25])` for `ledger_pattern_fires`.
  - Same detector returns `PatternResult(detected=False, ...)` for `ledger_pattern_clears` (the clean Phase 26 resets the consecutive-count streak).
  - Edge: `detect_repeated_veto_pattern({24: 1}, window=2)` -> detected=False (only one sealed phase).
  - Edge: `detect_repeated_veto_pattern({24: 5}, window=2)` -> detected=False (one phase with many passes is NOT the pattern; B18 is CROSS-phase).
  - Edge: `window=3` requires three consecutive phases with >1 pass.
  - `PatternResult` is a namedtuple with `(detected: bool, recent_phases: list[int], max_pass_count: int)`.
- `tests/test_veto_pattern_event.py`
  - `maybe_emit_pattern_event(result, session_id)` calls `shadow_process.append_event` exactly once when `detected=True`, with `event_type == "repeated_veto_pattern"`, `severity == 3`, and `details` containing `recent_phases` and `max_pass_count`.
  - No event emitted when `detected=False`.
  - Function is idempotent under repeated calls with the same result (uses existing `shadow_process` dedup semantics; test asserts no duplicate emission within a single call).

### Changes

- `qor/scripts/veto_pattern.py`:
  - Module-level constant `_PATTERN_WINDOW = 2` (default).
  - `PatternResult = namedtuple("PatternResult", ["detected", "recent_phases", "max_pass_count"])`.
  - Pure function `parse_phase_audit_counts(ledger_text: str) -> dict[int, int]`:
    - Walks `### Entry #N: (AUDIT|SEAL) -- Phase NN` style headers.
    - For each sealed phase (has a SEAL entry), counts the AUDIT entries that cite the same phase in their target line.
    - Returns `{phase_num: audit_pass_count}`.
  - Pure function `detect_repeated_veto_pattern(counts: dict[int, int], window: int = _PATTERN_WINDOW) -> PatternResult`:
    - Sorts phases, takes the last `window` phases, checks each has `count > 1`.
    - Returns PatternResult with `detected` + identifying phases + max pass count.
  - Thin wrapper `maybe_emit_pattern_event(result: PatternResult, session_id: str) -> bool`:
    - If `result.detected`, call `shadow_process.append_event` with the canonical payload and return True.
    - Else return False.
  - `check(ledger_path: Path = None, session_id: str = None) -> PatternResult`:
    - Convenience entry point. Reads ledger, parses, detects, optionally emits event.
    - Default `ledger_path` resolves via `qor.workdir.meta_ledger()`.

---

## Phase 2: Audit report language + template + doctrine

### Affected files

- `tests/test_audit_template_slots.py` (new) -- lint the canonical AUDIT_REPORT template for required per-ground slots
- `tests/test_audit_language_doctrine.py` (new) -- doctrine file lists every ground class in the canonical mapping
- `qor/references/doctrine-audit-report-language.md` (new) -- canonical ground-class -> skill mapping + template contract
- `qor/skills/governance/qor-audit/references/qor-audit-templates.md` -- edit to include per-ground directive slots + Process Pattern Advisory section
- `qor/skills/governance/qor-audit/SKILL.md` -- edit Step 3 passes to include `**Required next action:**` line per ground; edit Step 7 to append Process Pattern Advisory when detector fires

### Unit Tests (write FIRST)

- `tests/test_audit_template_slots.py`
  - **Parser policy**: markdown slot detection uses plain string operations + re (no YAML).
  - Walks `qor/skills/governance/qor-audit/references/qor-audit-templates.md`.
  - Asserts presence of the canonical ground-class headers (5 headers, one per row of the doctrine mapping).
  - Asserts each ground-class section contains a `**Required next action:**` line.
  - Asserts the template contains a `## Process Pattern Advisory` section header with the canonical placeholder `<!-- qor:veto-pattern-advisory -->`.
  - Fixture-based positive controls: `tests/fixtures/audit_template_good.md` passes; `tests/fixtures/audit_template_missing_slot.md` fails with a clear per-slot error message.
- `tests/test_audit_language_doctrine.py`
  - Asserts `qor/references/doctrine-audit-report-language.md` exists.
  - Asserts the doctrine contains exactly the 5 canonical ground classes named in this plan, paired with the skill names listed in the same table.
  - Cross-check: every skill named in the doctrine is a real skill (exists under `qor/skills/**/SKILL.md` or a loose skill), OR is the literal string "Governor" for plan-text edits.
  - Asserts the doctrine lists `repeated_veto_pattern` as the Shadow Genome event name and `severity: 3`.

### Changes

- `qor/references/doctrine-audit-report-language.md` (new):
  - Section: "Ground-class -> skill directive mapping" containing the 5-row table.
  - Section: "Template contract" describing the five required slots and the Process Pattern Advisory section.
  - Section: "Repeated-VETO pattern" naming the event + severity + remediation skill (`/qor-remediate`).
  - Reference to `qor/gates/delegation-table.md` as the upstream authority for skill-name mappings.
- `qor/skills/governance/qor-audit/references/qor-audit-templates.md`:
  - Add per-ground section template with `**Required next action:** <skill-or-Governor>` slot.
  - Add `## Process Pattern Advisory` section with canonical marker and instructions for when to populate it.
  - Remove the generic "Mandated Remediation" header from legacy examples.
- `qor/skills/governance/qor-audit/SKILL.md`:
  - Step 3 (Adversarial Audit): each pass (Security, OWASP, Ghost UI, Razor, Dependency, Macro-Arch, Orphan) is updated so its VETO block emits a `**Required next action:**` line citing the correct skill or "Governor".
  - Step 7 (Final Report): invoke `qor/scripts/veto_pattern.py` via python, parse the returned PatternResult, and populate the `## Process Pattern Advisory` section. If not detected, leave the section with text "No repeated-VETO pattern detected in the last `N` sealed phases."
  - Step 6 (Shadow Genome): if the detector fires AND the current audit also VETOs, call `maybe_emit_pattern_event`. If it fires on a PASS audit, still emit the event (pattern is sealed by Phase 25's example -- multi-pass phases that eventually pass are the signal).

---

## Phase 3: `/qor-audit` template integration + smoke tests

### Affected files

- `tests/test_audit_smoke_integration.py` (new) -- end-to-end shape assertion on a synthetic audit run
- `qor/skills/governance/qor-audit/SKILL.md` -- no additional changes beyond Phase 2 (cited for completeness)

### Unit Tests (write FIRST)

- `tests/test_audit_smoke_integration.py`
  - Stages a fixture ledger with the repeated-VETO pattern fired.
  - Runs the audit's pattern-check step (invokes `veto_pattern.check(ledger_path=fixture)`).
  - Asserts the returned `PatternResult` is `detected=True`.
  - Asserts that when the audit report template is rendered with this result, the `## Process Pattern Advisory` section contains the recommended `/qor-remediate` directive and the affected phase numbers.
  - Negative control: with `ledger_no_pattern.md`, the section reads "No repeated-VETO pattern detected."

### Changes

- No new runtime changes in Phase 3. This phase is a smoke-test phase that wires the Phase 1 detector and the Phase 2 template together and asserts they produce the expected audit-report output shape. If the smoke test exposes drift between detector and template (e.g., a format mismatch), that is a VETO finding for re-audit of this plan rather than a Phase 3 change.

---

## Delegation

- Plan complete -> `/qor-audit`.
- Phase 1 is pure Python with unit tests. Phase 2 is doctrine + skill-prose edits with lint. Phase 3 is integration. No module restructuring; `/qor-organize` not required.
- If audit flags a skill-prose change as semantically modifying `qor-audit`'s behavior (beyond language), escalate that specific change to `/qor-refactor`.
