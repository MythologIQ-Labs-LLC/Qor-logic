# AI Code Quality Doctrine

Rules for writing code that resists degradation from AI agents and human developers alike.
Inspired by QorLogic Section 4 Razor + Ben Swerdlow's AI coding principles.

## 1. Semantic vs Pragmatic Functions

### Semantic Functions (Building Blocks)

Pure logic units. Minimal, correct, reusable.

- Accept all required inputs as parameters, return all outputs directly
- No side effects unless that IS the function's purpose
- Name self-describes the operation — no comments needed
- Safe to reuse without understanding internals
- Break complex logic into a chain of semantic functions
- Each one takes what it needs, returns data for the next, does nothing else

```
Good: calculate_risk_score(action, trust_level) -> f64
Good: validate_workspace_path(raw) -> Result<PathBuf, Error>
Bad:  process_data(input) -> Output  (vague, could do anything)
```

**Testing**: Unit testable in isolation. If it isn't, it's not semantic.

### Pragmatic Functions (Orchestrators)

Wrappers that compose semantic functions with production glue.

- Organize messy real-world flows (webhooks, provisioning, migrations)
- Should NOT be reused in multiple places — if reused, extract semantic functions
- Expected to change completely over time
- MUST have doc comments (unlike semantic functions)
- Doc comments note unexpected behaviors, not obvious ones

```
Good: handle_user_signup_webhook(payload) -> Result<()>
Good: provision_workspace_for_repo(repo_url) -> Result<Workspace>
```

**Testing**: Integration tested within full app context, not unit tested.

### Function Degradation (Anti-Pattern)

Semantic functions morph into pragmatic ones "for ease":
- Someone adds a side effect to a pure function
- Dependents now trigger behavior they didn't intend
- Debugging becomes guesswork

**Rule**: If a semantic function gains side effects, rename it to signal its pragmatic nature or extract the side effect.

## 2. Model Design Rules

### Make Wrong States Impossible

The shape of your data should prevent invalid combinations.

- If two fields should never coexist, the type system must enforce it (use enums, not optional fields)
- Every optional field is a question the rest of the codebase must answer repeatedly
- Every loosely-typed field invites callers to pass incorrect values

```rust
// BAD: optional fields create ambiguity
struct User {
    verified_email: Option<String>,
    pending_verification: Option<String>,  // which one is set?
}

// GOOD: enum enforces exactly one state
enum EmailState {
    Unverified(String),
    Verified(String),
}
```

### Brand Types

Identical shapes can represent different domain concepts.

- Wrap primitives in distinct types: `DocumentId(Uuid)` vs bare `Uuid`
- Accidentally swapping two IDs becomes a compile error, not a silent bug
- Apply to: IDs, paths, tokens, scores — any value with domain meaning

```rust
struct AgentId(String);    // not just String
struct WorkspaceId(String); // compile-time distinct from AgentId
```

### Naming Precision

- Model name should tell you whether any given field belongs
- If the name doesn't indicate membership, the model is trying to be too many things
- Good: `UnverifiedEmail`, `PendingInvite`, `BillingAddress`
- Bad: `UserData`, `InfoObject`, `Payload`

### Composition Over Flattening

When two independent concepts are often needed together, compose them:

```rust
// GOOD: both models stay intact
struct UserWithWorkspace {
    user: User,
    workspace: Workspace,
}

// BAD: flattened fields lose boundary
struct UserWorkspaceBlob {
    user_id: String,
    user_name: String,
    workspace_id: String,
    workspace_path: String,
}
```

## 3. Anti-Slop Rules

Rules that prevent AI-generated code from degrading quality.

### Documentation

- Semantic functions: NO comments (code is self-describing)
- Pragmatic functions: MUST have doc comments
- Doc comments note unexpected behaviors, NOT obvious ones
- Never restate the function name in the doc comment
- Caveat: doc comments may be outdated — fact-check against implementation

### Naming

- Name functions by WHERE they're used, not just WHAT they do
- Names should signal whether behavior is tightly or loosely defined
- Generic names (`process`, `handle`, `manage`, `do`) are code smell
- If you can't name it precisely, the function does too much

### Code Entropy Prevention

- Every added optional field must justify its existence
- Every loosely-typed parameter must prove no stronger type exists
- One coding agent sloppifies a codebase — a swarm does it faster
- Self-describing code is the primary defense against accumulated slop

## 4. Integration with Section 4 Razor

These rules extend (not replace) the existing Section 4 constraints:

| Existing Rule | Extension |
|--------------|-----------|
| Functions <= 40 lines | + Must be classifiable as semantic OR pragmatic |
| Files <= 250 lines | + Single responsibility per file |
| No nested ternaries | + No nested optionals (flatten with enums) |
| Variables are noun/verbNoun | + Model names indicate field membership |
| No unwrap() in production | + No loose typing when brand types are possible |
| Early returns | + Semantic functions: no side effects |
