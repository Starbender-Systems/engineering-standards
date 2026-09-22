# Architecture

<!-- authority: standard.architecture -->

## Purpose and scope

Application boundaries, interfaces, persistence, and design decisions.

## Rules

- MUST identify affected interfaces and compatibility expectations before changing contracts.
- SHOULD preserve existing architectural boundaries; propose a documented decision before introducing a new cross-cutting pattern.
- MUST document material alternatives, tradeoffs, data ownership, and failure behavior for significant design changes.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Decide when architecture decisions require a designated reviewer.

## Validation expectations

Review changed contracts and exercise affected integration boundaries.

## Related workflows or skills

- [Feature development](../workflows/feature-development.md)
