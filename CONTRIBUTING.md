# Contributing

Read the [repository instructions](AGENTS.md) and [versioning policy](README.md#versioning).

## Ownership and review

Propose changes through a reviewable pull request. Explain the problem, affected consumers, intended behavior, validation, and compatibility impact. Ask maintainers of affected stacks to review meaningful behavior changes using the existing repository review process.

TODO: Name shared and stack-specific owners in [CODEOWNERS](.github/CODEOWNERS), and decide required reviewers and approval counts. Until assigned, do not imply that placeholder entries establish approval.

## Single authority

Put standing rules in the relevant standard. Workflows link to those rules; skills route to workflows; adapters and prompts route to the shared core. Keep application commands and constraints in consumers.

Each authoritative standard carries one HTML comment marker of the form `<!-- authority: standard.example -->` (example). The validator rejects duplicate marker identifiers outside fenced examples. References must use links, not copied markers. This catches explicitly marked duplicate authority; semantic duplicates still require human review.

## Compatibility and releases

Classify the change under the [semantic versioning policy](README.md#versioning). Describe the previous and new behavior and provide consumer migration steps for incompatible changes. Do not treat a new mandatory rule as a wording-only patch.

For release preparation, update VERSION, source catalog release, bootstrap manifest/VERSION, and changelog together. Validate using a temporary consumer and repeat sync/check. Published releases must remain immutable.

## Validation and handoff

Run the validator and standard-library tests documented in the README. Add behavioral tests when changing synchronization safety, schema handling, or validation failures. Check shared links remain inside the shared snapshot and templates work both here and at their consumer destinations.

Report commands and actual outcomes, including unavailable checks. Include remaining TODO decisions. Preserve unrelated work and the existing license.
