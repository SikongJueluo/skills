# Code craft standards

Shared quality bar for `code-craft` (writing code) and `code-craft-review` (reviewing it). Both apply it to the change in hand.

The target is not fewer lines. It is fewer concepts, assumptions, and hidden failure modes a reader must hold to trust the code. A branch, default, retry, wrapper, or layer earns its place by serving a fact about the current requirement or a real system boundary — not a gap in the author's knowledge.

## Evidence before code

| Uncertainty | Example | Response |
|---|---|---|
| System behavior: a real failure mode exists | network drop, malformed external payload, missing file, concurrent writer | handle it at the boundary |
| Author knowledge: the contract has not been checked | "maybe `getUser()` returns null" | read the definition, implementation, and tests; do not code the doubt |

- **Do not convert your own uncertainty into runtime complexity.** If you cannot name the failed case a guard serves and its consequence, you are not ready to write that guard.
- Find a contract in this order: the declaration and the implementation that establishes the guarantee; validation where data enters; tests that pin the behavior; docs and ADRs for intent. Callers show usage, not the guarantee.
- Comments, TODOs, and commit or PR descriptions are claims about the code, not evidence of its behavior. A comment that explains why a guard exists does not establish that the guard is needed.
- Trust guarantees already established inside the same trust domain — code that shares the same validation and invariants. Established means you can point to the code or test that enforces the invariant; a name, docstring, or convention alone is a lead. Verify data where it crosses into a new domain: network, disk, user input, subprocess, deserialized payload, hardware.
- Stop investigating when the decision is determined, not when the repository is understood. When a behavior-changing question stays open, report that specific unknown instead of coding around it.
- The bar is symmetric. Removing a guard also needs evidence: a contract, a test that pins the guarantee by asserting the behavior, or a simpler implementation that covers the same need. A test that merely avoids the case proves nothing, and the absence of a test or a caller says nothing about reachability.

## 1. Contract

- Rely on the narrowest stated guarantee. Check an invariant once, at the boundary that owns it; do not repeat the same check at every hop.
- Types and casts describe shape, not runtime truth. An external payload is unvalidated until the code that parses it says otherwise.
- When docs and code disagree, report the conflict: behavior is what callers actually get, while the doc may state the intended contract. Do not silently pick whichever side justifies more code.
- Duplicate-check test: a new check is redundant when the same path already established the guarantee and no new trust boundary sits between the two points.
- A function reachable from any path that lacks the validation owns its own check. A check is a duplicate only when every entry path already establishes the guarantee.

## 2. Error handling

- Classify the failure before handling it: normal absence (lookup miss, empty query), recoverable failure (retry with a bounded policy, fallback with defined semantics), or programmer error (fail fast, loudly).
- A handler does one stated thing: recover, translate, add context, or propagate. A default chosen only to keep the program running turns a failure into a false success.
- Fix the failure at its source when this change can reach it. A downstream default that makes the system look healthy treats the symptom, not the cause.
- Normal absence maps to a specific outcome where the code can recognize it: a missing directory becomes an empty list. A catch-all default that also swallows unexpected failures is not that outcome.
- If the failure will look exactly like the normal empty case to the caller, expose the difference or decide explicitly that they are the same outcome.
- Keep the original failure visible: chain the cause, log at the decision point, rethrow. A generic message that erases the specific error is not handling.
- When this code owns no recovery, use the project's existing propagation mechanism: exception, `Result`, error boundary, or log-and-rethrow.
- These are boundary duties, not over-defense: external input validation, resource cleanup, transaction rollback, concurrency and lifecycle guards. Keep them accurate rather than deleting them to simplify.

## 3. Control flow

- The main path reads top to bottom. Each branch condition maps to a distinct real case: requirement, contract, or confirmed failure.
- Prefer a clear sequence over a compressed expression that saves lines and costs a named concept. Concepts are the measure; line count is not.
- Early exits for preconditions are fine. Nesting depth is a symptom, not a rule; the defect is an unnecessary or unreachable branch.
- Keep one owner for each check and each state transition. Parallel flags or booleans that can disagree about the same state are a bug waiting to happen.

## 4. Naming and data

- Use the project's domain words. One concept keeps one name across the change.
- A name should read at the call site without the implementation. `result`, `data`, `tmp`, `handle`, and `manager` usually state nothing the type did not.
- Represent the states the domain actually has. Boolean parameters and stringly-typed modes hide state; use a named type or enum when the project has one.
- Return what the caller needs, not parallel out-parameters or sentinel values.
- Naming and structure findings still need a concrete cost: what a reader or caller will misread. Personal preference is not a finding.

## 5. Local abstraction

- An abstraction must hide a decision, name a concept, or centralize duplicated real work. Forwarding with no added meaning is a cost, not a layer.
- One call site is not a defect. A single-use helper earns its place when it names a domain concept the call site would otherwise re-derive, or keeps the caller readable; generalize when the second real variation exists.
- Configuration, flags, adapters, and compatibility branches need a current, named variation. "Might need it later" is not one.
- Remove-it test: delete the abstraction and reread the call site. If the call site becomes clearer, the abstraction had no job; if a real concept becomes unnamed, keep it.
- An abstraction that leaks its implementation — the caller must know internals to use it — is not hiding complexity.

## 6. Change scope

- Implement the requirement in front of you. New public parameters, extension points, migrations, and unrelated refactors wait for a requirement.
- Fix a neighboring defect only when the current change cannot be correct without it; otherwise report it.
- Compatibility needs a released or requested contract. Check the project's policy before removing published behavior, and do not invent one for futures that do not exist.
- A diff is not a place to demonstrate thoroughness. Unrelated cleanup makes the change harder to review and to revert.

## Comments

Project rules win: a comment policy, lint, waiver registry, or ownership rule is the local law. Where the project has none, this is the default.

- Add no ordinary explanatory comments: no new `#`/`//` commentary in function bodies, on individual statements, or to explain control flow. Code, types, tests, and the docstrings below carry the explanation.
- Short module, class, and function docstrings or declaration docs are allowed, not required, and are the only prose channel. Upper bounds, never quotas: 5 content lines for a module or file header, 3 for a class or function. In languages without docstrings, apply the same bound to the file's or declaration's doc comment.
- A docstring states the contract the signature cannot express: units or a coordinate system, ownership and lifetime, an external format, a constraint a reader could not reconstruct from the code or tests, or why the obvious alternative is wrong. It does not narrate the implementation.
- Long design history and experiment notes stay out of the code; when the project has a docs location, point to it instead.
- Keep comments true: fix or delete a comment the change makes false. Do not bulk-delete historical comments.
- Tool directives, license headers, linter suppressions, generated markers, type-checker pragmas, and issue-linked TODO markers are not explanatory comments; use them only as the tool or project requires.
- Do not satisfy the docstring bound by relocating the same explanation into Markdown, assertions, another file's comments, helper names, or long identifiers.
