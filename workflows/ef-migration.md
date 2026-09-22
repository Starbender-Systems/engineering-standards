# Entity Framework migration

## When to use

Changing a schema managed by Entity Framework migrations.

## Preconditions

DbContext, provider and EF tooling versions, intended schema change, and target environment.

## Implementation steps

1. Read [.NET](../standards/dotnet.md), [architecture](../standards/architecture.md), [testing](../standards/testing.md), and [security](../standards/security.md).
2. Inspect current migrations and schema assumptions; identify data transformations and compatibility windows.
3. Generate the migration using repository commands and inspect it and the model snapshot for unintended operations.
4. Test upgrade on a disposable representative database; assess locks, data loss, and application compatibility.
5. Prepare deployment and recovery instructions before any persistent environment change.

## Required validation

Build and test affected persistence behavior; test fresh creation and upgrade from the supported prior schema.

## Documentation requirements

Record provider, migration identifiers, generated SQL review, data impact, and recovery limits.

## Completion and handoff

Report code readiness separately from database deployment; retain existing authorization boundaries.

## Rollback or recovery

Test reversal only when safe; otherwise document backup restore or forward repair and its data implications.

