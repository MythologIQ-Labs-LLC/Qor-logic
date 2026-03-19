# Qorelogic — Canonical S.H.I.E.L.D. Skills Repository

Single source of truth for all QoreLogic governance skills.

## Pipeline

```
ingest/ → processed/ → compiled/
```

**Ingest**: Drop raw skills from any source into `ingest/`.
**Process**: Skills are normalized to S.H.I.E.L.D. compliance with consistent structure.
**Compile**: Processed skills are compiled to LLM-specific formats (.claude, .agent, .kilocode).

## Usage

Downstream projects consume compiled output. Never edit skills in project repos directly.
