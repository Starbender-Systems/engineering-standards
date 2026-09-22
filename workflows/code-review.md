# Code review

## When to use

Reviewing a proposed change before integration.

## Preconditions

The diff, task intent, relevant repository instructions, and reported validation.

## Implementation steps

1. Read [general](../standards/general.md), [git](../standards/git.md), [testing](../standards/testing.md), and [security](../standards/security.md).
2. Compare the implementation with the requested behavior and affected contracts.
3. Inspect correctness, failure cases, regressions, and maintainability; verify significant claims where practical.
4. Prioritize actionable findings by impact and cite affected locations; distinguish findings from open questions.

## Required validation

Evaluate reported checks and independently verify risk-sensitive behavior when feasible.

## Documentation requirements

Document findings with concrete triggers and consequences, plus testing gaps.

## Completion and handoff

Report findings first; if none are found, state the scope reviewed and residual limits. Follow local merge authority.

## Rollback or recovery

If a review assumption proves wrong, update the finding and re-evaluate dependent conclusions.

