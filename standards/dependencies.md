# Dependencies

<!-- authority: standard.dependencies -->

## Purpose and scope

Libraries, build tools, runtime versions, and third-party assets.

## Rules

- MUST review the need, provenance, compatibility, and licensing implications of a new dependency or asset.
- MUST update dependency declarations and applicable lock files together using the repository's tooling.
- SHOULD prefer an existing supported dependency or platform capability when it meets the need.
- MUST document breaking changes, transitive changes, and unresolved advisories relevant to the update.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Decide dependency approval ownership, supported versions, update cadence, and advisory response targets.

## Validation expectations

Restore from declared versions, build, and exercise affected behavior; review the dependency diff.

## Related workflows or skills

- [Dependency update](../workflows/dependency-update.md)
