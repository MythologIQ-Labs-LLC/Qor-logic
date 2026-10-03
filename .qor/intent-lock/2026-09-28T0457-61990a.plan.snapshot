# Plan: Phase 302 - Install records only sha256 values it has checked against the installed bytes, and dist manifests are drift-checked

**change_class**: hotfix

**doc_tier**: standard

**terms**: `[]` (this plan introduces no new term; the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: install checks only the manifest entries it copies; an entry whose source file is absent, or that no install route of the host covers, is still skipped without a check and makes no receipt claim (LD-4); the drift check compares a manifest as parsed JSON without `generated_ts`, so a change of key order or whitespace alone is not drift (LD-5); the committed-dist drift step runs in one Ubuntu CI job, while the test-matrix drift step still runs after the suite has recompiled `qor/dist` in place (LD-3, LD-6); Windows CI behaviour is argued from the repository's own line-ending record, not observed locally (LD-7)
- non_goals: changing the manifest schema or `generated_ts`; changing `dist_compile` or any compiled file under `qor/dist/`; making `tests/test_cli.py` stop recompiling `qor/dist` in place; pinning source line endings under `qor/skills/` or `qor/agents/`; verifying files at uninstall or at `list --installed`; release publication
- exclusions: install receipts written before this phase, which are not rewritten or re-verified (LD-8)

**iteration**: 1 (on branch `phase/302-dist-manifest-integrity`)

**Issue**: GH #440 ("dist manifests are the only file class excluded from drift checking, and their unverified sha256 becomes an integrity claim in the install receipt"). The issue body is empty; the defect statement below is derived from the code at the base and reproduced in scratch clones.

**Current base**: `f2e4be9aac7d3f7772969b996b53ff4a7beaede6` (`main` after Phase 301 merged; project version `0.175.5`, sealed at META_LEDGER #832)

**Target version**: `0.175.6` (hotfix bump from `0.175.5`)

**Citation currency**: every `git show` evidence statement below cites `f2e4be9aac7d3f7772969b996b53ff4a7beaede6` and was re-executed against it while authoring (one observed line per statement, 0 mismatches). Each statement's pattern is written exactly as it is run: the patterns use `.` in place of regex metacharacters, so no statement depends on a backslash escape. Lines that carry inline code spans, or a file:line reference of their own, are not quoted as `->` evidence; they are cited by line number in prose, or by a `grep -noE` command whose printed output is quoted in full and is ASCII. The other command outputs quoted (`git ls-tree`, `git check-attr`, `git grep`, `git ls-remote`, scratch runs) were observed on 2026-09-28. Scratch runs used clones of the base outside the repository, with the Phase 1 test file, the Phase 2 and Phase 3 code and the Phase 4 edits applied exactly as specified below.

## Open Questions

None. GH #440 names two faults (manifests excluded from drift, an unverified sha256 in the receipt); LD-4 decides the receipt fault, LD-5 and LD-6 decide the drift fault, and LD-7 decides the line-ending condition the receipt fix exposes.

## Problem

`qor-logic compile` writes a `manifest.json` per compiled variant (and a top-level copy of the claude one) listing every shipped file with its sha256. `qor-logic install` copies the files a manifest lists and writes `.qorlogic-installed.json`, the install receipt, with one `{path, sha256}` row per copied file. The sha256 in that row is copied from the manifest; install never hashes the bytes it copies. The manifest itself is the one file class `check_variant_drift` skips, so nothing checks that its sha256 values describe the shipped bytes.

Reproduction at the base (scratch clone of `f2e4be9a`, `PYTHONPATH` at the clone, installs to a scratch target):

1. Stale manifest hash: set the `skills/qor-plan/SKILL.md` entry of `qor/dist/variants/claude/manifest.json` to 64 zeros. `python qor/scripts/check_variant_drift.py` prints `OK: 406 files, no drift` and exits 0; `python -m qor.cli install --host claude --target <t>` prints `Installed 78 files to claude`; the receipt row for that file carries `0000...0000` while the installed file hashes to `921f39ce...1678`.
2. Edited shipped bytes: append a line to `qor/dist/variants/claude/skills/qor-plan/SKILL.md` without recompiling. The drift check exits 1 on that file, but install still exits 0 and the receipt row carries the manifest value `921f39ce...1678` while the installed file hashes to `e97a96f9...5644`.
3. Unlisted file: drop that entry from the claude manifest. The drift check prints `OK: 406 files, no drift`; install prints `Installed 77 files to claude` and silently leaves `skills/qor-plan/SKILL.md` out.
4. Line-ending rewrite: clone the base with `core.autocrlf=true`. Five `.yml`/`.yaml` files under the claude variant check out with CRLF endings; install exits 0 and 5 receipt rows carry a sha256 that is not the installed file's (`skills/qor-docs-technical-writing/SOURCE.yml`, `skills/qor-docs-technical-writing/agents/openai.yaml`, `skills/qor-meta-log-decision/SOURCE.yml`, `skills/qor-meta-track-shadow/SOURCE.yml`, `skills/qor-repo-scaffold/references/Issue templates/bug_report.yml`).

With the Phase 1 test file applied to the base, `python -B -m pytest tests/test_dist_manifest_integrity.py -q` gives `11 failed, 3 passed` (Phase 1).

## Locked Decisions

### LD-1: what the manifest holds and who writes it

`dist_compile` writes one manifest per variant directory and a top-level copy of the claude entries:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/dist_compile.py | grep -nE '_write_manifest.variant_dir / "manifest.json", files.'` -> `253:        _write_manifest(variant_dir / "manifest.json", files)`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/dist_compile.py | grep -nE '_write_manifest.out_root / "manifest.json", claude_files.'` -> `257:        _write_manifest(out_root / "manifest.json", claude_files)`

Each entry's sha256 is computed over the emitted file's bytes:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/dist_compile.py | grep -nE 'sha = hashlib.sha256.p.read_bytes....hexdigest'` -> `214:        sha = hashlib.sha256(p.read_bytes()).hexdigest()`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/dist_compile.py | grep -nE '"sha256": sha,'` -> `221:            "sha256": sha,`

The one volatile key is the compile timestamp:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/dist_compile.py | grep -nE '"generated_ts": datetime.now'` -> `229:        "generated_ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),`

The other keys are `schema_version` and `files`, and each entry has `id`, `source_path`, `install_rel_path` and `sha256` (lines 216 to 222 and 227 to 231 at the base). The committed tree carries seven manifests (`qor/dist/manifest.json` and one per variant: claude, cline, codex, cursor, gemini, kilo-code). Decision: the manifest schema, `generated_ts` and `dist_compile` are not changed; no compiled file under `qor/dist/` is edited by this plan.

### LD-2: who reads the sha256, and who does not

Install copies each listed file and records the manifest's value, not a hash of the copied bytes:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/install.py | grep -nE 'shutil.copy2.src, dst.'` -> `36:    shutil.copy2(src, dst)`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/install.py | grep -nE 'installed.append.."path": str.dst., "sha256": entry."sha256"...'` -> `67:            installed.append({"path": str(dst), "sha256": entry["sha256"]})`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/install.py | grep -nE 'if not src.exists.. or dst is None:'` -> `63:        if not src.exists() or dst is None:`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/install.py | grep -nE 'installed = _copy_manifest_entries'` -> `91:    installed = _copy_manifest_entries(manifest, source_root, target.install_map, dry_run)`

The receipt file is written by `_write_install_record` (line 41 at the base) and read back only for its `path` values, by uninstall (line 132) and `list --installed` (line 173). `list --available` reads only entry ids from the top-level manifest:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/install.py | grep -nE 'sid = entry."id".'` -> `163:        sid = entry["id"]`

`install_drift_check` does not read any manifest; it hashes source `SKILL.md` files against their installed counterparts:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/install_drift_check.py | grep -nE 'for source in _source_skills.repo.:'` -> `96:    for source in _source_skills(repo):`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/install_drift_check.py | grep -nE 'if _sha256.source. != _sha256.counterpart.:'` -> `103:        if _sha256(source) != _sha256(counterpart):`

`sbom_emit` globs the variant manifests only to name the hosts:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/sbom_emit.py | grep -nE 'for manifest in sorted.variants_dir.glob'` -> `75:    for manifest in sorted(variants_dir.glob("*/manifest.json")):`

and `git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/sbom_emit.py | grep -c sha256` prints `0`. So `qor/install.py` is the only place a manifest sha256 becomes a claim. Decision: the receipt fix is in `qor/install.py`; `install_drift_check` and `sbom_emit` are not changed.

### LD-3: why nothing catches a stale manifest today

The drift check skips every file named `manifest.json`:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/check_variant_drift.py | grep -nE '^_DRIFT_EXCLUDE = '` -> `22:_DRIFT_EXCLUDE = {"manifest.json"}`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/check_variant_drift.py | grep -nE 'if p.is_file.. and p.name not in _DRIFT_EXCLUDE:'` -> `31:        if p.is_file() and p.name not in _DRIFT_EXCLUDE:`

The gap was already recorded as known and unfixed, in a table row of a dated research brief (the row also names the drift script's line range, so it is cited by command): `git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:docs/research-brief-deep-audit-production-gap-2026-06-09.md | grep -noE 'GAP-ARCH-06 . drift check excludes manifest.json content'` prints `51:GAP-ARCH-06 | drift check excludes manifest.json content`; the same row rates it LOW and CONFIRMED (documented).

In CI the only drift step runs after the full suite in the test matrix:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.github/workflows/ci.yml | grep -nE 'run: python -m pytest tests/ -v'` -> `41:        run: python -m pytest tests/ -v`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.github/workflows/ci.yml | grep -nE 'run: python qor/scripts/check_variant_drift.py'` -> `50:      - run: python qor/scripts/check_variant_drift.py`

and the suite recompiles the committed `qor/dist` in place before that step. `tests/test_cli.py` calls the CLI compile with no output override:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_cli.py | grep -nE 'exit_code = main...compile'` -> `32:    exit_code = main(["compile"])`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/cli.py | grep -nE 'dist_compile.DEFAULT_OUT, dry_run'` -> `45:        dist_compile.DEFAULT_OUT, dry_run=getattr(args, "dry_run", False),`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/dist_compile.py | grep -nE '^DEFAULT_OUT = '` -> `23:DEFAULT_OUT = Path(str(_resources.asset("dist")))`

Observed at the base in a scratch clone: `python -m pytest tests/ -q` gives `3627 passed, 3 skipped, 4 deselected`, after which `git status --short` lists exactly the seven manifests as modified (`7 files changed, 7 insertions(+), 7 deletions(-)`, each the `generated_ts` line), and the drift check then prints `OK: 406 files, no drift`. So the test-matrix drift step compares a fresh compile with itself, and any committed staleness under `qor/dist`, manifest or not, is overwritten before it runs. Decision: this plan does not change `tests/test_cli.py` or the test-matrix step (Non-goals); LD-6 adds a drift step where the committed tree is still intact.

### LD-4: install verifies the bytes it copies and fails closed (GH #440, the receipt)

`_copy_manifest_entries` is replaced by two helpers. `_verified_entries(manifest, source_root, install_map)` walks the entries exactly as the base loop does (same `install_rel_path`, same `_resolve_dest`, same skip when the source is absent or unrouted), reads each copied file's bytes once, and compares `hashlib.sha256(data).hexdigest()` with the entry's `sha256`. It returns the planned copies `(src, dst, data)` and the `install_rel_path` of every mismatch. `_do_install` calls it before anything is written; on any mismatch it prints `Install refused: N file(s) under <source_root> do not match the sha256 in its manifest.json; nothing was installed. Rebuild the dist with 'qor-logic compile' or reinstall the package.` and one `  sha256 mismatch: <install_rel_path>` line per file to stderr, and returns 1, with no file copied and no receipt written. The check runs in a dry run too, since a dry run reports what install would do. `_copy_verified(planned, dry_run)` then writes each planned file's verified bytes (`dst.write_bytes(data)` followed by `shutil.copystat(src, dst)`, the two halves of the `shutil.copy2` it replaces) and records `hashlib.sha256(data).hexdigest()` in the receipt row. Because the bytes are read once, checked, and those same bytes are written, the receipt's sha256 is a hash of the bytes install wrote.

Why this option. It puts the check at the only place a manifest sha256 becomes a claim (LD-2), it holds for every install source (a checkout, a wheel, a hand-edited dist), and it does not depend on CI ordering (LD-3). Recording the computed hash without refusing would make the receipt true but would install bytes the manifest does not describe without saying so; refusing without a message would leave the operator no next step. Entries that install does not copy stay unchecked: they produce no receipt row, and checking them would refuse installs over files the host never receives.

`_do_install` has one caller that matters for behaviour, the CLI dispatch (`qor/cli.py` line 314 at the base), which already returns its exit code. Tests call it directly (`tests/test_cli_install_source.py`, `tests/test_cli_install_gemini.py`, `tests/test_phase21_harness.py`); all build their dist with correct hashes except the gemini fixture on hosts that translate newlines (LD-7). `_copy_manifest_entries` and `_copy_entry` have no caller outside `qor/install.py` (`git grep -n -e '_copy_manifest_entries' -e '_copy_entry' f2e4be9aac7d3f7772969b996b53ff4a7beaede6 -- qor/ tests/` lists only `qor/install.py` lines). Uninstall, `list` and the receipt shape `{"files": [{"path", "sha256"}]}` are unchanged.

### LD-5: the drift check compares manifests except `generated_ts` (GH #440, the exclusion)

`_DRIFT_EXCLUDE` is removed. `hash_tree` hashes `_comparable_bytes(p)` instead of `p.read_bytes()` (line 33 at the base). `_comparable_bytes` returns the file's own bytes, except for a file named `manifest.json`: that is parsed as JSON, the keys in `_VOLATILE_MANIFEST_KEYS = ("generated_ts",)` are dropped from the top-level object, and the rest is serialised with `json.dumps(doc, sort_keys=True)`. An unparseable manifest (`json.loads` raises `ValueError`, which covers `JSONDecodeError` and `UnicodeDecodeError`) is hashed raw, so it differs from any regenerated manifest and is reported as drift instead of raising.

The check already regenerates the whole dist into a temporary directory and compares it file by file (line 60 at the base, `compile_mod.compile_all(tmp_path)`), and the regenerated manifests are built from the regenerated bytes (LD-1). So a committed manifest now passes only when, apart from `generated_ts`, it equals the manifest of a fresh compile: every shipped file listed, nothing unshipped listed, every sha256 equal to the bytes, and the top-level copy equal to the claude one. At the base the committed manifests already pass: with the Phase 3 code the check prints `OK: 413 files, no drift` (406 plus the 7 manifests), before and after a full suite run.

Why this option. It reuses the comparison the check already makes instead of adding a second verifier, and it keeps `generated_ts` exactly as it is. A self-consistency check (committed manifest against committed bytes) would not catch a shipped file missing from both the manifest and the tree when the compile would emit it; the regenerate-and-compare form catches both.

### LD-6: a CI job runs the drift check on the committed dist

The `gate-chain-completeness` job runs on Ubuntu and runs no pytest:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.github/workflows/ci.yml | grep -nE 'gate-chain-completeness:'` -> `76:  gate-chain-completeness:`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.github/workflows/ci.yml | grep -nE '.dev. carries ruff, which the publication-boundary'` -> `92:      # [dev] carries ruff, which the publication-boundary and ruff steps below use.`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.github/workflows/ci.yml | grep -nE 'run: python -m qor.reliability.gate_chain_completeness --phase-min 52'` -> `95:        run: python -m qor.reliability.gate_chain_completeness --phase-min 52`

Line 93 at the base is that job's `pip install -e ".[dev]"` step. Decision: insert one step directly after line 93, named `Variant drift on the committed dist`, with a comment giving the LD-3 reason and `run: python qor/scripts/check_variant_drift.py`. No step before it in that job runs pytest or compiles. The test-matrix step on line 50 is kept as it is. The existing job-shape tests stay green (`tests/test_ci_workflow_gate_chain_completeness.py`, 2 passed with the step added).

### LD-7: dist files check out with LF endings, so the manifest hashes match a Windows checkout

The manifests hash the committed LF bytes, but only the markdown under `qor/dist/` is pinned to LF:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.gitattributes | grep -nE '^qor/dist/.*md text eol=lf'` -> `15:qor/dist/**/*.md text eol=lf`

The repository records that the Windows CI runner checks out with `core.autocrlf`:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.gitattributes | grep -nE 'bound on Windows CI while Linux passed'` -> `11:# bound on Windows CI while Linux passed. Pinning source + dist-variant skill`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:.github/workflows/ci.yml | grep -nE 'os: .ubuntu-latest, windows-latest.'` -> `25:        os: [ubuntu-latest, windows-latest]`

At the base, `git ls-tree -r --name-only f2e4be9aac7d3f7772969b996b53ff4a7beaede6 qor/dist | git check-attr --source=f2e4be9aac7d3f7772969b996b53ff4a7beaede6 --stdin eol` reports `lf` for 339 of the 413 files and `unspecified` for 74: 47 `.toml`, 16 `.yml`, 4 `.yaml` and 7 `.json`. Every index blob is already LF (`git ls-files --eol qor/dist` shows `i/lf` for all 413). Reproduction 4 in the Problem shows the consequence: an autocrlf checkout rewrites the bytes of the unpinned files, and with LD-4 alone `install --host claude` from such a checkout would be refused over those five files (observed in a scratch autocrlf clone with the Phase 2 code and no pin: exit 1, the five `sha256 mismatch:` lines).

Decision: append to `.gitattributes` a comment naming Phase 302 and GH #440 and the rule `qor/dist/** text eol=lf`. No blob changes (`git add --renormalize .` in the scratch clone staged nothing). Observed in a scratch autocrlf clone with the pin: the `.yml` files check out LF, and `install` exits 0 for claude (78 files), codex (78), kilo-code (78) and gemini (47). Sources under `qor/skills/` and `qor/agents/` stay as they are (Non-goals); `qor-logic compile` on such a checkout writes a manifest that hashes whatever bytes it emits, so install stays consistent after a local recompile too.

The gemini install fixture hashes the UTF-8 encoding of its body but writes the body with `write_text`, which translates newlines on Windows:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_cli_install_gemini.py | grep -nE 'sha = hashlib.sha256.body.encode'` -> `21:        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_cli_install_gemini.py | grep -nE 'write_text.body_a, encoding="utf-8".'` -> `14:    (commands / "a.toml").write_text(body_a, encoding="utf-8")`

On the Windows matrix its files would no longer match its manifest once LD-4 lands. Decision: lines 14 and 15 write `body_a.encode("utf-8")` and `body_b.encode("utf-8")` with `write_bytes`, with a one-line comment. This is regression-coverage maintenance of an existing fixture: on Linux the bytes are identical before and after, so no Linux run can show it RED.

### LD-8: residuals and limits

- Install checks only the entries it copies (LD-4). A listed entry whose source file is absent is still skipped silently at install; on the committed dist the LD-5 drift check reports that case (reproduction 3), and a hand-edited installed package is outside CI.
- The drift check compares manifests as parsed JSON (LD-5): a change of key order or whitespace alone is not drift. Every value is compared.
- The test-matrix drift step still runs after the suite recompiles `qor/dist` in place (LD-3). The committed tree is checked in one Ubuntu job (LD-6); a Windows checkout of the committed dist is not drift-checked in CI.
- The Windows CI effect of the LD-7 pin is argued from the repository's own record (lines 11 and 25 cited above) and from the Linux autocrlf simulation; it is not observed on a Windows host while authoring.
- Receipts already written are not rewritten or re-verified; the next install rewrites the receipt with checked values.
- Install reads each copied file into memory once (the claude variant is 78 files); no streaming is added.

### LD-9: tests, determinism and file sizes

The new tests go in a new file, `tests/test_dist_manifest_integrity.py`. They compile a two-file fake source tree into `tmp_path` (the pattern of `tests/test_compile.py` and `tests/test_e2e.py::test_compile_drift_full_cycle`), write the fixture source files and the damaged shipped file with `write_bytes`, and pin `dist_compile`'s clock with `monkeypatch.setattr(compile_mod, "datetime", _FixedClock)` so no result depends on the wall clock. They use no network and no live repository state, except the LF-pin test, which runs `git ls-files` and `git check-attr` on the checkout's own `qor/dist` (a property of the committed attributes, not of any sealed record). The file was observed green twice in a row with the Phase 2 and Phase 3 code (`14 passed`, twice).

`qor/install.py` is 193 lines at the base and 228 after (observed in the scratch clone); `qor/scripts/check_variant_drift.py` is 81 and 103; both stay under the 250-line cap. The new test file is 208 lines. All new and changed source is ASCII.

### LD-10: no spec delta and no documentation change

The only capability specs are `qor/specs/execution-context-governance` and `qor/specs/spec-corpus`; neither covers install or the drift check. No README, doctrine or skill states the manifest exclusion or the receipt's sha256 source: `git grep -n -e '_DRIFT_EXCLUDE' -e 'qorlogic-installed' f2e4be9aac7d3f7772969b996b53ff4a7beaede6 -- README.md 'qor/references/*.md' 'qor/skills/**/*.md'` prints nothing. The research briefs under `docs/` that mention the exclusion are dated historical records and are not edited. The Feature Index row for `qor-logic install` stays accurate (Feature Inventory Touches).

### LD-11: version target is 0.175.6

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.175.5"`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:CHANGELOG.md | grep -nE '^## .0.175.5. - '` -> `13:## [0.175.5] - 2026-09-28`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:docs/META_LEDGER.md | grep -nE '^### Entry #832'` -> `24528:### Entry #832: SESSION SEAL -- Phase 301 a shadow issue no longer claims a threshold breach its own numbers do not show (v0.175.5)`

`change_class: hotfix` bumps `0.175.5` to `0.175.6` at `/qor-substantiate`.

### LD-12: CHANGELOG Unreleased note

`/qor-implement` writes the user-facing note under `## [Unreleased]`; the seal stamps it and refuses an empty section:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:CHANGELOG.md | grep -nE '^## .Unreleased.'` -> `11:## [Unreleased]`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/references/doctrine-changelog.md | grep -nE 'with bullets describing the user-facing effect'` -> `14:  with bullets describing the user-facing effect of their work. Internal`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/references/doctrine-changelog.md | grep -nE 'refactors, ledger entry numbers, and hash values do NOT appear'` -> `15:  refactors, ledger entry numbers, and hash values do NOT appear in the`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/references/doctrine-changelog.md | grep -nE 'changes means this is not a real release'` -> `32:  changes means this is not a real release; check whether a seal is warranted).`

Lines 14 to 16 exclude internal refactors, ledger entry numbers and hash values from the CHANGELOG; line 32 continues the rule that an empty `Unreleased` section raises `ValueError` at the stamp; line 9 allows `Fixed` as a subsection label (lines 9, 13, 16 and 31 carry inline code spans and are paraphrased).

The note is one `### Fixed` bullet with exactly this text:

```markdown
- **Phase 302 (hotfix; the install receipt records only sha256 values checked against the installed bytes, and dist manifests are drift-checked, GH #440)**: `qor-logic install` wrote each file's sha256 from the variant's `manifest.json` into `.qorlogic-installed.json` without hashing the bytes it copied, so a stale or edited manifest, an edited shipped file, or a checkout that rewrote line endings produced a receipt whose sha256 values did not describe the installed files. Install now hashes each file it is about to copy; if any file's hash differs from its manifest sha256, it installs nothing, writes no receipt, names each mismatched file and exits 1, in a dry run as well. The receipt records the sha256 of the bytes written. Manifest entries that install does not copy (no source file, or no install route for the host) are still skipped without a check. `check_variant_drift` no longer excludes `manifest.json`: it compares each manifest with the regenerated one after removing only `generated_ts`, and a CI job now runs it on the committed dist before anything recompiles it. Every file under `qor/dist/` now checks out with LF line endings, so a checkout with `core.autocrlf` keeps the bytes the manifests hash. `docs/release-state.json` records `0.175.5` as `sealed_unpublished`.
```

It is ASCII only and states only what Phases 2 to 4 implement. It names the unchecked entries (the LD-8 residual) instead of claiming every listed file is verified, and says "a CI job" rather than claiming every CI drift step sees the committed tree. Its only `#` number is the issue reference `GH #440`; it carries no ledger entry number and no hash value. Clause to proof:

- install hashes, refuses, installs nothing, writes no receipt, names each file, exits 1, dry run too: `test_install_refuses_bytes_that_do_not_match_the_manifest` (4 items);
- the receipt records the sha256 of the bytes written: `test_install_receipt_hashes_equal_the_installed_bytes`;
- uncopied entries still skipped without a check: `test_install_does_not_verify_an_entry_it_does_not_install`;
- drift compares manifests, removing only `generated_ts`: `test_drift_flags_a_manifest_that_does_not_describe_the_shipped_bytes` (4 items), `test_drift_flags_an_unparseable_manifest`, `test_drift_ignores_only_the_generated_timestamp`;
- a CI job runs it on the committed dist before anything recompiles it: `test_a_ci_job_checks_variant_drift_on_the_committed_dist`;
- LF checkout of every `qor/dist/` file: `test_every_committed_dist_file_checks_out_with_lf_line_endings`;
- the release-state record: LD-13.

Its last sentence has the form of the sealed Phase 301 bullet under `## [0.175.5]`, which ends by recording `0.175.4` as `sealed_unpublished`.

### LD-13: release-state continuity for 0.175.5

Once the seal bumps the project version to `0.175.6`, `0.175.5` stops being the implicit candidate, and the coverage rule treats it as an orphan unless a reachable tag or a disposition covers it:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set.exceptions. - .project_version.'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/release_state.py | grep -nE 'if _semver.v. <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`0.175.5` has no release tag on the remote. At the base, `grep -n` for the sentence "No remote tag is created; the seal tag stays local." over `docs/META_LEDGER.md` ends with line 24550, the `**Version**:` line of Entry #832. While authoring, `git ls-remote --tags origin` listed no `v0.173` or later tag; the highest remote tag was `v0.172.2` (observation, 2026-09-28; not a test expectation).

The record at the base ends with `0.175.4` and has no `0.175.5` entry:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:docs/release-state.json | grep -nE '"version": "0.175.(4|5)"'` -> `85:      "version": "0.175.4",`

This phase appends exactly one entry after the `0.175.4` entry, mirroring how Phase 301 recorded `0.175.4`:

- `version`: `0.175.5`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #832); no release tag was pushed to the remote, so the version is sealed but not published.`

The immediate precedent:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:docs/release-state.json | grep -nE 'META_LEDGER #829'` -> `87:      "reason": "Sealed by /qor-substantiate (META_LEDGER #829); no release tag was pushed to the remote, so the version is sealed but not published."`

The changelog rule that excludes ledger entry numbers (LD-12) governs `CHANGELOG.md`, not this record; `qor/references/doctrine-changelog.md` lines 78 and 79 give the record's closed shape (each entry exactly `version`, `state`, `reason`), and lines 91 to 93 make every state an operator-asserted disposition whose validator checks the shape and the dated CHANGELOG section (cited in prose; the lines carry inline code spans). `0.175.5` has a dated section (LD-11), which the validator requires:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

A local seal tag `v0.175.5` is reachable from the base in a local checkout (`git merge-base --is-ancestor v0.175.5 f2e4be9aac7d3f7772969b996b53ff4a7beaede6` exits 0). It is not on the remote, so CI does not see it, and it does not void the disposition:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/references/doctrine-changelog.md | grep -nE 'stays authoritative even if a local seal tag exists'` -> `83:  stays authoritative even if a local seal tag exists. Publishing the version`

Because that local tag covers `0.175.5` locally, the plain local tag-coverage run cannot tell whether the entry is present. The proof therefore uses a CI view that ignores every tag absent from the remote, and runs twice (Phase 4): an in-memory simulation at `/qor-implement`, and a guarded clone proof after the seal commit. The suite consumes the live record:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state.RELEASE_STATE, versions.'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

No `release_state` code changes. The rule the entry relies on is already unit-tested:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

The entry is recorded by `/qor-implement` (Phase 4), not written by hand at seal time. No entry is recorded for `0.175.6`: after the seal it is the implicit candidate. No ledger entry, seal, gate artifact or dated CHANGELOG section is edited.

### LD-14: canonical governance shape

This file is the canonical `docs/plan-qor-phase302-*.md` plan on branch `phase/302-dist-manifest-integrity`, created from the base:

`git show f2e4be9aac7d3f7772969b996b53ff4a7beaede6:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase.nn'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

No other `docs/plan-qor-phase302*.md` exists at the base. The branch stays plan-only until `/qor-audit` returns PASS on this revision. No governance evidence is hand-authored.

## Feature Inventory Touches

- `entry_id`: `FX001` (`qor-logic install`, row 12 of `docs/FEATURE_INDEX.md` at the base; the row carries inline code spans and is paraphrased)
- `operation`: `MODIFIED`
- `test_path`: `tests/test_dist_manifest_integrity.py`
- `test_descriptor`: `install exits 1, copies nothing and writes no receipt when a copied file's bytes do not hash to its manifest sha256; otherwise every receipt sha256 equals the installed file's sha256`

The row's own test file, `tests/test_cli_install_gemini.py`, stays valid; the row is not edited.

## Phase 1: Regression tests

### Affected Files

- `tests/test_dist_manifest_integrity.py` - new file, eight test functions (14 items), written before Phases 2 and 3 (LD-9).

### Changes

Module helpers: `_FixedClock(datetime)` whose `now` returns `datetime(2026, 1, 1, tzinfo=timezone.utc)`; a `dist` fixture that writes `skills/governance/test-skill/SKILL.md` (the line `# test-skill` and a newline) and `agents/governance/test-agent.md` (the line `# agent` and a newline) under `tmp_path`, monkeypatches `compile_mod.SKILLS_SRC`, `compile_mod.AGENTS_SRC` and `compile_mod.datetime`, compiles into `tmp_path / "dist"` and returns it; `_drift(out, monkeypatch, capsys)` sets `sys.argv` to `["check_variant_drift", "--committed", str(out)]`, calls `drift_mod.main()` and returns the exit code and stdout; `_edit_manifest(path, edit)` loads, edits and rewrites a manifest; `SKILL_REL = "skills/test-skill/SKILL.md"`; `ZERO = "0" * 64`. Manifest edits: `_stale_hash` (the `SKILL_REL` entry's sha256 to `ZERO`), `_drop_entry` (remove the `SKILL_REL` entry), `_ghost_entry` (append an `agents/ghost.md` entry with sha256 `ZERO`). Dist damage: `_stale_manifest_hash` (`_stale_hash` on the claude manifest), `_append_to_shipped_file` (append the line `TAMPER` and a newline to the claude `SKILL_REL`).

### Unit Tests

- `tests/test_dist_manifest_integrity.py::test_drift_flags_a_manifest_that_does_not_describe_the_shipped_bytes`, parametrized `stale-hash`, `unlisted-file`, `unshipped-entry` (the three edits on `variants/claude/manifest.json`) and `top-level-index` (`_stale_hash` on `manifest.json`) - asserts the drift check exits 0 on the fresh compile, then, after the edit, exits 1 and prints `~ <manifest path> (content differs)`. Both directions in each item. RED at the base for all four items (exit 0 after the edit).
- `tests/test_dist_manifest_integrity.py::test_drift_flags_an_unparseable_manifest` - writes the single byte `{` to the claude manifest; asserts exit 1 and `~ variants/claude/manifest.json (content differs)`, not an exception. RED at the base.
- `tests/test_dist_manifest_integrity.py::test_drift_ignores_only_the_generated_timestamp` - sets `generated_ts` to `2000-01-01T00:00:00Z` in all seven manifests; asserts exit 0 and output starting `OK: `. GREEN at the base (manifests skipped) and after (the one volatile key removed); it is the counterpart of the first test, where changing any other value is drift.
- `tests/test_dist_manifest_integrity.py::test_install_refuses_bytes_that_do_not_match_the_manifest`, parametrized over damage `stale-manifest-hash` and `edited-shipped-bytes` and over `install` and `dry-run` - calls `_do_install("claude", target_override=<tmp target>, dist_root=dist, dry_run=...)`; asserts exit 1, stderr contains `sha256 mismatch: skills/test-skill/SKILL.md`, no file exists under the target (so no receipt), and stdout has no `Installed`. RED at the base for all four items (exit 0).
- `tests/test_dist_manifest_integrity.py::test_install_receipt_hashes_equal_the_installed_bytes` - installs an undamaged dist; asserts exit 0, the receipt's paths are exactly the installed files other than the receipt, and every row's sha256 equals `hashlib.sha256` of that file's bytes. GREEN at the base and after (pin: an honest manifest still installs, and the receipt describes the installed files).
- `tests/test_dist_manifest_integrity.py::test_install_does_not_verify_an_entry_it_does_not_install` - adds a shipped `extra/x.md` and a manifest entry for it with sha256 `ZERO`; `extra/` has no claude install route; asserts exit 0, no receipt row has `extra` in its path, and the receipt has 2 rows. GREEN at the base and after (pins the LD-4 scope).
- `tests/test_dist_manifest_integrity.py::test_a_ci_job_checks_variant_drift_on_the_committed_dist` - parses `.github/workflows/ci.yml` with `yaml.safe_load`; walks each job's steps in order and asserts some job reaches a step whose `run` contains `check_variant_drift` before any step whose `run` contains `pytest`, `dist_compile` or `qor-logic compile`. RED at the base (the only drift step follows pytest).
- `tests/test_dist_manifest_integrity.py::test_every_committed_dist_file_checks_out_with_lf_line_endings` - runs `git ls-files -z qor/dist` and `git check-attr -z eol -- <paths>` in the repository root; asserts the list is non-empty and every path's `eol` is `lf`. RED at the base (74 files `unspecified`).

TDD: observed RED at the base before Phases 2 and 3 (`11 failed, 3 passed`). Discrimination is proven after Phase 3 by local, uncommitted mutations, each run with `python -B -m pytest tests/test_dist_manifest_integrity.py tests/test_cli_install_gemini.py tests/test_cli_install_source.py tests/test_phase21_harness.py tests/test_compile.py -q` (53 items) and then reverted:

- M1: in `_verified_entries`, replace the sha256 comparison with `if False:` -> all four `test_install_refuses_bytes_that_do_not_match_the_manifest` items FAIL.
- M2: change `if mismatches:` in `_do_install` to `if mismatches and not dry_run:` -> the two `dry-run` items FAIL.
- M3: call `_copy_verified(planned, dry_run)` directly after `_verified_entries` returns, before the refusal -> the two `install` items FAIL (the agent file is copied before the refusal).
- M4: change `if p.is_file():` in `hash_tree` back to `if p.is_file() and p.name != _MANIFEST_NAME:` -> the four `test_drift_flags_a_manifest_that_does_not_describe_the_shipped_bytes` items and `test_drift_flags_an_unparseable_manifest` FAIL.
- M5: set `_VOLATILE_MANIFEST_KEYS = ()` -> `test_drift_ignores_only_the_generated_timestamp` FAILS.
- M6: drop the `try`/`except ValueError` around `json.loads` in `_comparable_bytes` -> `test_drift_flags_an_unparseable_manifest` FAILS (raises).
- M7: replace the new CI step's `run` with `echo removed` -> `test_a_ci_job_checks_variant_drift_on_the_committed_dist` FAILS.
- M8: delete the `qor/dist/** text eol=lf` line -> `test_every_committed_dist_file_checks_out_with_lf_line_endings` FAILS.

Observed in the scratch clone: M1 `4 failed, 49 passed`; M2 `2 failed, 51 passed`; M3 `2 failed, 51 passed`; M4 `5 failed, 48 passed`; M5, M6, M7 and M8 each `1 failed, 52 passed`. Each failing set is exactly the one named above. After each mutation the implementer restores the content and runs the set twice GREEN (`53 passed`, twice).

## Phase 2: Install checks the bytes it copies

### Affected Files

- `tests/test_cli_install_gemini.py` - the fixture writes its TOML bodies with `write_bytes` (LD-7).
- `qor/install.py` - import `hashlib`; `_copy_entry` writes verified bytes; replace `_copy_manifest_entries` with `_verified_entries` and `_copy_verified`; `_do_install` refuses on any mismatch (LD-4).

`_copy_manifest_entries` and `_copy_entry` are private with callers only in `qor/install.py` (LD-4); `_do_install` keeps its signature and return type.

### Changes

- After `import argparse` (line 11 at the base), add `import hashlib`.
- Replace `_copy_entry` (lines 31 to 36 at the base) with:

  ```python
  def _copy_entry(src: Path, dst: Path, data: bytes, dry_run: bool) -> None:
      """Write the already-verified ``data`` (read once from ``src``) to ``dst``."""
      if dry_run:
          print(f"  [dry-run] {src} -> {dst}")
          return
      dst.parent.mkdir(parents=True, exist_ok=True)
      dst.write_bytes(data)
      shutil.copystat(src, dst)
  ```

- Replace `_copy_manifest_entries` (lines 55 to 68 at the base) with:

  ```python
  def _verified_entries(
      manifest: dict, source_root: Path, install_map: dict[str, Path],
  ) -> tuple[list[tuple[Path, Path, bytes]], list[str]]:
      """Resolve the entries install copies and check each file's bytes.
      (Docstring continues: Phase 302 / GH #440 cause; returns (planned,
      mismatches); absent or unrouted entries are neither copied nor checked.)"""
      planned: list[tuple[Path, Path, bytes]] = []
      mismatches: list[str] = []
      for entry in manifest["files"]:
          rel = entry["install_rel_path"]
          src = source_root / rel
          dst = _resolve_dest(rel, install_map)
          if not src.exists() or dst is None:
              continue
          data = src.read_bytes()
          if hashlib.sha256(data).hexdigest() != entry["sha256"]:
              mismatches.append(rel)
              continue
          planned.append((src, dst, data))
      return planned, mismatches


  def _copy_verified(planned: list[tuple[Path, Path, bytes]], dry_run: bool) -> list[dict]:
      installed: list[dict] = []
      for src, dst, data in planned:
          _copy_entry(src, dst, data, dry_run)
          if not dry_run:
              installed.append({"path": str(dst), "sha256": hashlib.sha256(data).hexdigest()})
      return installed
  ```

  The `_verified_entries` docstring is written out in full in the module; the parenthesis above summarizes it.
- In `_do_install`, replace line 91 at the base with:

  ```python
      planned, mismatches = _verified_entries(manifest, source_root, target.install_map)
      if mismatches:
          print(
              f"Install refused: {len(mismatches)} file(s) under {source_root} do not "
              f"match the sha256 in its manifest.json; nothing was installed. "
              f"Rebuild the dist with 'qor-logic compile' or reinstall the package.",
              file=sys.stderr,
          )
          for rel in mismatches:
              print(f"  sha256 mismatch: {rel}", file=sys.stderr)
          return 1
      installed = _copy_verified(planned, dry_run)
  ```

  The dry-run message and the receipt write that follow are unchanged.
- In `tests/test_cli_install_gemini.py`, replace lines 14 and 15 at the base with a two-line comment (Phase 302: write the exact bytes the manifest hashes; `write_text` translates newlines on Windows and install now verifies the hash) and `(commands / "a.toml").write_bytes(body_a.encode("utf-8"))`, `(commands / "b.toml").write_bytes(body_b.encode("utf-8"))`.

### Unit Tests

- The six install items of `tests/test_dist_manifest_integrity.py` turn GREEN (the four refusal items were RED); mutations M1 to M3 (Phase 1).
- The existing install consumers stay GREEN unchanged: `python -m pytest tests/test_cli_install_gemini.py tests/test_cli_install_source.py tests/test_phase21_harness.py tests/test_compile.py tests/test_e2e.py tests/test_dry_run_modes.py tests/test_ci_workflow_gate_chain_completeness.py tests/test_cli_feature_index_backfill.py tests/test_seed_gitattributes.py tests/test_install_sync_with_source.py tests/test_dist_compile_gemini.py -q` (observed `78 passed` at the base and in the scratch clone with Phases 2 to 4 applied).

## Phase 3: Manifests are drift-checked, on the committed dist, with LF checkouts

### Affected Files

- `qor/scripts/check_variant_drift.py` - import `json`; replace `_DRIFT_EXCLUDE` with `_MANIFEST_NAME`, `_VOLATILE_MANIFEST_KEYS` and `_comparable_bytes`; `hash_tree` hashes `_comparable_bytes(p)`; the module docstring says manifests are compared without `generated_ts` (LD-5).
- `.github/workflows/ci.yml` - one step in the `gate-chain-completeness` job (LD-6).
- `.gitattributes` - the `qor/dist/** text eol=lf` rule with its comment (LD-7).

`hash_tree` and `compare` keep their names and signatures; `tests/test_compile.py` and `tests/test_e2e.py` call them and stay GREEN.

### Changes

- After `import hashlib` (line 10 at the base), add `import json`. In the module docstring, after the sentence ending on line 5, add: `A manifest.json is compared as its parsed JSON without the volatile generated_ts key (Phase 302, GH #440).`
- Replace lines 21 and 22 at the base (the comment and `_DRIFT_EXCLUDE`) with:

  ```python
  # Phase 302 (GH #440): manifest.json was excluded from the comparison because
  # it carries a compile-time timestamp. It is now compared with that one key
  # removed, so a manifest whose file list or sha256 values do not describe the
  # shipped bytes is drift.
  _MANIFEST_NAME = "manifest.json"
  _VOLATILE_MANIFEST_KEYS = ("generated_ts",)


  def _comparable_bytes(p: Path) -> bytes:
      """The bytes drift compares: the file's own bytes, except that a manifest
      is compared as its parsed JSON without its volatile keys. An unparseable
      manifest is compared raw, so it differs from any regenerated one."""
      data = p.read_bytes()
      if p.name != _MANIFEST_NAME:
          return data
      try:
          doc = json.loads(data)
      except ValueError:
          return data
      if isinstance(doc, dict):
          doc = {k: v for k, v in doc.items() if k not in _VOLATILE_MANIFEST_KEYS}
      return json.dumps(doc, sort_keys=True).encode("utf-8")
  ```

- In `hash_tree`, change line 31 at the base to `if p.is_file():` and line 33 to `h = hashlib.sha256(_comparable_bytes(p)).hexdigest()`.
- In `.github/workflows/ci.yml`, after line 93 at the base insert:

  ```yaml
        - name: Variant drift on the committed dist
          # Phase 302 (GH #440): the test job runs this after pytest, and the
          # suite recompiles qor/dist in place (test_cli compile), so there it
          # compares a fresh compile with itself. This job runs no pytest, so the
          # check here sees the committed dist and its manifests.
          run: python qor/scripts/check_variant_drift.py
  ```

  (indented to the job's step level, six spaces before `-`).
- At the end of `.gitattributes`, append a blank line, a three-line comment (Phase 302, GH #440: install verifies every shipped dist file against the sha256 its manifest records over the committed LF bytes, so every dist text file is pinned to LF, not only the markdown above) and `qor/dist/** text eol=lf`.

### Unit Tests

- The drift, CI and LF items of `tests/test_dist_manifest_integrity.py` turn GREEN; mutations M4 to M8 (Phase 1).
- `python qor/scripts/check_variant_drift.py` on the committed tree prints `OK: 413 files, no drift` (observed in the scratch clone before and after a full suite run).
- Full suite: `python -m pytest tests/ -q` stays GREEN (observed in the scratch clone with Phases 1 to 4 applied: `3641 passed, 3 skipped, 4 deselected`, base `3627 passed`); after it, `git status --short` lists only the seven manifests (their `generated_ts`), and the drift check still prints `OK: 413 files, no drift`, so the suite's in-place recompile does not turn the test-matrix drift step red. `python -m ruff check qor/ tests/` prints `All checks passed!`; `python -m qor.scripts.publication_boundary_lint --repo-root .` reports `0 finding(s)`.

## Phase 4: Release-state continuity and CHANGELOG note

### Affected Files

- `docs/release-state.json` - append the `0.175.5` `sealed_unpublished` entry (LD-13).
- `CHANGELOG.md` - the Phase 302 bullet under `## [Unreleased]` (LD-12). No dated section is edited.

### Changes

Append the LD-13 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-12 bullet under a `### Fixed` heading in `## [Unreleased]`. `/qor-substantiate` stamps `[0.175.6]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The record is data consumed by the existing suite; `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` and `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` already prove the rule it relies on (LD-13).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` and `python -m pytest tests/test_changelog_format.py -q` stay GREEN.
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.175.6`, remote tags only). At the base, before the entry exists, it prints `{'0.175.5'} {'0.175.5'}` (observed while authoring): the gap is RED. After the entry is appended it must print `set() {'0.175.5'}`: no orphan with the entry, exactly `{'0.175.5'}` with the entry removed in memory (observed in the scratch clone). That shows the entry is what keeps coverage green.
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.175.6` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and entry together. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.175.5` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in scratch clones of the base outside the repository with `origin` set to the real remote and `TMPDIR` inside the scratch area; the simulated commits never entered this repository):
  - base commit (`version = "0.175.5"`), no entry: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.6 (project version 0.175.5)`;
  - a commit that bumps `version` to `0.175.6` without the `[0.175.6]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.175.6 (project version 0.175.6)`;
  - simulated seal commit (`version = "0.175.6"`, `## [0.175.6] - ` section, local `v0.175.6` tag) with Phases 1 to 3 but no `0.175.5` entry: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.5`;
  - the same seal commit with the LD-13 entry added: exit 0, `4 passed`, and the same result on a second run.

## Definition of Done

### Deliverable: the install receipt records only checked sha256 values

- **D1**: `qor-logic install` hashes the bytes of every file it copies and compares each with its manifest sha256; on any mismatch it copies nothing, writes no receipt, names each mismatched `install_rel_path` on stderr and exits 1, in a dry run too; otherwise each receipt row's sha256 is the hash of the bytes written. Entries it does not copy stay unchecked (LD-8), and the LD-12 bullet says so.
- **D2**: `qor/install.py` defines `_verified_entries(manifest: dict, source_root: Path, install_map: dict[str, Path]) -> tuple[list[tuple[Path, Path, bytes]], list[str]]` and `_copy_verified(planned: list[tuple[Path, Path, bytes]], dry_run: bool) -> list[dict]`; `_copy_manifest_entries` is removed; `_do_install` keeps its signature.
- **D3**: no documentation, skill, schema, spec or compiled variant changes (LD-10). Phase 302 follows canonical branch and plan resolution and receives current-revision audit and substantiation evidence before promotion. The `## [Unreleased]` bullet carries exactly the LD-12 text at implement time.
- **D4**: the Phase 1 install items are RED at the base and GREEN after Phase 2; M1 to M3 turn exactly their named items RED; the install consumers stay GREEN (`78 passed`).

### Deliverable: manifests are drift-checked on the committed dist

- **D1**: `check_variant_drift` compares every `manifest.json` with the regenerated one after removing only `generated_ts`, reports an unparseable manifest as drift, and a CI job runs it before anything recompiles `qor/dist`. The test-matrix step after the suite is unchanged (LD-8).
- **D2**: `qor/scripts/check_variant_drift.py` defines `_comparable_bytes(p: Path) -> bytes`, `_MANIFEST_NAME` and `_VOLATILE_MANIFEST_KEYS`; `_DRIFT_EXCLUDE` is removed; `hash_tree` and `compare` keep their signatures. `.github/workflows/ci.yml` gains one step in `gate-chain-completeness`.
- **D3**: `dist_compile`, the manifest schema and `generated_ts` are unchanged (LD-1).
- **D4**: the Phase 1 drift and CI items are RED at the base (except the timestamp pin) and GREEN after Phase 3; M4 to M7 turn exactly their named items RED; the committed tree gives `OK: 413 files, no drift` before and after the full suite.

### Deliverable: dist files check out as the bytes the manifests hash

- **D1**: every tracked file under `qor/dist/` has `eol=lf`, so a `core.autocrlf` checkout keeps the committed bytes and install does not refuse it.
- **D2**: `.gitattributes` gains `qor/dist/** text eol=lf`; no blob changes; the gemini install fixture writes bytes.
- **D3**: sources under `qor/skills/` and `qor/agents/` keep their attributes (Non-goals).
- **D4**: `test_every_committed_dist_file_checks_out_with_lf_line_endings` is RED at the base and GREEN after; M8 turns it RED. The scratch autocrlf clone installs claude, codex, kilo-code and gemini with exit 0 after the pin, and claude with exit 1 without it (LD-7).

### Deliverable: release-state continuity for 0.175.5

- **D1**: after the Phase 302 seal bumps the project version to `0.175.6`, `0.175.5` (sealed on `main` at META_LEDGER #832, with no remote tag) stays covered by a truthful `sealed_unpublished` disposition.
- **D2**: `docs/release-state.json` gains exactly one entry, `0.175.5` / `sealed_unpublished` with the LD-13 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.175.5` to `0.175.6` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `set() {'0.175.5'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.175.6` with a dated `[0.175.6]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_dist_manifest_integrity.py -q` - verifies install refusal and receipt truth, manifest drift in both directions, the committed-dist CI step and the LF pin (14 test items).
- `python -m pytest tests/test_cli_install_gemini.py tests/test_cli_install_source.py tests/test_phase21_harness.py tests/test_compile.py tests/test_e2e.py tests/test_dry_run_modes.py tests/test_ci_workflow_gate_chain_completeness.py tests/test_cli_feature_index_backfill.py tests/test_seed_gitattributes.py tests/test_install_sync_with_source.py tests/test_dist_compile_gemini.py -q` - verifies the existing install, compile, drift, workflow and attribute consumers are unchanged.
- `python qor/scripts/check_variant_drift.py` - verifies the committed dist, manifests included, matches a fresh compile.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -m pytest tests/test_changelog_format.py -q` - verifies the `## [Unreleased]` section with the LD-12 bullet keeps the Keep-a-Changelog structure.
- `python -c "import subprocess; from pathlib import Path; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.175.6'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(rs.coverage_violations(versions, tags, '0.175.6', ex).orphans, rs.coverage_violations(versions, tags, '0.175.6', {k: v for k, v in ex.items() if k != '0.175.5'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `set() {'0.175.5'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s\n' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.175.6' and '## [0.175.6] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.175.6 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.175.6`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the changed modules and the new test file.
- `python -m qor.scripts.publication_boundary_lint --repo-root .` - verifies the publication-boundary surface remains clean.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `tests/test_packaging_install.py` - packaging integration smoke; no packaging surface changes.
- `python -m qor.scripts.dependency_admission_lint` - PR Dependency Review admission steps; no dependency or lockfile changes in this plan.

## Non-goals

- changing the manifest schema, `generated_ts`, `dist_compile`, or any compiled file under `qor/dist/` (LD-1);
- making `tests/test_cli.py` compile outside `qor/dist`, or moving the test-matrix drift step (LD-3, LD-8);
- pinning line endings of sources under `qor/skills/` or `qor/agents/` (LD-7);
- checking entries install does not copy, or files at uninstall or `list --installed` (LD-4, LD-8);
- changing `install_drift_check` or `sbom_emit` (LD-2);
- rewriting receipts already written (LD-8);
- documentation, skill, schema or spec edits (LD-10);
- release-state dispositions for any version other than `0.175.5`, changes to `qor/scripts/release_state.py`, remote tag pushes, or publication;
- hand-issuing governance evidence;
- unrelated repository cleanup.
