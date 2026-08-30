# Qor-logic Refactor Examples and Templates

This reference contains the example transformations and report templates used by /qor-refactor.

The transformation examples below are illustrative and use TypeScript for concreteness. The pattern they show (decomposition, flattening, ternary elimination, renaming) applies regardless of language; discover the target environment's own idioms rather than porting these examples literally.

## Function Decomposition Example

```typescript
// BEFORE: 60-line monolith
function processOrder(order) {
  // validation (15 lines)
  // ...
  // transformation (20 lines)
  // ...
  // persistence (15 lines)
  // ...
  // notification (10 lines)
  // ...
}

// AFTER: Specialized sub-functions
function processOrder(order) {
  const validatedOrder = validateOrder(order);
  const transformedOrder = transformOrder(validatedOrder);
  const savedOrder = persistOrder(transformedOrder);
  notifyOrderComplete(savedOrder);
  return savedOrder;
}

function validateOrder(order) {
  /* 15 lines */
}
function transformOrder(order) {
  /* 20 lines */
}
function persistOrder(order) {
  /* 15 lines */
}
function notifyOrderComplete(order) {
  /* 10 lines */
}
```

## Logic Flattening Example

```typescript
// BEFORE: 4 levels (VIOLATION)
function getUser(id) {
  if (id) {
    const user = db.find(id);
    if (user) {
      if (user.active) {
        if (user.verified) {
          return user;
        }
      }
    }
  }
  return null;
}

// AFTER: 1 level (COMPLIANT)
function getUser(id) {
  if (!id) return null;

  const user = db.find(id);
  if (!user) return null;
  if (!user.active) return null;
  if (!user.verified) return null;

  return user;
}
```

## Ternary Elimination Example

```typescript
// BEFORE: Nested ternary (VIOLATION)
const status = isActive
  ? (isPremium ? "active-premium" : "active-basic")
  : "inactive";

// AFTER: Explicit logic (COMPLIANT)
function getStatus(isActive, isPremium) {
  if (!isActive) return "inactive";
  return isPremium ? "active-premium" : "active-basic";
}
const status = getStatus(isActive, isPremium);
```

## Variable Renaming Examples

| Generic (BAD) | Explicit (GOOD)      |
| ------------- | -------------------- |
| `x`           | `userCount`          |
| `data`        | `responsePayload`    |
| `obj`         | `configOptions`      |
| `temp`        | `intermediateResult` |
| `item`        | `orderLineItem`      |
| `result`      | `validationOutcome`  |

## Orphan Detection Report (Template)

```markdown
### Orphan Detection Report

| File   | Connected   | Import Chain        |
| ------ | ----------- | ------------------- |
| [path] | OK          | main -> App -> [file] |
| [path] | FAIL ORPHAN | No import found     |
```

## File Splitting Example

```
BEFORE:
src/utils.ts (400 lines)
  - stringHelpers (80 lines)
  - dateHelpers (120 lines)
  - validationHelpers (100 lines)
  - formatters (100 lines)

AFTER:
src/utils/
  - index.ts (re-exports)
  - stringHelpers.ts (80 lines)
  - dateHelpers.ts (120 lines)
  - validationHelpers.ts (100 lines)
  - formatters.ts (100 lines)
```

## God Object Elimination Example

```typescript
// BEFORE: God Object
class UserManager {
  // User CRUD (should be UserRepository)
  createUser() {}
  getUser() {}
  updateUser() {}
  deleteUser() {}

  // Authentication (should be AuthService)
  login() {}
  logout() {}
  validateToken() {}

  // Email (should be EmailService)
  sendWelcome() {}
  sendPasswordReset() {}
}

// AFTER: Single Responsibility
class UserRepository {
  /* CRUD only */
}
class AuthService {
  /* auth only */
}
class EmailService {
  /* email only */
}
```

## Dependency Audit (Template)

```markdown
### Dependency Audit

| Package | Used | Stdlib Possible | Recommendation  |
| ------- | ---- | ---------------- | --------------- |
| lodash  | OK   | Yes (3 lines)    | REMOVE          |
| dayjs   | OK   | No               | KEEP            |
| uuid    | FAIL | N/A              | REMOVE (unused) |
```

Column names generalize across ecosystems: "Package" may be a crate, module, or gem; "Stdlib Possible" asks whether the target language's own standard library replaces it in a small, justified amount of code.

## Section 4 Compliance Report (Template)

```markdown
### Section 4 Razor Compliance After Refactor

| File   | Lines   | Max Function | Max Nesting | Status |
| ------ | ------- | ------------ | ----------- | ------ |
| [path] | [X]/250 | [X]/40       | [X]/3       | OK/FAIL |
```

## Simplification Test Finding (Template)

Record one of these per breach identified in Step 2, before touching code.

```markdown
### Finding: [file:line or symbol]

1. Complexity removed: [description]
2. Why unnecessary/obscuring: [reasoning]
3. Contract that must remain unchanged: [tests / schema / type signature / invariant]
4. Evidence for that contract: [pointer]
5. Result actually easier to understand: YES/NO
6. Removes a useful abstraction/boundary/defensive mechanism: YES/NO
7. Behavior equivalence verifiable: YES/NO, [how]

**Verdict**: APPLY / NO REFACTOR REQUIRED
```

## Post-Refactor Verification Report (Template)

```markdown
### Post-Refactor Verification

- Behavior preserved: YES/NO/INCONCLUSIVE
- Complexity reduced: YES/NO
- Clarity improved: YES/NO/SUBJECTIVE
- Contract weakened: YES/NO
- Scope exceeded: YES/NO
- Tests/checks executed: [command] -> [result]
```

## NO REFACTOR REQUIRED Report (Template)

Use when the Simplification Test finds no justified change for a given breach.

```markdown
### No Refactor Required: [file:line or symbol]

**Metric breach observed**: [e.g. function is 47 lines]
**Simplification Test outcome**: [which question(s) failed and why]
**Decision**: Existing implementation retained. No structural change applied.
```

## Ledger Entry (Template)

```markdown
---

### Entry #[N]: REFACTOR

**Timestamp**: [ISO 8601]
**Phase**: IMPLEMENT (refactor)
**Author**: Specialist
**Scope mode**: [changeset / focused / component / explicit]
**Outcome**: [refactored / NO REFACTOR REQUIRED]

**Changes**:
- [summary of changes, or "none - see Simplification Test findings" for NO REFACTOR REQUIRED]

**Content Hash**:
```
SHA256(modified files)
= [hash]
```

**Previous Hash**: [from entry N-1]

**Chain Hash**:
```
SHA256(content_hash + previous_hash)
= [calculated]
```

**Decision**: KISS refactor complete. Section 4 compliance verified.
```

## Handoff Report (Template)

```markdown
## Refactor Complete

**Scope mode**: [changeset / focused / component / explicit]
**Scope**: [file or directory]
**Violations Fixed**: [count]
**NO REFACTOR REQUIRED findings**: [count]
**Files Modified**: [count]

### Changes Summary

| Change Type          | Count |
| -------------------- | ----- |
| Functions split      | [X]   |
| Nesting flattened    | [X]   |
| Variables renamed    | [X]   |
| Files split          | [X]   |
| Orphans removed      | [X]   |
| Dependencies removed | [X]   |

### Next Action

The Judge should invoke `/qor-substantiate` to verify and seal.

---

_Simplification complete. Awaiting substantiation._
```
