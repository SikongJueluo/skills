---
name: loop-iterate
description: Checks results against the previous loop's contract, repairs the project environment and harness, and connects to the next loop's definition. Use after a loop is implemented and accepted.
argument-hint: "[the loop just finished: task name or scope]"
---

# loop-iterate

Check results against the previous loop's contract, fix the friction it exposed in the environment, and connect to the next loop.

Read the code changes, test results, and execution records against the contract, and bring specific facts to the human rather than asking vaguely what went wrong.

Rework on the business side either folds into the next loop's contract or returns to `loop-discuss` for a new one; do not slip business code edits into the review. Repairs at the environment level, including toolchain friction, test blind spots, gaps in the project conventions, and defects in this skill set itself, are fixed and written down directly, not deferred to the next loop.

Revise the big circle only when new facts are enough to overturn the original direction; otherwise say explicitly that it stands. Gather the latest state and open items into a new starting point and move to `loop-discuss`.

## Review template

Append the review to the end of the previous loop's contract page, `docs/plan/<time-final-goal>/<n-minimum-closed-loop>.md`; do not create a separate document. Leave the contract body untouched. An acceptance criterion found wrong in hindsight is recorded in the review, not edited back, or the next loop loses its baseline.

```markdown
## Review

### Against expectations
* Met: <outputs that passed acceptance>
* Not met: <where it fell short, and why>
* Carried: <old debt folded into the next loop>

### Environment and harness
* <repairs landed or still open>

### Input to the next loop
* Big circle: <stands, or what it becomes>
* New starting point: <where to cut in>
```
