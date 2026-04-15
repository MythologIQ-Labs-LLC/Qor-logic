# UI Diagnosis Patterns Reference

## Failure Analysis Methodology

### Phase 1: Audit (Identify What is Broken)
1. Review design specs and intended behavior
2. Inventory all UI components that should exist
3. Test each component for actual behavior
4. Create gap matrix: Component x Intended Function x Actual Status
5. Categorize root causes (missing code, wrong types, broken integration)

### Phase 2: Plan (Prioritize Fixes)
1. Prioritize: P0 (blocks all use) > P1 (major features) > P2 (polish)
2. Map fix dependencies (what must be fixed first)
3. Identify surgical changes (minimal edits, maximum impact)
4. Define "done" criteria for each fix
5. Estimate hours per fix, identify critical path

### Phase 3: Fix (Execute Repairs)
1. Fix P0 blockers (data not flowing, components not rendering)
2. Fix P1 features (CRUD operations, navigation)
3. Fix P2 polish (animations, keyboard nav, accessibility)
4. Validate after each fix before proceeding

## Diagnostic Patterns

### Pattern 1: Component Renders But Shows No Data

**Symptoms**: UI shell appears, but content area is empty or shows placeholder

**Diagnosis Steps**:
1. Check browser DevTools console for errors
2. Check Network tab for API calls (are they being made?)
3. Add console.log before and after data fetch call
4. Verify response shape matches expected TypeScript type
5. Verify setState is called with correct data

**Common Root Causes**:
- Data fetch method never called (missing useEffect or event trigger)
- API response shape doesn't match TypeScript interface
- State not updating (setState missing, wrong key, async issue)
- Data mapping error (wrong field names in JSX)
- Bridge/IPC method called with wrong parameters

**Fix Strategy**: Trace the data flow from source to render, fix first break point

### Pattern 2: Button Clicks Do Nothing

**Symptoms**: Interactive elements are visible but produce no effect

**Diagnosis Steps**:
1. Inspect element: is onClick handler attached?
2. Is the handler function defined and implemented?
3. Check console for errors when clicking
4. Is the handler async? Check for unhandled promise rejections
5. Is the button disabled or covered by another element?

**Common Root Causes**:
- Event handler not attached (missing onClick prop)
- Handler calls undefined method
- Async handler not awaited (promise fails silently)
- Element overlapped by invisible div (z-index issue)
- Form submission intercepted by browser default behavior

**Fix Strategy**: Attach handler > implement body > add try-catch > add loading state

### Pattern 3: TypeScript Errors Blocking Compilation

**Symptoms**: Application won't build or hot-reload fails

**Diagnosis Steps**:
1. Read exact error messages (file, line, expected vs actual type)
2. Compare TypeScript interface against backend contract (backend is source of truth)
3. Check for missing imports
4. Look for required fields missing in request objects

**Common Root Causes**:
- Types don't match backend contracts
- Required fields missing in request objects
- Discriminated unions not narrowed properly
- Import paths broken after file moves

**Fix Strategy**:
- During active debugging: use `// @ts-expect-error` to unblock, add TODO
- After functionality restored: remove suppressions, fix types properly
- Never ship with suppressed type errors

### Pattern 4: Navigation Doesn't Work

**Symptoms**: Links or navigation elements don't change the view

**Diagnosis Steps**:
1. Check route configuration (router config file)
2. Verify path strings match exactly (case sensitive, leading slashes)
3. Ensure target component is imported and exported correctly
4. Check for auth guards blocking access

**Common Root Causes**:
- Route not registered in router config
- Path mismatch between link and route definition
- Component not imported or default/named export mismatch
- Auth middleware redirecting to login

### Pattern 5: Layout or Styling Broken

**Symptoms**: Elements overlap, disappear, or appear in wrong position

**Diagnosis Steps**:
1. Inspect computed styles in DevTools
2. Check for CSS class name mismatches (especially with CSS modules)
3. Look for conflicting styles (specificity issues)
4. Check responsive breakpoints
5. Verify parent container has expected dimensions

**Common Root Causes**:
- Missing or wrong CSS class names
- Flex/grid parent missing required properties
- Absolute positioning without relative parent
- Overflow hidden clipping content
- Z-index stacking context issues

### Pattern 6: State Not Persisting

**Symptoms**: Data disappears on navigation or refresh

**Diagnosis Steps**:
1. Is state stored in component (lost on unmount) vs global store?
2. Is persistence layer (localStorage, database) being written to?
3. Is data loaded on component mount?
4. Check for race conditions between save and load

**Common Root Causes**:
- State only in component, not persisted
- Save operation fails silently
- Load operation runs before save completes
- Wrong storage key (writing to key A, reading from key B)

## Correction Principles

### 1. Surgical Over Rewrite
- Fix the specific break point, not the entire module
- Three broken bridge calls are a 1-hour fix, not a full rewrite
- Ask: "What is the minimum change to restore functionality?"

### 2. Data Flow First
Debug in this order (stop at the first failure):
1. Does the backend work? (Test endpoint directly)
2. Does the bridge/API call reach the backend? (Check network tab)
3. Does the component receive the response? (Console.log after call)
4. Does the UI render the data? (Check JSX mapping)

### 3. Functionality Before Type Safety
During active correction:
- Use `// @ts-expect-error` to bypass blocking type errors
- Focus on runtime functionality first
- Return to fix types after functionality is verified

After correction:
- Remove all `@ts-expect-error` annotations
- Fix types to match backend contracts
- Run type checker to verify no new errors

### 4. Validate Incrementally
After each fix:
1. Test manually in browser
2. Check console for new errors
3. Verify no regressions in other features
4. Commit if fix works (atomic commits for safe rollback)

## Failure Audit Template

```
# UI Failure Audit: [Module Name]

## Design Intent
- Expected behavior: [what user should be able to do]
- Source docs: [links to specs]

## Actual Behavior
- Observed: [what actually happens]
- Evidence: [screenshots, console errors]

## Gap Analysis
| Component | Intended Function | Actual Status | Severity |
|-----------|-------------------|---------------|----------|
| [Name]    | [Function]        | [Status]      | P0/P1/P2 |

## Root Causes
### P0: Data Flow Failures
1. [Component]: [description of break]
   - File: [path:line]
   - Fix: [minimal change needed]
   - Effort: [time estimate]

### P1: Feature Gaps
[Same format]

### P2: Polish Issues
[Same format]

## Summary
- P0 (Critical): X issues, Y hours total
- P1 (High): X issues, Y hours total
- P2 (Medium): X issues, Y hours total
```

## Correction Plan Template

```
# UI Correction Plan: [Module Name]

## Summary
- Total issues: X
- Critical path: P0 (Yh) > P1 (Yh) > P2 (Yh)
- Success criteria: all intended functionality working

## Phase 1: Data Flow Restoration (P0)
### Fix 1.1: [Component] - [description] (Xm)
- File: [path]
- Problem: [what's wrong]
- Solution: [minimal change]
- Validation: [how to verify]

## Phase 2: Feature Completion (P1)
[Same format]

## Phase 3: Polish (P2)
[Same format]

## Rollback Plan
- Branch: fix/ui-correction-phase-N
- Checkpoint commits after each fix
- Revert: git revert [commit-sha]
```

## Success Criteria

- [ ] All components render without console errors
- [ ] Data flows from backend to UI correctly
- [ ] User can perform all intended CRUD operations
- [ ] Navigation works between all screens
- [ ] No new bugs introduced, existing tests still pass
- [ ] TypeScript errors reduced (not increased)
- [ ] Performance and accessibility not degraded
- [ ] Failure audit and correction plan delivered
- [ ] Remaining known issues and prevention recommendations documented
