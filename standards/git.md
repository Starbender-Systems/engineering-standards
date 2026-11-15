# Git and change history

<!-- authority: standard.git -->

## Purpose and scope

Repository changes, reviews, and history management.

## Rules

- Apply the [general change-scope rules](general.md#rules) when preparing commits.
- MUST avoid rewriting shared history or discarding changes without task authorization.
- MUST include a concise title and a nonempty summary body in every commit message, separated by a blank line. Summarize what changed and why; include relevant validation or compatibility details and scale the body to the change.
- SHOULD keep changes reviewable and explain intent, validation, and compatibility in the change description.
- MUST use the consumer repository's documented branch, commit, and merge conventions when they exist.
- GitHub repositories for applications with .NET and controller code MUST run GitHub Actions on every push and pull request. The workflow MUST build the application and expose distinct, stable checks for the .NET test suite and controller test suite.
- These repositories MUST protect `main` so changes require a pull request and the named .NET and controller checks both pass before merge.
- These repositories MUST configure Dependabot for NuGet, npm, and GitHub Actions dependencies. Dependabot updates MUST be submitted as pull requests to a protected integration branch so the required checks run before merge.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Choose any additional protected branches, commit conventions, merge strategy, and review requirements per repository.

## Validation expectations

Inspect the final diff and status; verify no generated noise or unrelated files are included. Check that each commit message's title and summary body accurately describe its changes.

## Related workflows or skills

- [Code review](../workflows/code-review.md)
- [GitHub repository setup](../workflows/github-repository-setup.md)
- [Release](../workflows/release.md)
