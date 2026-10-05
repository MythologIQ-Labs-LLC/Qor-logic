# Plan: Phase 305 - Wheels built with the release tools carry every tracked file under qor/dist, so `list --available` finds its manifest and variant installs copy every listed file; the freeze notices name 0.176.1 as the final release

**change_class**: hotfix

**doc_tier**: standard

**terms**: `[]` (this plan introduces no new term; the plan gate artifact carries `terms: []`)

**boundaries**:
- limitations: the packaging fix is to packaging only; `install` still skips, without a message, a manifest entry whose source file is absent (LD-7); the shipped-set claim is limited to the tracked `qor/dist` tree (413 files at the base): real wheels built with the pinned build tool carried every tracked file, with the setuptools versions observed (84.0.0, and 68.0.0, the floor), and the release workflow builds from a checkout whose committed dist CI's drift check holds equal to a fresh compile (LD-4); the build can drop other paths, among them a path with a dot-prefixed segment (the `build_py` glob) and a path under a directory named `RCS` or `CVS`, or `_darcs` at 84.0.0 (the sdist prune), and that list is not claimed complete; untracked files may or may not ship (LD-4, LD-5, LD-7); a guard test fails if any dist manifest lists a path with a dot-prefixed, `RCS`, `CVS` or `_darcs` segment, so such a file fails CI instead of installing short, but the guard covers only the segments named (LD-5, LD-7); the staged-dist simulation is checked against real builds for the tracked tree only and is not a model of the build (LD-5); release builds resolve setuptools at build time from `setuptools>=68` in an isolated environment, so the setuptools version is not pinned (LD-7); the freeze notices are prose that `freeze_check` checks for presence and non-emptiness only, not for wording (LD-8); the `0.176.0` disposition is an operator-asserted record of the owner's statement that the release run was cancelled, backed by the observed absence of `0.176.0` from the package index (LD-9)
- non_goals: changing `qor/install.py`, `qor/cli.py` or `qor/scripts/dist_compile.py`; making install report or refuse an absent manifest source; adding `cursor` or `cline` to the `qor-logic install --host` choices; pinning the build backend; building a wheel in the test suite; changing `qor/scripts/freeze_check.py` or `qor/scripts/release_state.py`; release publication, tag pushes or triggering the release workflow
- exclusions: the silent skip of absent manifest sources (owner decision, LD-7); the host choices of the `install` command (LD-7); any change after 0.176.1 (the freeze stays in force, LD-8)

**Owner decision (freeze lift)**: Qor-logic is under a maintenance freeze (Phase 304, sealed as `0.176.0`). On 2026-10-05 the owner lifted the freeze for exactly one phase, this Phase 305, to land the packaging fix that was planned, audited and sealed only locally as an earlier "Phase 304 / 0.175.8" on a branch that was abandoned and never pushed. The owner also decided that this phase amends the freeze notices so that `0.176.1` is named the final release and the freeze otherwise stays in force (LD-8). The lift covers this phase only; it does not lift the freeze for any other change.

**Design reference**: the abandoned branch's plan (iteration 3, audit PASS on that branch after two VETOs, both for claims about what setuptools ships beyond what was observed). This plan reuses its design (the glob, the test shape, the guard and the evidence approach). Every citation and observation below was re-derived at the new base; nothing is copied from the old base. Its lessons are kept: no claim about what setuptools ships beyond the tracked `qor/dist` tree observed in real builds, and no exclusion list is claimed complete.

**Issue**: none. The defect was found while preparing a release candidate: after installing the built wheel, `qor-logic list --available` exits 1. The owner decided the fix (packaging only, one `dist/**/*` glob in place of the three variant globs, a staged-dist unit test, a guard for path segments the build is known to drop), the research-gate override with a stated reason, the freeze lift for this phase, and the target `0.176.1`.

**Current base**: `2f3017807a707272cdc0f0bb464a2a13229cbdeb` (`main` after PR #531 merged Phase 304, the maintenance freeze; project version `0.176.0`, sealed at META_LEDGER #846)

**Target version**: `0.176.1` (hotfix bump from `0.176.0`)

**Citation currency**: every `git show ... | grep ... ->` evidence statement below cites `2f3017807a707272cdc0f0bb464a2a13229cbdeb` and was executed against it while authoring (one observed line per statement); so was every quoted `prints` command that reads the repository. The setuptools source lines are quoted as `prints` output of a command that reads the setuptools 84.0.0 or 68.0.0 wheel fetched into a scratch directory, not as `->` evidence, because those files are not in this repository. Each statement's pattern is written exactly as it is run: the patterns use `.` or a bracket class in place of regex metacharacters, so no statement depends on a backslash escape. Lines that carry backticks are not quoted as `->` evidence; they are cited by a `grep -c` or `grep -noE` command whose printed output is quoted in full. Every other command output quoted (`git ls-tree`, `git ls-remote`, package-index queries, wheel builds, installs and scratch runs) was observed on 2026-10-05 at this base. Scratch runs used clones of the base outside the repository, with the Phase 1 test changes and the Phase 2 and Phase 3 edits applied exactly as specified below; nothing built, installed or committed while authoring entered this repository.

## Open Questions

None. The owner decided the approach (packaging only), the glob, the test shape, the freeze lift and its scope, and the version target. LD-9 records the release-state decision for `0.176.0` that the doctrine allows. The silent skip of absent manifest sources is a declared residual (LD-7), not an open question.

## Problem

Two packaging faults, both reproduced at the base with a wheel built from it, and one release-state fault.

1. `qor-logic list --available` reads `qor/dist/manifest.json` from the installed package, and the package data does not ship that file. After installing the built wheel, the command prints `No manifest. Run 'qor-logic compile' first.` to stderr and exits 1. The README tells a user to run it right after `pip install qor-logic` and the install commands (LD-2). The newest version on the package index, `0.172.2`, has the same fault (observed: its wheel, downloaded with `pip download --no-deps qor-logic==0.172.2`, has no `qor/dist/manifest.json` and no `.yml` or `.yaml` file under `qor/dist`; installed in a fresh virtual environment, `qor-logic list --available` prints the same `No manifest` line and exits 1).
2. The package-data globs select only `.md`, `.json` and `.toml` files under `qor/dist/variants/`, so the 20 tracked `.yml` and `.yaml` files of the claude, codex, cursor and kilo-code variants do not ship. Each of those four variant manifests lists 78 files; an install from the wheel copies 73 and says nothing about the other 5, because install skips an entry whose source file is absent (LD-3). The cline and gemini variants carry no such file and install 47 of 47.
3. The freeze notices name `0.176.0` as the final release, and the README says the published package works as documented. The `v0.176.0` tag is on the remote, but nothing of `0.176.0` was published (LD-9), and the published `0.172.2` fails `list --available` (item 1). With this phase, `0.176.1` becomes the final release (owner decision), so the notices must say so (LD-8).

With the Phase 1 test file applied to the base, `python -B -m pytest tests/test_package_data_ships_dist.py -q -p no:cacheprovider` gives `5 failed, 3 passed` (Phase 1).

## Locked Decisions

### LD-1: the base package-data globs select three extensions under qor/dist/variants only

The package-data table:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '^.tool.setuptools.package-data.$'` -> `74:[tool.setuptools.package-data]`

Its three dist globs:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '"dist/variants/[*][*]/[*][.]md",'` -> `87:    "dist/variants/**/*.md",`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '"dist/variants/[*][*]/[*][.]json",'` -> `88:    "dist/variants/**/*.json",`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '"dist/variants/[*][*]/[*][.]toml",'` -> `89:    "dist/variants/**/*.toml",`

No other package-data line names `dist` (`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -cE 'dist/'` prints `3`). `include-package-data` is on, but the repository has no `MANIFEST.in` (`git ls-tree --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb | grep -ciE '^manifest[.]in$'` prints `0`), and the built wheel shows it adds none of the missing files (LD-4):

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '^include-package-data = '` -> `68:include-package-data = true`

The committed dist holds 413 files (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | wc -l` prints `413`). One is the root manifest (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | grep -cE '^qor/dist/manifest[.]json$'` prints `1`), 20 are `.yml` or `.yaml` files (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | grep -cE '[.]ya?ml$'` prints `20`), all 20 under the claude, codex, cursor and kilo-code variants (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | grep -E '[.]ya?ml$' | grep -cE '^qor/dist/variants/(claude|codex|cursor|kilo-code)/'` prints `20`), and every other file ends in `.md`, `.json` or `.toml` (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | grep -vcE '[.](md|json|toml|ya?ml)$'` prints `0`). The three globs therefore leave out exactly 21 tracked files: the root manifest and the 20 YAML files.

### LD-2: `list --available` reads the root manifest from the installed package

The dist root is the package's own `dist` resource:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/cli.py | grep -nE 'return Path.str._resources.asset."dist"...'` -> `22:    return Path(str(_resources.asset("dist")))`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/cli.py | grep -nE '"list": lambda: _do_list.args.,'` -> `322:        "list": lambda: _do_list(args),`

`_list_available` loads the root manifest there and exits 1 when it is absent:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE '^def _list_available'` -> `191:def _list_available() -> int:`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'manifest = _load_manifest.dist_root / "manifest.json".'` -> `194:    manifest = _load_manifest(dist_root / "manifest.json")`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'No manifest. Run .qor-logic compile. first'` -> `196:        print("No manifest. Run 'qor-logic compile' first.", file=sys.stderr)`

The compile writes that root file as the index for this command (the docstring line carries backticks, so its prefix is quoted with `-o`): `git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/dist_compile.py | grep -noE 'as a backwards-compatible cross-variant index for'` prints `241:as a backwards-compatible cross-variant index for`, and the write itself:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/dist_compile.py | grep -nE '_write_manifest.out_root / "manifest.json", claude_files.'` -> `257:        _write_manifest(out_root / "manifest.json", claude_files)`

The README documents the command as the step after install:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:README.md | grep -nE '^qor-logic list --available$'` -> `82:qor-logic list --available`

The existing behavioral test of this command stages its own manifest under `tmp_path`, so it passes whatever the package ships:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_cli_feature_index_backfill.py | grep -nE '_stage_manifest.tmp_path, ..qor-plan'` -> `36:    _stage_manifest(tmp_path, ["qor-plan", "qor-audit", "qor-plan"])`

The root manifest lists 78 entries (`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/dist/manifest.json | grep -cE '"install_rel_path"'` prints `78`) with 47 distinct ids (observed: `list --available` from the fixed wheel prints 47 lines, equal in order to the de-duplicated ids of that manifest).

### LD-3: an install skips the absent YAML sources without a message

The claude, codex, cursor and kilo-code variant manifests each list 78 files and cline and gemini 47 each: `for h in claude codex cursor kilo-code cline gemini; do git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/dist/variants/$h/manifest.json | grep -cE '"install_rel_path"'; done` prints `78`, `78`, `78`, `78`, `47` and `47`, one per line. The compile builds each variant manifest from every file under the variant directory, whatever its extension:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/dist_compile.py | grep -nE 'for p in sorted.variant_root.rglob."[*]".'` -> `210:    for p in sorted(variant_root.rglob("*")):`

Install skips an entry whose source is absent, by design and documented:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'file whose bytes do not. Entries whose source file is absent, or that no'` -> `69:    file whose bytes do not. Entries whose source file is absent, or that no`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'if not src.exists.. or dst is None:'` -> `78:        if not src.exists() or dst is None:`

The install record lists one entry per copied file:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'installed.append.'` -> `93:            installed.append({"path": str(dst), "sha256": hashlib.sha256(data).hexdigest()})`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE '_write_install_record.target.base, installed.'` -> `132:        _write_install_record(target.base, installed)`

The `install` command offers four hosts; cursor and cline are installable through `_do_install` and `qor.hosts.resolve`, not from the command line:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/cli.py | grep -nE '^_HOSTS_CHOICES = '` -> `145:_HOSTS_CHOICES = ["claude", "kilo-code", "codex", "gemini"]`

Observed with the base wheel installed in a fresh virtual environment, run outside the repository: `qor-logic install --host claude` (and `codex`, `kilo-code`) with `--target` exits 0, prints `Installed 73 files to <host>`, and its install record lists 73 files; `--host gemini` lists 47. Through `_do_install` against the staged base dist, cursor installs 73 of 78 and cline 47 of 47 (the Phase 1 RED run).

### LD-4: one glob; real wheels carry every tracked file under qor/dist

Decision: in `[tool.setuptools.package-data]` `qor`, replace lines 87 to 89 at the base with the single line `    "dist/**/*",`. No other line of `pyproject.toml` changes.

Why this option. The compile defines each variant manifest as every file under the variant directory (LD-3). A glob with no extension filter selects every tracked file under `qor/dist` the same way, so a compiled file with a new extension is selected without another packaging change. Whether the build ships a path also depends on its segment names, which the extension does not change (LD-5, LD-7). Adding the root manifest and two YAML globs would fix today's 21 files and leave the next new extension to recur silently. Changing install or the compile instead would leave the package without files its own manifests list.

The release workflow builds with the pinned tools:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:.github/workflows/release.yml | grep -nE 'run: pip install --require-hashes -r requirements-release.txt$'` -> `55:        run: pip install --require-hashes -r requirements-release.txt`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:.github/workflows/release.yml | grep -nE 'run: python -m build$'` -> `56:      - run: python -m build`

The pinned build tool is `build` 1.6.1 (`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:requirements-release.txt | grep -cE '^build==1[.]6[.]1 '` prints `1`).

Observed while authoring, with wheels built from scratch clones of the base by `build` 1.6.1 run as `python -m build`, which builds the sdist and then the wheel from it in isolated environments; the backend resolved to setuptools 84.0.0 (the wheel's `Generator` line). Both wheels carry the base project version, `0.176.0`, because the bump happens at the seal:

- base: the wheel holds 578 files under `qor/` that do not end in `.py`, set-equal to the 578 files the recursive `glob.glob` of the package-data globs selects relative to `qor/`; the sdist and the wheel each hold 392 of the 413 tracked `qor/dist` files, and the 21 missing are the root manifest and the 20 YAML files;
- with Phases 1 to 3 applied: the wheel holds 599 such files, set-equal to the 599 the same simulation selects, and the sdist and the wheel each hold all 413 tracked `qor/dist` files and no other file under `qor/dist`;
- the fixed wheel installed in a fresh virtual environment, run outside the repository: `qor-logic list --available` exits 0 and prints 47 lines, equal in order to the de-duplicated ids of the root manifest, and `qor-logic install` with `--target` exits 0 and lists 78 files in the install record for claude, codex and kilo-code and 47 for gemini; the base wheel gives exit 1 with the `No manifest` line, and 73, 73, 73 and 47.

Observed in further scratch clones of the base with Phases 1 to 3 applied, built the same way:

- with untracked `RCS/y.md`, `variants/claude/CVS/x.md`, `variants/claude/skills/qor-plan/_darcs/z.md`, `.hidden`, `variants/claude/.DS_Store`, `variants/claude/.cfg/inner.md` and `notes.tmp` under `qor/dist` (`Generator: setuptools (84.0.0)`): the LD-5 simulation selects 603 files under `qor/` that do not end in `.py` and the wheel holds 600; the sdist and the wheel each hold 414 files under `qor/dist`, the 413 tracked files plus `notes.tmp`; the `RCS`, `CVS` and `_darcs` files are selected by the simulation and are in neither the sdist nor the wheel, and the three dot-prefixed paths are in none of the three;
- the same tree built with the isolated build environment constrained to `setuptools==68.0.0` (through `PIP_CONSTRAINT`; the build log lists `setuptools==68.0.0` and the wheel's `Generator` line reads `bdist_wheel (0.48.0)`): the wheel holds 601 such files; the sdist and the wheel each hold 415 files under `qor/dist`, the 413 tracked files plus `notes.tmp` and the `_darcs` file; the `RCS` and `CVS` files and the three dot-prefixed paths are in neither;
- with an untracked `qor/dist/variants/claude/skills/qor-plan/CVS/notes.md` and the claude manifest's file list rebuilt with `dist_compile._build_manifest_entries`, leaving out the manifest's own entry (79 entries): the new test file gives `1 failed, 7 passed`, the failure being the LD-5 guard, on two runs in a row; the wheel built from that tree (84.0.0) lacks the file while its claude manifest lists it, and installed in a fresh virtual environment, `qor-logic install --host claude --target <scratch>` exits 0, prints `Installed 78 files to claude`, and its install record lists 78 files. The guard is what catches this case before a build.

So the shipped-set claim of this plan is this: a wheel built with the pinned build tool carried every tracked file under `qor/dist`, 413 at the base, with setuptools 84.0.0 and with 68.0.0. The plan makes no claim about any other path. The build can drop other paths, among them those named in LD-5, and that list is not claimed complete; an untracked file may or may not ship (LD-7). The release workflow builds from a checkout, and CI runs `python qor/scripts/check_variant_drift.py`, which holds the committed dist equal to a fresh compile.

### LD-5: tests stage the selected dist, run the two commands against it, and guard the manifest paths

New file `tests/test_package_data_ships_dist.py`. No build, no network, no clock, no subprocess.

- `_package_data_globs()` reads `[tool.setuptools.package-data]` `qor` from the live `pyproject.toml` with `tomllib`, as `tests/test_package_data_ships_matrix.py` does.
- `_stage_shipped_dist(dest)` selects, for every glob, `glob.glob(pattern, root_dir=QOR, recursive=True)` entries that are files under `qor/`, normalizes each with `Path(rel).as_posix()`, copies those starting with `dist/` to the same relative path under `dest` (`shutil.copyfile`), and returns `dest / "dist"`. The normalization keeps the `dist/` prefix test true on Windows, where `glob` returns backslash separators; CI runs the suite on Windows:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:.github/workflows/ci.yml | grep -nE 'os: .ubuntu-latest, windows-latest.'` -> `25:        os: [ubuntu-latest, windows-latest]`

- `HOSTS` is the sorted names of the directories under `qor/dist/variants` (claude, cline, codex, cursor, gemini, kilo-code), so a new variant is covered without a test change.
- `test_list_available_reads_the_shipped_root_manifest(tmp_path, monkeypatch, capsys)`: stages the dist, monkeypatches `qor.cli._default_dist_root` to return it (the pattern `tests/test_cli_feature_index_backfill.py` uses), calls `_do_list(argparse.Namespace(available=True))`, and asserts the return code is 0 and the printed lines equal, in order, the de-duplicated ids of the live `qor/dist/manifest.json`.
- `test_install_from_the_shipped_dist_installs_every_manifest_file(tmp_path, host)`, parametrized over `HOSTS`: calls `_do_install(host, target_override=tmp_path / "target", dist_root=<staged dist>)`, asserts it returns 0, that exactly one `.qorlogic-installed.json` exists under the target, and that the number of files the record lists equals the number of files the live `qor/dist/variants/<host>/manifest.json` lists. The counts are bound to two integer locals before the assert, so a failure prints the two counts only.
- `BUILD_DROPPED_SEGMENTS` is `{"RCS", "CVS", "_darcs"}`. `_listed_paths()` returns every `install_rel_path` of the root manifest, and for each host in `HOSTS` every `install_rel_path` of `qor/dist/variants/<host>/manifest.json` prefixed with `variants/<host>/`, the path under `qor/dist` that install reads it from:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'source_root = dist_root / "variants" / host$'` -> `54:    source_root = dist_root / "variants" / host`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'rel = entry."install_rel_path".$'` -> `75:        rel = entry["install_rel_path"]`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/install.py | grep -nE 'src = source_root / rel$'` -> `76:        src = source_root / rel`

- `test_no_manifest_path_has_a_segment_the_build_drops()`: collects the paths of `_listed_paths()` that have a `/`-separated segment starting with `.` or equal to one of `BUILD_DROPPED_SEGMENTS`, and asserts that list is empty, so a failure names the paths. It reads only the live manifests and asserts on their content, so it holds on every platform. It is GREEN at the base and after: no tracked `qor/dist` path has such a segment (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | grep -cE '(^|/)(RCS|CVS|_darcs)(/|$)'` prints `0`, and the dot-prefixed count below is `0`). The guard is deliberately stricter than the build: it also rejects a file whose own name is one of those, and a variant directory name. It does not claim that the segments it names are all the build drops (LD-7).

The expected values come from the live manifests, not from constants, so a recompile that changes the file counts needs no test change. Observed at the base with the file applied: `5 failed, 3 passed` (the list test with `assert 1 == 0`, and claude, codex, cursor and kilo-code each with `assert 73 == 78`; cline, gemini and the guard pass), twice in a row. With Phase 2 applied: `8 passed`, twice in a row. The file is 93 lines and ASCII; with it in place `python -m ruff check qor/ tests/` prints `All checks passed!`.

The first two tests prove the selection the globs make, as Python's recursive `glob.glob` computes it, not what a build ships. Setuptools selects package data with that same standard-library call: its `build_py` command imports the function, and `find_data_files` expands each package-data pattern with it, recursively, and keeps the matches that are files. Observed in the setuptools 84.0.0 wheel, the version the pinned build resolved (LD-4). The wheel was fetched into a scratch directory with `python -m pip download --no-deps setuptools==84.0.0 -d <scratch>`, and each line below is the output of `unzip -p <scratch>/setuptools-84.0.0-py3-none-any.whl setuptools/command/build_py.py` piped to the grep named:

- `grep -nE '^from glob import glob$'` prints `11:from glob import glob`;
- `grep -nE 'globs_expanded = map.partial.glob, recursive=True., patterns.'` prints `131:        globs_expanded = map(partial(glob, recursive=True), patterns)`;
- `grep -nE 'glob_files = filter.os.path.isfile, globs_matches.'` prints `134:        glob_files = filter(os.path.isfile, globs_matches)`;
- `grep -c include_hidden` prints `0`: the call leaves the standard-library `include_hidden` flag at its default, so a pattern without a leading dot matches no name that starts with a dot.

The 68.0.0 floor of the build requirement (LD-7) has the same selection path. Fetched the same way (`python -m pip download --no-deps setuptools==68.0.0 -d <scratch>`), `unzip -p <scratch>/setuptools-68.0.0-py3-none-any.whl setuptools/command/build_py.py` piped to the same greps prints `2:from glob import glob`, `117:        globs_expanded = map(partial(glob, recursive=True), patterns)` and `120:        glob_files = filter(os.path.isfile, globs_matches)`, and `grep -c include_hidden` prints `0`.

Neither selection therefore matches a path with a dot-prefixed segment, as the LD-4 builds showed: neither the simulation nor the sdist nor the wheel held `.hidden`, `.DS_Store` or `.cfg/inner.md`. No tracked `qor/dist` path has a dot-prefixed segment (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor/dist | grep -cE '/[.]'` prints `0`), so at the base the globs select every tracked dist file.

The simulation models the glob selection only. It is checked against real builds for the tracked tree only: the LD-4 wheels built from the tracked tree held exactly the files the simulation selects (set-equal), at the base and after; with untracked files present they did not (LD-4). The suite does not build a wheel (owner decision: no build or network coupling in tests). Beyond the version, which is not pinned (LD-7), these are the known ways the real build diverges from the simulation. The list is not claimed complete; the wheel observations show none removes a tracked file here:

- implicit patterns (`grep -nE '^_IMPLICIT_DATA_FILES = '` on the 84.0.0 `build_py.py` prints `25:_IMPLICIT_DATA_FILES = ('*.pyi', 'py.typed')`): `qor` has no `.pyi` file (`git ls-tree -r --name-only 2f3017807a707272cdc0f0bb464a2a13229cbdeb qor | grep -cE '[.]pyi$'` prints `0`), and `py.typed` is a declared glob already:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '^    "py[.]typed",$'` -> `76:    "py.typed",`

- the files `include-package-data` collects (`grep -nE 'self.manifest_files.get.package, ...,'` on the same file prints `136:            self.manifest_files.get(package, []),`): the repository has no `MANIFEST.in` (LD-1), and the build requirement names setuptools only (LD-7);
- exclusions (`grep -nE 'return self.exclude_data_files.package, src_dir, files.'` on the same file prints `139:        return self.exclude_data_files(package, src_dir, files)`): `pyproject.toml` declares none (`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -cE 'exclude-package-data'` prints `0`);
- the sdist prune. `python -m build` builds the sdist and then the wheel from the unpacked sdist (LD-4), so a path the sdist file list prunes never reaches `build_py`. Setuptools' `sdist` takes its file list from `egg_info`'s `manifest_maker`, which prunes it. Each line below is `prints` output of `unzip -p <scratch>/<wheel> <file>` piped to the grep named:
  - 84.0.0, `setuptools/command/sdist.py`: `grep -nE 'self.filelist = ei_cmd.filelist'` prints `65:        self.filelist = ei_cmd.filelist`, and `grep -nE 'super...prune_file_list..$'` prints `166:        super().prune_file_list()`;
  - 84.0.0, `setuptools/command/egg_info.py`: `grep -nE '^class manifest_maker.sdist.:$'` prints `555:class manifest_maker(sdist):`, `grep -nE '^        self.prune_file_list..$'` prints `577:        self.prune_file_list()`, and `grep -c 'def prune_file_list'` prints `0` (it inherits the `sdist` method above);
  - 84.0.0, `setuptools/_distutils/command/sdist.py`: `grep -nE 'def prune_file_list'` prints `388:    def prune_file_list(self) -> None:`, `grep -noE "vcs_dirs = .'RCS', 'CVS'"` prints `407:vcs_dirs = ['RCS', 'CVS'`, `grep -noE "'_darcs'.$"` prints `407:'_darcs']`, and `grep -nE 'self.filelist.exclude_pattern.vcs_ptrn, is_regex=True.'` prints `409:        self.filelist.exclude_pattern(vcs_ptrn, is_regex=True)`: a path with a directory segment named `RCS`, `CVS` or `_darcs` (or a dot-named version-control directory) is pruned;
  - 68.0.0, `setuptools/command/sdist.py`: `grep -nE 'self.filelist = ei_cmd.filelist'` prints `48:        self.filelist = ei_cmd.filelist`;
  - 68.0.0, `setuptools/command/egg_info.py`: `grep -nE '^class manifest_maker.sdist.:$'` prints `534:class manifest_maker(sdist):`, `grep -nE '^        self.prune_file_list..$'` prints `556:        self.prune_file_list()`, `grep -nE 'def prune_file_list'` prints `620:    def prune_file_list(self):`, `grep -noE '[(]RCS.CVS.'` prints `626:(RCS|CVS|`, and `grep -c _darcs` prints `0`: at the floor the method is `manifest_maker`'s own and prunes `RCS` and `CVS` directory segments, not `_darcs`.

  The LD-4 builds agree: at 84.0.0 the `RCS`, `CVS` and `_darcs` files were in neither the sdist nor the wheel; at 68.0.0 the `RCS` and `CVS` files were in neither and the `_darcs` file shipped. The simulation selects all three. No tracked path is affected (count `0`, above).

The compile lists every file under a variant directory, whatever its segment names (LD-3, `rglob`), so a compiled file with a dot-prefixed, `RCS`, `CVS` or `_darcs` segment would be listed by its manifest and not shipped (LD-7). The guard test fails on each of these for a manifest in the tree (mutations M5 to M8, Phase 1); for a dot-prefixed file the LD-5 install test also fails, since the simulation does not select it, while for an `RCS`, `CVS` or `_darcs` file only the guard fails, since the simulation selects it (LD-4).

### LD-6: the existing package-data presence test follows the glob

`test_pyproject_declares_package_data` requires each fragment to appear as a substring of the joined globs:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_packaging.py | grep -nE '"dist/variants/",'` -> `41:        "dist/variants/",`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_packaging.py | grep -nE 'assert fragment in globs_joined'` -> `45:        assert fragment in globs_joined, f"package-data must include {fragment} glob"`

With the LD-4 glob and the base test, `python -B -m pytest tests/test_packaging.py -q -p no:cacheprovider` gives `1 failed, 4 passed` (observed, M4): `dist/**/*` does not contain `dist/variants/`. Decision: change the fragment on line 41 to `"dist/",`, a one-string change. The test keeps its purpose, a presence check that a dist glob is declared. The fragment is weaker than before, since any glob under `dist/` satisfies it, the base globs included; the behavior it stood for is now proven by LD-5, whose tests fail if the package-data globs do not select the root manifest or any variant file listed in a manifest. No other line of `tests/test_packaging.py` changes, and no other test reads the dist globs (`tests/test_package_data_ships_matrix.py` checks the compliance matrix glob only and stays green).

### LD-7: residuals and limits

- Install still skips, without a message, a manifest entry whose source file is absent (LD-3); the owner kept install unchanged. With this phase a wheel built from the committed dist carried all 413 tracked dist files (LD-4), the LD-5 tests show the globs select every file the committed manifests list, and the guard rejects a listed path with a segment named there; a source missing for any other reason, including a path the build drops that the guard does not name, is still skipped silently.
- Release builds resolve setuptools at build time in an isolated environment, constrained only by the build requirement:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '^requires = '` -> `2:requires = ["setuptools>=68"]`

  The tracked-tree observations of LD-4 were made with setuptools 84.0.0 and with the 68.0.0 floor (LD-4, LD-5). Another version could select or prune differently, and no test would see it unless a manifest lists a path the guard names.
- An untracked file under `qor/dist` may or may not ship. The glob selects any file present at build time whose path has no dot-prefixed segment, and some such files shipped (`notes.tmp` in every LD-4 untracked build), while others were dropped by the build (the next bullet). The plan makes no claim about which untracked files ship.
- The build can drop paths under `qor/dist` other than those the plan observed shipping. Known cases, cited and observed at 84.0.0 and at the 68.0.0 floor (LD-4, LD-5): a path with a dot-prefixed segment (the `build_py` glob, both versions), and a path with a directory segment named `RCS` or `CVS` (the sdist prune, both versions) or `_darcs` (the sdist prune at 84.0.0; it shipped at 68.0.0). This list is not claimed complete. The compile lists every file under a variant directory in its manifest (LD-3), so if such a file is ever compiled, an install from the package skips it without a message. None is tracked at the base (LD-5). For a manifest in the tree, the LD-5 guard fails for each case named here (M5 to M8); a path dropped for a reason the guard does not name is not caught, and the suite does not see an untracked file that no manifest lists.
- The `install` command offers claude, kilo-code, codex and gemini only (LD-3); cursor and cline are covered by LD-5 through `_do_install`. The host choices are out of scope.
- Versions already on the package index keep the packaging fault (Problem, item 1); this phase changes no published artifact. Whether `0.176.1` is published is the owner's release action after merge, outside this phase (LD-10).
- The `docs/SYSTEM_STATE.md` paragraph the Phase 304 seal wrote ("v0.176.0, the final release", "v0.176.0 is the tag intended for PyPI publication") is a seal-written record and is not edited; the Phase 305 paragraph that `/qor-substantiate` writes corrects it forward (LD-12).

### LD-8: the freeze is lifted for this phase only; the notices name 0.176.1 as the final release

The owner lifted the maintenance freeze for this one phase (header, owner decision). The freeze otherwise stays in force: this plan does not touch any other frozen property. `freeze_check` checks four properties: the classifier, the absence of a dependabot configuration, the absence of a workflow `schedule` trigger, and a non-empty `## Maintenance freeze` section in README and AGENTS:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/freeze_check.py | grep -nE '^FROZEN_CLASSIFIER = '` -> `30:FROZEN_CLASSIFIER = "Development Status :: 7 - Inactive"`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/freeze_check.py | grep -nE '^FREEZE_HEADING = '` -> `31:FREEZE_HEADING = "## Maintenance freeze"`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/freeze_check.py | grep -nE '^NOTICE_FILES = '` -> `32:NOTICE_FILES = ("README.md", "AGENTS.md")`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/freeze_check.py | grep -nE 'section is empty'` -> `108:            violations.append(f"{name}: {FREEZE_HEADING!r} section is empty")`

Its tests run it on this repository and on a copy of `pyproject.toml`, `README.md` and `AGENTS.md`:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_freeze_check.py | grep -nE '^def test_the_repository_is_frozen'` -> `46:def test_the_repository_is_frozen():  # K0`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_freeze_check.py | grep -nE 'for name in ."pyproject.toml", "README.md", "AGENTS.md".:'` -> `24:    for name in ("pyproject.toml", "README.md", "AGENTS.md"):`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_freeze_check.py | grep -nE 'parametrize."name", ."README.md", "AGENTS.md"..'` -> `87:@pytest.mark.parametrize("name", ["README.md", "AGENTS.md"])`

The notices at the base name `0.176.0`:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:README.md | grep -nE '^## Maintenance freeze$'` -> `34:## Maintenance freeze`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:README.md | grep -nE '^Qor-logic is feature-complete and frozen as of version 0.176.0, its final release. '` -> `36:Qor-logic is feature-complete and frozen as of version 0.176.0, its final release. It has been superseded and receives no further development: no new features, fixes, dependency updates, or releases. The published package stays on PyPI and continues to install and work as documented below. New issues and pull requests are not accepted.`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:AGENTS.md | grep -nE '^## Maintenance freeze$'` -> `6:## Maintenance freeze`

The AGENTS notice line carries backticks, so its prefix is quoted with `-o`: `git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:AGENTS.md | grep -noE '^Qor-logic is frozen at version 0.176.0 and superseded.'` prints `8:Qor-logic is frozen at version 0.176.0 and superseded.`

README is the package long description:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '^readme = '` -> `9:readme = "README.md"`

Decision: replace README line 36 and AGENTS line 8, each with one line, exactly as Phase 3 gives. The README line names `0.176.1` as the final release, says the owner lifted the freeze for that one packaging fix, says `0.176.0` was tagged but never published (LD-9), and drops the sentence "The published package stays on PyPI and continues to install and work as documented below.": the newest published version, `0.172.2`, does not work as documented (Problem, item 1). The AGENTS line names `0.176.1` as the final release and states the one-phase lift and that the freeze is otherwise in force; its rule sentences are unchanged. Both headings and the sections around them are unchanged, so `freeze_check` and `tests/test_freeze_check.py` keep their meaning: observed at the base and with Phases 1 to 3 applied, `qor-logic scripts freeze_check` prints `freeze_check: OK` and exits 0, and `tests/test_freeze_check.py` gives `9 passed`, including the K4 and K5 items that remove each section from a copy and expect a violation.

CLAUDE.md and CONTRIBUTING.md name no version and stay true, so they do not change: `git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:CLAUDE.md | grep -c '0.176'` prints `0`, `git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:CONTRIBUTING.md | grep -c '0.176'` prints `0`, and the CLAUDE rule ends with `git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:CLAUDE.md | grep -noE 'or any other change unless the owner lifts the freeze.'` printing `54:or any other change unless the owner lifts the freeze.`, which this phase follows. The tracked files that name `0.176.0` at the base (`git grep -lE '0[.]176[.]0' 2f3017807a707272cdc0f0bb464a2a13229cbdeb`) are README.md, AGENTS.md, CHANGELOG.md, pyproject.toml, docs/SYSTEM_STATE.md, docs/META_LEDGER.md, the sealed Phase 304 plan, `.agent/staging/AUDIT_REPORT.md` and the Phase 304 gate and intent-lock records; only README.md and AGENTS.md are edited, `pyproject.toml` changes at the seal, and the others are sealed or seal-written records (LD-7, LD-11, LD-12).

### LD-9: release state of 0.176.0 is `sealed_unpublished`

What happened (owner statement, 2026-10-05): the Release run queued for the `v0.176.0` tag was cancelled before anything was published, and there is no GitHub release for `v0.176.0`. This phase does not use the GitHub API, so the run and the release are not observed here. Observed: `git ls-remote --tags origin` lists `refs/tags/v0.176.0` (peeled to `3997423350550da2ad5188d3720f2f6f1cf38a81`, the Phase 304 seal commit), and `git merge-base --is-ancestor 3997423350550da2ad5188d3720f2f6f1cf38a81 2f3017807a707272cdc0f0bb464a2a13229cbdeb` exits 0; `python -m pip index versions qor-logic` prints `qor-logic (0.172.2)` as its first line, and `python -m pip download --no-deps qor-logic==0.176.0 -d <scratch>` ends with `ERROR: No matching distribution found for qor-logic==0.176.0`.

The doctrine separates the two transitions and makes publication need both a remote tag and the release path (`qor/references/doctrine-changelog.md`, lines 57 to 62, cited in prose because they carry inline code spans):

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/references/doctrine-changelog.md | grep -nE 'released/published..: the version.s tag reaches the remote and the'` -> `59:- **released/published**: the version's tag reaches the remote and the`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/references/doctrine-changelog.md | grep -nE 'tag-driven release path runs. Only this is publication.'` -> `60:  tag-driven release path runs. Only this is publication.`

The tag reached the remote; the release path did not publish. So `0.176.0` is sealed and was never published, which is the definition of the `sealed_unpublished` state (line 82, cited in prose), one of the three states the validator allows:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/release_state.py | grep -nE '^STATES = '` -> `32:STATES = frozenset({"sealed_unpublished", "legacy_untagged", "unreachable_tag"})`

The record is where versions whose tag or publication history differs from the ordinary release path are recorded (`qor/scripts/release_state.py` docstring, lines 3 to 5; doctrine line 80, "It is not a release registry"), and every state is an operator-asserted disposition (doctrine lines 91 to 93). `legacy_untagged` (history cannot be reconstructed) and `unreachable_tag` (tag not reachable from `HEAD`) do not describe `0.176.0`. The doctrine can therefore express it truthfully, and no new state is introduced.

Decision: `/qor-implement` appends exactly one entry after the `0.175.7` entry, in the same shape:

- `version`: `0.176.0`
- `state`: `sealed_unpublished`
- `reason`: `Sealed by /qor-substantiate (META_LEDGER #846); the v0.176.0 tag reached the remote, but its release run was cancelled before anything was published, so the version is sealed but not published.`

The record at the base ends with the `0.175.7` entry and has no `0.176` entry:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:docs/release-state.json | grep -nE 'META_LEDGER #839'` -> `102:      "reason": "Sealed by /qor-substantiate (META_LEDGER #839); no release tag was pushed to the remote, so the version is sealed but not published."`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:docs/release-state.json | grep -cE '"version": "0.176'` prints `0`.

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:docs/META_LEDGER.md | grep -nE '^### Entry #846'` -> `24845:### Entry #846: SESSION SEAL -- Phase 304 maintenance freeze: Qor-logic is declared feature-complete and frozen, and a check keeps it frozen (v0.176.0)`

`0.176.0` has a dated CHANGELOG section, which the validator requires:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:CHANGELOG.md | grep -nE '^## .0.176.0. - '` -> `13:## [0.176.0] - 2026-10-05`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/release_state.py | grep -nE 'has no dated CHANGELOG section'` -> `84:        raise ReleaseStateError(f"{path}: {version} has no dated CHANGELOG section")`

Tag coverage after the seal. Once the seal bumps the project version to `0.176.1`, `0.176.0` stops being the implicit candidate. The coverage rule exempts a version with a reachable tag or a disposition:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/release_state.py | grep -nE 'v for v in versions - tags - set.exceptions. - .project_version.'` -> `118:        v for v in versions - tags - set(exceptions) - {project_version}`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/release_state.py | grep -nE 'if _semver.v. <= ceiling'` -> `119:        if _semver(v) <= ceiling`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/release_state.py | grep -nE 'out = _git.repo_root, "tag", "--merged", "HEAD", "--list", "v[*]".'` -> `102:    out = _git(repo_root, "tag", "--merged", "HEAD", "--list", "v*")`

`v0.176.0` is on the remote and reachable from the base, so CI's tag set covers `0.176.0` with or without the entry; the entry is for truthfulness, not coverage, and coverage does not depend on it. A version with both a reachable tag and a disposition is clean under the rule, as the existing test shows:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_release_state.py | grep -nE 'def test_sealed_unpublished_version_with_local_tag_is_clean'` -> `115:def test_sealed_unpublished_version_with_local_tag_is_clean():`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_release_state.py | grep -nE 'def test_disposition_exempts_only_the_named_version'` -> `109:def test_disposition_exempts_only_the_named_version():`

The suite consumes the live record:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_changelog_tag_coverage.py | grep -nE 'exceptions = release_state.load_release_state.RELEASE_STATE, versions.'` -> `54:    exceptions = release_state.load_release_state(RELEASE_STATE, versions)`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:tests/test_changelog_tag_coverage.py | grep -nE 'def test_every_changelog_section_has_tag'` -> `68:def test_every_changelog_section_has_tag():`

The CI view sees only the remote's tags; locally, never-pushed seal tags (among them `v0.175.7`, reachable from the base) cover versions that CI does not. The proof therefore uses a CI view that ignores every tag absent from the remote, and runs twice (Phase 3): an in-memory simulation at `/qor-implement`, and a guarded clone proof after the seal commit. No `release_state` code changes. No entry is recorded for `0.176.1`: after the seal it is the implicit candidate. If `0.176.0` is ever published, the doctrine's rule for this state applies: the entry is removed or changed in that governed release action (doctrine lines 83 and 84).

### LD-10: version target is 0.176.1

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:pyproject.toml | grep -nE '^version = '` -> `7:version = "0.176.0"`

`change_class: hotfix` bumps `0.176.0` to `0.176.1` at `/qor-substantiate`. The release workflow publishes on a pushed `v*.*.*` tag:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:.github/workflows/release.yml | grep -nE "tags: ..v[*].[*].[*]..$"` -> `5:    tags: ['v*.*.*']`

This phase pushes no tag and publishes nothing; pushing `v0.176.1` is the owner's release action after the merge. No claim in this plan or its CHANGELOG bullets says `0.176.1` is published.

### LD-11: CHANGELOG Unreleased notes; the dated 0.176.0 section is corrected forward

`/qor-implement` writes the user-facing notes under `## [Unreleased]`; the seal stamps them and refuses an empty section:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:CHANGELOG.md | grep -nE '^## .Unreleased.'` -> `11:## [Unreleased]`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/references/doctrine-changelog.md | grep -nE 'with bullets describing the user-facing effect'` -> `14:  with bullets describing the user-facing effect of their work. Internal`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/references/doctrine-changelog.md | grep -nE 'refactors, ledger entry numbers, and hash values do NOT appear'` -> `15:  refactors, ledger entry numbers, and hash values do NOT appear in the`

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/references/doctrine-changelog.md | grep -nE 'changes means this is not a real release'` -> `32:  changes means this is not a real release; check whether a seal is warranted).`

The dated `[0.176.0]` bullet says there are no releases after `0.176.0` and that the published package keeps working; the line carries backticks, so it is cited with `-o`: `git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:CHANGELOG.md | grep -noE 'no new features, fixes, dependency updates, or releases after this one. The published package stays on PyPI and keeps working as documented.'` prints `18:no new features, fixes, dependency updates, or releases after this one. The published package stays on PyPI and keeps working as documented.` That section is dated and is not edited; the `### Changed` bullet below corrects it forward.

The notes are one `### Changed` bullet and one `### Fixed` bullet, in that order, with exactly this text:

```markdown
### Changed
- **Phase 305 (hotfix; the freeze notices name 0.176.1 as the final release)**: The owner lifted the maintenance freeze for this one packaging fix; the freeze otherwise stays in force, and no release follows 0.176.1. Version 0.176.0 was tagged but never published: its release run was cancelled before anything was published, and no 0.176.0 package is on PyPI. README (the package long description) and AGENTS.md now name 0.176.1 as the final release, and the README says that 0.176.0 was never published. The README no longer says that the published package works as documented: 0.172.2, the newest version on PyPI on 2026-10-05, lacks `qor/dist/manifest.json`, so `qor-logic list --available` exits 1 after installing it. `docs/release-state.json` records `0.176.0` as `sealed_unpublished`.

### Fixed
- **Phase 305 (hotfix; the package ships the tracked files under `qor/dist`, so `qor-logic list --available` works after a package install and variant installs copy every file their manifest lists)**: The package data shipped only the `.md`, `.json` and `.toml` files under `qor/dist/variants/`. An installed package therefore lacked `qor/dist/manifest.json`, so `qor-logic list --available` exited 1 with `No manifest. Run 'qor-logic compile' first.`, and lacked the 20 `.yml` and `.yaml` files of the claude, codex, cursor and kilo-code variants, so installing one of those variants copied 73 of the 78 files its manifest lists without saying so. The package data now declares one `dist/**/*` glob in place of the three extension globs, and a wheel built from these sources with the release build tools carried every tracked file under `qor/dist`. A new test fails if a dist manifest lists a path with a segment the build is known to drop: a name that starts with a dot, or `RCS`, `CVS` or `_darcs`. Install still skips, without a message, a manifest entry whose source file is absent.
```

Both are ASCII only, name no other project, and carry no ledger entry number, hash value or issue number. They state only what Phases 1 to 3 implement, what the LD-4 builds and the LD-9 index queries observed, and what the owner stated, and they name the residual a reader needs (the silent skip). Clause to proof:

- "The owner lifted the maintenance freeze for this one packaging fix; the freeze otherwise stays in force, and no release follows 0.176.1": the owner decision (header) and LD-8; `freeze_check` stays OK (LD-8);
- "Version 0.176.0 was tagged but never published", "its release run was cancelled before anything was published", "no 0.176.0 package is on PyPI": LD-9 (the remote tag and the index query observed; the cancelled run is the owner's statement);
- "README ... and AGENTS.md now name 0.176.1 as the final release, and the README says that 0.176.0 was never published": Phase 3 and LD-8;
- "0.172.2, the newest version on PyPI on 2026-10-05, lacks `qor/dist/manifest.json`, so `qor-logic list --available` exits 1 after installing it": Problem, item 1 (observed);
- "`docs/release-state.json` records `0.176.0` as `sealed_unpublished`": LD-9 and Phase 3;
- "lacked `qor/dist/manifest.json`", "exited 1", "copied 73 of the 78 files": the LD-3 and LD-4 base-wheel observations, and the five Phase 1 items RED at the base (`assert 1 == 0`, `assert 73 == 78`);
- "one `dist/**/*` glob in place of the three extension globs": Phase 2 (LD-4), and `tests/test_packaging.py` (LD-6);
- "a wheel built from these sources with the release build tools carried every tracked file under `qor/dist`": the LD-4 wheel observations (413 of 413 tracked dist files, with setuptools 84.0.0 and with 68.0.0); the clause names tracked files only and says nothing about other paths;
- the Fixed title's "`qor-logic list --available` works after a package install and variant installs copy every file their manifest lists": the LD-4 installed fixed-wheel observation (47 ids; 78, 78, 78 and 47 files), and `test_list_available_reads_the_shipped_root_manifest` and the six `test_install_from_the_shipped_dist_installs_every_manifest_file` items on the selected files;
- "A new test fails if a dist manifest lists a path with a segment the build is known to drop": `test_no_manifest_path_has_a_segment_the_build_drops` and mutations M5 to M8 (Phase 1); "known" names the LD-5 cases, not a complete list (LD-7);
- "Install still skips, without a message": LD-3 and LD-7.

### LD-12: no spec delta; documentation changes are the two notices only

The only capability specs are `qor/specs/execution-context-governance` and `qor/specs/spec-corpus`; neither covers packaging or the freeze. The README step `qor-logic list --available` (LD-2) becomes true for an installed package built from this revision:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:README.md | grep -nE '^qor-logic list --available$'` -> `82:qor-logic list --available`

No README, doctrine or skill text names the package-data globs (`git grep -nE 'dist/variants/[*][*]' 2f3017807a707272cdc0f0bb464a2a13229cbdeb -- README.md 'qor/references/*.md' 'qor/skills/**/*.md' docs/operations.md` prints nothing). The only documentation edits are the README and AGENTS notice lines (LD-8). `docs/SYSTEM_STATE.md` is written by `/qor-substantiate`; its Phase 304 paragraph says `v0.176.0` is the final release and the tag intended for publication (`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:docs/SYSTEM_STATE.md | grep -noE 'v0.176.0 is the tag intended for PyPI publication once the seal commit is on main with green CI.'` prints `5:v0.176.0 is the tag intended for PyPI publication once the seal commit is on main with green CI.`). That paragraph is a seal-written record and is not edited; the Phase 305 paragraph the seal writes states that `0.176.1` is the final release and that `0.176.0` was tagged but not published (LD-9).

### LD-13: canonical governance shape

This file is the canonical `docs/plan-qor-phase305-*.md` plan on branch `phase/305-package-data-ships-dist`, created from the base:

`git show 2f3017807a707272cdc0f0bb464a2a13229cbdeb:qor/scripts/governance_helpers.py | grep -nE 'plan-qor-phase.nn'` -> `64:    candidates = sorted(docs_dir.glob(f"plan-qor-phase{nn}*.md"))`

No `docs/plan-qor-phase305*.md` exists at the base. The branch stays plan-only until `/qor-audit` returns PASS on this revision. No governance evidence is hand-authored. No sealed plan, ledger entry, seal, gate artifact, intent-lock record or dated CHANGELOG section is edited.

## Feature Inventory Touches

- `entry_id`: `FX003` (`qor-logic list`, line 14 of `docs/FEATURE_INDEX.md` at the base; the row carries inline code spans and is paraphrased)
- `operation`: `n/a-justified`
- `test_path`: `tests/test_package_data_ships_dist.py`
- `test_descriptor`: `list --available against a dist staged from the package-data globs returns 0 and prints exactly the de-duplicated ids of the root manifest`

- `entry_id`: `FX001` (`qor-logic install`, line 12 of `docs/FEATURE_INDEX.md` at the base; paraphrased)
- `operation`: `n/a-justified`
- `test_path`: `tests/test_package_data_ships_dist.py`
- `test_descriptor`: `install of every variant host from a dist staged from the package-data globs returns 0 and its install record lists as many files as that host's manifest`

- `entry_id`: `FX028` (`qor-logic scripts freeze_check`, line 39 of `docs/FEATURE_INDEX.md` at the base; paraphrased)
- `operation`: `n/a-justified`
- `test_path`: `tests/test_freeze_check.py`
- `test_descriptor`: `freeze_check.check returns [] on this repository with the amended notices, and reports README.md or AGENTS.md when its freeze section is removed from a copy`

The three commands keep their code, flags and output: the plan changes the package data `list` and `install` read in an installed package, and the notice text `freeze_check` reads, not the commands, so no row is edited. The rows stay `verified`.

## Phase 1: Regression tests

### Affected Files

- `tests/test_package_data_ships_dist.py` - new file, three test functions (8 items), written before Phase 2 (LD-5).
- `tests/test_packaging.py` - line 41 at the base, the fragment `"dist/variants/",` becomes `"dist/",` (LD-6). No other line changes.

### Changes

Module docstring naming Phase 305 and stating that the tests prove the glob selection, not what a build ships. Module constants `REPO` (two parents above the test file), `QOR` (`REPO / "qor"`), `HOSTS`, `BUILD_DROPPED_SEGMENTS`; helpers `_package_data_globs()`, `_stage_shipped_dist(dest)`, `_manifest(rel)` (reads `QOR / "dist" / rel` as JSON) and `_listed_paths()`; the three tests of LD-5. Imports: `argparse`, `glob`, `json`, `shutil`, `tomllib`, `pathlib.Path`, `pytest`, `qor.cli`, and `_do_install`, `_do_list` from `qor.install`. The `tests/test_packaging.py` fragment change of LD-6.

### Unit Tests

- `tests/test_package_data_ships_dist.py::test_list_available_reads_the_shipped_root_manifest` - `_do_list` with `available=True` against the staged dist returns 0 and prints exactly the root manifest's de-duplicated ids, in order. RED at the base (return code 1: the root manifest is not selected).
- `tests/test_package_data_ships_dist.py::test_install_from_the_shipped_dist_installs_every_manifest_file`, 6 items - `_do_install` from the staged dist returns 0 and its install record lists as many files as the host's manifest. RED at the base for claude, codex, cursor and kilo-code (73 of 78); GREEN at the base and after for cline and gemini (pins: hosts without YAML files keep installing every listed file).
- `tests/test_package_data_ships_dist.py::test_no_manifest_path_has_a_segment_the_build_drops` - no path listed by the root manifest or by any variant manifest (variant paths as install reads them under `qor/dist`) has a segment that starts with `.` or equals `RCS`, `CVS` or `_darcs`; on failure it names the offending paths. GREEN at the base and after on the real tree (a guard, not a RED item: no tracked path has such a segment, LD-5); M5 to M8 show it fails when a manifest lists such a path.
- `tests/test_packaging.py::test_pyproject_declares_package_data` (changed fragment) - GREEN at the base and after; with Phase 2 and the base fragment it fails (M4).

TDD: observed RED at the base before Phase 2: the new file gives `5 failed, 3 passed`, twice in a row, the failing items being the list test and the claude, codex, cursor and kilo-code install items. Discrimination is proven after Phase 2 by local, uncommitted mutations, each run with `python -B -m pytest tests/test_package_data_ships_dist.py -q -p no:cacheprovider` and then reverted (ignored files included):

- M1: restore the three base globs in place of `"dist/**/*"` -> the list test and the claude, codex, cursor and kilo-code install items FAIL.
- M2: the three base globs plus `"dist/manifest.json"` -> only the claude, codex, cursor and kilo-code install items FAIL.
- M3: the three base globs plus `"dist/variants/**/*.yml"` and `"dist/variants/**/*.yaml"` -> only the list test FAILS.
- M4: with Phase 2 applied, restore the base blob of `tests/test_packaging.py` -> `test_pyproject_declares_package_data` FAILS (run with `python -B -m pytest tests/test_packaging.py -q -p no:cacheprovider`).
- M5: add an untracked `qor/dist/variants/claude/skills/qor-plan/CVS/notes.md` and rebuild the claude manifest's file list with `dist_compile._build_manifest_entries`, leaving out the manifest's own entry as a fresh compile does (79 entries) -> only the guard FAILS.
- M6: the same with `qor/dist/variants/claude/.DS_Store` -> the guard and the claude install item FAIL.
- M7: the same with `qor/dist/variants/claude/skills/qor-plan/_darcs/notes.md` -> only the guard FAILS.
- M8: append to the root manifest one entry whose `install_rel_path` is `RCS/x.md` -> only the guard FAILS.

Observed in a scratch clone of the base: M1 `5 failed, 3 passed`; M2 `4 failed, 4 passed`; M3 `1 failed, 7 passed`; M4 `1 failed, 4 passed`; M5 `1 failed, 7 passed`; M6 `2 failed, 6 passed`; M7 `1 failed, 7 passed`; M8 `1 failed, 7 passed`. Each failing set is exactly the one named above. After the mutations were reverted, the new file gives `8 passed` and `tests/test_packaging.py` `5 passed`, twice in a row.

## Phase 2: Ship every tracked file under qor/dist

### Affected Files

- `pyproject.toml` - in `[tool.setuptools.package-data]` `qor`, the three dist globs (lines 87 to 89 at the base) become `"dist/**/*"` (LD-4).

No Python source changes: `qor/install.py`, `qor/cli.py` and `qor/scripts/dist_compile.py` are unchanged (LD-7), and no function signature changes.

### Changes

Replace the three lines `    "dist/variants/**/*.md",`, `    "dist/variants/**/*.json",` and `    "dist/variants/**/*.toml",` with the one line `    "dist/**/*",`, at the same indentation and position. No other line changes.

### Unit Tests

- The 8 items of `tests/test_package_data_ships_dist.py` are GREEN; mutations M1 to M8 (Phase 1).
- The packaging and install consumers stay GREEN: the second entry of `## CI Commands` gives `58 passed` at the base and `58 passed` with Phases 1 and 2 applied, and `1 failed, 57 passed` with Phase 2 and the base `tests/test_packaging.py` (observed in scratch clones).
- `python qor/scripts/check_variant_drift.py` is unaffected: no file under `qor/dist` changes (observed with Phases 1 to 3 applied: `OK: 413 files, no drift`).
- Full suite: `python -m pytest tests/ -q` stays GREEN. Observed in fresh scratch clones of the base, each run from the clone root as `PYTHONPATH=<clone> python -m pytest tests/ -q -p no:cacheprovider`, whose last line is the summary: at the base, `3671 passed, 3 skipped, 4 deselected, 4 warnings` and exit 0; with Phase 1 applied only, `5 failed, 3674 passed, 3 skipped, 4 deselected, 4 warnings` and exit 1, the five failures being the Phase 1 RED items; with Phases 1 to 3 applied, `3679 passed, 3 skipped, 4 deselected, 4 warnings` and exit 0. The warnings count is environment-sensitive, so it is quoted as observed and is not an acceptance criterion. A second `-q` lowers pytest's verbosity below the level at which it prints that summary line, so the counts are read from a single `-q` run.

## Phase 3: Freeze notices, release-state record and CHANGELOG notes

### Affected Files

- `README.md` - line 36 at the base, the freeze notice paragraph, is replaced by the one line below (LD-8). No other line changes.
- `AGENTS.md` - line 8 at the base, the freeze notice paragraph, is replaced by the one line below (LD-8). No other line changes.
- `docs/release-state.json` - append the `0.176.0` `sealed_unpublished` entry (LD-9).
- `CHANGELOG.md` - the two Phase 305 bullets under `## [Unreleased]` (LD-11). No dated section is edited.

`CLAUDE.md`, `CONTRIBUTING.md`, `docs/architecture.md`, `docs/FEATURE_INDEX.md`, `qor/scripts/freeze_check.py` and `tests/test_freeze_check.py` do not change (LD-8).

### Changes

README line 36 becomes exactly:

```markdown
Qor-logic is feature-complete and frozen as of version 0.176.1, its final release. It has been superseded and receives no further development: no new features, fixes, dependency updates, or releases after 0.176.1. The owner lifted the freeze for that one packaging fix; version 0.176.0 was tagged but never published. New issues and pull requests are not accepted.
```

AGENTS line 8 becomes exactly:

```markdown
Qor-logic is frozen at version 0.176.1, its final release, and superseded. The owner lifted the freeze once, for the Phase 305 packaging fix that 0.176.1 carries; the freeze is otherwise in force. Do not start new phases, plans, features, fixes, dependency updates, or releases in this repository. A change requires the owner to lift the freeze explicitly first; `qor-logic scripts freeze_check` and `tests/test_freeze_check.py` keep the frozen state checked.
```

Append the LD-9 entry as the last element of `exceptions`, with the same key order and indentation as the existing entries. No other entry changes. Add the LD-11 bullets under `## [Unreleased]`, `### Changed` first. `/qor-substantiate` stamps `[0.176.1]` and records the seal; this phase writes no ledger entry, tag or dated section.

### Unit Tests

- None added. The notices are prose; the behavior that depends on them is `freeze_check`, already tested (LD-8). The record is data consumed by the existing suite; `tests/test_release_state.py::test_sealed_unpublished_version_with_local_tag_is_clean` and `tests/test_release_state.py::test_disposition_exempts_only_the_named_version` already prove the rule it relies on (LD-9).
- At `/qor-implement`, `python -m qor.scripts.freeze_check --repo-root .` prints `freeze_check: OK` and exits 0, and `python -m pytest tests/test_freeze_check.py -q` gives `9 passed` (observed at the base and with Phases 1 to 3 applied).
- At `/qor-implement`, `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` and `python -m pytest tests/test_changelog_format.py -q` stay GREEN (observed with Phases 1 to 3 applied: `29 passed` and `5 passed`).
- At `/qor-implement`, the CI-view simulation in `## CI Commands` models the post-seal state (project version `0.176.1`, remote tags only) and prints five values: the state the record gives `0.176.0`, whether `0.176.0` is in the CI-view tag set, the orphans with the full record, the orphans with the `0.176.0` entry removed in memory, and the orphans with the `0.175.7` entry removed in memory. At the base it prints `None True set() set() {'0.175.7'}`; with Phases 1 to 3 applied it prints `sealed_unpublished True set() set() {'0.175.7'}` (both observed in scratch clones with `origin` set to the real remote). The first value shows the entry validates and is the only change; the second and fourth show `0.176.0` is covered by its remote tag, with or without the entry; the fifth shows the simulation reports an orphan when a needed disposition is missing.
- Post-seal verification: the substantiating operator runs the guarded CI-view clone proof in `## CI Commands` after `/qor-substantiate` Step 9.5.5 (seal commit and local `v0.176.1` tag exist) and before Step 9.6 (push/merge). It must exit 0, which requires the guard to pass, pytest to pass, and no test to be skipped. It clones the seal commit, so it proves the committed bump, stamp and record together, and it deletes every tag the remote does not have (the local `v0.176.1` and never-pushed tags such as `v0.175.7`), keeping `v0.176.0`. The command holds no backslash. The operator records the observed output in the substantiation hand-off report. A non-zero exit blocks Step 9.6; the legal next action is `/qor-remediate`, and the seal is not pushed. Run earlier, the clone holds a `0.176.0` commit and the guard fails by design.
- Proof that the post-seal verification discriminates (observed while authoring, in scratch clones outside the repository with `origin` set to the real remote, which then listed no `v0.176.1` tag, and `TMPDIR` inside the scratch area; the simulated commits never entered this repository):
  - base commit (`version = "0.176.0"`): exit 1, `CI-view guard FAIL: clone is not a sealed 0.176.1 (project version 0.176.0)`;
  - a commit with Phases 1 to 3 that bumps `version` to `0.176.1` without the `[0.176.1]` CHANGELOG stamp: exit 1, `CI-view guard FAIL: clone is not a sealed 0.176.1 (project version 0.176.1)`;
  - a simulated seal commit (`version = "0.176.1"`, the bullets stamped by `changelog_stamp.apply_stamp` under `## [0.176.1] - 2026-10-05`, local `v0.176.1` tag) with Phases 1 to 3 but with the `0.175.7` entry removed: exit 1, `1 failed, 3 passed`, with `test_every_changelog_section_has_tag` asserting on orphan `0.175.7`; the plain local run of `tests/test_changelog_tag_coverage.py` on the same commit gives `4 passed`, because the local `v0.175.7` tag covers it, which is why the proof uses the CI view;
  - the same seal commit with the full record: exit 0, `4 passed`, and the same result on a second run;
  - that seal commit with only the `0.176.0` entry removed: exit 0, `4 passed` (the remote `v0.176.0` tag covers `0.176.0`; LD-9).

## Definition of Done

### Deliverable: the package ships every tracked file under qor/dist

- **D1**: a wheel built from this revision with the pinned build tool carries every tracked file under `qor/dist`, `qor/dist/manifest.json` and every file the committed variant manifests list among them, so `qor-logic list --available` exits 0 with the root manifest's ids and a variant install copies every listed file (observed for the tracked tree, LD-4). No claim is made about other paths; the build can drop some (LD-7). A dist manifest that lists a path with a dot-prefixed, `RCS`, `CVS` or `_darcs` segment fails the suite. Install's silent skip of an absent source stays (LD-7).
- **D2**: `pyproject.toml` `[tool.setuptools.package-data]` `qor` declares `"dist/**/*"` in place of the three base dist globs; no Python source changes.
- **D3**: the declared residuals are in LD-7 and the plan boundaries, including that the list of paths the build drops is not claimed complete; no sealed record is edited.
- **D4**: the list test and the claude, codex, cursor and kilo-code install items of `tests/test_package_data_ships_dist.py` are RED at the base and GREEN after Phase 2; M1 to M3 turn exactly their named items RED. `test_no_manifest_path_has_a_segment_the_build_drops` is GREEN at the base and after on the real tree, and M5 to M8 turn it RED. The LD-4 wheel observations (578 to 599 selected files, 392 to 413 tracked dist files, `list --available` exit 1 to 0, 73 to 78 files installed; 413 of 413 tracked dist files with setuptools 84.0.0 and 68.0.0) are recorded as authoring evidence, not suite tests.

### Deliverable: the package-data presence test follows the glob

- **D1**: `test_pyproject_declares_package_data` still requires a dist glob, under the new glob.
- **D2**: line 41 of `tests/test_packaging.py` at the base reads `"dist/",`; nothing else in the file changes.
- **D3**: the change is declared and justified in LD-6, including that the fragment is weaker and why LD-5 carries the behavior.
- **D4**: `tests/test_packaging.py` passes after Phase 2; M4 shows the base fragment fails against the new glob.

### Deliverable: the freeze notices name 0.176.1 as the final release; the freeze stays in force

- **D1**: README and AGENTS state that `0.176.1` is the final release, that the owner lifted the freeze for this one phase and that it is otherwise in force; the README states that `0.176.0` was tagged but never published and no longer says the published package works as documented.
- **D2**: README line 36 and AGENTS line 8 at the base are replaced by the Phase 3 lines; the headings, CLAUDE.md, CONTRIBUTING.md, `freeze_check` and its tests are unchanged.
- **D3**: the owner decision is stated in the plan header and LD-8; the dated `[0.176.0]` CHANGELOG section is corrected forward by the `### Changed` bullet, not edited (LD-11); the Phase 305 paragraph `/qor-substantiate` writes to `docs/SYSTEM_STATE.md` states that `0.176.1` is the final release and that `0.176.0` was tagged but not published (LD-12).
- **D4**: with Phase 3 applied, `qor-logic scripts freeze_check` prints `freeze_check: OK` and exits 0, and `tests/test_freeze_check.py` passes, including K4 and K5, which remove each notice section from a copy and expect a violation naming that file.

### Deliverable: release-state record for 0.176.0

- **D1**: after the seal bumps the project version to `0.176.1`, `docs/release-state.json` records `0.176.0` as `sealed_unpublished`, the README notice and the `### Changed` bullet say it was never published, and tag coverage stays clean in the CI view. The seal-written records that call `0.176.0` the final release (the dated `[0.176.0]` CHANGELOG section and the Phase 304 paragraph of `docs/SYSTEM_STATE.md`) keep their text and are corrected forward (LD-11, LD-12).
- **D2**: `docs/release-state.json` gains exactly one entry, `0.176.0` / `sealed_unpublished` with the LD-9 reason. No other entry and no `release_state` code changes.
- **D3**: the entry is recorded by `/qor-implement`, and the seal changes the version from `0.176.0` to `0.176.1` (hotfix). No tag is pushed and nothing is published.
- **D4**: at `/qor-implement`, the CI-view simulation prints `sealed_unpublished True set() set() {'0.175.7'}` and `tests/test_release_state.py` stays GREEN. After the seal commit and before push, the guarded post-seal clone proof exits 0 on the seal commit: its guard confirms `[project].version` is `0.176.1` with a dated `[0.176.1]` CHANGELOG section, and `tests/test_changelog_tag_coverage.py::test_every_changelog_section_has_tag` passes in the CI view (remote tags only), with no skip.

## CI Commands

- `python -m pytest tests/test_package_data_ships_dist.py -q` - verifies the staged package-data selection carries the root manifest for `list --available` and every file each variant manifest lists for install, and that no dist manifest lists a path with a dot-prefixed, `RCS`, `CVS` or `_darcs` segment (8 test items).
- `python -m pytest tests/test_packaging.py tests/test_package_data_ships_matrix.py tests/test_cli_feature_index_backfill.py tests/test_cli_install_gemini.py tests/test_cli_install_source.py tests/test_dist_manifest_integrity.py tests/test_compile.py tests/test_install_sync_with_source.py tests/test_installed_import_paths.py -q` - verifies the packaging, list, install and compile consumers stay green (58 test items).
- `python qor/scripts/check_variant_drift.py` - verifies the committed dist, manifests included, matches a fresh compile.
- `python -m qor.scripts.freeze_check --repo-root .` - verifies the frozen state still holds with the amended notices.
- `python -m pytest tests/test_freeze_check.py -q` - verifies the freeze check on this repository and on regressed copies.
- `python -m qor.scripts.publication_boundary_lint --repo-root . --expect-scope structural` - the CI step: verifies the publication-boundary surface is clean and that the scope reached is the structural scope CI states.
- `python -m pytest tests/test_release_state.py tests/test_changelog_tag_coverage.py -q` - verifies the release-state record validates with the new entry and local tag coverage holds.
- `python -m pytest tests/test_changelog_format.py -q` - verifies the `## [Unreleased]` section with the LD-11 bullets keeps the Keep-a-Changelog structure.
- `python -c "import subprocess; from qor.scripts import release_state as rs; import tests.test_changelog_tag_coverage as t; remote = {l.rsplit('/', 1)[1] for l in subprocess.run(['git', 'ls-remote', '--tags', 'origin'], capture_output=True, text=True, check=True).stdout.split() if l.startswith('refs/tags/v') and not l.endswith('^{}')}; tags = {v for v in rs.merged_semver_tags(t.REPO) if 'v' + v in remote}; versions = t._changelog_versions() | {'0.176.1'}; ex = rs.load_release_state(t.RELEASE_STATE, versions); print(ex.get('0.176.0'), '0.176.0' in tags, rs.coverage_violations(versions, tags, '0.176.1', ex).orphans, rs.coverage_violations(versions, tags, '0.176.1', {k: v for k, v in ex.items() if k != '0.176.0'}).orphans, rs.coverage_violations(versions, tags, '0.176.1', {k: v for k, v in ex.items() if k != '0.175.7'}).orphans)"` - CI-view simulation of the post-seal state at `/qor-implement` (network: reads remote tag names only); expected output `sealed_unpublished True set() set() {'0.175.7'}`.
- `(T=$(mktemp -d) && R=$(git ls-remote --tags origin | awk '{print $2}') && git clone -q --no-local . "$T/c" && git -C "$T/c" tag -l 'v*' | while read tg; do printf '%s' "$R" | grep -qx "refs/tags/$tg" || git -C "$T/c" tag -d "$tg" >/dev/null; done && cd "$T/c" && python -c "import sys, tomllib; v = tomllib.load(open('pyproject.toml', 'rb'))['project']['version']; c = open('CHANGELOG.md', encoding='utf-8').read(); sys.exit(0 if v == '0.176.1' and '## [0.176.1] - ' in c else 'CI-view guard FAIL: clone is not a sealed 0.176.1 (project version ' + v + ')')" && PYTHONPATH=. python -m pytest tests/test_changelog_tag_coverage.py -q -rs -p no:cacheprovider > "$T/out" 2>&1; rc=$?; cat "$T/out" 2>/dev/null; [ "$rc" -eq 0 ] && ! grep -q skipped "$T/out")` - post-seal verification: after `/qor-substantiate` Step 9.5.5 and before Step 9.6, runs the real tag-coverage suite in the CI view (remote tags only) on a clone of the seal commit. It fails unless the clone is a sealed `0.176.1`, and it fails on any skip.
- `python -m pytest tests/ -q` - verifies repository regression safety.
- `python qor/scripts/ledger_hash.py verify docs/META_LEDGER.md` - verifies the ledger chain.
- `python -m ruff check qor/ tests/` - lints the new test file.

## CI Coverage Exemptions

- `python -m qor.reliability.seal_entry_check` - seal-time check; runs at `/qor-substantiate`.
- `python -m qor.reliability.ledger_base_currency` - WARN-only ledger freshness; not affected by this plan.
- `python -m qor.reliability.gate_chain_completeness` - sealed-phase gate-chain check; runs at seal.
- `python -m qor.reliability.intent_lock_committed` - sealed-phase intent-lock check; runs at seal.
- `python -m qor.scripts.seal_artifacts` - seal-artifact currency; runs at seal.
- `python -m qor.scripts.gate_provenance` - sealed-phase provenance verify/attest; runs at seal and in CI with a secret.
- `python -m qor.scripts.status_json --self-test` - nightly health self-test; not affected by this plan.
- `python -m qor.scripts.github_surface` - GitHub-surface scan; not affected by this plan.
- `tests/test_packaging_install.py` - packaging integration smoke (integration marker, deselected by default); it imports modules and resolves resources from the environment it runs in and builds no wheel, so it neither covers nor is changed by the package-data glob. The packaging surface this plan changes is proven by `tests/test_package_data_ships_dist.py` and the LD-4 wheel observation.
- `python -m qor.scripts.dependency_admission_lint` - PR Dependency Review admission steps; no dependency or lockfile changes in this plan.

## Declared Residuals

- Install's silent skip of an absent manifest source (LD-3, LD-7).
- Paths the build can drop beyond the tracked tree, a list not claimed complete; the guard covers only the segments it names (LD-5, LD-7).
- The unpinned setuptools version of release builds (LD-7).
- Untracked files under `qor/dist` may or may not ship (LD-7).
- Published versions on the package index keep the packaging fault; publication of `0.176.1` is outside this phase (LD-7, LD-10).
- The cancelled release run and the absent GitHub release for `v0.176.0` are the owner's statement, not observed here (LD-9).
- The seal-written Phase 304 paragraph of `docs/SYSTEM_STATE.md` and the dated `[0.176.0]` CHANGELOG section keep their text and are corrected forward (LD-11, LD-12).

## Non-goals

- changing install, the compile or the CLI, including making install report or refuse an absent manifest source (LD-7);
- adding `cursor` or `cline` to the `install` command's host choices (LD-7);
- pinning the build backend or building a wheel in the test suite (LD-5, LD-7);
- changing `freeze_check`, its tests, the classifier, the dependabot removal or the workflow schedules, or lifting the freeze beyond this phase (LD-8);
- documentation, doctrine or spec changes other than the two notice lines (LD-8, LD-12);
- hand-editing any compiled file under `qor/dist/`;
- release-state dispositions for any version other than `0.176.0`, changes to `qor/scripts/release_state.py`, remote tag pushes, triggering the release workflow, or publication;
- editing any sealed plan, ledger entry, gate artifact, intent-lock record, seal-written paragraph or dated CHANGELOG section;
- hand-issuing governance evidence;
- unrelated repository cleanup.
