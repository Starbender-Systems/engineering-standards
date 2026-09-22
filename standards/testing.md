# Testing

<!-- authority: standard.testing -->

## Purpose and scope

Evidence for software changes, regressions, and test maintenance.

## Rules

- MUST choose validation based on changed behavior and failure risk, using the repository's established test commands.
- MUST cover a defect with a regression test when practical; otherwise record a reproducible verification procedure.
- SHOULD test public behavior and boundary conditions rather than mirror private implementation details.
- MUST report failed or unavailable checks separately from passing checks; a skipped check is not a pass.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Set repository-specific coverage targets, required suites, and ownership of flaky tests.

## Validation expectations

Run relevant checks and retain commands, outcomes, and material environment limitations.

## Related workflows or skills

- [Defect investigation](../workflows/defect-investigation.md)
- [Code review](../workflows/code-review.md)
