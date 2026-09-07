# Research brief: three unverified assumptions about external state

**Date**: 2026-09-07
**Session**: 2026-09-07T1643-325626
**Issues**: GH #427, GH #429, GH #445

## The shared shape

Each of these reads something outside itself and trusts it without checking. Each was correct when written. Each fails quietly rather than loudly.

| Issue | Reads | Assumes | Fails when |
|---|---|---|---|
| #427 | `pyproject.toml` at a computed path | the file is ours | installed beside a package that ships one |
| #429 | the platform marker | an existing file parses | a truncated or partial write |
| #445 | a number written into a docstring | it still describes the code | the code moves |

The absent case is handled correctly in both #427 and #429. The malformed and the foreign cases are not. That asymmetry is the defect, not the individual lines.

## #427: the version stamp is another package's

`ai_provenance._REPO_ROOT` is `Path(__file__).resolve().parent.parent.parent`. In a source checkout that is the repository root. Under an installed package it is **site-packages**, so `_PYPROJECT` becomes `<venv>/Lib/site-packages/pyproject.toml`.

`_read_system_version()` guards on `exists()` and then reads `project.version` from whatever file is there. Measured against the installed copy in this environment:

```
installed at: <venv>/Lib/site-packages/qor/scripts/ai_provenance.py
_REPO_ROOT  : <venv>/Lib/site-packages
_PYPROJECT  : <venv>/Lib/site-packages/pyproject.toml   exists: True
version     : 0.15.1        <- an unrelated package's version
```

That value is stamped as `"version"` on every artifact `build_manifest()` produces, which is every gate artifact.

**`importlib.metadata` alone is not the fix.** Measured in this working tree:

```
importlib.metadata.version("qor-logic") -> 0.109.5
pyproject.toml project.version          -> 0.169.4
```

Metadata reports the last `pip install`, not the working tree, so a source checkout would start under-reporting its own version by sixty releases. Each source is authoritative in exactly one environment and wrong in the other.

The discriminator neither source provides on its own is **identity**: `project.name`. A pyproject that names this project is ours and its version is the truth; one that does not is somebody else's file at a path we computed.

Resolution order that is correct in all three environments:

1. `_PYPROJECT` exists **and** its `project.name` is this project -> use its version. (source checkout)
2. otherwise `importlib.metadata.version(...)`. (installed, including beside a foreign pyproject)
3. otherwise `"unknown"`.

## #429: an existing marker is assumed parseable

```python
if not marker.exists():
    return None
return json.loads(marker.read_text(encoding="utf-8"))
```

Confirmed: a marker containing `{` raises `JSONDecodeError` out of the helper; the absent case returns `None`.

`None` is already the established "no platform state" answer, so a correct degraded value exists. The marker caches detected environment rather than authored state, so discarding a corrupt one loses nothing that cannot be re-detected.

## #445: one drifted claim, and the sweep that decides the fix

`ledger_hash.py::_report_sequence` states `verify` is "a pre-existing Section 4 violation at 97 lines". Measured by AST: 123 lines. Drifted by 26.

The issue proposes a lint only if a sweep finds more than one instance. The sweep was run over every module in `qor/` and `tests/`, by AST, for docstring claims of the form `<name> ... at N lines`, then again with a looser `N lines` pattern including comments:

- **one** load-bearing instance: this one.
- one threshold statement (`modules stay under 250 lines`), which is a policy, not a measurement of a named span, and cannot drift the same way.
- remaining comment hits are vendored or dist-generated files, or unrelated ("read first 15 lines").

So the issue's own criterion selects the cheap fix. Drop the figure, keep the normative clause. A lint guarding a single instance costs more than the instance.

This is the restatement class again: the cure is deletion, not a checker. The number's truth-maker was the code, and nothing re-derived it.

## Boundary note for the operator

GH #427's body on the public issue surface names the unrelated package by name. That is an identity-term reference, and `doctrine-publication-boundary.md:82-83` reserves anonymisation of those for a human operator. It is flagged here rather than edited. This brief and everything downstream of it refer to it only as an unrelated package.

## Reach

`#427` reaches every gate artifact's `version` field, which makes it the only one of the three with a provenance consequence. In THIS repository the stamped value is already correct, because the checkout resolves to the real pyproject, so no committed artifact changes and the phase claims no correction to existing evidence. The defect is real for installed consumers only, which is also why no test caught it: the suite runs from the checkout, where the resolution happens to work.
