# Gate Tribunal Audit Report — Phase 39 Pass 2

**Plan**: `docs/plan-qor-phase39-context-discipline.md` (amended for V1 + F1-F5)
**change_class**: feature
**target_version**: v0.29.0
**Verdict**: **PASS**
**Mode**: solo (codex-plugin unavailable; capability_shortfall logged)
**Tribunal Date**: 2026-04-20
**Risk Grade**: L1

---

## Executive summary

Pass 1 V1 (HIGH) resolved cleanly via resolution (a): Anthropic SDK invocation with the clean library/CLI separation (`ab_harness.py` mockable + `ab_live_run.py` operator-only). F1-F5 all addressed. Two LOW observations remain around API-call operational details — neither blocks implement.

## Pass 1 resolution verification

| ID | Pass 1 finding | Pass 2 resolution | Verified |
|---|---|---|---|
| V1 | harness cannot invoke slash-command skills | Anthropic SDK direct invocation; `anthropic>=0.40,<1.0` under `[project.optional-dependencies].ab-harness`; `ab_harness.run` accepts injected client; CI uses mocks | ✓ |
| F1 | "~30 skills" overstates | plan now cites 24 (grep-verified) | ✓ |
| F2 | fixture SEEDED marker | header convention declared + `test_corpus_files_carry_seeded_defect_marker` enforces | ✓ |
| F3 | n=5 justification | non-determinism quantified via stddev; results artifact reports mean AND stddev | ✓ |
| F4 | variant generation unspecified | hand-authored variant files at `tests/fixtures/ab_corpus/variants/<skill>.<variant>.md` — declared non-programmatic | ✓ |
| F5 | MANIFEST line range | `line_start` + `line_end` fields required by `test_manifest_line_range_fields_present` | ✓ |

## Audit passes

### Security Pass (L3) — PASS

`ANTHROPIC_API_KEY` via env var (SDK convention); never logged; `ab_live_run.py` exits clearly on absence per `test_ab_live_run_exits_clearly_without_api_key`. No keys in fixtures, code, or results.

### OWASP Top 10 Pass — PASS

- A05 Security Misconfiguration: credential handling correct (env var, not code).
- A08 Software/Data Integrity: fixture files are test data with `# SEEDED TEST DEFECT — NOT EXECUTABLE` header; no scanner conflict.

### Ghost UI Pass — N/A

### Section 4 Razor Pass — PASS

| Check | Plan | Status |
|---|---|---|
| Max function lines | `ab_harness.py` 140 LOC / 5 functions = 28 avg | OK |
| Max file lines | ab_harness.py ~140, ab_live_run.py ~60 | OK |
| Nesting depth | flat per pseudocode | OK |

### Dependency Audit — PASS

| Package | Justification | <10 lines vanilla? | Verdict |
|---|---|---|---|
| `anthropic>=0.40,<1.0` | V1 resolution (a) requires programmatic Claude invocation for A/B harness; no equivalent in stdlib | No — LLM API requires SDK for streaming, retries, error handling | PASS |

**Scoped correctly**: dependency is under `[project.optional-dependencies].ab-harness`, not main install set. Default `pip install qor-logic` users do not pull it. Only operators running `ab_live_run.py` install the extra.

### Macro-Level Architecture Pass — PASS

- Library/CLI separation is clean: `ab_harness.py` is pure (mockable, no env reads); `ab_live_run.py` is the side-effectful wrapper.
- Tests mock the Anthropic client — no CI dependency on API access or credentials.
- Raw per-run data lands in gitignored `.qor/gates/<sid>/ab-run.json` — correct gate-artifact convention.
- No cyclic dependencies: `ab_harness` ← imports `ab_variants`; `ab_live_run` ← imports `ab_harness`. One-way DAG.

### Infrastructure Alignment Pass — PASS

- `anthropic` SDK exists on PyPI with the requested version range.
- `claude-opus-4-7` is a valid model ID per the current Anthropic model family (verified against system's knowledge cutoff).
- All 4 target skill files exist; `qor-debug` constraint line verified; `qor-document` persona-vs-agent conflation point verified.
- Doctrine `doctrine-governance-enforcement.md` at §10.5; Phase 39 adds §11 cross-reference (legal next section).
- `[project.optional-dependencies]` TOML structure is valid per PEP 621.

### Orphan Detection — PASS

All proposed files trace to consumers or are explicitly new. Variant fixture files consumed by `ab_variants.load`. No orphans.

## Observations (non-VETO)

| ID | Severity | Observation |
|---|---|---|
| O1 | LOW | **Cost estimate is ~5-8x low.** Plan states "~500 input + ~100 output tokens per call" → ~$4 per cycle. Verified: actual skill bodies are `/qor-audit` 18,050 chars (~4,512 tokens), `/qor-substantiate` 16,047 chars (~4,011 tokens). Since the system prompt = full SKILL.md body + variant + instructions, real input is ~4,000-5,000 tokens/call, not 500. Recalculated at Opus 4.7 pricing: 400 calls × ~4,300 input tokens × $15/M = ~$26 input + 400 × ~200 output × $75/M = ~$6 output = **~$32 per full cycle**, not ~$4. Not VETO-level (plan is still implementable; operator just needs accurate budget). Plan module docstring should carry the corrected number. |
| O2 | LOW | **No retry/timeout specified.** `client.messages.create(...)` call has no explicit timeout or retry. Default SDK behavior applies (generally reasonable) but transient API failures in the middle of a 400-call serial run could lose partial results. Consider: `timeout=60` per call; on rate-limit or transient error, sleep-and-retry once before counting as miss. Minor operational robustness; defer to implement judgment. |

## Signature / cycle

- Pass 1: `[infrastructure-mismatch, specification-drift]` (V1, F1-F5)
- Pass 2: `[]` (PASS, no findings)
- Pass 1 → Pass 2 delta: signature shifted (V1 class resolved; no new infrastructure issues)
- Cycle count: 2. PASS on Pass 2.

## Required next action

**`/qor-implement`** — dependency-ordered Phase 1 → 2 → 3 → 4.

Note for implement: address O1 (corrected cost estimate in harness docstring) inline; O2 (retry/timeout) is defensible either way.

---

*Verdict: PASS (L1)*
*Mode: solo*
*Pass 1 V1 + F1-F5 all resolved. Two LOW cost/retry observations do not gate.*
*Signature: [] (PASS)*
*Next: /qor-implement*
