# Feature development

## When to use

Implementing a feature or intentional behavior change.

## Preconditions

Task acceptance criteria, repository instructions, current architecture, and runnable development commands.

## Implementation steps

1. Read [general](../standards/general.md), [architecture](../standards/architecture.md), [testing](../standards/testing.md), and [documentation](../standards/documentation.md) guidance plus applicable stack standards.
2. Inspect current behavior and identify affected contracts and acceptance criteria.
3. Implement the smallest coherent change and appropriate behavior checks.
4. Update affected usage and design documentation; review the complete diff.

## Required validation

Run the relevant repository build and tests, including affected boundary cases.

## Documentation requirements

Record changed behavior, decisions, and any new setup or operational steps.

## Completion and handoff

Report acceptance criteria met, changed files, validation evidence, and unresolved work.

## Rollback or recovery

Identify how to revert the change and whether persisted data or contracts require a separate recovery step.

