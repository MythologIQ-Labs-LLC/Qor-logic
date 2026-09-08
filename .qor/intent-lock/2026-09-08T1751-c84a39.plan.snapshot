# Phase 277: gate_provenance attests pairs that never coexisted

**change_class**: hotfix
**Issues**: GH #467 (partial -- see D4)
**Research**: docs/research-brief-content-hash-consolidation-2026-09-08.md
**Iteration**: 4 (iterations 1-3 VETOed)
**Session**: 2026-09-08T1751-c84a39

## Scope note

One module's read is wrong and has been wrong in production. A second is corrected for consistency and has no production consumer. `gate_provenance.latest_seal_hashes` promises the hash pair of "the last ledger entry that carries both canonical hash markers" and instead takes two independent whole-file last matches. **At 187 historical ledger states the two came from different entries**, and CI HMAC'd the mismatched pair on every push.

Iteration 1 proposed consolidating three modules. One is removed because its narrowness is deliberate correctness (D4); one is kept but is cosmetic (D3).

**The 160-of-741 figure applies only to `gate_provenance`.** It is a whole-ledger count and only that module scans the whole file. `evidence_bundle` restricts to `### Entry #N: SESSION SEAL` blocks, so its real figure is **168 of 235**; `ledger_commitment` restricts to committing kinds with a citation, **256 of 337**. An earlier draft applied the whole-ledger number to all three.

## What iterations 1 and 2 got wrong

Iteration 1's three, then the four iteration 2 introduced while correcting them.

1. **`ledger_commitment`'s "no observable effect" claim was the opposite of the truth.** The plan measured that 1 of 765 entries carries `**Artifact**` and concluded the fix changes nothing. The gate's citation pattern is `^\*\*(?:Artifact|Plan|Brief)\*\*` -- **491 entries**. The fix would have added **81** commitments, 45 of them false, into a hard ABORT gate. (108 is the unfiltered count; `latest_commitments` skips non-committing kinds at `_COMMITTING_KINDS` before it looks at the artifact or hash, so 27 of those entries are never read.)
2. **The plan asserted the narrowness was accidental without checking what documented it.** `ledger_commitment.py:26-30` carries a hazard note -- *"A GATE TRIBUNAL entry cites `**Plan**` but its content hash binds the AUDIT REPORT... a false stale reading. Found by running this gate against its own phase."* -- but it is bound to `_COMMITTING_KINDS` at `:31` and covers the kind filter. `_CONTENT_RE` had no comment. So the invariant was stated adjacently and a careful reader could have generalized it, but nothing guarded the line iteration 1 proposed changing. "Author ignored documentation" and "the invariant was undocumented at the line that holds it" route to different countermeasures; this is the second, and D4 fixes it at that line.
3. **D3 was listed as test "additions" when it breaks two existing tests.** `tests/test_gate_provenance.py`'s fixtures contain no `### Entry #` heading at all, so an entry-anchored read returns `None` and two tests fail. Existence of the file was verified; its content was not.
4. **"the change is the pattern, nothing else" was false for `evidence_bundle`** -- it is a dict consumed by a generic `.group(1)` loop, so a pattern swap walks straight into the three-capture-group trap the same plan warns about two sections earlier, and leaves the chain field with **zero gain** while appearing fixed (D3).
5. **The 160-of-741 headline was applied to all three modules** when only `gate_provenance` scans the whole ledger. It also made `test_all_three_read_the_live_ledger_completely` unwritable, since `evidence_bundle`'s ceiling is 235.
6. **108 and 148 were both wrong** -- 108 counts entries the gate never reads because `_COMMITTING_KINDS` filters first; the control is 147, not 148.
7. **"prose cannot displace the field" was generalized from three cases that shared an ordering.** BEFORE and AFTER were tested; **BETWEEN** was not, and it fails -- a prose hex between the label and its value wins, because `_HASH_SPAN` is lazy. Corrected in the brief; the load-bearing empirical result (0 disagreements across 640 entries) is unaffected.

All seven are the same error: measuring or asserting without reading the code that consumes the value. Items 4-7 were introduced by the iteration that corrected items 1-3, which is the strongest argument in this plan for why the numbers here are cited with their source rather than restated.

## D1: the defect is realized, not latent

```python
content = re.findall(r"\*\*Content Hash\*\*:\s*`([0-9a-f]{64})`", text)
chain   = re.findall(r"\*\*Chain Hash \(Merkle seal\)\*\*:\s*`([0-9a-f]{64})`", text)
if not content or not chain:
    return None
return content[-1], chain[-1]
```

Nothing constrains those two lists to the same entry, and the docstring says they are. Replaying the ledger at each of its historical states -- text truncated at the end of entry N -- and asking which entry owned each last match:

| | |
|---|---|
| states where both lists are non-empty | 640 |
| states where the two came from **different entries** | **187** (29% of 640; 24% of 765 entries) |
| span | entry #127 through #631 |

At the state ending in entry #631 the function returned `(content_of_630, chain_of_631)`. `ci_attest` (`gate_provenance.py:166`) then HMAC'd `f"{content_hash}|{chain_hash}"` over a pair that never coexisted in any entry, and `.github/workflows/ci.yml:151` runs `attest-latest` on every push. The attestation does not fail -- it is meaningless, and nothing reports it.

**128 entries carry a backticked Content Hash without a backticked Chain Hash; 70 the reverse.** `if not content or not chain` cannot detect the mismatch because both lists are non-empty. It works at this instant by coincidence, having not worked at 29% of the states it has run against.

**The most reachable trigger needs no unusual markup at all.** A ledger truncated after a new entry's content hash but before its chain hash -- an interrupted append, not a rare value form -- makes the current code return `(content_of_the_new_entry, chain_of_the_previous_one)`:

```
truncated: heading only            old=('aaaa','bbbb')   new=None
truncated: label, no value         old=('aaaa','bbbb')   new=None
truncated: content but no chain    old=('cccc','bbbb')   new=None    <- the mismatch, deterministic
truncated: mid-hex value           old=('aaaa','bbbb')   new=None
truncated: heading missing colon   old=('aaaa','bbbb')   new=('aaaa','bbbb')
```

The last row is load-bearing rather than lucky: `_ENTRY_RE` requires the colon, so a half-written heading falls back to the last *complete* entry instead of anchoring to a partial one.

## D2: fix the selection and the pattern together

The pattern is also narrow -- it reads 523 of 740 chain hashes, a gap of **217**, the largest measured, because it hardcodes `(Merkle seal)` as literal text rather than tolerating a suffix. **A pattern-only fix makes this worse**: it widens the population the two independent last-matches draw from.

```python
_ENTRY_RE = re.compile(r"^### Entry #(\d+):", re.MULTILINE)   # module-private

starts = list(_ENTRY_RE.finditer(text))
entry = text[starts[-1].start():] if starts else ""
content = ledger_dialect.hash_value(ledger_dialect.CONTENT_HASH_RE.search(entry))
chain   = ledger_dialect.hash_value(ledger_dialect.CHAIN_HASH_RE.search(entry))
if content is None or chain is None:
    return None
return content, chain
```

Reading one entry makes the pair coherent by construction and makes the value form irrelevant. Both defects have one root cause and one fix.

`hash_value` is required, not stylistic: `CONTENT_HASH_RE` has three capture groups, one per value form, and `.group(1)` returns `None` for two of the three.

**The split is local, not a new `ledger_dialect` helper.** The dialect has no last-entry accessor, and adding one would widen this phase into changing the owner's API. `ledger_commitment.py:25` and `snapshot_export.py:33` already carry their own `_ENTRY_RE`.

### Availability: strictly greater, never less

Measured across all 765 states:

| | |
|---|---|
| new returns `None` where old returned a pair | **0** |
| new returns a pair where old returned `None` | **100** |

The regression case requires the final entry to lack a parseable pair while an earlier entry has one. The 25 entries with no content+chain pair are all at or below **#122**, and `ledger_dialect.MARKUP_COMPAT_BOUNDARY = 123` makes markup mandatory at or above #123 -- so such a state is one `ledger_hash verify` rejects before `attest-latest` runs. Stated as bounded by that boundary rather than impossible: the empirical 0 and the constant's contract are verified, every enforcement path for an unmarked entry appended above the cutoff is not.

Either way no gate verdict moves: `main()` at `gate_provenance.py:292-296` prints `SKIP` and returns **0** on `None`.

## D3: `evidence_bundle` is included, and labelled cosmetic

Its `content_hash` pattern is narrow the same way (**168 of 235** seal blocks, not 581 of 741), and its own `chain_hash` pattern at line 29 already tolerates a suffix -- two fields, one dict, two conventions.

**This is a restructure, not a pattern swap, and the plan must say so or it walks the implementer into D2's own trap.** `_FIELD_RES` (`:25-32`) is a dict consumed by a generic loop at `:40-42`:

```python
for key, rx in _FIELD_RES.items():
    found = rx.search(body)
    block[key] = found.group(1) if found else None
```

`CONTENT_HASH_RE.groups == 3`, so dropping it into that dict calls `.group(1)` on it. Measured over the 235 seal blocks:

| field | narrow | dialect + `hash_value` | dialect + `.group(1)` |
|---|---|---|---|
| content_hash | 168 | 235 | **234** -- loses one silently |
| chain_hash | 219 | 235 | **219 -- zero gain** |

A naive substitution leaves the chain field exactly where it was while appearing to have been fixed. `_seal_blocks` gains a per-field accessor that routes dialect patterns through `hash_value`.

**What the widening actually admits, disclosed so no consumer assumes otherwise:** of the 67 `content_hash` gains across the seal blocks, **59 come from the suffixed `(session seal)` label** and 8 from plain labels with a non-backtick value. The key therefore does not always hold a plain artifact digest -- the same suffixed form that must never become a commitment in `ledger_commitment` (D4) will now appear here, where nothing pairs it to a file and no false-stale reading is possible.

**It has no production consumer.** Nothing in `qor/skills/`, `.github/workflows/`, or any non-test module invokes it; the release workflow's "evidence bundle" is an unrelated inline heredoc producing `dist/evidence.json`. So this is a correctness fix with no observable production effect, stated plainly rather than counted toward the phase's value.

It is included because leaving one of the identified narrow readers unfixed after a consolidation phase is the half-measure shape, and because it does not share D4's hazard: it emits fields per entry into a bundle and never pairs a hash with a cited artifact, so no false-stale reading is possible.

## D4: `ledger_commitment` is OUT, and its narrowness gets a test

Removed from scope. Its narrow pattern is load-bearing correctness, measured:

| | entries | value equals the cited file's live hash |
|---|---|---|
| suffixed `**Content Hash (session seal)**` seals citing a `**Plan**` | 45 | **0** |
| plain `**Content Hash**` seals citing an on-disk file (control) | 147 | 99 |

Zero of 45 against 99 of 147: the suffixed form binds the seal digest, not the cited plan. Consolidating would take on-disk stale commitments from 74 to 116 -- **42 artifacts newly stale**, all `docs/plan-qor-phase*.md` -- and `ledger_commitment` is a hard ABORT at seal. A later doc sweep touching any of the 42 would abort and be told to amend a commitment that never existed.

**A regression test is added to `tests/test_ledger_commitment.py`** asserting that a suffixed session-seal content hash never becomes a commitment.

**The invariant was undocumented at the line that holds it, and that is the actual failure mode.** An earlier draft recorded it as "the module explains why and the author did not read it", which is wrong: the module's hazard note is bound to `_COMMITTING_KINDS` and explains the *kind-filter* case. `_CONTENT_RE` carried no comment, and nothing in the module warned against widening the pattern. Iteration 1 did not walk past a warning -- there was none at that line.

Citations here are by symbol rather than line number, because this phase inserts the missing comment and therefore moves every line below it. A line citation written now would be wrong by the time the change lands.

Those two diagnoses route to different countermeasures, and the shadow-genome entry inherits whichever is written here. So this phase does both: a comment at `_CONTENT_RE` stating why the pattern is narrow, and the test. The comment prevents the proposal; the test catches the regression. Neither changes behaviour. This is the phase's only addition to a module it otherwise leaves alone, and it is scoped to pinning existing behaviour, not altering it.

## D5: what this does NOT do

- **Does not close #467.** It fixes 2 of the 3 modules named there and establishes the third must not be fixed. The issue is updated with the measurement; the PR carries no closing keyword.
- **Does not fix #428, #461, #468**, or add the lint (#469).
- **Does not audit the 187 historical attestations.** They are meaningless, not wrong, and nothing consumed them for a verdict. Recording that they happened is this plan's job; deciding whether any need revoking is not.

## Tests

Written first, red before the change. Each runs twice for determinism.

| Test | Pins | Red before |
|---|---|---|
| `test_latest_seal_hashes_returns_a_pair_from_one_entry` | **D1**; the realized defect. Fixture: two entries, the newer carrying only a chain hash | yes |
| `test_latest_seal_hashes_reads_a_suffixed_chain_hash_label` | the 217-hash chain gap | yes |
| `test_latest_seal_hashes_returns_none_when_last_entry_lacks_a_hash` | the honest-skip path survives | no |
| `test_attest_latest_still_skips_and_exits_zero_on_none` | no gate verdict moves | no |
| `test_evidence_bundle_reads_a_suffixed_content_hash_label` | D3 | yes |
| `test_evidence_bundle_reads_a_non_backtick_value_form` | D3 | yes |
| `test_a_suffixed_session_seal_hash_is_not_a_commitment` | **D4**; the hazard that must stay closed | no |
| `test_evidence_bundle_chain_hash_gains_coverage` | **HIGH-4**; a `.group(1)` substitution gives chain ZERO gain while appearing to work | yes |

`test_latest_seal_hashes_rewritten_fixture_has_real_entries` was in an earlier draft and is **removed**: it asserted a property of a fixture and never invoked `latest_seal_hashes`, which is presence-only by `doctrine-test-functionality.md` and would ABORT the seal under /qor-substantiate's presence-only gate. Its intent is already covered -- if the fixture lacks entries, `test_latest_seal_hashes_returns_a_pair_from_one_entry` fails.

Three existing tests in `tests/test_gate_provenance.py` need their fixtures changed: `test_latest_seal_hashes_extracts_last_entry` (line 160), `test_attest_latest_cli_emits_under_secret` (line 190), and `test_attest_latest_cli_skips_without_secret` (line 177), none of which carry an entry heading.

**The constraint is: insert entry headings, change no assertion.** "Rewritten, not added to" as an earlier draft put it is licence to weaken three tests, and the fact that their current fixtures encode the defect is exactly why an unconstrained rewrite is dangerous here. Each existing assertion survives the fixture change and one is strengthened by it:

| test | what it protects | after |
|---|---|---|
| `:160` | last match, not first (`c`/`d` over `a`/`b`) | protects that **and** pair coherence -- strictly stronger |
| `:190` | the CLI emits an HMAC equal to `ci_attest` of the parsed hashes | unchanged |
| `:177` | no secret -> SKIP, exit 0 | unchanged, and now for the reason in its name rather than because no entry exists |

## Affected files

- `qor/scripts/gate_provenance.py`
- `qor/scripts/evidence_bundle.py`
- `tests/test_gate_provenance.py` (**fixture changes to three tests** -- entry headings inserted, no assertion changed)
- `tests/test_evidence_bundle.py` (additions)
- `qor/scripts/ledger_commitment.py` (**a comment at `_CONTENT_RE` only** -- no behaviour change)
- `tests/test_ledger_commitment.py` (one regression test)
- `CHANGELOG.md`

## Reach

- `gate_provenance` returns a coherent pair where it previously could return a mismatched one, and returns a pair at 100 states where it previously skipped. No gate verdict moves in either direction.
- `evidence_bundle` gains fields for entries it previously omitted; no production consumer exists.
- `ledger_commitment` is unchanged in behaviour; it gains one comment and one test.
- No skill or template changes, so the dist tree is untouched.

**`hotfix` is justified by version impact, not by blast radius.** `doctrine-governance-enforcement.md:25` maps it to a patch bump; there is no new capability, no new CLI surface and no signature change -- a wrong output made right. That the corrected path is CI-invoked raises the stakes of getting it right; it does not make it a feature. The class also buys no skipped obligation here: its only exemption is the README/CHANGELOG requirement (`doctrine-documentation-integrity.md:166`), which this phase satisfies anyway.

## CI Commands

```
python -m pytest tests/test_gate_provenance.py tests/test_evidence_bundle.py tests/test_ledger_commitment.py -q
python -m qor.scripts.gate_provenance verify-committed --phase-min 158
python -m qor.scripts.gate_provenance attest-latest
python -m qor.scripts.ledger_hash verify docs/META_LEDGER.md
python -m qor.reliability.seal_entry_check --ledger docs/META_LEDGER.md --auto
python -m qor.scripts.seal_artifacts --check --skip-tests --repo-root .
python -m qor.scripts.publication_boundary_lint
python -m pytest -q
```

## Limitations

- The 187 historical mismatched attestations are recorded, not remediated.
- `evidence_bundle`'s fix has no observable production effect; it is included for consistency, not value.
- The `_ENTRY_RE` split would mis-anchor on an entry heading inside a fenced block or block quote. Measured: **0 occurrences** in the live ledger, and the same exposure already exists in two other modules.
- Two other narrow readers of these fields remain by design (`ledger_commitment`) or out of scope (`ledger_migrate`). Nothing prevents a fourth; that is #469, parked.
- `Timestamp`, `Session` and `Phase` have multiple parsers too. Out of scope: widening past the filed defect is how the previous phase reached four review rounds.
