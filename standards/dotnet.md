# .NET engineering

<!-- authority: standard.dotnet -->

## Purpose and scope

Repositories using .NET, C#, and related build tooling.

## Rules

- MUST use the repository's declared SDK and target frameworks and preserve existing nullable and analyzer settings.
- MUST propagate cancellation through asynchronous operations where the calling contract supports it; avoid blocking waits on asynchronous work.
- MUST make resource lifetimes explicit and dispose owned disposable resources.
- SHOULD keep persistence concerns at established boundaries; schema changes MUST use the migration workflow.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Choose supported .NET versions, analyzer baselines, and formatting rules per repository.

## Validation expectations

Restore, build, and run affected tests with the declared SDK; review analyzer output and migration effects.

## Related workflows or skills

- [Feature development](../workflows/feature-development.md)
- [Entity Framework migration](../workflows/ef-migration.md)
