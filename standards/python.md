# Python engineering

<!-- authority: standard.python -->

## Purpose and scope

Python applications, automation, and libraries.

## Rules

- MUST use the repository's declared Python versions and isolate environment-specific dependencies.
- MUST use explicit encodings for maintained text files and platform-neutral path handling.
- SHOULD keep module imports free of external side effects and expose scripts through a main entry point.
- MUST preserve public interfaces and document changed runtime or dependency requirements.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Choose supported runtime versions and formatting, typing, and packaging tools per repository.

## Validation expectations

Run applicable tests and entry points on supported runtimes; exercise platform-sensitive behavior.

## Related workflows or skills

- [Feature development](../workflows/feature-development.md)
- [Dependency update](../workflows/dependency-update.md)
