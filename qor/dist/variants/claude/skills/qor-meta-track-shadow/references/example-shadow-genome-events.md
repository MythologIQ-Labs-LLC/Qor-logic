# Reference: qor-meta-track-shadow event examples (Phase 98, F5+F6)

Three concrete examples of Shadow Genome entries spanning the
common failure modes — dependency bloat, premature optimization,
hallucination. Moved out of `SKILL.md` per the progressive-disclosure
doctrine (`SG-SkillCorpusGrowth-A`) so the skill body stays lean while
the example detail remains available for operators who need it.

## Example 1: Dependency Bloat

```markdown
## Shadow Genome Entry: SG-001

- id: "SG-001"
  timestamp: "2025-12-24T15:30:00Z"
  context: "Week 2 - Implementing database transaction safety"
  attempted_solution: "Use SQLAlchemy ORM for transaction management"
  failure_mode: "COMPLEXITY_VIOLATION"
  why_failed: "Added 5 new dependencies (50MB), introduced complexity in simple use case. Standard sqlite3 library has built-in transaction support."
  impact: "2 hours evaluating, 3 hours testing, 15MB production binary increase"
  lesson_learned: "Check stdlib first before adding dependencies. SQLite transactions are simple: conn.execute('BEGIN'), conn.commit(), conn.rollback()"
  correct_approach: "Manual transaction wrapper using stdlib sqlite3 - 10 lines of code, zero dependencies"
  preventability: "Could have been caught in architecture review with KISS checklist"
```

**Preventive Action Created:**
> Added rule: "Before adding ORM dependency, require proof that raw SQL is insufficient"

## Example 2: Premature Optimization

```markdown
## Shadow Genome Entry: SG-002

- id: "SG-002"
  timestamp: "2025-12-26T10:00:00Z"
  context: "Week 3 - Validation dataset construction"
  attempted_solution: "Implement distributed processing with Celery for dataset generation"
  failure_mode: "PREMATURE_OPTIMIZATION"
  why_failed: "Dataset is 1000 examples, processes in 10 minutes single-threaded. Celery adds Redis dependency, deployment complexity. No measured bottleneck."
  impact: "1 day implementing Celery, 4 hours debugging Redis, added 200MB+ dependencies"
  lesson_learned: "Measure first, optimize second. 10 minutes is acceptable for weekly task. Only parallelize if >1 hour or run frequently."
  correct_approach: "Simple for-loop with tqdm progress bar. Fast enough, zero complexity."
  related_entries: ["SG-001"]
  preventability: "Pre-mortem would have identified: 'What if generation is fast enough without optimization?'"
```

**Preventive Action Created:**
> Added rule: "Performance optimizations require benchmark proving >30min latency or >10 requests/sec load"

## Example 3: Hallucination

```markdown
## Shadow Genome Entry: SG-003

- id: "SG-003"
  timestamp: "2025-12-28T14:00:00Z"
  context: "Week 4 - Tier 3 formal verification design"
  attempted_solution: "Document that PyVeritas provides 100% verification coverage"
  failure_mode: "HALLUCINATION"
  why_failed: "PyVeritas research paper states ~80% accuracy. We claimed 100% without validation. Would have mislead users about system capabilities."
  impact: "Documentation would have been dishonest, violating Divergence Doctrine"
  lesson_learned: "ALWAYS cite exact numbers from source. Never round up. 80% ≠ 100%. Honest limitations build trust."
  correct_approach: "Document 'PyVeritas provides ~80% verification accuracy (per original research), complemented by Z3 for critical paths'"
  preventability: "Sentinel validation caught this before publication. Need to enforce citation accuracy checks."
```

**Preventive Action Created:**
> Added rule: "All quantitative claims must have citation with exact number. No rounding 80→100%."

## Cross-references

- `qor/skills/meta/qor-meta-track-shadow/SKILL.md` — the parent skill body.
- `qor/references/doctrine-shadow-genome-countermeasures.md` `SG-SkillCorpusGrowth-A` — the progressive-disclosure doctrine that drove this move.
- `docs/plan-qor-phase98-meta-skill-examples-to-references.md` — the sealed Phase 98 plan.
