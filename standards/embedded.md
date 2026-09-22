# Embedded engineering

<!-- authority: standard.embedded -->

## Purpose and scope

Firmware and software interacting with physical hardware.

## Rules

- MUST identify board revision, toolchain, memory constraints, and relevant hardware interfaces before changing firmware.
- MUST document timing, concurrency, interrupt, and resource assumptions affected by a change.
- MUST distinguish simulation evidence from hardware measurements.
- MUST establish a recovery method before flashing or changing persistent device configuration.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Define hardware safety limits, qualified test fixtures, and firmware release ownership per product.

## Validation expectations

Build for the intended target; record timing or resource changes and relevant bench tests with hardware revision.

## Related workflows or skills

- [Feature development](../workflows/feature-development.md)
- [Release](../workflows/release.md)
