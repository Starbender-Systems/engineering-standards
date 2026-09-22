# Dependency update

## When to use

Adding, removing, or updating libraries, tools, runtimes, or design assets.

## Preconditions

Current declarations, lock files, target versions, and compatibility information.

## Implementation steps

1. Read [dependencies](../standards/dependencies.md), [security](../standards/security.md), and [testing](../standards/testing.md).
2. Review compatibility changes and the reason for the update.
3. Update declarations and generated locks with the established tooling; inspect transitive changes.
4. Adapt affected code and documentation; keep unrelated upgrades separate where practical.

## Required validation

Restore from a clean environment where practical, build, and exercise affected integrations.

## Documentation requirements

Record old and new versions, migration notes, and unresolved advisories or licensing questions.

## Completion and handoff

Hand off the dependency diff, validation, compatibility impact, and remaining decisions.

## Rollback or recovery

Restore prior declarations and locks together; assess persistent data or generated artifacts before rollback.

