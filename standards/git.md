# Git and change history

<!-- authority: standard.git -->

## Purpose and scope

Repository changes, reviews, and history management.

## Rules

- Apply the [general change-scope rules](general.md#rules) when preparing commits.
- MUST avoid rewriting shared history or discarding changes without task authorization.
- SHOULD keep changes reviewable and explain intent, validation, and compatibility in the change description.
- MUST use the consumer repository's documented branch, commit, and merge conventions when they exist.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Choose branch protection, commit conventions, merge strategy, and review requirements per repository.

## Validation expectations

Inspect the final diff and status; verify no generated noise or unrelated files are included.

## Related workflows or skills

- [Code review](../workflows/code-review.md)
- [Release](../workflows/release.md)
